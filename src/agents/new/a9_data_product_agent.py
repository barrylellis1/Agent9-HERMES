"""
A9_Data_Product_Agent - Centralized data access for data products.

This agent provides a standardized interface for data access operations,
acting as the single authoritative layer for all dynamic SQL generation
using registry-driven SELECT, JOIN, GROUP BY, and aggregation SQL.

It is designed to provide business-ready, summarized, filtered, and pre-joined
data products to other agents and services within the system.

Protocol compliance:
- Explicitly implements DataProductProtocol
- All request/response models inherit from A9AgentBaseModel
- Factory method pattern for orchestrator-driven lifecycle
- Standardized error handling and logging
- Protocol-compliant request/response models
"""

import asyncio
import datetime
import json
import logging
import os
import re
import time
import traceback
import uuid
from typing import Dict, Any, List, Optional, Union, Tuple, ClassVar, Set
from dotenv import load_dotenv
import yaml

from src.agents.agent_config_models import A9_Data_Product_Agent_Config
from src.agents.protocols.data_product_protocol import DataProductProtocol
from src.agents.shared.a9_agent_base_model import A9AgentBaseModel
from src.database.backends.duckdb_manager import DuckDBManager
from src.database.manager_factory import DatabaseManagerFactory
from src.registry.factory import RegistryFactory
from src.registry.providers.data_product_provider import DataProductProvider
from src.registry.providers.kpi_provider import KPIProvider
# Import shared SQL execution models
from src.agents.models.sql_models import SQLExecutionRequest, SQLExecutionResponse
# ViewProvider not available in current codebase

# Business glossary (neutral term mapping)
from src.registry.providers.business_glossary_provider import BusinessGlossaryProvider
from src.agents.models.data_governance_models import KPIViewNameRequest
from src.agents.a9_llm_service_agent import A9_LLM_SQLGenerationRequest
from src.agents.models.data_product_onboarding_models import (
    DataProductSchemaInspectionRequest,
    DataProductSchemaInspectionResponse,
    DataProductContractGenerationRequest,
    DataProductContractGenerationResponse,
    DataProductRegistrationRequest,
    DataProductRegistrationResponse,
    DataProductQARequest,
    DataProductQAResponse,
    TableProfile,
    TableColumnProfile,
    ForeignKeyRelationship,
    KPIProposal,
    QAResult,
    ValidateKPIQueriesRequest,
    ValidateKPIQueriesResponse,
    KPIQueryValidationResult,
)

try:  # Optional dependency for admin console defaults
    from src.config.connection_profiles import get_active_profile  # type: ignore
except Exception:  # pragma: no cover - optional component
    get_active_profile = None  # type: ignore

logger = logging.getLogger(__name__)

# Ensure .env is loaded so runtime feature flags are available (e.g., A9_ENABLE_LLM_SQL)
try:
    load_dotenv()
except Exception:
    # Non-fatal if dotenv is missing; env vars may still be set by the host
    pass

class A9_Data_Product_Agent(DataProductProtocol):
    """
    Data Product Agent - Implements DataProductProtocol
    
    This agent is responsible for:
    - Managing data products and their metadata
    - Generating SQL for data access
    - Creating and managing views
    - Executing SQL queries
    - Providing data to other agents
    """
    
    @classmethod
    async def create(cls, config: Dict[str, Any], logger: Optional[logging.Logger] = None) -> 'A9_Data_Product_Agent':
        """
        Factory method to create and initialize a Data Product Agent.
        
        Args:
            config: Configuration dictionary
            logger: Optional logger instance to use
            
        Returns:
            Initialized Data Product Agent
        """
        # Create instance
        instance = cls(config)
        
        # Set custom logger if provided
        if logger:
            instance.logger = logger
        
        # Initialize async resources
        await instance._async_init()
        
        return instance
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Data Product Agent.
        
        Args:
            config: Configuration dictionary
        """
        # Parse config
        self.config = A9_Data_Product_Agent_Config(**config)
        
        # Set up logging
        self.logger = logger
        
        # Initialize database path
        self.data_directory = config.get('data_directory', 'data')
        db_config = config.get('database', {})
        db_type = db_config.get('type', 'duckdb')
        db_path = db_config.get('path', f"agent9-hermes.duckdb")
        
        # Ensure we don't double-include the data directory
        if os.path.dirname(db_path) == self.data_directory:
            self.db_path = db_path
        else:
            self.db_path = os.path.join(self.data_directory, os.path.basename(db_path))
        self.logger.info(f"Initializing database connection with type: {db_type}, path: {self.db_path}")
        
        # Initialize database manager
        self.db_manager = DuckDBManager({'type': db_type, 'path': self.db_path}, logger=self.logger)
        self.is_connected = False
        self.logger.info("Database connection initialized successfully")
        # Cached BigQuery manager — created on first BigQuery SQL execution
        self._bq_manager = None
        
        # MCP Service Agent will be initialized in _async_init
        self.mcp_service_agent = None
        
        # Store orchestrator reference if provided in config
        self.orchestrator = config.get('orchestrator')
        if self.orchestrator:
            self.logger.info("Orchestrator reference stored from config")
        else:
            self.logger.warning("No orchestrator provided in config")
        
        # Allow tests or callers to inject a pre-configured LLM Service Agent
        self.llm_service_agent = config.get('llm_service_agent')
        if self.llm_service_agent:
            self.logger.info("Using pre-configured LLM Service Agent instance from config")
        
        # Initialize registry providers
        self.registry_factory = config.get('registry_factory') or RegistryFactory()

        self.data_product_provider = self.registry_factory.get_provider("data_product")
        if self.data_product_provider is None:
            self.data_product_provider = self.registry_factory.get_data_product_provider()

        self.kpi_provider = self.registry_factory.get_provider("kpi")
        if self.kpi_provider is None:
            self.kpi_provider = self.registry_factory.get_kpi_provider()
        self.logger.info("Registry providers initialized successfully")

        # Bypass MCP toggle (config or env), defaults to False
        try:
            import os as _os
            cfg_bypass = bool(config.get('bypass_mcp', False))
            env_bypass = str(_os.environ.get('A9_BYPASS_MCP', 'false')).lower() in ('1','true','yes','y','on')
            self.bypass_mcp = cfg_bypass or env_bypass
            if self.bypass_mcp:
                self.logger.warning("[A9_BYPASS_MCP] MCP delegation is bypassed; executing queries directly via DuckDBManager")
        except Exception:
            self.bypass_mcp = False

        # Registry will be loaded in _async_init after database connection is established
        # Cache for exposed columns per view (to avoid repeated YAML reads)
        self._view_exposed_columns_cache: Dict[str, Set[str]] = {}
    
    async def _async_init(self):
        """Initialize async resources."""
        # Connect to the database
        try:
            success = await self.db_manager.connect({'database_path': self.db_path})
            if success:
                self.is_connected = True
                self.logger.info(f"Connected to database at {self.db_path}")
                # Ensure shared Time Dimension exists for consistent timeframe handling
                try:
                    await self._ensure_time_dimension()
                    self.logger.info("Time Dimension ensured (table: time_dim)")
                except Exception as td_err:
                    self.logger.warning(f"Failed to ensure Time Dimension: {td_err}")
                # Load registry after successful connection
                await self._load_registry()
            else:
                self.logger.warning(f"Failed to connect to database at {self.db_path}, continuing with limited functionality")
                self.is_connected = False
        except Exception as e:
            self.logger.warning(f"Database connection error: {str(e)}, continuing with limited functionality")
            self.is_connected = False
        
        # No MCP Service Agent in MVP path; execution is handled via DuckDBManager directly
            
        # Initialize Data Governance Agent connection - do this regardless of database connection status
        try:
            self.logger.info("Initializing Data Governance Agent connection")
            # Get the orchestrator if available
            if hasattr(self, 'orchestrator') and self.orchestrator:
                self.data_governance_agent = await self.orchestrator.get_agent("A9_Data_Governance_Agent")
                if self.data_governance_agent:
                    self.logger.info("Successfully connected to Data Governance Agent via orchestrator")
                else:
                    self.logger.warning("Data Governance Agent not found in orchestrator")
            else:
                self.logger.warning("Orchestrator not available for Data Governance Agent connection")
        except Exception as e:
            self.logger.error(f"Error connecting to Data Governance Agent: {str(e)}")
            self.logger.warning("Will use fallback view name resolution")
            # Ensure the attribute exists even if connection failed
            self.data_governance_agent = None

        # Initialize LLM Service Agent connection (optional)
        try:
            self.logger.info("Initializing LLM Service Agent connection")
            if not getattr(self, 'llm_service_agent', None):
                if hasattr(self, 'orchestrator') and self.orchestrator:
                    try:
                        # Request LLM Service Agent from registry
                        self.llm_service_agent = await self.orchestrator.get_agent("A9_LLM_Service_Agent")
                    except Exception:
                        self.llm_service_agent = None
                    if not getattr(self, 'llm_service_agent', None):
                        try:
                            from src.agents.a9_llm_service_agent import A9_LLM_Service_Agent
                            self.llm_service_agent = await A9_LLM_Service_Agent.create({})
                            try:
                                await self.orchestrator.register_agent("A9_LLM_Service_Agent", self.llm_service_agent)
                            except Exception:
                                pass
                            self.logger.info("Successfully created and registered LLM Service Agent (OpenAI)")
                        except Exception as create_err:
                            self.logger.warning(f"LLM Service Agent unavailable: {str(create_err)}")
                            self.llm_service_agent = None
                else:
                    self.logger.warning("Orchestrator not available for LLM Service Agent connection")
            else:
                self.logger.info("Using pre-configured LLM Service Agent instance")
        except Exception as e:
            self.logger.error(f"Error connecting to LLM Service Agent: {str(e)}")
    
    async def _ensure_db_connected(self) -> bool:
        """
        Ensure the embedded DuckDB connection is available. Establish a lazy connection
        if one is not already present. Returns True when connected.
        """
        try:
            # If DB manager is missing, we cannot proceed
            if not hasattr(self, 'db_manager') or self.db_manager is None:
                return False
            # If a connection already exists, we're good
            if getattr(self.db_manager, 'duckdb_conn', None) is not None:
                return True
            # Attempt to connect lazily
            ok = await self.db_manager.connect({'database_path': self.db_path})
            if ok:
                self.is_connected = True
                # Best-effort: ensure time dimension exists for timeframe filters
                try:
                    await self._ensure_time_dimension()
                except Exception as td_err:
                    self.logger.warning(f"Failed to ensure Time Dimension (lazy): {td_err}")
                return True
            self.logger.warning("DuckDB connection attempt failed in _ensure_db_connected")
            return False
        except Exception as e:
            self.logger.warning(f"_ensure_db_connected error: {e}")
            return False

    async def _ensure_time_dimension(self) -> None:
        """
        Create and populate a shared Time Dimension table (time_dim) for consistent timeframe handling.
        Range: 2021-01-01 through 2026-12-31.
        Fiscal attributes are computed using configurable fiscal_year_start_month (default January).
        """
        try:
            # Read fiscal start month from config (default 1)
            try:
                fsm = int(getattr(self.config, 'fiscal_year_start_month', 1) or 1)
            except Exception:
                fsm = 1
            if fsm < 1 or fsm > 12:
                fsm = 1

            create_sql = f"""
                CREATE OR REPLACE TABLE time_dim AS
                WITH bounds AS (
                    SELECT DATE '2021-01-01' AS start_date, DATE '2030-12-31' AS end_date
                ), series AS (
                    SELECT start_date + gs*INTERVAL 1 DAY AS dt
                    FROM bounds, generate_series(0, DATEDIFF('day', start_date, end_date)) AS s(gs)
                )
                SELECT
                    CAST(dt AS DATE) AS "date",
                    EXTRACT(year FROM dt) AS year,
                    EXTRACT(quarter FROM dt) AS quarter,
                    EXTRACT(month FROM dt) AS month,
                    EXTRACT(isodow FROM dt) AS day_of_week,
                    DATE_TRUNC('quarter', dt) AS quarter_start,
                    DATE_TRUNC('month', dt) AS month_start,
                    DATE_TRUNC('quarter', dt) + INTERVAL '3 months' - INTERVAL '1 day' AS quarter_end,
                    DATE_TRUNC('month', dt) + INTERVAL '1 month' - INTERVAL '1 day' AS month_end,
                    -- Fiscal attributes derived from configured start month
                    CASE WHEN EXTRACT(month FROM dt) >= {fsm}
                         THEN EXTRACT(year FROM dt)
                         ELSE EXTRACT(year FROM dt) - 1 END AS fiscal_year,
                    CAST(FLOOR(((( (CAST(EXTRACT(month FROM dt) AS INTEGER) - {fsm} + 12) % 12) + 1 ) - 1) / 3.0) + 1 AS INTEGER) AS fiscal_quarter
                FROM series;
            """
            await self.db_manager.execute_query(create_sql, {}, str(uuid.uuid4()))
            # Create an index for faster joins
            try:
                await self.db_manager.execute_query("CREATE INDEX IF NOT EXISTS idx_time_dim_date ON time_dim(\"date\");", {}, str(uuid.uuid4()))
            except Exception:
                pass
        except Exception as e:
            self.logger.warning(f"_ensure_time_dimension failed: {e}")
    
    async def _load_registry(self):
        """Load data product registry metadata only, not all products."""
        transaction_id = str(uuid.uuid4())
        registry_path = self.config.registry_path
        
        # Store registry path for later selective loading
        self._registry_path = registry_path
        self._registry_data = None
        
        if registry_path:
            self.logger.info(f"[TXN:{transaction_id}] Initializing data product registry from: {registry_path}")
            # Check if registry_path is a directory or file
            if os.path.isdir(registry_path):
                # If it's a directory, look for data_product_registry.yaml
                yaml_path = os.path.join(registry_path, "data_product_registry.yaml")
                if os.path.exists(yaml_path):
                    self.logger.info(f"[TXN:{transaction_id}] Found data product registry at {yaml_path}")
                    try:
                        # Load the YAML file directly but don't register products yet
                        import yaml
                        with open(yaml_path, 'r') as f:
                            data = yaml.safe_load(f)
                            
                        # Store registry data for later selective loading
                        if isinstance(data, dict) and 'data_products' in data:
                            self._registry_data = data
                            self.logger.info(f"[TXN:{transaction_id}] Registry metadata loaded with {len(data['data_products'])} data products available")
                        else:
                            self.logger.warning(f"[TXN:{transaction_id}] Registry file format not recognized")
                        
                        # Auto-hydrate tables and views for local development
                        # This ensures that if raw CSVs exist (as defined in contracts), they are loaded
                        # and Views are created, without requiring manual onboarding steps.
                        if self._registry_data and 'data_products' in self._registry_data:
                            self.logger.info(f"[TXN:{transaction_id}] Auto-hydrating data products for local dev...")
                            for dp in self._registry_data['data_products']:
                                try:
                                    # Support both keys for flexibility
                                    contract_path = dp.get('yaml_contract_path') or dp.get('contract_path')
                                    
                                    # Handle relative paths from project root if needed
                                    if contract_path and not os.path.isabs(contract_path) and not os.path.exists(contract_path):
                                        # Try resolving relative to CWD (Project Root) or Registry Path
                                        # But usually CWD is project root.
                                        pass 

                                    if contract_path and os.path.exists(contract_path):
                                        self.logger.info(f"Auto-hydrating product {dp.get('product_id')} from {contract_path}")
                                        # 1. Register Source Tables
                                        await self.register_tables_from_contract(contract_path)
                                        
                                        # 2. Create Views
                                        # We need to peek into the contract to find view names
                                        with open(contract_path, 'r') as cf:
                                            c_data = yaml.safe_load(cf)
                                            views = c_data.get('views', [])
                                            for v in views:
                                                v_name = v.get('name')
                                                if v_name:
                                                    await self.create_view_from_contract(contract_path, v_name)
                                except Exception as hydrate_err:
                                    self.logger.warning(f"Auto-hydration failed for {dp.get('product_id')}: {hydrate_err}")

                    except Exception as e:
                        self.logger.error(f"[TXN:{transaction_id}] Error loading registry metadata: {str(e)}")
                else:
                    self.logger.warning(f"[TXN:{transaction_id}] No data_product_registry.yaml found in {registry_path}")
            else:
                # If it's a file, store the path for later
                self._registry_file_path = registry_path
                self.logger.info(f"[TXN:{transaction_id}] Registry file path stored for selective loading")
        else:
            self.logger.warning(f"[TXN:{transaction_id}] No registry path specified. In an enterprise environment, data products must be properly registered.")
            # No default data products in enterprise environment
    
    async def load_data_products_for_principal(self, principal_context):
        """Load data products selectively based on principal context."""
        transaction_id = str(uuid.uuid4())
        self.logger.info(f"[TXN:{transaction_id}] Loading data products for principal: {getattr(principal_context, 'principal_id', 'unknown')}")
        
        # Extract relevant domains and business processes from principal context
        domains = []
        business_processes = []
        
        # Extract domain from role if available
        if hasattr(principal_context, 'role'):
            role = principal_context.role
            if isinstance(role, str):
                # Simple heuristic: first word of role is often the domain
                domains.append(role.split()[0])
        
        # Extract business processes
        if hasattr(principal_context, 'business_processes'):
            bps = principal_context.business_processes
            if isinstance(bps, list):
                for bp in bps:
                    if isinstance(bp, str):
                        business_processes.append(bp)
                    elif hasattr(bp, 'name'):
                        business_processes.append(bp.name)
                    elif hasattr(bp, 'id'):
                        business_processes.append(bp.id)
        
        # Make domains and business processes unique and case-insensitive
        domains = [d.lower() for d in domains]
        business_processes = [bp.lower() for bp in business_processes]
        
        self.logger.info(f"[TXN:{transaction_id}] Relevant domains: {domains}")
        self.logger.info(f"[TXN:{transaction_id}] Relevant business processes: {business_processes}")
        
        # Load data products from registry data
        if self._registry_data and 'data_products' in self._registry_data:
            loaded_count = 0
            for dp in self._registry_data['data_products']:
                should_load = False
                
                # Check if data product matches any relevant domain
                if 'domain' in dp and any(dp['domain'].lower() == d for d in domains):
                    should_load = True
                
                # Check if data product is related to any relevant business process
                if 'related_business_processes' in dp and isinstance(dp['related_business_processes'], list):
                    dp_bps = [bp.lower() for bp in dp['related_business_processes']]
                    if any(bp in dp_bps for bp in business_processes):
                        should_load = True
                
                # Always load FI data products for now (temporary until all mappings are complete)
                if 'product_id' in dp and 'fi' in dp['product_id'].lower():
                    should_load = True
                
                # Load the data product if relevant
                if should_load and 'product_id' in dp:
                    self.logger.info(f"[TXN:{transaction_id}] Loading relevant data product: {dp['product_id']}")
                    from src.registry.models.data_product import DataProduct
                    try:
                        # Set id to product_id if id is not present
                        if 'id' not in dp and 'product_id' in dp:
                            dp['id'] = dp['product_id']
                        
                        # Add required fields if missing
                        if 'owner' not in dp:
                            # Extract domain from name or use default
                            domain = None
                            if 'domain' in dp:
                                domain = dp['domain']
                            elif 'name' in dp and ':' in dp['name']:
                                domain = dp['name'].split(':', 1)[0].strip()
                            else:
                                # Try to extract domain from product_id
                                if 'product_id' in dp:
                                    parts = dp['product_id'].split('_')
                                    if len(parts) > 1:
                                        domain = parts[1].upper()
                            
                            # Set default owner based on domain
                            if domain:
                                dp['owner'] = f"{domain} Team"
                            else:
                                dp['owner'] = "Enterprise Data Team"
                        
                        # Add other required fields if missing
                        if 'domain' not in dp and 'owner' in dp:
                            # Extract domain from owner if possible
                            if ' Team' in dp['owner']:
                                dp['domain'] = dp['owner'].replace(' Team', '')
                            else:
                                dp['domain'] = "Enterprise"
                                
                        data_product = DataProduct(**dp)
                        self.data_product_provider.register(data_product)
                        loaded_count += 1
                    except Exception as e:
                        self.logger.error(f"[TXN:{transaction_id}] Error creating DataProduct: {str(e)}")
                        # Try a simpler approach
                        try:
                            self.data_product_provider._add_data_product(dp)
                            loaded_count += 1
                        except Exception as e2:
                            self.logger.error(f"[TXN:{transaction_id}] Error adding data product: {str(e2)}")
            
            self.logger.info(f"[TXN:{transaction_id}] Loaded {loaded_count} relevant data products for principal")
        else:
            self.logger.warning(f"[TXN:{transaction_id}] No registry data available for selective loading")
            # Fall back to loading all data products
            if hasattr(self, '_registry_path') and self._registry_path:
                self.logger.info(f"[TXN:{transaction_id}] Falling back to loading all data products")
                if os.path.isdir(self._registry_path):
                    yaml_path = os.path.join(self._registry_path, "data_product_registry.yaml")
                    if os.path.exists(yaml_path):
                        self.data_product_provider.load_from_yaml(yaml_path)
                else:
                    self.data_product_provider.load_from_yaml(self._registry_path)
        
        # Log registry status with detailed information
        data_products = self.data_product_provider.get_all()
        has_data_products = len(data_products) > 0
        
        if has_data_products:
            self.logger.info(f"[TXN:{transaction_id}] Registry status: has_data_products=True")
            self.logger.info(f"Data Product Agent initialized with {len(data_products)} data products")
            # Log each data product for debugging
            for dp in data_products:
                # Handle both dict and DataProduct objects
                if isinstance(dp, dict):
                    dp_id = dp.get('product_id', dp.get('id', 'unknown'))
                    dp_name = dp.get('name', 'unnamed')
                else:
                    # For DataProduct objects
                    dp_id = getattr(dp, 'id', getattr(dp, 'product_id', 'unknown'))
                    dp_name = getattr(dp, 'name', 'unnamed')
                self.logger.info(f"[TXN:{transaction_id}] Loaded data product: {dp_id} - {dp_name}")
        else:
            self.logger.warning(f"[TXN:{transaction_id}] No data products found in registry. Please use Data Product and Data Governance Agents to onboard new data products.")
            self.logger.info(f"Data Product Agent initialized with 0 data products")
            # Log provider details for debugging
            self.logger.info(f"[TXN:{transaction_id}] Data product provider: {self.data_product_provider.__class__.__name__}")
            self.logger.info(f"[TXN:{transaction_id}] Registry path: {registry_path}")
            if os.path.exists(registry_path):
                if os.path.isdir(registry_path):
                    yaml_path = os.path.join(registry_path, "data_product_registry.yaml")
                    self.logger.info(f"[TXN:{transaction_id}] YAML path exists: {os.path.exists(yaml_path)}")
                    if os.path.exists(yaml_path):
                        with open(yaml_path, 'r') as f:
                            self.logger.info(f"[TXN:{transaction_id}] YAML content length: {len(f.read())} bytes")
                else:
                    self.logger.info(f"[TXN:{transaction_id}] Registry path is a file")
            else:
                self.logger.warning(f"[TXN:{transaction_id}] Registry path does not exist: {registry_path}")
    
    # The _load_default_data_products method has been removed as it's not appropriate for an enterprise environment
    # In an enterprise setting, data products must be properly registered through the Data Product and Data Governance Agents
    
    def _get_data_product_by_id(self, data_product_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a data product by ID.
        
        Args:
            data_product_id: ID of the data product to retrieve
            
        Returns:
            Data product dictionary if found, None otherwise
        """
        if not self.data_product_provider:
            return None
        
        return self.data_product_provider.get(data_product_id)
    
    async def get_data_product(self, data_product_id: str) -> Dict[str, Any]:
        """
        Get a data product by ID.
        
        Args:
            data_product_id: ID of the data product to retrieve
            
        Returns:
            Dictionary with data product information and status
        """
        transaction_id = str(uuid.uuid4())
        self.logger.info(f"[TXN:{transaction_id}] Getting data product: {data_product_id}")
        
        # Get the data product
        data_product = self._get_data_product_by_id(data_product_id)
        
        # Return in protocol-compliant format
        if data_product:
            self.logger.info(f"[TXN:{transaction_id}] Data product {data_product_id} found")
            return {
                "success": True,
                "message": f"Data product {data_product_id} found",
                "data_product": data_product
            }
        else:
            self.logger.warning(f"[TXN:{transaction_id}] Data product {data_product_id} not found")
            return {
                "success": False,
                "message": f"Data product {data_product_id} not found",
                "data_product": None
            }
    
    async def list_data_products(self) -> Dict[str, Any]:
        """
        List available data products from the registry provider.
        Returns a protocol-compliant dict with data_products list.
        """
        transaction_id = str(uuid.uuid4())
        try:
            self.logger.info(f"[LLM_SQL] ENTER generate_sql txn={transaction_id} has_llm_agent={getattr(self, 'llm_service_agent', None) is not None}")
        except Exception:
            pass
        try:
            items = self.data_product_provider.get_all() if self.data_product_provider else []
            data_products: List[Dict[str, Any]] = []
            for dp in items:
                try:
                    if hasattr(dp, 'model_dump'):
                        data_products.append(dp.model_dump())
                    elif isinstance(dp, dict):
                        data_products.append(dp)
                    else:
                        data_products.append({
                            "id": getattr(dp, "id", getattr(dp, "product_id", None)),
                            "name": getattr(dp, "name", None),
                            "domain": getattr(dp, "domain", None)
                        })
                except Exception:
                    continue
            return {
                "success": True,
                "message": f"Found {len(data_products)} data products",
                "data_products": data_products
            }
        except Exception as e:
            self.logger.error(f"[TXN:{transaction_id}] list_data_products error: {str(e)}\n{traceback.format_exc()}")
            return {
                "success": False,
                "message": str(e),
                "data_products": []
            }

    # ------------------------------------------------------------------
    # Data Product Onboarding entrypoints
    # ------------------------------------------------------------------

    async def inspect_source_schema(
        self, request: DataProductSchemaInspectionRequest
    ) -> DataProductSchemaInspectionResponse:
        """Profile tables/columns from a source schema for onboarding."""

        request_id = request.request_id
        tables: List[TableProfile] = []
        inferred_kpis: List[KPIProposal] = []
        warnings: List[str] = []
        blockers: List[str] = []
        inspection_metadata: Dict[str, Any] = {}

        settings = self._resolve_inspection_settings(request)
        source_system = settings["source_system"]
        inspection_metadata["source_system"] = source_system
        if settings.get("schema"):
            inspection_metadata["schema"] = settings["schema"]
        if settings.get("project"):
            inspection_metadata["project"] = settings["project"]

        try:
            inspection_manager, cleanup_needed = await self._prepare_inspection_manager(settings)
        except Exception as conn_err:
            msg = f"Unable to connect to {source_system}: {conn_err}"
            blockers.append(msg)
            return DataProductSchemaInspectionResponse.error(
                request_id=request_id,
                error_message=msg,
                environment=request.environment,
                tables=tables,
                inferred_kpis=inferred_kpis,
                warnings=warnings,
                blockers=blockers,
                inspection_metadata=inspection_metadata,
            )

        try:
            try:
                table_names = await self._discover_tables_for_inspection(
                    inspection_manager,
                    settings,
                )
                if not table_names:
                    warnings.append("No tables or views discovered for inspection")
            except Exception as discover_err:
                msg = f"Failed to enumerate objects for inspection: {discover_err}"
                blockers.append(msg)
                return DataProductSchemaInspectionResponse.error(
                    request_id=request_id,
                    error_message=msg,
                    environment=request.environment,
                    tables=tables,
                    inferred_kpis=inferred_kpis,
                    warnings=warnings,
                    blockers=blockers,
                    inspection_metadata=inspection_metadata,
                )

            # Profile each table/view using the resolved backend
            for table_name in table_names:
                try:
                    profile = await self._profile_table(
                        inspection_manager=inspection_manager,
                        table_name=table_name,
                        settings=settings,
                    )
                    if profile:
                        tables.append(profile)
                except Exception as profile_err:
                    warnings.append(f"Failed to profile {table_name}: {profile_err}")

            # Infer KPI candidates from measures/dimensions heuristics
            inferred_kpis = self._infer_kpis_from_profiles(tables)
            inspection_metadata["table_count"] = len(tables)

            return DataProductSchemaInspectionResponse.success(
                request_id=request_id,
                environment=request.environment,
                tables=tables,
                inferred_kpis=inferred_kpis,
                warnings=warnings,
                blockers=blockers,
                inspection_metadata=inspection_metadata,
            )
        except Exception as err:
            self.logger.error(f"Schema inspection error: {err}\n{traceback.format_exc()}")
            return DataProductSchemaInspectionResponse.error(
                request_id=request_id,
                error_message=str(err),
                environment=request.environment,
                tables=tables,
                inferred_kpis=inferred_kpis,
                warnings=warnings,
                blockers=blockers or ["Unexpected error"],
                inspection_metadata=inspection_metadata,
            )
        finally:
            if "cleanup_needed" in locals() and cleanup_needed:
                try:
                    await inspection_manager.disconnect()
                except Exception:
                    pass

    async def generate_contract_yaml(
        self, request: DataProductContractGenerationRequest
    ) -> DataProductContractGenerationResponse:
        """Generate a YAML contract from inspection results and overrides."""

        request_id = request.request_id
        try:
            contract_dict = self._build_contract_dict(
                data_product_id=request.data_product_id,
                schema_summary=request.schema_summary,
                kpi_proposals=request.kpi_proposals,
                overrides=request.contract_overrides,
            )
            contract_yaml = yaml.safe_dump(
                contract_dict, sort_keys=False, allow_unicode=True
            )

            contract_path: Optional[str] = None
            if request.target_contract_path:
                try:
                    contract_path = self._persist_contract_yaml(
                        request.target_contract_path, contract_yaml
                    )
                except Exception as persist_err:
                    return DataProductContractGenerationResponse.error(
                        request_id=request_id,
                        error_message=f"Failed to write contract YAML: {persist_err}",
                        contract_yaml=contract_yaml,
                        contract_path=None,
                        validation_messages=[],
                        warnings=["Contract persisted to memory only"],
                    )

            # Minimal schema validation: ensure required top-level sections exist
            validation_messages: List[str] = self._validate_contract_dict(contract_dict)

            return DataProductContractGenerationResponse.success(
                request_id=request_id,
                contract_yaml=contract_yaml,
                contract_path=contract_path,
                validation_messages=validation_messages,
                warnings=[],
            )
        except Exception as err:
            self.logger.error(f"Contract generation error: {err}\n{traceback.format_exc()}")
            return DataProductContractGenerationResponse.error(
                request_id=request_id,
                error_message=str(err),
                contract_yaml="",
                contract_path=None,
                validation_messages=[],
                warnings=[],
            )

    async def register_data_product(
        self, request: DataProductRegistrationRequest
    ) -> DataProductRegistrationResponse:
        """Persist the data product entry in the registry provider."""

        request_id = request.request_id
        try:
            if not self.data_product_provider:
                raise RuntimeError("Data product provider is not initialized")

            registry_entry = {
                "id": request.data_product_id,
                "product_id": request.data_product_id,
                "name": request.display_name or request.data_product_id,
                "domain": request.domain or "Unknown",
                "description": request.description or "",
                "owner": request.owner_metadata.get("owner", "system") if request.owner_metadata else "system",
                "contract_path": request.contract_path,
                "tags": request.tags,
                "owner_metadata": request.owner_metadata,
                "additional_metadata": request.additional_metadata,
            }

            existing = self.data_product_provider.get(request.data_product_id)
            self.data_product_provider.upsert(registry_entry)
            was_created = existing is None

            registry_path = getattr(self.data_product_provider, "source_path", None)

            return DataProductRegistrationResponse.success(
                request_id=request_id,
                registry_entry=registry_entry,
                was_created=was_created,
                registry_path=registry_path,
            )
        except Exception as err:
            self.logger.error(f"Registry registration error: {err}\n{traceback.format_exc()}")
            return DataProductRegistrationResponse.error(
                request_id=request_id,
                error_message=str(err),
                registry_entry={},
                was_created=False,
                registry_path=None,
            )

    async def validate_data_product_onboarding(
        self, request: DataProductQARequest
    ) -> DataProductQAResponse:
        """Optional QA step that lint-checks the contract and runs smoke tests."""

        request_id = request.request_id
        results: List[QAResult] = []
        blockers: List[str] = []
        overall_status = "pass"

        try:
            checks = request.checks or [
                "lint_contract",
                "register_tables",
                "create_default_view",
            ]

            contract_yaml: Optional[str] = None
            try:
                with open(request.contract_path, "r", encoding="utf-8") as fh:
                    contract_yaml = fh.read()
            except Exception as read_err:
                msg = f"Failed to read contract: {read_err}"
                blockers.append(msg)
                results.append(
                    QAResult(
                        check="lint_contract",
                        status="fail",
                        details={"error": msg},
                        human_action_required=True,
                    )
                )
                overall_status = "fail"
                return DataProductQAResponse.error(
                    request_id=request_id,
                    error_message=msg,
                    results=results,
                    blockers=blockers,
                    overall_status=overall_status,
                )

            contract_obj = yaml.safe_load(contract_yaml) if contract_yaml else {}

            # Lint: ensure critical sections exist
            if "lint_contract" in checks:
                missing_sections = [
                    section
                    for section in ["metadata", "tables", "views"]
                    if section not in contract_obj
                ]
                status = "pass" if not missing_sections else "fail"
                details = {"missing_sections": missing_sections}
                results.append(
                    QAResult(
                        check="lint_contract",
                        status=status,
                        details=details,
                        human_action_required=bool(missing_sections),
                    )
                )
                if missing_sections:
                    blockers.append(
                        f"Contract missing required sections: {', '.join(missing_sections)}"
                    )
                    overall_status = "fail"

            if "register_tables" in checks:
                reg_result = await self.register_tables_from_contract(
                    contract_path=request.contract_path,
                    schema=request.environment,
                )
                check_status = "pass" if reg_result.get("success") else "fail"
                results.append(
                    QAResult(
                        check="register_tables",
                        status=check_status,
                        details=reg_result,
                        human_action_required=not reg_result.get("success", False),
                    )
                )
                if not reg_result.get("success"):
                    blockers.append("Table registration failed")
                    overall_status = "fail"

            if "create_default_view" in checks:
                default_view = request.additional_context.get("default_view_name", "Onboarded_View")
                create_result = await self.create_view_from_contract(
                    contract_path=request.contract_path,
                    view_name=default_view,
                )
                check_status = "pass" if create_result.get("success") else "warn"
                results.append(
                    QAResult(
                        check="create_default_view",
                        status=check_status,
                        details=create_result,
                        human_action_required=not create_result.get("success", False),
                    )
                )
                if not create_result.get("success"):
                    warnings.append(
                        f"View {default_view} creation failed; contract may require manual review"
                    )
                    overall_status = "warn" if overall_status != "fail" else overall_status

            if not results:
                overall_status = "warn"

            return DataProductQAResponse.success(
                request_id=request_id,
                results=results,
                blockers=blockers,
                overall_status=overall_status,
            )
        except Exception as err:
            self.logger.error(f"QA validation error: {err}\n{traceback.format_exc()}")
            blockers.append(str(err))
            if "cleanup_needed" in locals() and cleanup_needed:
                try:
                    await inspection_manager.disconnect()
                except Exception:
                    pass
            return DataProductQAResponse.error(
                request_id=request_id,
                error_message=str(err),
                results=results,
                blockers=blockers,
                overall_status="fail",
            )

    # ------------------------------------------------------------------
    # Schema Inspection Helper Methods
    # ------------------------------------------------------------------

    def _resolve_inspection_settings(self, request: DataProductSchemaInspectionRequest) -> Dict[str, Any]:
        """
        Resolve inspection settings from request, registry, and connection profile.
        
        Returns a settings dict with: source_system, schema, project, tables, 
        connection_config, connection_params, connection_overrides.
        """
        settings: Dict[str, Any] = {
            "source_system": "duckdb",
            "schema": None,
            "project": None,
            "tables": None,
            "connection_config": {},
            "connection_params": {},
            "connection_overrides": {},
        }
        
        # Start with request values
        if request.source_system:
            settings["source_system"] = request.source_system.lower()
        if request.schema:
            settings["schema"] = request.schema
        if request.database:
            settings["project"] = request.database
        if request.tables:
            settings["tables"] = request.tables
        if request.connection_overrides:
            settings["connection_overrides"] = request.connection_overrides
        
        # Merge registry metadata if data_product_id provided
        if request.data_product_id and self.data_product_provider:
            try:
                dp = self.data_product_provider.get(request.data_product_id)
                if dp:
                    if hasattr(dp, "source_system") and dp.source_system and not request.source_system:
                        settings["source_system"] = dp.source_system.lower()
                    if hasattr(dp, "metadata") and isinstance(dp.metadata, dict):
                        if not settings["project"] and "project" in dp.metadata:
                            settings["project"] = dp.metadata["project"]
                        if not settings["schema"] and "dataset" in dp.metadata:
                            settings["schema"] = dp.metadata["dataset"]
            except Exception as e:
                self.logger.warning(f"Failed to load registry metadata for {request.data_product_id}: {e}")
        
        # Build connection config for manager factory
        source_system = settings["source_system"]
        if source_system == "duckdb":
            db_path = settings["connection_overrides"].get("path") or self.db_path
            settings["connection_config"] = {"type": "duckdb", "path": db_path}
            settings["connection_params"] = {}
        elif source_system == "bigquery":
            project = settings["project"] or settings["connection_overrides"].get("project")
            dataset = settings["schema"] or settings["connection_overrides"].get("dataset")
            settings["connection_config"] = {
                "type": "bigquery",
                "project": project,
                "dataset": dataset,
            }
            # Build connection params from overrides
            conn_params = {}
            self.logger.info(f"BigQuery connection_overrides keys: {list(settings['connection_overrides'].keys())}")
            if "service_account_info" in settings["connection_overrides"]:
                conn_params["service_account_info"] = settings["connection_overrides"]["service_account_info"]
                self.logger.info("Using service_account_info from overrides")
            elif "service_account_json_path" in settings["connection_overrides"]:
                conn_params["service_account_json_path"] = settings["connection_overrides"]["service_account_json_path"]
                self.logger.info(f"Using service_account_json_path: {conn_params['service_account_json_path']}")
            elif "service_account_path" in settings["connection_overrides"]:
                conn_params["service_account_json_path"] = settings["connection_overrides"]["service_account_path"]
                self.logger.info(f"Using service_account_path: {conn_params['service_account_json_path']}")
            else:
                self.logger.warning("No service account credentials found in connection_overrides")
            settings["connection_params"] = conn_params
            self.logger.info(f"BigQuery connection_params: project={project}, dataset={dataset}, has_credentials={bool(conn_params)}")
        
        # Set defaults for inspection
        if not settings["schema"]:
            settings["schema"] = "main" if source_system == "duckdb" else None
        
        return settings
    
    async def _prepare_inspection_manager(self, settings: Dict[str, Any]):
        """
        Instantiate and connect the appropriate database manager.
        
        Returns (manager, cleanup_needed) tuple.
        For DuckDB, reuses existing connection (cleanup_needed=False).
        For other backends, creates new manager (cleanup_needed=True).
        """
        source_system = settings["source_system"]
        
        if source_system == "duckdb":
            # Reuse existing DuckDB connection
            await self._ensure_db_connected()
            return self.db_manager, False
        
        # Create new manager for other backends
        from src.database.manager_factory import DatabaseManagerFactory
        
        self.logger.info(f"Creating {source_system} manager with config: {settings['connection_config']}")
        manager = DatabaseManagerFactory.create_manager(
            source_system,
            settings["connection_config"],
            logger=self.logger
        )
        
        # Connect with provided params
        self.logger.info(f"Connecting {source_system} manager with params keys: {list(settings['connection_params'].keys())}")
        connected = await manager.connect(settings["connection_params"])
        if not connected:
            raise RuntimeError(f"Failed to connect to {source_system} with provided credentials")
        
        self.logger.info(f"{source_system} manager connected successfully")
        return manager, True
    
    async def _discover_tables_for_inspection(
        self, inspection_manager, settings: Dict[str, Any]
    ) -> List[str]:
        """
        Discover tables/views to inspect.
        
        If explicit tables provided in settings, use those.
        Otherwise, query INFORMATION_SCHEMA for the backend.
        """
        # Use explicit tables if provided
        if settings.get("tables"):
            return settings["tables"]
        
        source_system = settings["source_system"]
        schema = settings.get("schema")
        project = settings.get("project")
        
        if source_system == "duckdb":
            # Query DuckDB information_schema
            query = f"""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = '{schema or "main"}'
                AND table_type IN ('BASE TABLE', 'VIEW')
            """
            result = await inspection_manager.execute_query(query, {})
            rows = result.get("rows", []) if isinstance(result, dict) else []
            return [row.get("table_name") or row.get("TABLE_NAME") for row in rows if row]
        
        elif source_system == "bigquery":
            # Query BigQuery INFORMATION_SCHEMA
            query = f"""
                SELECT table_name
                FROM `{project}.{schema}.INFORMATION_SCHEMA.TABLES`
                WHERE table_type IN ('BASE TABLE', 'VIEW')
            """
            self.logger.info(f"Executing BigQuery discovery query with project={project}, schema={schema}")
            self.logger.info(f"Query: {query}")
            result = await inspection_manager.execute_query(query, {})
            
            self.logger.info(f"BigQuery result type: {type(result)}, hasattr to_dict: {hasattr(result, 'to_dict')}, hasattr empty: {hasattr(result, 'empty')}")
            
            # BigQuery returns a pandas DataFrame
            if hasattr(result, 'to_dict'):
                # It's a DataFrame
                self.logger.info(f"DataFrame shape: {result.shape}, columns: {list(result.columns) if hasattr(result, 'columns') else 'N/A'}")
                if not result.empty and 'table_name' in result.columns:
                    tables = result['table_name'].tolist()
                    self.logger.info(f"Discovered {len(tables)} tables: {tables}")
                    return tables
                else:
                    self.logger.warning(f"DataFrame is empty={result.empty if hasattr(result, 'empty') else 'N/A'}, has table_name={'table_name' in result.columns if hasattr(result, 'columns') else 'N/A'}")
                    if hasattr(result, 'empty') and result.empty:
                        self.logger.error("BigQuery query returned 0 rows - check if dataset exists and has tables")
                    return []
            # Fallback for dict format
            rows = result.get("rows", []) if isinstance(result, dict) else []
            return [row.get("table_name") or row.get("TABLE_NAME") for row in rows if row]
        
        return []
    
    async def _profile_table(
        self, inspection_manager, table_name: str, settings: Dict[str, Any]
    ) -> Optional[TableProfile]:
        """
        Profile a table/view using the appropriate backend method.
        
        Dispatches to _profile_table_duckdb or _profile_table_bigquery.
        """
        source_system = settings["source_system"]
        include_samples = settings.get("include_samples", False)
        inspection_depth = settings.get("inspection_depth", "standard")
        
        if source_system == "duckdb":
            return await self._profile_table_duckdb(
                inspection_manager, table_name, include_samples, inspection_depth
            )
        elif source_system == "bigquery":
            return await self._profile_table_bigquery(
                inspection_manager, table_name, include_samples, inspection_depth, settings
            )
        
        return None
    
    async def _profile_table_duckdb(
        self, inspection_manager, table_name: str, include_samples: bool, inspection_depth: str
    ) -> Optional[TableProfile]:
        """Profile a DuckDB table using PRAGMA and direct queries with FK inference."""
        try:
            # Get column metadata via PRAGMA
            pragma_result = await inspection_manager.execute_query(f"PRAGMA table_info('{table_name}')", {})
            pragma_rows = pragma_result.get("rows", []) if isinstance(pragma_result, dict) else []
            
            columns = []
            for row in pragma_rows:
                col_name = row.get("name")
                col_type = row.get("type")
                is_nullable = row.get("notnull", 0) == 0
                if col_name:
                    semantic_tags = self._infer_semantic_tags(col_name, col_type)
                    columns.append(TableColumnProfile(
                        name=col_name,
                        data_type=col_type or "UNKNOWN",
                        is_nullable=is_nullable,
                        semantic_tags=semantic_tags,
                    ))
            
            # Get row count
            count_result = await inspection_manager.execute_query(f"SELECT COUNT(*) as count FROM {table_name}", {})
            count_rows = count_result.get("rows", []) if isinstance(count_result, dict) else []
            row_count = count_rows[0].get("count", 0) if count_rows else 0
            
            # Infer FK relationships via naming conventions
            foreign_keys = await self._infer_foreign_keys_duckdb(
                inspection_manager, table_name, columns
            )
            
            # Infer primary keys and timestamp columns from semantic tags
            primary_keys = [col.name for col in columns if "identifier" in col.semantic_tags and col.name.lower().endswith("id")]
            timestamp_columns = [col.name for col in columns if "time" in col.semantic_tags]
            
            # Infer table role
            table_role = self._infer_table_role(table_name, columns, None)
            
            return TableProfile(
                name=table_name,
                row_count=row_count,
                columns=columns,
                primary_keys=primary_keys,
                timestamp_columns=timestamp_columns,
                foreign_keys=foreign_keys,
                table_role=table_role,
            )
        except Exception as e:
            self.logger.error(f"Failed to profile DuckDB table {table_name}: {e}")
            return None
    
    async def _infer_foreign_keys_duckdb(
        self, inspection_manager, table_name: str, columns: List[TableColumnProfile]
    ) -> List:
        """
        Infer FK relationships for DuckDB via naming conventions.
        
        Heuristics:
        - Column ending in _id → look for table with singular/plural name
        - Validate target table exists
        - Check for matching PK column (id or {table}_id)
        """
        from src.agents.models.data_product_onboarding_models import ForeignKeyRelationship
        
        foreign_keys = []
        
        # Get list of available tables
        try:
            tables_query = "SELECT name FROM sqlite_master WHERE type='table'"
            tables_result = await inspection_manager.execute_query(tables_query, {})
            available_tables = [row.get("name") for row in tables_result.get("rows", [])]
        except Exception as e:
            self.logger.warning(f"Could not query available tables for FK inference: {e}")
            available_tables = []
        
        for col in columns:
            col_lower = col.name.lower()
            
            # Check if column looks like a FK (ends with _id)
            if col_lower.endswith("_id") and col_lower != "id":
                # Extract potential table name
                potential_table_base = col_lower[:-3]  # Remove _id
                
                # Try singular and plural forms
                potential_tables = [
                    potential_table_base,
                    potential_table_base + "s",
                    potential_table_base[:-1] if potential_table_base.endswith("s") else None,
                ]
                potential_tables = [t for t in potential_tables if t]
                
                # Check if any potential table exists
                for target_table in potential_tables:
                    if target_table in available_tables:
                        # Assume target has PK column named 'id' or '{table}_id'
                        target_column = "id"
                        
                        foreign_keys.append(ForeignKeyRelationship(
                            source_table=table_name,
                            source_column=col.name,
                            target_table=target_table,
                            target_column=target_column,
                            confidence=0.7,  # Inferred, not catalog-extracted
                            relationship_type="many-to-one",
                        ))
                        self.logger.info(f"Inferred FK: {table_name}.{col.name} -> {target_table}.{target_column} (confidence: 0.7)")
                        break
        
        return foreign_keys
    
    async def _profile_table_bigquery(
        self, inspection_manager, table_name: str, include_samples: bool, 
        inspection_depth: str, settings: Dict[str, Any]
    ) -> Optional[TableProfile]:
        """Profile a BigQuery view using INFORMATION_SCHEMA with FK extraction."""
        try:
            project = settings.get("project")
            schema = settings.get("schema")
            
            # Get column metadata from INFORMATION_SCHEMA
            columns_query = f"""
                SELECT column_name, data_type, is_nullable
                FROM `{project}.{schema}.INFORMATION_SCHEMA.COLUMNS`
                WHERE table_name = @table_name
                ORDER BY ordinal_position
            """
            columns_result = await inspection_manager.execute_query(
                columns_query, 
                {"table_name": table_name}
            )
            
            columns = []
            # Handle DataFrame response
            if hasattr(columns_result, 'iterrows'):
                for _, row in columns_result.iterrows():
                    col_name = row.get("column_name")
                    col_type = row.get("data_type")
                    is_nullable = row.get("is_nullable", "YES") == "YES"
                    if col_name:
                        semantic_tags = self._infer_semantic_tags(col_name, col_type)
                        columns.append(TableColumnProfile(
                            name=col_name,
                            data_type=col_type or "UNKNOWN",
                            is_nullable=is_nullable,
                            semantic_tags=semantic_tags,
                        ))
            else:
                # Fallback for dict format
                column_rows = columns_result.get("rows", []) if isinstance(columns_result, dict) else []
                for row in column_rows:
                    col_name = row.get("column_name")
                    col_type = row.get("data_type")
                    is_nullable = row.get("is_nullable", "YES") == "YES"
                    if col_name:
                        semantic_tags = self._infer_semantic_tags(col_name, col_type)
                        columns.append(TableColumnProfile(
                            name=col_name,
                            data_type=col_type or "UNKNOWN",
                            is_nullable=is_nullable,
                            semantic_tags=semantic_tags,
                        ))
            
            # Get row count
            count_query = f"SELECT COUNT(1) as row_count FROM `{project}.{schema}.{table_name}`"
            count_result = await inspection_manager.execute_query(count_query, {})
            
            # Handle DataFrame response
            if hasattr(count_result, 'iloc'):
                row_count = int(count_result.iloc[0]['row_count']) if not count_result.empty else 0
            else:
                # Fallback for dict format
                count_rows = count_result.get("rows", []) if isinstance(count_result, dict) else []
                row_count = count_rows[0].get("row_count", 0) if count_rows else 0
            
            # Extract FK relationships from INFORMATION_SCHEMA (if available)
            foreign_keys = []
            try:
                fk_query = f"""
                    SELECT 
                        kcu.column_name,
                        kcu.referenced_table_name,
                        kcu.referenced_column_name,
                        tc.constraint_name
                    FROM `{project}.{schema}.INFORMATION_SCHEMA.KEY_COLUMN_USAGE` kcu
                    JOIN `{project}.{schema}.INFORMATION_SCHEMA.TABLE_CONSTRAINTS` tc
                        ON kcu.constraint_name = tc.constraint_name
                    WHERE kcu.table_name = @table_name
                      AND tc.constraint_type = 'FOREIGN KEY'
                """
                fk_result = await inspection_manager.execute_query(
                    fk_query,
                    {"table_name": table_name}
                )
                
                from src.agents.models.data_product_onboarding_models import ForeignKeyRelationship
                
                # Handle DataFrame response
                if hasattr(fk_result, 'iterrows'):
                    for _, fk_row in fk_result.iterrows():
                        foreign_keys.append(ForeignKeyRelationship(
                            source_table=table_name,
                            source_column=fk_row.get("column_name"),
                            target_table=fk_row.get("referenced_table_name"),
                            target_column=fk_row.get("referenced_column_name"),
                            confidence=1.0,  # Catalog-extracted
                            constraint_name=fk_row.get("constraint_name"),
                        ))
                        self.logger.info(f"Extracted FK: {table_name}.{fk_row.get('column_name')} -> {fk_row.get('referenced_table_name')}.{fk_row.get('referenced_column_name')}")
                else:
                    # Fallback for dict format
                    fk_rows = fk_result.get("rows", []) if isinstance(fk_result, dict) else []
                    for fk_row in fk_rows:
                        foreign_keys.append(ForeignKeyRelationship(
                            source_table=table_name,
                            source_column=fk_row.get("column_name"),
                            target_table=fk_row.get("referenced_table_name"),
                            target_column=fk_row.get("referenced_column_name"),
                            confidence=1.0,  # Catalog-extracted
                            constraint_name=fk_row.get("constraint_name"),
                        ))
                        self.logger.info(f"Extracted FK: {table_name}.{fk_row.get('column_name')} -> {fk_row.get('referenced_table_name')}.{fk_row.get('referenced_column_name')}")
            except Exception as fk_error:
                self.logger.warning(f"Could not extract FK relationships for {table_name}: {fk_error}")
            
            # Extract view definition if this is a view
            view_definition = None
            try:
                view_query = f"""
                    SELECT view_definition
                    FROM `{project}.{schema}.INFORMATION_SCHEMA.VIEWS`
                    WHERE table_name = @table_name
                """
                view_result = await inspection_manager.execute_query(
                    view_query,
                    {"table_name": table_name}
                )
                
                # Handle DataFrame response
                if hasattr(view_result, 'iloc'):
                    if not view_result.empty:
                        view_definition = view_result.iloc[0].get("view_definition")
                        self.logger.info(f"Extracted view definition for {table_name}")
                else:
                    # Fallback for dict format
                    view_rows = view_result.get("rows", []) if isinstance(view_result, dict) else []
                    if view_rows:
                        view_definition = view_rows[0].get("view_definition")
                        self.logger.info(f"Extracted view definition for {table_name}")
            except Exception as view_error:
                self.logger.debug(f"Table {table_name} is not a view or view definition unavailable: {view_error}")
            
            # If this is a view with no FK constraints, infer FKs from the view definition
            if view_definition and len(foreign_keys) == 0:
                self.logger.info(f"Inferring FK relationships from view definition for {table_name}")
                self.logger.debug(f"View definition length: {len(view_definition)}")
                self.logger.debug(f"View definition sample: {view_definition[-500:]}")
                inferred_fks = self._infer_fks_from_view_definition(table_name, view_definition, columns)
                foreign_keys.extend(inferred_fks)
                self.logger.info(f"Inferred {len(inferred_fks)} FK relationships from view definition")
            
            # Infer primary keys and timestamp columns from semantic tags
            primary_keys = [col.name for col in columns if "identifier" in col.semantic_tags and col.name.lower().endswith("id")]
            timestamp_columns = [col.name for col in columns if "time" in col.semantic_tags]
            
            # Determine table role from view definition or heuristics
            table_role = self._infer_table_role(table_name, columns, view_definition)
            
            return TableProfile(
                name=table_name,
                row_count=row_count,
                columns=columns,
                primary_keys=primary_keys,
                timestamp_columns=timestamp_columns,
                foreign_keys=foreign_keys,
                table_role=table_role,
                view_definition=view_definition,
            )
        except Exception as e:
            self.logger.error(f"Failed to profile BigQuery table {table_name}: {e}")
            return None
    
    def _infer_semantic_tags(self, column_name: str, data_type: Optional[str]) -> List[str]:
        """Infer semantic tags from column name and data type."""
        tags = []
        lower_name = column_name.lower()
        
        if any(token in lower_name for token in ["amount", "revenue", "cost", "price", "total", "sum"]):
            tags.append("measure")
        if any(token in lower_name for token in ["date", "time", "_at", "timestamp"]):
            tags.append("time")
        if any(token in lower_name for token in ["id", "key"]):
            tags.append("identifier")
        if not tags:
            tags.append("dimension")

        if data_type and any(token in str(data_type).lower() for token in ("int", "decimal", "double", "numeric", "float")):
            if "measure" not in tags:
                tags.append("numeric")

        return tags

    def _infer_table_role(
        self, table_name: str, columns: List[TableColumnProfile], view_definition: Optional[str]
    ) -> Optional[str]:
        """
        Infer table role (FACT, DIMENSION) from table characteristics.
        
        Heuristics:
        - FACT: Many measures, few dimensions, FK columns, large row counts
        - DIMENSION: Few/no measures, many dimensions, PK column, smaller row counts
        """
        measure_count = sum(1 for col in columns if "measure" in col.semantic_tags)
        dimension_count = sum(1 for col in columns if "dimension" in col.semantic_tags)
        fk_count = sum(1 for col in columns if col.name.lower().endswith("_id") and not col.name.lower() == "id")
        has_id = any(col.name.lower() == "id" for col in columns)
        
        # Check table name patterns
        lower_name = table_name.lower()
        if any(token in lower_name for token in ["_fact", "fact_", "transaction", "event", "log"]):
            return "FACT"
        if any(token in lower_name for token in ["_dim", "dim_", "_dimension", "dimension_"]):
            return "DIMENSION"
        
        # Heuristic-based inference
        if measure_count > 2 and fk_count > 0:
            return "FACT"
        if dimension_count > measure_count and has_id:
            return "DIMENSION"
        
        # Parse view definition for JOIN patterns (fact tables typically JOIN many dimensions)
        if view_definition:
            join_count = view_definition.upper().count("JOIN")
            if join_count > 2:
                return "FACT"
        
        return None  # Unable to determine

    def _infer_fks_from_view_definition(
        self, view_name: str, view_definition: str, columns: List[TableColumnProfile]
    ) -> List[ForeignKeyRelationship]:
        """
        Infer FK relationships from view definition by parsing JOIN clauses.
        
        Example:
        FROM SalesOrders so JOIN BusinessPartners bp ON so.PartnerID = bp.PartnerID
        -> Infers: SalesOrders.PartnerID -> BusinessPartners.PartnerID
        """
        import re
        
        foreign_keys = []
        
        # Pattern to match JOIN clauses with ON conditions
        # BigQuery format: `project-id`.dataset.table AS alias
        # Backticks only around project name if it contains dashes
        # Match: optional `project`, then .dataset.table or just table_name
        join_pattern = re.compile(
            r'(?:INNER\s+|LEFT\s+|RIGHT\s+|FULL\s+)?JOIN\s+(?:`[^`]+`\.)?(\S+)\s+(?:AS\s+)?(\w+)\s+ON\s+(\w+)\.(\w+)\s*=\s*(\w+)\.(\w+)',
            re.IGNORECASE | re.DOTALL
        )
        
        # Build a map of table aliases to table names from the view definition
        # Pattern: FROM `project`.dataset.table AS alias or FROM table AS alias
        from_pattern = re.compile(r'FROM\s+(?:`[^`]+`\.)?(\S+)\s+(?:AS\s+)?(\w+)', re.IGNORECASE)
        
        alias_to_table = {}
        
        # Extract FROM clause alias
        from_match = from_pattern.search(view_definition)
        if from_match:
            table_name = from_match.group(1)
            alias = from_match.group(2)
            # Extract just the table name from fully qualified names (project.dataset.table)
            if '.' in table_name:
                table_name = table_name.split('.')[-1]
            alias_to_table[alias.lower()] = table_name
            self.logger.debug(f"FROM clause: {alias} -> {table_name}")
        else:
            self.logger.warning(f"No FROM clause matched in view definition")
        
        # Extract JOIN clause aliases and FK relationships
        join_matches = list(join_pattern.finditer(view_definition))
        self.logger.debug(f"Found {len(join_matches)} JOIN matches")
        
        for match in join_matches:
            # Group 1: table name (backtick-quoted), Group 2: alias
            # Groups 3-6: ON clause (left_alias.left_col = right_alias.right_col)
            table_name = match.group(1)
            alias = match.group(2)
            
            # Extract just the table name from fully qualified names
            if '.' in table_name:
                table_name = table_name.split('.')[-1]
            alias_to_table[alias.lower()] = table_name
            self.logger.debug(f"JOIN clause: {alias} -> {table_name}")
        
        # Parse JOIN conditions (iterate again to extract FK relationships)
        for match in join_pattern.finditer(view_definition):
            # Groups: 1=table, 2=alias, 3=left_alias, 4=left_col, 5=right_alias, 6=right_col
            left_alias = match.group(3).lower()
            left_col = match.group(4)
            right_alias = match.group(5).lower()
            right_col = match.group(6)
            
            # Resolve aliases to table names
            left_table = alias_to_table.get(left_alias, left_alias)
            right_table = alias_to_table.get(right_alias, right_alias)
            
            # Check if the column exists in the view's columns
            column_names = [col.name.lower() for col in columns]
            
            # Create FK relationship if the column is in the view
            # Convention: the table with "ID" suffix column is typically the FK source
            if left_col.lower() in column_names or right_col.lower() in column_names:
                # Determine which side is the FK (source) and which is the PK (target)
                # Heuristic: if column name matches table name + "ID", it's likely the FK
                if left_col.lower().endswith("id") and left_table.lower() != right_table.lower():
                    foreign_keys.append(ForeignKeyRelationship(
                        source_table=view_name,
                        source_column=left_col,
                        target_table=right_table,
                        target_column=right_col,
                        confidence=0.8,  # Inferred from view definition
                        constraint_name=f"inferred_{view_name}_{left_col}_{right_table}_{right_col}",
                    ))
                    self.logger.info(f"Inferred FK from view: {view_name}.{left_col} -> {right_table}.{right_col}")
                elif right_col.lower().endswith("id") and left_table.lower() != right_table.lower():
                    foreign_keys.append(ForeignKeyRelationship(
                        source_table=view_name,
                        source_column=right_col,
                        target_table=left_table,
                        target_column=left_col,
                        confidence=0.8,  # Inferred from view definition
                        constraint_name=f"inferred_{view_name}_{right_col}_{left_table}_{left_col}",
                    ))
                    self.logger.info(f"Inferred FK from view: {view_name}.{right_col} -> {left_table}.{left_col}")
        
        return foreign_keys

    def _infer_kpis_from_profiles(self, tables: List[TableProfile]) -> List[KPIProposal]:
        proposals: List[KPIProposal] = []
        for table in tables:
            measures = [
                col.name
                for col in table.columns
                if "measure" in col.semantic_tags or "numeric" in col.semantic_tags
            ]
            dims = [
                col.name
                for col in table.columns
                if "dimension" in col.semantic_tags and col.name not in measures
            ]
            for measure in measures:
                if measure.lower() in {"amount", "total_amount", "revenue", "sales"}:
                    proposals.append(
                        KPIProposal(
                            name=f"Total {measure.replace('_', ' ').title()}",
                            expression=f"SUM({measure})",
                            grain=",".join(table.primary_keys) or None,
                            dimensions=dims[:5],
                            description=f"Aggregated {measure} for {table.name}",
                            confidence=0.8,
                        )
                    )
        return proposals

    def _build_contract_dict(
        self,
        data_product_id: str,
        schema_summary: List[TableProfile],
        kpi_proposals: List[KPIProposal],
        overrides: Dict[str, Any],
    ) -> Dict[str, Any]:
        contract: Dict[str, Any] = {
            "metadata": {
                "id": data_product_id,
                "name": overrides.get("display_name", data_product_id.replace("_", " ").title()),
                "domain": overrides.get("domain", "Unknown"),
            },
            "tables": [],
            "views": [],
            "kpis": [],
        }

        for profile in schema_summary:
            contract_table = {
                "name": profile.name,
                "columns": [
                    {
                        "name": col.name,
                        "data_type": col.data_type,
                        "semantic_tags": col.semantic_tags,
                    }
                    for col in profile.columns
                ],
            }
            if profile.primary_keys:
                contract_table["primary_keys"] = profile.primary_keys
            if profile.timestamp_columns:
                contract_table["time_columns"] = profile.timestamp_columns
            contract["tables"].append(contract_table)

        if overrides.get("views"):
            contract["views"].extend(overrides["views"])
        else:
            for profile in schema_summary:
                view_name = f"{data_product_id}_{profile.name.split('.')[-1]}_view"
                columns = [col.name for col in profile.columns]
                select_list = ", ".join(columns)
                view_sql = f"SELECT {select_list} FROM {profile.name}"
                contract["views"].append({
                    "name": view_name,
                    "sql": view_sql,
                    "source_table": profile.name,
                })

        for proposal in kpi_proposals:
            contract["kpis"].append(
                {
                    "name": proposal.name,
                    "expression": proposal.expression,
                    "grain": proposal.grain,
                    "dimensions": proposal.dimensions,
                    "description": proposal.description,
                }
            )

        for key, value in overrides.items():
            if key not in contract:
                contract[key] = value

        return contract

    def _persist_contract_yaml(self, target_path: str, yaml_text: str) -> str:
        path = os.path.abspath(target_path)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(yaml_text)
        return path

    def _validate_contract_dict(self, contract: Dict[str, Any]) -> List[str]:
        messages: List[str] = []
        if "tables" in contract and not contract["tables"]:
            messages.append("Contract contains no tables")
        if "views" in contract and not contract["views"]:
            messages.append("Contract contains no views")
        if "metadata" in contract and "id" not in contract["metadata"]:
            messages.append("Metadata missing id field")
        return messages

    async def register_tables_from_contract(self, contract_path: str, schema: str = "main") -> Dict[str, Any]:
        """
        Register base tables defined in a YAML contract by creating DuckDB tables from CSVs.
        This method is idempotent and returns a summary instead of raising on failure.
        """
        transaction_id = str(uuid.uuid4())
        # Ensure database connection is available before registering sources
        if not await self._ensure_db_connected():
            self.logger.warning(f"[TXN:{transaction_id}] Database not connected; cannot register tables from contract")
            return {"success": False, "message": "Database not connected", "registered": {}}
        try:
            with open(contract_path, "r") as f:
                contract = yaml.safe_load(f)
        except Exception as e:
            msg = f"Failed to read contract at {contract_path}: {e}"
            self.logger.error(f"[TXN:{transaction_id}] {msg}")
            return {"success": False, "message": msg, "registered": {}}

        tables = contract.get("tables", []) if isinstance(contract, dict) else []
        results: Dict[str, bool] = {}
        success_count = 0
        total = len(tables)
        for t in tables:
            try:
                table_name = t.get("name") if isinstance(t, dict) else None
                ds_path = t.get("data_source_path") if isinstance(t, dict) else None
                if not table_name or not ds_path:
                    results[table_name or "unknown"] = False
                    continue
                # Determine CSV file path
                csv_path = ds_path
                if os.path.isdir(ds_path):
                    candidates = [
                        os.path.join(ds_path, f"{table_name}.csv"),
                        os.path.join(ds_path, f"{table_name}.CSV"),
                        os.path.join(ds_path, f"{table_name.lower()}.csv"),
                        os.path.join(ds_path, f"{table_name.upper()}.csv"),
                    ]
                    for c in candidates:
                        if os.path.exists(c):
                            csv_path = c
                            break
                
                # Check if table already exists to avoid overwriting patched data (e.g. from reload_duckdb.py)
                # We use a direct SQL check via db_manager
                try:
                    check_sql = f"SELECT count(*) FROM information_schema.tables WHERE table_schema = '{schema}' AND table_name = '{table_name}'"
                    # execution is async in db_manager but returns a DF or similar. 
                    # We can use execute_query.
                    exists_df = await self.db_manager.execute_query(check_sql)
                    if not exists_df.empty and exists_df.iloc[0, 0] > 0:
                        self.logger.info(f"[TXN:{transaction_id}] Table {schema}.{table_name} already exists. Skipping auto-hydration to preserve data.")
                        results[table_name] = True
                        success_count += 1
                        continue
                except Exception as check_err:
                    self.logger.warning(f"[TXN:{transaction_id}] Failed to check if table exists: {check_err}. Proceeding with registration.")

                # Extract CSV options if present
                csv_options = t.get("csv_options", {})
                
                ok = await self.db_manager.register_data_source({
                    "type": "csv",
                    "path": csv_path,
                    "schema": schema,
                    "table_name": table_name,
                    "csv_options": csv_options
                }, transaction_id=transaction_id)
                results[table_name] = bool(ok)
                if ok:
                    success_count += 1
            except Exception as e:
                self.logger.error(f"[TXN:{transaction_id}] Error registering table {t}: {str(e)}\n{traceback.format_exc()}")
                results[str(t)] = False

        overall = success_count > 0
        return {
            "success": overall,
            "message": f"Registered {success_count}/{total} tables from contract",
            "registered": results
        }

    async def create_view(
        self,
        view_name: str,
        sql_query: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a view from a SQL query.
        
        Args:
            view_name: Name of the view to create
            sql_query: SQL query defining the view
            metadata: Optional metadata for the view
            
        Returns:
            Dictionary containing the view definition or status
        """
        transaction_id = str(uuid.uuid4())
        
        # Ensure database connection is available before creating a view
        if not await self._ensure_db_connected():
            self.logger.warning(f"[TXN:{transaction_id}] Database not connected; cannot create view '{view_name}'")
            return {"success": False, "message": "Database not connected", "view_name": view_name}
            
        try:
            # Validate SQL is a string
            if not isinstance(sql_query, str) or not sql_query.strip():
                 return {"success": False, "message": "Invalid SQL query", "view_name": view_name}
            
            ok = await self.db_manager.create_view(
                view_name=view_name, 
                sql=sql_query, 
                replace_existing=True, 
                transaction_id=transaction_id
            )
            
            return {
                "success": bool(ok),
                "message": f"View '{view_name}' created" if ok else f"Failed to create view '{view_name}'",
                "view_name": view_name
            }
        except Exception as e:
            self.logger.error(f"[TXN:{transaction_id}] Error creating view {view_name}: {str(e)}\n{traceback.format_exc()}")
            return {"success": False, "message": str(e), "view_name": view_name}

    async def create_view_from_contract(self, contract_path: str, view_name: str) -> Dict[str, Any]:
        """
        Create or replace a view defined in the YAML contract. Returns a status dict.
        """
        transaction_id = str(uuid.uuid4())
        # Ensure database connection is available before creating a view
        if not await self._ensure_db_connected():
            self.logger.warning(f"[TXN:{transaction_id}] Database not connected; cannot create view '{view_name}'")
            return {"success": False, "message": "Database not connected", "view_name": view_name}
        try:
            with open(contract_path, "r") as f:
                contract = yaml.safe_load(f)
        except Exception as e:
            msg = f"Failed to read contract at {contract_path}: {e}"
            self.logger.error(f"[TXN:{transaction_id}] {msg}")
            return {"success": False, "message": msg}

        views = contract.get("views", []) if isinstance(contract, dict) else []
        target_sql = None
        for v in views:
            try:
                if isinstance(v, dict) and v.get("name") == view_name:
                    target_sql = v.get("sql")
                    break
            except Exception:
                continue

        if not target_sql or not isinstance(target_sql, str):
            msg = f"View '{view_name}' not found in contract or has no SQL definition"
            self.logger.warning(f"[TXN:{transaction_id}] {msg}")
            return {"success": False, "message": msg}

        try:
            ok = await self.db_manager.create_view(view_name=view_name, sql=target_sql, replace_existing=True, transaction_id=transaction_id)
            return {
                "success": bool(ok),
                "message": f"View '{view_name}' created" if ok else f"Failed to create view '{view_name}'",
                "view_name": view_name
            }
        except Exception as e:
            self.logger.error(f"[TXN:{transaction_id}] Error creating view {view_name}: {str(e)}\n{traceback.format_exc()}")
            return {"success": False, "message": str(e), "view_name": view_name}

    async def generate_sql(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generic SQL generation endpoint.
        Behavior:
        - If the input already looks like SQL, return it (pass-through)
        - Otherwise, attempt LLM-based SQL generation via LLM Service Agent (if available)
        - On failure or if disabled, return a standard error response
        Returns a protocol-compliant dict: { success, sql, message, transaction_id }.
        """
        transaction_id = str(uuid.uuid4())
        try:
            if isinstance(query, str) and query.strip():
                q = query.strip()
                # naive detection: if the string appears to be SQL already, echo it back
                m = re.match(r"^\s*(with|select|from|create|explain)\b", q, flags=re.IGNORECASE)
                if m:
                    return {"success": True, "sql": q, "message": "Pass-through SQL", "transaction_id": transaction_id}

            # Attempt LLM-based SQL generation for natural language queries
            # Feature flag to enforce LLM-only path (no fallback here other than pass-through already handled)
            force_llm = str(os.environ.get('A9_FORCE_LLM_SQL', 'false')).lower() in ('1','true','yes','y','on')

            # Resolve auxiliary context
            ctx = context or {}
            dp_id = ctx.get('data_product_id') or 'fi_star_schema'
            yaml_contract_text = None
            cpath = ctx.get('contract_path')
            if isinstance(cpath, str):
                try:
                    if os.path.exists(cpath):
                        with open(cpath, 'r', encoding='utf-8') as _f:
                            yaml_contract_text = _f.read()
                except Exception:
                    yaml_contract_text = None
            filters = ctx.get('filters') if isinstance(ctx.get('filters'), dict) else None
            include_explain = bool(ctx.get('include_explain', False))
            
            # Prefer a minimal LLM profile over full contract YAML to avoid alias leakage
            target_view_label = dp_id  # default text for prompt
            profile_yaml_text = None
            schema_fields: Dict[str, Dict[str, str]] = {}
            exposed_columns_list: List[str] = []
            default_measure_name = None
            default_agg = 'SUM'
            try:
                if yaml_contract_text:
                    ydoc = yaml.safe_load(yaml_contract_text)
                    # Find a view with an llm_profile; otherwise use the first view name
                    views = ydoc.get('views', []) if isinstance(ydoc, dict) else []
                    chosen_view = None
                    if isinstance(views, list):
                        for v in views:
                            if isinstance(v, dict) and v.get('llm_profile'):
                                chosen_view = v
                                break
                        if not chosen_view and views:
                            first = views[0]
                            chosen_view = first if isinstance(first, dict) else None
                    if chosen_view:
                        view_name = chosen_view.get('name') or 'FI_Star_View'
                        target_view_label = view_name
                        llm_profile = chosen_view.get('llm_profile')
                        if isinstance(llm_profile, dict):
                            # Build a trimmed YAML with only the llm_profile and view name
                            profile_yaml_text = yaml.safe_dump(
                                {'view_name': view_name, 'llm_profile': llm_profile},
                                sort_keys=False, allow_unicode=True
                            )
                            # Build fields map for the LLM service's schema_context
                            exp_cols = llm_profile.get('exposed_columns', [])
                            if isinstance(exp_cols, list):
                                for col in exp_cols:
                                    if isinstance(col, str):
                                        schema_fields[col] = {"description": "", "type": ""}
                                        exposed_columns_list.append(col)
                            # Capture default measure/agg if provided
                            meas = llm_profile.get('measure_semantics') if isinstance(llm_profile, dict) else None
                            if isinstance(meas, dict):
                                default_measure_name = meas.get('default_measure') or default_measure_name
                                default_agg = str(meas.get('default_aggregation') or default_agg).upper()
            except Exception:
                # If profile extraction fails, fall back silently
                profile_yaml_text = None

            if getattr(self, 'llm_service_agent', None) is not None:
                try:
                    req = A9_LLM_SQLGenerationRequest(
                        request_id=transaction_id,
                        timestamp=datetime.datetime.utcnow().isoformat(),
                        principal_id=ctx.get('principal_id', 'dpa_agent'),
                        natural_language_query=q,
                        data_product_id=target_view_label,
                        yaml_contract=profile_yaml_text or yaml_contract_text,
                        schema_details={'fields': schema_fields} if schema_fields else None,
                        filters=filters,
                        include_explain=include_explain
                    )
                    llm_resp = await self.llm_service_agent.generate_sql(req)
                    if getattr(llm_resp, 'status', '') == 'success' and getattr(llm_resp, 'sql_query', ''):
                        sql_out = llm_resp.sql_query
                        # Fix common LLM mistakes
                        try:
                            if profile_yaml_text and exposed_columns_list and isinstance(sql_out, str):
                                # 1) single-quoted identifiers for exposed columns -> convert to proper identifiers
                                for col in exposed_columns_list:
                                    bad = f"'{col}'"
                                    good = f'"{col}"'
                                    if bad in sql_out:
                                        sql_out = sql_out.replace(bad, good)
                                # 2) constant alias for total_revenue -> replace with aggregate on default measure when available
                                if default_measure_name:
                                    pattern = r"'total_revenue'\s+AS\s+total_revenue"
                                    repl = f'{default_agg}("{default_measure_name}") AS total_revenue'
                                    sql_out = re.sub(pattern, repl, sql_out, flags=re.IGNORECASE)
                                # 3) When LLM emits "'Col' AS \"Col\"", collapse to just the column identifier
                                for col in exposed_columns_list:
                                    pattern = rf"'{re.escape(col)}'\s+AS\s+\"{re.escape(col)}\""
                                    repl = f'"{col}"'
                                    sql_out = re.sub(pattern, repl, sql_out, flags=re.IGNORECASE)
                        except Exception:
                            pass
                        return {
                            "success": True,
                            "sql": sql_out,
                            "message": "SQL generated via LLM Service",
                            "transaction_id": transaction_id
                        }
                    else:
                        warn = getattr(llm_resp, 'error_message', None) or 'Unknown LLM error'
                        self.logger.warning(f"LLM Service returned no SQL: {warn}")
                except Exception as e:
                    self.logger.warning(f"LLM Service SQL generation failed: {e}")
                    # fall through to error unless we can do other deterministic fallback here
            else:
                self.logger.info("LLM Service Agent not available for SQL generation")

            # If we reach here, LLM path did not produce SQL
            if force_llm:
                return {"success": False, "sql": "", "message": "A9_FORCE_LLM_SQL enabled; LLM did not return SQL", "transaction_id": transaction_id}

            # Final fallback: return error (deterministic SQL for NL requires LLM or explicit KPI context)
            return {"success": False, "sql": "", "message": "Unable to generate SQL from natural language without LLM", "transaction_id": transaction_id}
        except Exception as e:
            return {"success": False, "sql": "", "message": str(e), "transaction_id": transaction_id}

    async def generate_sql_for_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Compatibility wrapper to align with callers expecting generate_sql_for_query.
        """
        return await self.generate_sql(query, context)

    async def _generate_sql_for_kpi(self, kpi_definition: Any, timeframe: Any = None, filters: Dict[str, Any] = None, topn: Any = None, breakdown: bool = False, override_group_by: Optional[List[str]] = None) -> str:
        """
        Generate SQL for a KPI definition.
        
        Args:
            kpi_definition: KPI definition object
            timeframe: Optional timeframe filter
            filters: Optional additional filters
            topn: Optional Top/Bottom N spec
            breakdown: When True, allow grouping via GROUP BY precedence; when False, return a single aggregated value (no grouping)
            override_group_by: Optional explicit list of group-by terms to use when breakdown=True (bypasses precedence)
            
        Returns:
            SQL query string
        """
        # Validate KPI definition
        if not kpi_definition:
            self.logger.warning("KPI definition is None")
            return "SELECT 1 WHERE 1=0 -- Invalid KPI definition (None)"
            
        # Check if KPI definition has necessary attributes
        if not hasattr(kpi_definition, '__dict__'):
            self.logger.warning("KPI definition has no attributes")
            return "SELECT 1 WHERE 1=0 -- Invalid KPI definition (no attributes)"
        
        # Initialize variables
        attributes = []
        group_by_items = []
        kpi_filters = {}
        
        # Extract filters from KPI definition and merge with provided filters
        if hasattr(kpi_definition, 'filters') and kpi_definition.filters:
            kpi_filters.update(kpi_definition.filters)
            
        if filters:
            kpi_filters.update(filters)
        
        # Resolve view name early so we can map attribute names appropriately
        view_name = await self._get_view_name_from_kpi(kpi_definition)
        if not view_name:
            self.logger.error("No view_name resolved for KPI and fallback disabled; aborting SQL generation.")
            return ""

        # Base query
        base_query = "SELECT "
        
        # Add attributes to select clause
        select_items = []
        measure_alias: Optional[str] = None
        
        # Handle attributes if present; otherwise derive a measure and build SUM(...)
        if not hasattr(kpi_definition, 'attributes') or not kpi_definition.attributes:
            # 0) Try to extract explicit SQL expression from sql_query or calculation if present
            # This supports complex KPIs (e.g. ratios) defined in YAML
            explicit_expr = None
            
            # Check sql_query first (legacy)
            if hasattr(kpi_definition, 'sql_query') and kpi_definition.sql_query:
                try:
                    qt = kpi_definition.sql_query
                    # Only use explicit SQL if it doesn't have a GROUP BY (implies scalar definition)
                    # If it has GROUP BY, it likely contains dimensions we don't want in a scalar SELECT
                    if 'group by' not in qt.lower():
                        # Extract everything between SELECT and FROM
                        m_expr = re.search(r'^\s*SELECT\s+(.+?)\s+FROM\s+', qt, re.IGNORECASE | re.DOTALL)
                        if m_expr and m_expr.group(1):
                            candidate = m_expr.group(1).strip()
                            if candidate != '*' and candidate.lower() != 'count(*)':
                                explicit_expr = candidate
                except Exception:
                    pass
            
            # Check calculation if sql_query yielded nothing
            if not explicit_expr and hasattr(kpi_definition, 'calculation') and kpi_definition.calculation:
                try:
                    calc = kpi_definition.calculation
                    qt = None
                    if isinstance(calc, str):
                        qt = calc
                    elif isinstance(calc, dict):
                        qt = calc.get('query_template') or calc.get('template')
                    
                    if isinstance(qt, str) and 'select' in qt.lower() and 'from' in qt.lower():
                        if 'group by' not in qt.lower():
                            # Extract everything between SELECT and FROM
                            m_expr = re.search(r'^\s*SELECT\s+(.+?)\s+FROM\s+', qt, re.IGNORECASE | re.DOTALL)
                            if m_expr and m_expr.group(1):
                                candidate = m_expr.group(1).strip()
                                if candidate != '*' and candidate.lower() != 'count(*)':
                                    explicit_expr = candidate
                except Exception:
                    pass

            if explicit_expr:
                # Use the user-provided expression
                # Check if it already has an alias
                m_alias = re.search(r'\s+as\s+([\w_]+)$', explicit_expr, re.IGNORECASE)
                if m_alias:
                     measure_alias = m_alias.group(1)
                     select_items.append(explicit_expr)
                else:
                     select_items.append(f"{explicit_expr} as total_value")
                     measure_alias = "total_value"
            else:
                # Derive primary measure column
                derived = self._resolve_measure_from_kpi(kpi_definition)
                if not derived:
                    # Use contract column_aliases instead of hardcoded product checks
                    aliases = self._get_contract_column_aliases()
                    measure_col = aliases.get('measure')
                    if measure_col:
                        derived = f'"{measure_col}"'
                if derived:
                    select_items.append(f"COALESCE(SUM({derived}), 0) as total_value")
                    measure_alias = "total_value"
                else:
                    self.logger.warning("KPI definition has no attributes and no resolvable measure")
                    return "SELECT 1 WHERE 1=0 -- Invalid KPI definition (no attributes or measure)"
        else:
            for attr in kpi_definition.attributes:
                if isinstance(attr, dict) and 'name' in attr and 'aggregation' in attr:
                    # Handle aggregated attributes
                    agg = attr['aggregation'].lower()
                    resolved = self._resolve_attribute_name(str(attr['name']), kpi_definition, view_name)
                    if agg in ['sum', 'avg', 'min', 'max', 'count']:
                        alias = f"{attr['name']}_{agg}"
                        select_items.append(f"{agg}({resolved}) as {alias}")
                    else:
                        select_items.append(resolved)
                elif isinstance(attr, str):
                    # Handle simple string attributes with smart defaults
                    # Map generic 'value' to the canonical measure and aggregate for single-value KPIs
                    resolved = self._resolve_attribute_name(attr, kpi_definition, view_name)
                    attr_l = attr.strip().lower()
                    if attr_l in {'value', 'amount', 'revenue', 'measure', 'metric'} or getattr(kpi_definition, 'name', '').strip().lower() == 'gross revenue':
                        # If resolution still yields a generic placeholder, try to derive from KPI metadata/calculation
                        if resolved.strip().strip('"').lower() == 'value':
                            derived = self._resolve_measure_from_kpi(kpi_definition)
                            if derived:
                                resolved = derived
                        select_items.append(f"COALESCE(SUM({resolved}), 0) as total_value")
                        measure_alias = "total_value"
                    else:
                        select_items.append(resolved)
        
        # If no attributes, use count(*)
        if not select_items:
            select_items = ["count(*) as count"]
            
        # Defer constructing the SELECT clause until after grouping columns are added
        
        # Determine group by items using centralized precedence only when breakdown mode is requested
        # For initial situation awareness, no grouping is recommended to avoid per-row threshold evaluation
        if breakdown and isinstance(override_group_by, list) and override_group_by:
            group_by_items = [str(x) for x in override_group_by if isinstance(x, (str, int, float))]
        else:
            group_by_items = self._collect_group_by_items(kpi_definition) if breakdown else []

        # If grouping is requested, include the grouping columns in the SELECT list
        if group_by_items:
            for gb in group_by_items:
                try:
                    resolved_gb = self._resolve_attribute_name(str(gb), kpi_definition, view_name)
                    # Avoid duplicate SELECT items
                    if resolved_gb not in select_items:
                        select_items.insert(0, resolved_gb)
                except Exception:
                    # Best-effort: include raw group by
                    if gb not in select_items:
                        select_items.insert(0, gb)

        # Now construct the SELECT clause including any grouping columns
        base_query += ", ".join(select_items)
        
        # Apply default version filter from contract if not already specified
        try:
            aliases = self._get_contract_column_aliases()
            version_col = aliases.get('version')
            default_version = aliases.get('default_version_value')
            if version_col and default_version:
                has_version = any(str(k).strip().lower() == version_col.lower() for k in kpi_filters.keys()) if isinstance(kpi_filters, dict) else False
                if not has_version:
                    kpi_filters[version_col] = default_version
        except Exception:
            pass

        # Build where clause from filters (map keys to actual view columns)
        all_conditions = []
        join_time_dim = False
        join_on_col: Optional[str] = None
        for key, value in kpi_filters.items():
            # Resolve attribute/column name against the target view
            resolved_col = self._resolve_attribute_name(str(key), kpi_definition, view_name)
            
            # Treat special "all" sentinel tokens as no-op filters
            def _is_all_token(v: Any) -> bool:
                try:
                    return str(v).strip().lower() in {"total", "#", "all"}
                except Exception:
                    return False

            if isinstance(value, str):
                if _is_all_token(value):
                    continue
                safe_value = value.replace("'", "''")
                # Direct equality for string filters, including Version
                all_conditions.append(f"{resolved_col} = '{safe_value}'")
            elif isinstance(value, (int, float)):
                all_conditions.append(f"{resolved_col} = {value}")
            elif isinstance(value, list):
                if all(isinstance(item, str) for item in value):
                    # Filter out sentinel tokens representing the total/all bucket
                    value = [item for item in value if not _is_all_token(item)]
                    if not value:
                        continue
                    formatted_values = []
                    for item in value:
                        escaped_item = item.replace("'", "''")
                        formatted_values.append(f"'{escaped_item}'")
                    all_conditions.append(f"{resolved_col} IN ({', '.join(formatted_values)})")
                elif all(isinstance(item, (int, float)) for item in value):
                    all_conditions.append(f"{resolved_col} IN ({', '.join(map(str, value))})")
                else:
                    self.logger.warning(f"Skipping filter with mixed types in list: {key}")
            elif value is None:
                all_conditions.append(f"{resolved_col} IS NULL")
            else:
                self.logger.warning(f"Skipping unsupported filter type: {key} = {type(value)}")
                continue
        
        # Add time filter if present and no explicit timeframe is provided
        # If a timeframe is provided, we will apply conditions via time_dim (t."date") only,
        # to avoid mixing transaction-date filters with time-dimension filters.
        if (not timeframe) and hasattr(kpi_definition, 'time_filter') and kpi_definition.time_filter:
            time_filter = kpi_definition.time_filter
            if isinstance(time_filter, dict):
                if 'column' in time_filter and 'start' in time_filter:
                    column = time_filter['column']
                    # Ensure column is properly quoted
                    safe_column = '"' + column.replace('"', '""') + '"'
                    
                    # Handle date string properly
                    start = time_filter['start']
                    if isinstance(start, str):
                        start = start.replace("'", "''")
                        all_conditions.append(f"{safe_column} >= '{start}'")
                    else:
                        all_conditions.append(f"{safe_column} >= {start}")
                    
                    if 'end' in time_filter:
                        end = time_filter['end']
                        if isinstance(end, str):
                            end = end.replace("'", "''")
                            all_conditions.append(f"{safe_column} <= '{end}'")
                        else:
                            all_conditions.append(f"{safe_column} <= {end}")
        
        # Add timeframe condition if provided (only when a date column can be resolved generically)
        if timeframe:
            timeframe_condition = self._get_timeframe_condition(timeframe)
            if timeframe_condition:
                resolved_date_col = None
                try:
                    # Prefer explicit KPI time_filter column if available
                    if hasattr(kpi_definition, 'time_filter') and isinstance(kpi_definition.time_filter, dict):
                        col = kpi_definition.time_filter.get('column')
                        if isinstance(col, str) and col.strip():
                            resolved_date_col = col.strip()
                    # Fall back to simple metadata hints if present
                    if not resolved_date_col and hasattr(kpi_definition, 'date_column') and isinstance(kpi_definition.date_column, str):
                        resolved_date_col = kpi_definition.date_column.strip()
                    if not resolved_date_col and hasattr(kpi_definition, 'metadata') and isinstance(kpi_definition.metadata, dict):
                        meta_col = kpi_definition.metadata.get('date_column')
                        if isinstance(meta_col, str) and meta_col.strip():
                            resolved_date_col = meta_col.strip()
                except Exception:
                    resolved_date_col = None

                # Use contract column_aliases for date column fallback
                if not resolved_date_col:
                    try:
                        aliases = self._get_contract_column_aliases()
                        date_col = aliases.get('date')
                        if date_col:
                            resolved_date_col = date_col
                    except Exception:
                        resolved_date_col = None

                if resolved_date_col:
                    # Safely quote date column; timeframe condition already references time_dim alias 't'
                    safe_date_col = '"' + resolved_date_col.replace('"', '""') + '"'
                    all_conditions.append(timeframe_condition)
                    join_time_dim = True
                    join_on_col = safe_date_col
                else:
                    self.logger.warning("Timeframe provided but no date column resolvable; skipping timeframe condition")
        
        # Construct where clause
        where_clause = ""
        if all_conditions:
            where_clause = f"WHERE {' AND '.join(all_conditions)}"
        
        # Construct the final query
        base_lower = base_query.strip().lower()
        if "from" not in base_lower:
            # Ensure view name is properly quoted for SQL syntax
            safe_view_name = view_name.replace('"', '""')  # Escape quotes if present
            base_query += f" FROM \"{safe_view_name}\" "
            if join_time_dim and join_on_col:
                base_query += f" JOIN time_dim t ON t.\"date\" = {join_on_col} "
            
        if where_clause:
            base_query += f" {where_clause}"
            
        if group_by_items:
            try:
                resolved_group_by = [self._resolve_attribute_name(str(gb), kpi_definition, view_name) for gb in group_by_items]
                base_query += f" GROUP BY {', '.join(resolved_group_by)}"
            except Exception:
                base_query += f" GROUP BY {', '.join(group_by_items)}"
            
        # Apply Top/Bottom N ordering and limit when provided (takes precedence over KPI order_by/limit)
        applied_order = False
        try:
            tn = topn
            # Support dict-like or object with attributes
            limit_type = None
            limit_n = None
            limit_field = None
            metric = None
            if tn is not None:
                if isinstance(tn, dict):
                    limit_type = tn.get('limit_type') or tn.get('type')
                    limit_n = tn.get('limit_n') or tn.get('n')
                    limit_field = tn.get('limit_field') or tn.get('field')
                    metric = tn.get('metric')
                else:
                    limit_type = getattr(tn, 'limit_type', None)
                    limit_n = getattr(tn, 'limit_n', None)
                    limit_field = getattr(tn, 'limit_field', None)
                    metric = getattr(tn, 'metric', None)

            # Special metric: rank by growth vs previous timeframe (delta between current and previous totals)
            # Only when grouping is present and timeframe is provided
            self.logger.debug(f"[SQL] topn check: metric={metric}, group_by_items={group_by_items}, timeframe={timeframe}, limit_n={limit_n}, limit_type={limit_type}")
            if (
                isinstance(metric, str) and metric.strip().lower() == 'delta_prev'
                and group_by_items and timeframe and isinstance(limit_n, int) and limit_n > 0
            ):
                try:
                    # Re-resolve group-by columns for join and projection
                    try:
                        resolved_group_by = [self._resolve_attribute_name(str(gb), kpi_definition, view_name) for gb in group_by_items]
                    except Exception:
                        resolved_group_by = group_by_items[:]

                    # Use the Decision UI timeframe as CURRENT, and compute PREVIOUS relative to it
                    curr_cond = self._get_timeframe_condition(timeframe)
                    prev_cond = self._get_previous_timeframe_condition(timeframe)

                    # Start from base_query which likely already includes the timeframe condition
                    curr_sql = base_query.strip()
                    if curr_cond and curr_cond not in curr_sql:
                        lower_sql = curr_sql.lower()
                        if ' where ' in lower_sql:
                            curr_sql = curr_sql + f" AND {curr_cond}"
                        else:
                            curr_sql = curr_sql + f" WHERE {curr_cond}"

                    # Build PREVIOUS sql by replacing CURRENT with PREVIOUS (or append if not found)
                    prev_sql = curr_sql
                    if curr_cond and prev_cond and (curr_cond in prev_sql):
                        prev_sql = prev_sql.replace(curr_cond, prev_cond, 1)
                    elif prev_cond:
                        lower_sql = prev_sql.lower()
                        if ' where ' in lower_sql:
                            prev_sql = prev_sql + f" AND {prev_cond}"
                        else:
                            prev_sql = prev_sql + f" WHERE {prev_cond}"

                    # Build join predicate across all grouping columns
                    try:
                        join_pred = ' AND '.join([f"curr.{col} = prev.{col}" for col in resolved_group_by])
                    except Exception:
                        # Fallback: use the first group-by column only
                        col = resolved_group_by[0] if resolved_group_by else '1'
                        join_pred = f"curr.{col} = prev.{col}"

                    # Construct final ranked query using CTEs
                    direction = 'DESC' if (isinstance(limit_type, str) and limit_type.lower() == 'top') else 'ASC'
                    gb_select = ', '.join([f"curr.{c}" for c in resolved_group_by])
                    ranked_sql = (
                        f"WITH curr AS ({curr_sql}), prev AS ({prev_sql}) "
                        f"SELECT {gb_select}, curr.{measure_alias or 'total_value'} AS current_value, "
                        f"COALESCE(prev.{measure_alias or 'total_value'}, 0) AS previous_value, "
                        f"(curr.{measure_alias or 'total_value'} - COALESCE(prev.{measure_alias or 'total_value'}, 0)) AS delta_prev "
                        f"FROM curr LEFT JOIN prev ON {join_pred} "
                        f"ORDER BY delta_prev {direction} LIMIT {int(limit_n)}"
                    )
                    base_query = ranked_sql
                    applied_order = True
                except Exception:
                    # If growth ranking fails, fall back to standard ordering below
                    pass
            if isinstance(limit_type, str) and isinstance(limit_n, int) and limit_n > 0:
                direction = 'DESC' if limit_type.lower() == 'top' else 'ASC'
                # Determine order expression
                order_expr = None
                if isinstance(limit_field, str) and limit_field.strip():
                    try:
                        resolved_rank_col = self._resolve_attribute_name(str(limit_field), kpi_definition, view_name)
                        # If a specific rank field is provided, order by its aggregated value
                        order_expr = f"COALESCE(SUM({resolved_rank_col}), 0)"
                    except Exception:
                        pass
                if not order_expr:
                    # Fallback to primary measure alias if present
                    if measure_alias:
                        order_expr = measure_alias
                    else:
                        # Last resort: use first numeric-looking select item or position 1
                        try:
                            order_expr = measure_alias or '1'
                        except Exception:
                            order_expr = '1'
                # Append ORDER BY and LIMIT only if not already present
                lower_sql = base_query.lower()
                if ' order by ' not in lower_sql:
                    base_query += f" ORDER BY {order_expr} {direction}"
                if f" limit {limit_n}" not in lower_sql:
                    base_query += f" LIMIT {limit_n}"
                applied_order = True
        except Exception:
            # Non-fatal; simply skip TopN ordering if parsing fails
            pass

        # Add order by if present
        if hasattr(kpi_definition, 'order_by') and kpi_definition.order_by:
            # Do not override TopN ordering if already applied
            if not applied_order:
                order_items = []
                for order_item in kpi_definition.order_by:
                    if isinstance(order_item, str):
                        order_items.append(order_item)
                    elif isinstance(order_item, dict) and 'name' in order_item:
                        direction = order_item.get('direction', 'ASC').upper()
                        order_items.append(f"{order_item['name']} {direction}")
                if order_items:
                    base_query += f" ORDER BY {', '.join(order_items)}"
                
        # Add limit if present (do not override TopN limit)
        if hasattr(kpi_definition, 'limit') and kpi_definition.limit and not applied_order:
            base_query += f" LIMIT {kpi_definition.limit}"
        
        # Final validation to ensure we have a valid SQL statement (SELECT or CTE WITH)
        base_query = base_query.strip()
        head = base_query.lstrip().upper()
        if not (head.startswith("SELECT ") or head.startswith("WITH ")):
            self.logger.warning("Invalid SQL statement (neither SELECT nor WITH): " + base_query)
            return "SELECT 1 WHERE 1=0 -- Invalid SQL generated"
            
        self.logger.info(f"[SQL] Generated KPI SQL for '{getattr(kpi_definition, 'name', 'unknown')}': {base_query}")
        return base_query

    def _collect_group_by_items(self, kpi_definition: Any) -> List[str]:
        """
        Centralized GROUP BY resolution precedence:
        1) KPI.group_by
        2) KPI.metadata['fallback_group_by_dimensions']
        3) KPI.dimensions
        4) DataProduct.metadata['fallback_group_by_dimensions'] for KPI.data_product_id
        Returns a list of raw attribute names (not yet resolved to technical columns).
        """
        items: List[str] = []
        # 1) KPI.group_by
        try:
            if hasattr(kpi_definition, 'group_by') and kpi_definition.group_by:
                for group_item in kpi_definition.group_by:
                    if isinstance(group_item, str):
                        items.append(group_item)
                    elif isinstance(group_item, dict) and 'name' in group_item:
                        items.append(group_item['name'])
        except Exception:
            pass
        # 2) KPI.metadata fallback
        if not items:
            try:
                meta = getattr(kpi_definition, 'metadata', {}) or {}
                fgbd = meta.get('fallback_group_by_dimensions')
                if isinstance(fgbd, list) and fgbd:
                    items = [str(x) for x in fgbd if isinstance(x, (str, int, float))]
            except Exception:
                pass
        # 3) KPI.dimensions
        if not items:
            try:
                dims = getattr(kpi_definition, 'dimensions', None)
                if isinstance(dims, list) and dims:
                    items = [str(x) for x in dims if isinstance(x, (str, int, float))]
            except Exception:
                pass
        # 4) DataProduct.metadata fallback
        if not items:
            try:
                dp_id = getattr(kpi_definition, 'data_product_id', None)
                if isinstance(dp_id, str) and dp_id.strip() and getattr(self, 'data_product_provider', None):
                    dp = self.data_product_provider.get(dp_id)
                    dp_meta = None
                    if dp is not None:
                        try:
                            dp_meta = getattr(dp, 'metadata', None)
                        except Exception:
                            dp_meta = None
                        if dp_meta is None and isinstance(dp, dict):
                            dp_meta = dp.get('metadata')
                    if isinstance(dp_meta, dict):
                        fgbd = dp_meta.get('fallback_group_by_dimensions')
                        if isinstance(fgbd, list) and fgbd:
                            items = [str(x) for x in fgbd if isinstance(x, (str, int, float))]
            except Exception:
                pass
        # Deduplicate while preserving order
        try:
            seen: Set[str] = set()
            deduped: List[str] = []
            for it in items:
                s = str(it)
                if s not in seen:
                    seen.add(s)
                    deduped.append(s)
            return deduped
        except Exception:
            return items or []

    def _get_contract_column_aliases(self, data_product_id: Optional[str] = None) -> Dict[str, str]:
        """
        Get column aliases from the contract for a data product.
        Returns a dict with keys: measure, date, version, default_version_value
        This removes hardcoded FI_Star_Schema checks from SQL generation.
        """
        try:
            cpath = self._contract_path()
            if not os.path.exists(cpath):
                return {}
            with open(cpath, "r", encoding="utf-8") as f:
                doc = yaml.safe_load(f)
            aliases = (doc or {}).get("column_aliases", {})
            if isinstance(aliases, dict):
                return aliases
            return {}
        except Exception:
            return {}

    def _contract_path(self, data_product_id: Optional[str] = None) -> str:
        """
        Resolve contract path from the registry's yaml_contract_path.
        This ensures we use the single source of truth in registry_references.
        
        Args:
            data_product_id: Optional product ID to look up specific contract.
                            Defaults to FI Star Schema if not specified.
        """
        try:
            # First, try to get path from loaded registry data
            if self._registry_data and 'data_products' in self._registry_data:
                target_id = data_product_id or 'dp_fi_20250516_001'  # Default to FI Star
                for dp in self._registry_data['data_products']:
                    dp_id = dp.get('product_id', '')
                    # Match by ID or by domain/name containing 'fi_star'
                    if dp_id == target_id or (not data_product_id and 'fi' in dp_id.lower()):
                        contract_path = dp.get('yaml_contract_path') or dp.get('contract_path')
                        if contract_path:
                            # Handle relative paths
                            if not os.path.isabs(contract_path):
                                # Try from CWD (project root)
                                if os.path.exists(contract_path):
                                    return contract_path
                                # Try from project root explicitly
                                proj_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
                                abs_path = os.path.join(proj_root, contract_path)
                                if os.path.exists(abs_path):
                                    return abs_path
                            elif os.path.exists(contract_path):
                                return contract_path
            
            # Fallback: use registry_references path directly (canonical location)
            canonical = "src/registry_references/data_product_registry/data_products/fi_star_schema.yaml"
            if os.path.exists(canonical):
                return canonical
            
            # Last resort: project root relative
            proj_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
            return os.path.join(proj_root, canonical)
        except Exception:
            return "src/registry_references/data_product_registry/data_products/fi_star_schema.yaml"

    def _get_exposed_columns(self, view_name: Optional[str]) -> Optional[Set[str]]:
        """
        Return the set of exposed column labels for a given view from the contract.
        Uses an in-memory cache keyed by lowercase view name.
        """
        try:
            if not isinstance(view_name, str) or not view_name.strip():
                return None
            key = view_name.strip().lower()
            if key in self._view_exposed_columns_cache:
                return self._view_exposed_columns_cache.get(key)
            cpath = self._contract_path()
            if not os.path.exists(cpath):
                return None
            with open(cpath, "r", encoding="utf-8") as f:
                doc = yaml.safe_load(f)
            views = (doc or {}).get("views", [])
            target = None
            for v in views:
                if isinstance(v, dict) and str(v.get("name", "")).strip().lower() == key:
                    target = v
                    break
            # Fallback to FI_Star_View if the requested name isn't present
            if target is None:
                for v in views:
                    if isinstance(v, dict) and v.get("name") == "FI_Star_View":
                        target = v
                        break
            if not isinstance(target, dict):
                return None
            llm_profile = target.get("llm_profile", {}) or {}
            cols = llm_profile.get("exposed_columns") or []
            out: Set[str] = set()
            for c in cols:
                try:
                    s = str(c).strip()
                    # Normalize quotes for comparison/storage, but keep original label
                    if s.startswith('"') and s.endswith('"') and len(s) > 1:
                        s = s[1:-1]
                    if s:
                        out.add(s)
                except Exception:
                    continue
            self._view_exposed_columns_cache[key] = out
            return out
        except Exception:
            return None

    def _resolve_attribute_name(self, attr: str, kpi_definition: Any, view_name: Optional[str]) -> str:
        """
        Resolve a KPI attribute name to an actual column name (neutral).
        - Uses BusinessGlossaryProvider for business-term-to-technical mapping where possible.
        - Avoids any data-product-specific mappings; falls back to safe quoting.
        """
        try:
            raw_attr = (attr or "").strip().strip('"')
            if not raw_attr:
                return '""'

            # Label-first short-circuit: if attr matches a contract-exposed label for the view, use it unchanged
            try:
                if isinstance(view_name, str) and view_name.strip():
                    allowed = self._get_exposed_columns(view_name)
                    if allowed:
                        # Case-insensitive lookup to restore canonical label casing
                        lower_map = {s.lower(): s for s in allowed}
                        canon = lower_map.get(raw_attr.lower())
                        if isinstance(canon, str) and canon:
                            safe = canon.replace('"', '""')
                            return f'"{safe}"'
            except Exception:
                # If contract lookup fails, continue to glossary fallback
                pass

            # Try neutral business glossary mapping first
            try:
                if not hasattr(self, '_glossary_provider') or self._glossary_provider is None:
                    self._glossary_provider = BusinessGlossaryProvider()
                tech = self._glossary_provider.get_technical_mapping(raw_attr, system="duckdb")
                if isinstance(tech, str) and tech.strip():
                    safe = tech.replace('"', '""')
                    return f'"{safe}"'
            except Exception:
                # If glossary is unavailable or unmapped, continue to fallback
                pass

            # Generic measure fallback: use KPI-provided base column when available
            try:
                generic_measures: Set[str] = {"value", "amount", "revenue", "measure", "metric"}
                if raw_attr.lower() in generic_measures:
                    base_col = None
                    if hasattr(kpi_definition, 'base_column') and isinstance(kpi_definition.base_column, str):
                        base_col = kpi_definition.base_column
                    elif hasattr(kpi_definition, 'metadata') and isinstance(kpi_definition.metadata, dict):
                        meta_bc = kpi_definition.metadata.get('base_column')
                        if isinstance(meta_bc, str):
                            base_col = meta_bc
                    # Fallback: extract from calculation.query_template (e.g., 'SUM("[Transaction Value Amount]")')
                    if not base_col and hasattr(kpi_definition, 'calculation') and getattr(kpi_definition, 'calculation'):
                        calc = getattr(kpi_definition, 'calculation')
                        qt = None
                        if isinstance(calc, dict):
                            qt = calc.get('query_template') or calc.get('template')
                        elif isinstance(calc, str):
                            qt = calc
                        if isinstance(qt, str) and qt.strip():
                            # Try to extract a quoted or bracketed column name
                            m = re.search(r'"([^\"]+)"', qt)
                            if m and m.group(1):
                                base_col = m.group(1)
                            else:
                                m2 = re.search(r'\[([^\]]+)\]', qt)
                                if m2 and m2.group(1):
                                    base_col = m2.group(1)

                    if isinstance(base_col, str) and base_col.strip():
                        bc = base_col.strip()
                        if bc.startswith('[') and bc.endswith(']') and len(bc) > 2:
                            bc = bc[1:-1].strip()
                        safe_bc = bc.replace('"', '""')
                        return f'"{safe_bc}"'

                    # Use contract column_aliases for measure fallback
                    try:
                        aliases = self._get_contract_column_aliases()
                        measure_col = aliases.get('measure')
                        if measure_col:
                            return f'"{measure_col}"'
                    except Exception:
                        pass
            except Exception:
                # Ignore and fall through to safe quoting
                pass

            # Neutral fallback: quote original attribute safely
            safe_attr = raw_attr.replace('"', '""')
            return f'"{safe_attr}"'
        except Exception:
            # Best-effort fallback
            safe_attr = (attr or "").replace('"', '""')
            return f'"{safe_attr}"'

    def _resolve_measure_from_kpi(self, kpi_definition: Any) -> Optional[str]:
        """
        Resolve a KPI's primary measure column from available hints without any product-specific logic.
        - Checks kpi_definition.base_column and kpi_definition.metadata.base_column
        - Extracts column from calculation.query_template or calculation string
        Returns quoted column name or None
        """
        try:
            # 1) Explicit base_column
            base_col = None
            if hasattr(kpi_definition, 'base_column') and isinstance(kpi_definition.base_column, str):
                base_col = kpi_definition.base_column
            elif hasattr(kpi_definition, 'metadata') and isinstance(getattr(kpi_definition, 'metadata'), dict):
                meta_bc = kpi_definition.metadata.get('base_column')
                if isinstance(meta_bc, str):
                    base_col = meta_bc

            # 2) Extract from calculation template if needed
            if not base_col and hasattr(kpi_definition, 'calculation') and getattr(kpi_definition, 'calculation'):
                calc = getattr(kpi_definition, 'calculation')
                qt = None
                if isinstance(calc, dict):
                    qt = calc.get('query_template') or calc.get('template')
                elif isinstance(calc, str):
                    qt = calc
                if isinstance(qt, str) and qt.strip():
                    m = re.search(r'"([^\"]+)"', qt)
                    if m and m.group(1):
                        base_col = m.group(1)
                    else:
                        m2 = re.search(r'\[([^\]]+)\]', qt)
                        if m2 and m2.group(1):
                            base_col = m2.group(1)

            # 3) Extract from sql_query if present
            if not base_col and hasattr(kpi_definition, 'sql_query') and kpi_definition.sql_query:
                qt = kpi_definition.sql_query
                # Try to match SUM(col) or SUM("col") or COUNT(DISTINCT col)
                # Match SUM(col)
                m = re.search(r'SUM\s*\(\s*"?([a-zA-Z0-9_]+)"?\s*\)', qt, re.IGNORECASE)
                if m and m.group(1):
                    base_col = m.group(1)
                else:
                    # Match COUNT(DISTINCT col)
                    m_count = re.search(r'COUNT\s*\(\s*DISTINCT\s*"?([a-zA-Z0-9_]+)"?\s*\)', qt, re.IGNORECASE)
                    if m_count and m_count.group(1):
                        base_col = m_count.group(1)

            if isinstance(base_col, str) and base_col.strip():
                bc = base_col.strip()
                if bc.startswith('[') and bc.endswith(']') and len(bc) > 2:
                    bc = bc[1:-1].strip()
                safe_bc = bc.replace('"', '""')
                return f'"{safe_bc}"'

            # Use contract column_aliases for measure fallback
            try:
                aliases = self._get_contract_column_aliases()
                measure_col = aliases.get('measure')
                if measure_col:
                    return f'"{measure_col}"'
            except Exception:
                pass
        except Exception:
            return None
        return None

    async def _get_view_name_from_kpi(self, kpi_definition: Any) -> str:
        """
        Resolve the target view name for a KPI using the Data Governance Agent when available.
        This method intentionally avoids data-product-specific logic; if the governance agent is
        unavailable, it falls back to KPI-provided metadata and finally a neutral default.
        """
        try:
            kpi_name = getattr(kpi_definition, 'name', 'unknown')
            # Prefer Data Governance Agent if connected
            if hasattr(self, 'data_governance_agent') and self.data_governance_agent:
                try:
                    req = KPIViewNameRequest(kpi_name=kpi_name)
                    resp = await self.data_governance_agent.get_view_name_for_kpi(req)
                    view_name = getattr(resp, 'view_name', None)
                    if isinstance(view_name, str) and view_name.strip() and view_name.strip().lower() != 'unknown':
                        return view_name
                except Exception as e:
                    self.logger.warning(f"View name resolution via Data Governance Agent failed for KPI '{kpi_name}': {str(e)}")

            # Fallbacks without embedding product-specific logic
            if hasattr(kpi_definition, 'view_name') and isinstance(kpi_definition.view_name, str) and kpi_definition.view_name.strip():
                return kpi_definition.view_name.strip()
            if hasattr(kpi_definition, 'metadata') and isinstance(kpi_definition.metadata, dict):
                meta_vn = kpi_definition.metadata.get('view_name')
                if isinstance(meta_vn, str) and meta_vn.strip():
                    return meta_vn.strip()

            # Strict mode (Option 1): do not invent view names.
            # If we cannot resolve a view name, return empty so SQL generation can abort loudly.
            self.logger.error(
                f"Unable to resolve view name for KPI '{kpi_name}'. "
                "Data Governance Agent did not provide a view_name and KPI metadata did not include one."
            )
            return ""
        except Exception:
            return ""
    
    def _get_timeframe_condition(self, timeframe: Any) -> Optional[str]:
        """
        Generate a SQL condition for a given timeframe using time_dim attributes.
        Returns a string that references:
        - t.fiscal_year / t.fiscal_quarter for fiscal-aware frames
        - t.year / t.quarter / t.month for calendar frames
        - t."date" for day-based ranges
        """
        if not timeframe:
            return None

        # Normalize timeframe from string or enum-like
        tf: Optional[str] = None
        if isinstance(timeframe, str):
            tf = timeframe.strip().lower()
        elif hasattr(timeframe, 'value'):
            try:
                tf = str(getattr(timeframe, 'value')).strip().lower()
            except Exception:
                tf = None

        # Compute fiscal expressions (match time_dim derivation) for CURRENT_DATE and shifted dates
        def fiscal_exprs(date_sql: str) -> Tuple[str, str]:
            try:
                fsm = int(getattr(self.config, 'fiscal_year_start_month', 1) or 1)
                if fsm < 1 or fsm > 12:
                    fsm = 1
            except Exception:
                fsm = 1
            fy = (
                f"(CASE WHEN EXTRACT(month FROM {date_sql}) >= {fsm} "
                f"THEN EXTRACT(year FROM {date_sql}) ELSE EXTRACT(year FROM {date_sql}) - 1 END)"
            )
            fq = (
                "CAST(FLOOR(((( (CAST(EXTRACT(month FROM "
                f"{date_sql}) AS INTEGER) - {fsm} + 12) % 12) + 1 ) - 1) / 3.0) + 1 AS INTEGER)"
            )
            return fy, fq

        if isinstance(tf, str):
            # Fiscal-aware periods
            if tf in ("this_quarter", "current_quarter"):
                fy, fq = fiscal_exprs("CURRENT_DATE")
                return f"t.fiscal_year = {fy} AND t.fiscal_quarter = {fq}"
            if tf == "last_quarter":
                fy, fq = fiscal_exprs("(CURRENT_DATE - INTERVAL '3 months')")
                return f"t.fiscal_year = {fy} AND t.fiscal_quarter = {fq}"
            if tf in ("this_year", "current_year"):
                fy, _ = fiscal_exprs("CURRENT_DATE")
                return f"t.fiscal_year = {fy}"
            if tf == "last_year":
                fy, _ = fiscal_exprs("(CURRENT_DATE - INTERVAL '1 year')")
                return f"t.fiscal_year = {fy}"

            # Calendar periods
            if tf in ("this_month", "current_month"):
                return "t.year = EXTRACT(year FROM CURRENT_DATE) AND t.month = EXTRACT(month FROM CURRENT_DATE)"
            if tf == "last_month":
                return "t.year = EXTRACT(year FROM (CURRENT_DATE - INTERVAL '1 month')) AND t.month = EXTRACT(month FROM (CURRENT_DATE - INTERVAL '1 month'))"

            # Day-based ranges referenced to time_dim date
            if tf == "last_7_days":
                return "t.\"date\" >= CURRENT_DATE - INTERVAL '7 days' AND t.\"date\" <= CURRENT_DATE"
            if tf == "last_30_days":
                return "t.\"date\" >= CURRENT_DATE - INTERVAL '30 days' AND t.\"date\" <= CURRENT_DATE"
            if tf == "last_90_days":
                return "t.\"date\" >= CURRENT_DATE - INTERVAL '90 days' AND t.\"date\" <= CURRENT_DATE"

            # To-date periods combine fiscal/calendar attribute with date upper bound
            if tf == "year_to_date":
                fy, _ = fiscal_exprs("CURRENT_DATE")
                return f"t.fiscal_year = {fy} AND t.\"date\" <= CURRENT_DATE"
            if tf == "quarter_to_date":
                fy, fq = fiscal_exprs("CURRENT_DATE")
                return f"t.fiscal_year = {fy} AND t.fiscal_quarter = {fq} AND t.\"date\" <= CURRENT_DATE"
            if tf == "month_to_date":
                return "t.year = EXTRACT(year FROM CURRENT_DATE) AND t.month = EXTRACT(month FROM CURRENT_DATE) AND t.\"date\" <= CURRENT_DATE"

        # Unsupported timeframe type
        return None

    def _get_previous_timeframe_condition(self, timeframe: Any) -> Optional[str]:
        """
        Compute the previous timeframe condition relative to the provided timeframe.
        Examples:
        - this/current_quarter -> last_quarter
        - last_quarter -> two quarters ago
        - this/current_month -> last_month
        - last_month -> two months ago
        - this/current_year -> last_year
        - last_year -> two years ago
        - *_to_date -> same to-date cutoff but shifted to the prior unit
        Returns a condition referencing the same time_dim alias 't'.
        """
        # Normalize timeframe to string
        tf: Optional[str] = None
        if isinstance(timeframe, str):
            tf = timeframe.strip().lower()
        elif hasattr(timeframe, 'value'):
            try:
                tf = str(getattr(timeframe, 'value')).strip().lower()
            except Exception:
                tf = None

        # Helper for fiscal expressions (must mirror _get_timeframe_condition)
        def fiscal_exprs(date_sql: str) -> Tuple[str, str]:
            try:
                fsm = int(getattr(self.config, 'fiscal_year_start_month', 1) or 1)
                if fsm < 1 or fsm > 12:
                    fsm = 1
            except Exception:
                fsm = 1
            fy = (
                f"(CASE WHEN EXTRACT(month FROM {date_sql}) >= {fsm} "
                f"THEN EXTRACT(year FROM {date_sql}) ELSE EXTRACT(year FROM {date_sql}) - 1 END)"
            )
            fq = (
                "CAST(FLOOR(((( (CAST(EXTRACT(month FROM "
                f"{date_sql}) AS INTEGER) - {fsm} + 12) % 12) + 1 ) - 1) / 3.0) + 1 AS INTEGER)"
            )
            return fy, fq

        if not tf:
            return None

        # Quarters
        if tf in ("this_quarter", "current_quarter"):
            return self._get_timeframe_condition('last_quarter')
        if tf == "last_quarter":
            fy, fq = fiscal_exprs("(CURRENT_DATE - INTERVAL '6 months')")
            return f"t.fiscal_year = {fy} AND t.fiscal_quarter = {fq}"
        if tf == "quarter_to_date":
            fy, fq = fiscal_exprs("(CURRENT_DATE - INTERVAL '3 months')")
            return f"t.fiscal_year = {fy} AND t.fiscal_quarter = {fq} AND t.\"date\" <= (CURRENT_DATE - INTERVAL '3 months')"

        # Months
        if tf in ("this_month", "current_month"):
            return self._get_timeframe_condition('last_month')
        if tf == "last_month":
            return (
                "t.year = EXTRACT(year FROM (CURRENT_DATE - INTERVAL '2 months')) "
                "AND t.month = EXTRACT(month FROM (CURRENT_DATE - INTERVAL '2 months'))"
            )
        if tf == "month_to_date":
            return (
                "t.year = EXTRACT(year FROM (CURRENT_DATE - INTERVAL '1 month')) "
                "AND t.month = EXTRACT(month FROM (CURRENT_DATE - INTERVAL '1 month')) "
                "AND t.\"date\" <= (CURRENT_DATE - INTERVAL '1 month')"
            )

        # Years
        if tf in ("this_year", "current_year"):
            return self._get_timeframe_condition('last_year')
        if tf == "last_year":
            return "t.year = EXTRACT(year FROM (CURRENT_DATE - INTERVAL '2 years'))"
        if tf == "year_to_date":
            fy, _ = fiscal_exprs("(CURRENT_DATE - INTERVAL '1 year')")
            return f"t.fiscal_year = {fy} AND t.\"date\" <= (CURRENT_DATE - INTERVAL '1 year')"

        # Fallback
        return self._get_timeframe_condition('last_quarter')

    async def generate_sql_for_kpi_comparison(self, kpi_definition: Any, timeframe: Any = None, comparison_type: str = "previous_period", filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate SQL for a KPI comparison (e.g., previous period, year-over-year).

        Returns a dict with keys: sql, kpi_name, comparison_type, transaction_id, success, message
        """
        transaction_id = str(uuid.uuid4())
        kpi_name = getattr(kpi_definition, 'name', 'unknown')
        self.logger.info(f"[TXN:{transaction_id}] Generating comparison SQL for KPI: {kpi_name}, type: {comparison_type}")

        try:
            # Base SQL for KPI (with current timeframe condition embedded via time_dim)
            base_sql_resp = await self.generate_sql_for_kpi(kpi_definition, timeframe=timeframe, filters=filters)
            if not base_sql_resp.get('success'):
                return base_sql_resp
            base_sql = base_sql_resp['sql']

            # Determine comparison type string
            comp_str = None
            ct = comparison_type
            if hasattr(ct, 'value'):
                try:
                    comp_str = str(ct.value).strip().lower()
                except Exception:
                    comp_str = None
            if not comp_str and isinstance(ct, str):
                comp_str = ct.strip().lower()

            # Handle Budget vs Actual by switching Version filter to 'Budget' while keeping the same timeframe
            if comp_str and 'budget' in comp_str:
                try:
                    # Replace any explicit Version='Actual' (case-insensitive) with Version='Budget'
                    pattern = r'(\"Version\"\s*=\s*\')Actual(\')'
                    comparison_sql = re.sub(pattern, r'\1Budget\2', base_sql, flags=re.IGNORECASE)
                    # If no Version filter existed, append one
                    if comparison_sql == base_sql:
                        if ' where ' in base_sql.lower():
                            comparison_sql = base_sql + " AND \"Version\" = 'Budget'"
                        else:
                            comparison_sql = base_sql + " WHERE \"Version\" = 'Budget'"
                    return {
                        'sql': comparison_sql,
                        'kpi_name': kpi_name,
                        'comparison_type': comparison_type,
                        'transaction_id': transaction_id,
                        'success': True,
                        'message': f"Comparison SQL (Budget vs Actual) generated successfully for KPI: {kpi_name}"
                    }
                except Exception as _budget_err:
                    self.logger.warning(f"Budget vs Actual comparison SQL generation fallback to base due to: {_budget_err}")
                    return {
                        'sql': base_sql,
                        'kpi_name': kpi_name,
                        'comparison_type': comparison_type,
                        'transaction_id': transaction_id,
                        'success': True,
                        'message': f"Budget comparison fallback: returning base SQL for KPI: {kpi_name}"
                    }

            # Compute the original timeframe condition and a target comparison timeframe
            orig_cond = self._get_timeframe_condition(timeframe) if timeframe else None
            target_tf = None
            if comp_str:
                if 'month' in comp_str:
                    target_tf = 'last_month'
                elif 'quarter' in comp_str:
                    target_tf = 'last_quarter'
                elif 'year' in comp_str:
                    target_tf = 'last_year'

            # If we cannot determine a target timeframe or original condition, return base SQL
            if not target_tf or not orig_cond:
                self.logger.warning("Comparison timeframe mapping not available; returning base SQL for comparison")
                return {
                    'sql': base_sql,
                    'kpi_name': kpi_name,
                    'comparison_type': comparison_type,
                    'transaction_id': transaction_id,
                    'success': True,
                    'message': f"Comparison SQL generated successfully for KPI: {kpi_name}"
                }

            # Build replacement timeframe condition using time_dim attributes
            # Handle comparison types relative to the selected base timeframe
            replacement_cond = None

            # Normalize base timeframe string (used in all branches below)
            base_tf_str: Optional[str] = None
            if isinstance(timeframe, str):
                base_tf_str = timeframe.strip().lower()
            elif hasattr(timeframe, 'value'):
                try:
                    base_tf_str = str(getattr(timeframe, 'value')).strip().lower()
                except Exception:
                    base_tf_str = None

            # Helper to build fiscal expressions consistent with _get_timeframe_condition
            def _fiscal_exprs(date_sql: str) -> Tuple[str, str]:
                try:
                    fsm = int(getattr(self.config, 'fiscal_year_start_month', 1) or 1)
                    if fsm < 1 or fsm > 12:
                        fsm = 1
                except Exception:
                    fsm = 1
                fy = (
                    f"(CASE WHEN EXTRACT(month FROM {date_sql}) >= {fsm} "
                    f"THEN EXTRACT(year FROM {date_sql}) ELSE EXTRACT(year FROM {date_sql}) - 1 END)"
                )
                fq = (
                    "CAST(FLOOR(((( (CAST(EXTRACT(month FROM "
                    f"{date_sql}) AS INTEGER) - {fsm} + 12) % 12) + 1 ) - 1) / 3.0) + 1 AS INTEGER)"
                )
                return fy, fq

            # Year-over-year: compare to same unit in prior year
            if comp_str and 'year' in comp_str:
                # Normalize base timeframe string
                # Choose anchor date for prior-year same unit
                if base_tf_str in ("last_quarter", "current_quarter", "this_quarter"):
                    # Anchor quarter = (CURRENT_DATE - 1 year) for current quarter, and (-1 year - 3 months) for last quarter
                    anchor = "(CURRENT_DATE - INTERVAL '1 year')" if base_tf_str in ("current_quarter", "this_quarter") else "(CURRENT_DATE - INTERVAL '1 year' - INTERVAL '3 months')"
                    fy, fq = _fiscal_exprs(anchor)
                    replacement_cond = f"t.fiscal_year = {fy} AND t.fiscal_quarter = {fq}"
                elif base_tf_str in ("last_month", "current_month", "this_month"):
                    # Anchor month = (CURRENT_DATE - 1 year) or (CURRENT_DATE - 1 year - 1 month)
                    anchor = "(CURRENT_DATE - INTERVAL '1 year')" if base_tf_str in ("current_month", "this_month") else "(CURRENT_DATE - INTERVAL '1 year' - INTERVAL '1 month')"
                    replacement_cond = (
                        f"t.year = EXTRACT(year FROM {anchor}) AND "
                        f"t.month = EXTRACT(month FROM {anchor})"
                    )
                elif base_tf_str in ("quarter_to_date", "year_to_date", "month_to_date"):
                    # To-date YOY: mirror the same to-date cutoff in the prior year
                    if base_tf_str == "quarter_to_date":
                        fy, fq = _fiscal_exprs("(CURRENT_DATE - INTERVAL '1 year')")
                        replacement_cond = f"t.fiscal_year = {fy} AND t.fiscal_quarter = {fq} AND t.\"date\" <= (CURRENT_DATE - INTERVAL '1 year')"
                    elif base_tf_str == "year_to_date":
                        fy, _ = _fiscal_exprs("(CURRENT_DATE - INTERVAL '1 year')")
                        replacement_cond = f"t.fiscal_year = {fy} AND t.\"date\" <= (CURRENT_DATE - INTERVAL '1 year')"
                    else:  # month_to_date
                        replacement_cond = (
                            "t.year = EXTRACT(year FROM (CURRENT_DATE - INTERVAL '1 year')) "
                            "AND t.month = EXTRACT(month FROM (CURRENT_DATE - INTERVAL '1 year')) "
                            "AND t.\"date\" <= (CURRENT_DATE - INTERVAL '1 year')"
                        )

                # Fallback if base timeframe not recognized
                if not replacement_cond:
                    replacement_cond = self._get_timeframe_condition('last_year')
            # Quarter-over-quarter: previous quarter relative to base timeframe
            elif comp_str and 'quarter' in comp_str:
                if base_tf_str in ("current_quarter", "this_quarter"):
                    replacement_cond = self._get_timeframe_condition('last_quarter')
                elif base_tf_str == "last_quarter":
                    # Two quarters ago
                    fy, fq = _fiscal_exprs("(CURRENT_DATE - INTERVAL '6 months')")
                    replacement_cond = f"t.fiscal_year = {fy} AND t.fiscal_quarter = {fq}"
                elif base_tf_str == "quarter_to_date":
                    fy, fq = _fiscal_exprs("(CURRENT_DATE - INTERVAL '3 months')")
                    replacement_cond = f"t.fiscal_year = {fy} AND t.fiscal_quarter = {fq} AND t.\"date\" <= (CURRENT_DATE - INTERVAL '3 months')"
                else:
                    replacement_cond = self._get_timeframe_condition('last_quarter')
            # Month-over-month: previous month relative to base timeframe
            elif comp_str and 'month' in comp_str:
                if base_tf_str in ("current_month", "this_month"):
                    replacement_cond = self._get_timeframe_condition('last_month')
                elif base_tf_str == "last_month":
                    # Two months ago
                    replacement_cond = (
                        "t.year = EXTRACT(year FROM (CURRENT_DATE - INTERVAL '2 months')) "
                        "AND t.month = EXTRACT(month FROM (CURRENT_DATE - INTERVAL '2 months'))"
                    )
                elif base_tf_str == "month_to_date":
                    replacement_cond = (
                        "t.year = EXTRACT(year FROM (CURRENT_DATE - INTERVAL '1 month')) "
                        "AND t.month = EXTRACT(month FROM (CURRENT_DATE - INTERVAL '1 month')) "
                        "AND t.\"date\" <= (CURRENT_DATE - INTERVAL '1 month')"
                    )
                else:
                    replacement_cond = self._get_timeframe_condition('last_month')
            else:
                # Non-YOY mappings use the simple previous unit mapping above
                replacement_cond = self._get_timeframe_condition(target_tf)
            if not replacement_cond:
                return {
                    'sql': base_sql,
                    'kpi_name': kpi_name,
                    'comparison_type': comparison_type,
                    'transaction_id': transaction_id,
                    'success': True,
                    'message': f"Comparison SQL generated successfully for KPI: {kpi_name}"
                }

            # Replace only the first occurrence of the current timeframe condition with the comparison one
            if orig_cond in base_sql:
                comparison_sql = base_sql.replace(orig_cond, replacement_cond, 1)
            else:
                # If not found verbatim (spacing differences), return base SQL as a safe fallback
                self.logger.warning("Original timeframe condition not found for replacement; returning base SQL")
                comparison_sql = base_sql

            return {
                'sql': comparison_sql,
                'kpi_name': kpi_name,
                'comparison_type': comparison_type,
                'transaction_id': transaction_id,
                'success': True,
                'message': f"Comparison SQL generated successfully for KPI: {kpi_name}"
            }
        except Exception as e:
            error_msg = f"Error generating comparison SQL for KPI {kpi_name}: {str(e)}"
            self.logger.error(f"[TXN:{transaction_id}] {error_msg}\n{traceback.format_exc()}")
            return {
                'sql': "",
                'kpi_name': kpi_name,
                'comparison_type': comparison_type,
                'transaction_id': transaction_id,
                'success': False,
                'message': error_msg,
                'error': str(e)
            }
        
    def _replace_date_conditions(self, sql: str, new_start_date: str, new_end_date: str) -> str:
        """
        Replace date conditions in SQL with new dates for comparison.
        
        Args:
            sql: Original SQL
            new_start_date: New start date expression
            new_end_date: New end date expression
            
        Returns:
            SQL with updated date conditions
        """
        # Simple replacement for common date patterns
        # This is a simplified approach - in a real system, we would use a proper SQL parser
        sql_lower = sql.lower()
        
        # Look for date range conditions
        if "between" in sql_lower and "and" in sql_lower:
            # Try to find and replace BETWEEN date1 AND date2 pattern
            pattern = r"(\w+)\s+between\s+'([^']+)'\s+and\s+'([^']+)'"  
            replacement = f"\1 BETWEEN {new_start_date} AND {new_end_date}"
            comparison_sql = re.sub(pattern, replacement, sql, flags=re.IGNORECASE)
        elif ">= '" in sql or "<= '" in sql:
            # Try to find and replace >= 'date' and <= 'date' patterns
            start_pattern = r"(\w+)\s*>=\s*'([^']+)'"
            end_pattern = r"(\w+)\s*<=\s*'([^']+)'"
            
            # Replace start date condition
            comparison_sql = re.sub(start_pattern, f"\1 >= {new_start_date}", sql, flags=re.IGNORECASE)
            # Replace end date condition
            comparison_sql = re.sub(end_pattern, f"\1 <= {new_end_date}", comparison_sql, flags=re.IGNORECASE)
        else:
            # If we can't find date patterns, return original SQL with a comment
            comparison_sql = f"-- Unable to automatically modify date conditions for comparison\n{sql}"
            self.logger.warning("Could not identify date conditions in SQL for comparison")
            
        return comparison_sql

    async def _ensure_bq_connected(self) -> bool:
        """Return a connected BigQueryManager, creating and caching it on first call."""
        if self._bq_manager is not None:
            return True
        try:
            from src.database.backends.bigquery_manager import BigQueryManager
            import os
            creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")
            self._bq_manager = BigQueryManager({}, logger=self.logger)
            ok = await self._bq_manager.connect({"service_account_json_path": creds_path} if creds_path else {})
            if not ok:
                self._bq_manager = None
                self.logger.warning("BigQueryManager failed to connect")
            return ok
        except Exception as e:
            self.logger.error(f"Error creating BigQueryManager: {e}")
            self._bq_manager = None
            return False

    async def execute_sql(self, sql_query: Union[str, 'SQLExecutionRequest'], parameters: Optional[Dict[str, Any]] = None, principal_context=None) -> Dict[str, Any]:
        """
        Execute a SQL query using the embedded DuckDBManager (or BigQueryManager when the SQL
        contains fully-qualified BigQuery table references).  Returns a protocol-compliant dict
        with columns, rows, row_count, execution_time, and success flag.
        """
        transaction_id = str(uuid.uuid4())
        # Normalize request
        if not isinstance(sql_query, str):
            if hasattr(sql_query, 'sql'):
                parameters = getattr(sql_query, 'parameters', parameters)
                sql_query = sql_query.sql
            elif hasattr(sql_query, 'sql_query'):
                parameters = getattr(sql_query, 'parameters', parameters)
                sql_query = sql_query.sql_query
            else:
                return {"transaction_id": transaction_id, "sql": "", "columns": [], "rows": [], "row_count": 0, "execution_time": 0, "query_time_ms": 0, "success": False, "status": "error", "message": "Invalid SQL request payload", "data": []}

        if not isinstance(sql_query, str) or not sql_query.strip():
            return {
                "transaction_id": transaction_id,
                "sql": sql_query or "",
                "columns": [],
                "rows": [],
                "row_count": 0,
                "execution_time": 0,
                "query_time_ms": 0,
                "success": False,
                "status": "error",
                "message": "Invalid SQL request: empty query",
                "data": []
            }

        normalized_sql = sql_query.lstrip().upper()
        if not (normalized_sql.startswith("SELECT") or normalized_sql.startswith("WITH")):
            return {
                "transaction_id": transaction_id,
                "sql": sql_query,
                "columns": [],
                "rows": [],
                "row_count": 0,
                "execution_time": 0,
                "query_time_ms": 0,
                "success": False,
                "status": "error",
                "message": "Invalid SQL statement: only SELECT/WITH queries are permitted",
                "data": []
            }

        try:
            # ── BigQuery routing ────────────────────────────────────────────────
            # Detect fully-qualified BigQuery references: `project.dataset.table`
            import re as _re
            _BQ_PATTERN = _re.compile(r'`[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+\.[a-zA-Z0-9_.-]+`')
            if _BQ_PATTERN.search(sql_query):
                self.logger.info(f"[TXN:{transaction_id}] Routing to BigQuery (detected BQ table reference)")
                bq_ok = await self._ensure_bq_connected()
                if bq_ok and self._bq_manager is not None:
                    t0 = time.time()
                    try:
                        df = await self._bq_manager.execute_query(sql_query, parameters or {}, transaction_id)
                        exec_ms = (time.time() - t0) * 1000.0
                        columns = list(getattr(df, "columns", [])) if hasattr(df, "columns") else []
                        rows = df.to_dict(orient="records") if hasattr(df, "to_dict") else (df if isinstance(df, list) else [])
                        return {
                            "transaction_id": transaction_id,
                            "sql": sql_query,
                            "columns": columns,
                            "rows": rows,
                            "row_count": len(rows),
                            "execution_time": exec_ms,
                            "query_time_ms": exec_ms,
                            "success": True,
                            "status": "success",
                            "message": f"BigQuery executed in {exec_ms:.2f} ms",
                            "data": rows,
                        }
                    except Exception as bq_err:
                        self.logger.error(f"[TXN:{transaction_id}] BigQuery execution error: {bq_err}")
                        return {
                            "transaction_id": transaction_id,
                            "sql": sql_query,
                            "columns": [], "rows": [], "row_count": 0,
                            "execution_time": 0, "query_time_ms": 0,
                            "success": False, "status": "error",
                            "message": str(bq_err), "error": str(bq_err), "data": [],
                        }
                else:
                    return {
                        "transaction_id": transaction_id,
                        "sql": sql_query,
                        "columns": [], "rows": [], "row_count": 0,
                        "execution_time": 0, "query_time_ms": 0,
                        "success": False, "status": "error",
                        "message": "BigQuery not available — check GOOGLE_APPLICATION_CREDENTIALS",
                        "data": [],
                    }
            # ── End BigQuery routing ─────────────────────────────────────────────

            # Validate SQL using manager guardrails
            try:
                if hasattr(self, 'db_manager') and self.db_manager is not None and hasattr(self.db_manager, 'validate_sql'):
                    is_valid, val_err = await self.db_manager.validate_sql(sql_query)
                    if not is_valid:
                        return {
                            "transaction_id": transaction_id,
                            "sql": sql_query,
                            "columns": [],
                            "rows": [],
                            "row_count": 0,
                            "execution_time": 0,
                            "query_time_ms": 0,
                            "success": False,
                            "status": "error",
                            "message": val_err or "SQL validation failed",
                            "data": []
                        }
            except Exception:
                pass
            # Ensure a live database connection before executing
            if not await self._ensure_db_connected():
                return {
                    "transaction_id": transaction_id,
                    "sql": sql_query,
                    "columns": [],
                    "rows": [],
                    "row_count": 0,
                    "execution_time": 0,
                    "query_time_ms": 0,
                    "success": False,
                    "status": "error",
                    "message": "Database not connected",
                    "data": []
                }
            t0 = time.time()
            resp = await self.db_manager.execute_query(sql_query, parameters or {}, transaction_id)
            exec_ms = (time.time() - t0) * 1000.0
            # Normalize result to columns + list-of-dicts rows for downstream consumers
            columns: List[str] = []
            rows: List[Dict[str, Any]] = []
            if isinstance(resp, dict):
                # Already normalized by a manager implementation
                columns = resp.get("columns", []) or []
                rows = resp.get("rows", []) or resp.get("data", []) or []
            else:
                # Likely a pandas DataFrame from DuckDBManager.fetchdf()
                try:
                    # Avoid importing pandas at top-level; use duck-typing
                    if hasattr(resp, "to_dict") and hasattr(resp, "columns"):
                        columns = list(getattr(resp, "columns", []))
                        rows = resp.to_dict(orient="records")  # list of dicts
                    elif isinstance(resp, list):
                        # Best-effort: list of rows but unknown columns
                        rows = resp
                    else:
                        # Wrap scalar into a single-row result
                        rows = [resp]
                except Exception:
                    # Fallback to empty on unexpected structures
                    rows = []

            return {
                "transaction_id": transaction_id,
                "sql": sql_query,
                "columns": columns,
                "rows": rows,
                "row_count": len(rows) if isinstance(rows, list) else 0,
                "execution_time": exec_ms,
                "query_time_ms": exec_ms,
                "success": True,
                "status": "success",
                "message": f"Query executed in {exec_ms:.2f} ms",
                "data": rows
            }
        except Exception as e:
            return {
                "transaction_id": transaction_id,
                "sql": sql_query,
                "columns": [],
                "rows": [],
                "row_count": 0,
                "execution_time": 0,
                "query_time_ms": 0,
                "success": False,
                "status": "error",
                "message": str(e),
                "error": str(e),
                "data": []
            }

    async def generate_sql_for_kpi(self, kpi_definition: Any, timeframe: Any = None, filters: Dict[str, Any] = None, topn: Any = None, breakdown: bool = False, override_group_by: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Wrapper that generates SQL for a KPI definition using _generate_sql_for_kpi and returns
        a protocol-compliant response.
        """
        transaction_id = str(uuid.uuid4())
        kpi_name = getattr(kpi_definition, "name", "unknown")
        self.logger.info(f"[TXN:{transaction_id}] Generating SQL for KPI: {kpi_name}, timeframe={timeframe}, topn={topn}, breakdown={breakdown}, override_group_by={override_group_by}")
        try:
            sql = await self._generate_sql_for_kpi(
                kpi_definition,
                timeframe=timeframe,
                filters=filters,
                topn=topn,
                breakdown=breakdown,
                override_group_by=override_group_by,
            )
            if not isinstance(sql, str) or not sql.strip():
                return {"sql": "", "kpi_name": kpi_name, "transaction_id": transaction_id, "success": False, "message": "No SQL generated"}
            return {"sql": sql, "kpi_name": kpi_name, "transaction_id": transaction_id, "success": True, "message": f"SQL generated successfully for KPI: {kpi_name}"}
        except Exception as e:
            self.logger.error(f"[TXN:{transaction_id}] Error generating SQL for KPI {kpi_name}: {str(e)}\n{traceback.format_exc()}")
            return {"sql": "", "kpi_name": kpi_name, "transaction_id": transaction_id, "success": False, "message": str(e), "error": str(e)}

    async def get_kpi_definition(self, kpi_name: str, *, include_mapping: bool = False) -> Optional[Any]:
        """Retrieve a KPI definition using orchestrator-provisioned providers.

        This helper keeps KPI access centralized inside the Data Product Agent so the tests (and other
        agents) can ask for the definition without manually touching RegistryFactory.
        """
        if not isinstance(kpi_name, str) or not kpi_name.strip():
            return None

        # Ensure KPI provider is available
        if self.kpi_provider is None:
            self.kpi_provider = self.registry_factory.get_provider("kpi") or self.registry_factory.get_kpi_provider()
        provider = self.kpi_provider
        if provider is None:
            return None

        # Attempt to load if the provider supports it
        if hasattr(provider, "load") and callable(provider.load):
            try:
                await provider.load()
            except TypeError:
                provider.load()
            except Exception:
                pass

        # Try to retrieve by name (case variants) and id
        candidate = provider.get(kpi_name)
        if not candidate:
            candidate = provider.get(kpi_name.lower()) if hasattr(provider, "get") else None
        if not candidate:
            try:
                all_kpis = provider.get_all()
                if isinstance(all_kpis, list):
                    lname = kpi_name.lower()
                    for k in all_kpis:
                        nm = getattr(k, "name", None)
                        if isinstance(nm, str) and nm.lower() == lname:
                            candidate = k
                            break
            except Exception:
                candidate = None

        if not candidate or not include_mapping:
            return candidate

        # Optionally enrich with governance mapping
        if hasattr(self, "data_governance_agent") and self.data_governance_agent:
            try:
                from src.agents.models.data_governance_models import KPIDataProductMappingRequest

                mapping_req = KPIDataProductMappingRequest(kpi_names=[kpi_name], context={})
                mapping_resp = await self.data_governance_agent.map_kpis_to_data_products(mapping_req)
                if mapping_resp and mapping_resp.mappings:
                    candidate.metadata = candidate.metadata or {}
                    candidate.metadata.setdefault("data_product_mapping", mapping_resp.mappings[0].model_dump())
            except Exception:
                pass

        return candidate

    async def get_kpi_data(self, kpi_definition: Any, timeframe: Any = None, filters: Dict[str, Any] = None, principal_context: Any = None) -> Dict[str, Any]:
        """
        High-level helper to retrieve KPI data (single-value or small resultset) by generating SQL
        and executing it, returning a simplified response with the KPI value.
        """
        transaction_id = str(uuid.uuid4())
        kpi_name = getattr(kpi_definition, "name", "unknown")
        self.logger.info(f"[TXN:{transaction_id}] get_kpi_data start for KPI: {kpi_name}")

        try:
            # Merge principal default filters with provided filters
            try:
                pc_defaults = {}
                if principal_context is not None:
                    if isinstance(getattr(principal_context, 'default_filters', None), dict):
                        pc_defaults = getattr(principal_context, 'default_filters') or {}
                    elif hasattr(principal_context, 'model_dump'):
                        pc_defaults = (principal_context.model_dump() or {}).get('default_filters', {}) or {}
                filters = {**(pc_defaults or {}), **(filters or {})}
            except Exception:
                filters = filters or {}

            # Generate SQL
            gen = await self.generate_sql_for_kpi(kpi_definition=kpi_definition, timeframe=timeframe, filters=filters)
            if not gen.get("success"):
                return {"status": "error", "message": gen.get("message", "Failed to generate SQL"), "kpi_value": None, "metadata": {"transaction_id": transaction_id}}
            sql = gen["sql"]

            # Execute SQL
            exec_resp = await self.execute_sql(sql, principal_context=principal_context)
            if not exec_resp.get("success") and not exec_resp.get("status") == "success":
                msg = exec_resp.get("message") or exec_resp.get("error") or "SQL execution failed"
                return {"status": "error", "message": msg, "kpi_value": None, "metadata": {"transaction_id": transaction_id}}

            rows = exec_resp.get("rows", []) or exec_resp.get("data", [])
            if not rows:
                return {"status": "error", "message": "No data returned for KPI", "kpi_value": None, "metadata": {"transaction_id": transaction_id}}

            first_row = rows[0]
            if isinstance(first_row, dict) and first_row:
                first_col = next(iter(first_row.keys()))
                kpi_value = first_row[first_col]
            elif isinstance(first_row, (list, tuple)) and first_row:
                kpi_value = first_row[0]
            else:
                kpi_value = first_row

            return {
                "status": "success",
                "message": "KPI data retrieved successfully",
                "kpi_value": kpi_value,
                "metadata": {
                    "transaction_id": transaction_id,
                    "row_count": len(rows),
                    "columns": exec_resp.get("columns", []),
                    "execution_time": exec_resp.get("execution_time", 0)
                }
            }
        except Exception as e:
            self.logger.error(f"[TXN:{transaction_id}] get_kpi_data error: {str(e)}\n{traceback.format_exc()}")
            return {"status": "error", "message": f"Error retrieving KPI data: {str(e)}", "kpi_value": None, "metadata": {"transaction_id": transaction_id}}

    async def connect(self, orchestrator=None):
        """
        Connect the agent to required services.
        
        Args:
            orchestrator: Optional orchestrator agent for service discovery
            
        Returns:
            Dict with success status and message
        """
        self.logger.info("Connecting Data Product Agent")
        
        # Store orchestrator reference for service discovery
        if orchestrator:
            self.orchestrator = orchestrator
            self.logger.info("Orchestrator reference stored for service discovery")
            
            # Try to connect to Data Governance Agent via orchestrator
            try:
                self.logger.info("Connecting to Data Governance Agent via orchestrator")
                # First check if the agent is already registered
                agents = await self.orchestrator.list_agents()
                self.logger.info(f"Available agents: {agents}")
                
                if "A9_Data_Governance_Agent" in agents:
                    self.data_governance_agent = await self.orchestrator.get_agent("A9_Data_Governance_Agent", resolve_dependencies=False)
                    if self.data_governance_agent:
                        self.logger.info("Successfully connected to Data Governance Agent")
                    else:
                        self.logger.warning("Data Governance Agent found but could not be retrieved")
                else:
                    self.logger.warning("Data Governance Agent not registered with orchestrator")
                    # Try to create it if not found
                    try:
                        self.logger.info("Attempting to create Data Governance Agent")
                        from src.agents.new.a9_data_governance_agent import A9_Data_Governance_Agent
                        dg_agent_config = {
                            "orchestrator": self.orchestrator,
                            "registry_factory": self.registry_factory
                        }
                        self.data_governance_agent = await A9_Data_Governance_Agent.create(dg_agent_config)
                        await self.orchestrator.register_agent("A9_Data_Governance_Agent", self.data_governance_agent)
                        self.logger.info("Successfully created and registered Data Governance Agent")
                    except Exception as create_err:
                        self.logger.error(f"Failed to create Data Governance Agent: {str(create_err)}")
            except Exception as e:
                self.logger.error(f"Error connecting to Data Governance Agent: {str(e)}")
                self.data_governance_agent = None
        
        return {
            "success": True,
            "message": "Data Product Agent connected successfully"
        }
    
    async def disconnect(self):
        """Disconnect from resources."""
        self.logger.info("Disconnecting Data Product Agent")
        
        # Close database connection if available
        if hasattr(self, 'db_manager') and self.db_manager:
            try:
                await self.db_manager.disconnect()
                self.logger.info("Database connection closed")
            except Exception as e:
                self.logger.error(f"Error closing database connection: {str(e)}")
        
        return {
            "success": True,
            "message": "Data Product Agent disconnected successfully"
        }

    async def get_kpi_comparison_data(self, kpi_definition: Any, timeframe: Any = None, comparison_type: str = "previous_period", filters: Dict[str, Any] = None, principal_context: Any = None) -> Dict[str, Any]:
        """
        High-level helper to retrieve comparison KPI data (e.g., previous period, YoY).
        Keeps SQL generation and execution inside the Data Product Agent.

        Returns dict with: status, message, comparison_value, metadata
        """
        transaction_id = str(uuid.uuid4())
        kpi_name = getattr(kpi_definition, "name", "unknown")
        self.logger.info(f"[TXN:{transaction_id}] get_kpi_comparison_data start for KPI: {kpi_name}, type: {comparison_type}")

        try:
            # 1) Merge principal default filters with provided filters
            try:
                pc_defaults = {}
                if principal_context is not None:
                    if isinstance(getattr(principal_context, 'default_filters', None), dict):
                        pc_defaults = getattr(principal_context, 'default_filters') or {}
                    elif hasattr(principal_context, 'model_dump'):
                        pc_defaults = (principal_context.model_dump() or {}).get('default_filters', {}) or {}
                filters = {**(pc_defaults or {}), **(filters or {})}
            except Exception:
                filters = filters or {}

            # 2) Generate comparison SQL
            gen = await self.generate_sql_for_kpi_comparison(
                kpi_definition=kpi_definition,
                timeframe=timeframe,
                comparison_type=comparison_type,
                filters=filters or {}
            )
            if not gen.get("success"):
                return {
                    "status": "error",
                    "message": gen.get("message", "Failed to generate comparison SQL"),
                    "comparison_value": None,
                    "metadata": {"transaction_id": transaction_id}
                }
            sql = gen["sql"]

            # 3) Execute SQL
            exec_resp = await self.execute_sql(sql, principal_context=principal_context)
            if not exec_resp.get("success") and not exec_resp.get("status") == "success":
                msg = exec_resp.get("message") or exec_resp.get("error") or "SQL execution failed"
                return {
                    "status": "error",
                    "message": msg,
                    "comparison_value": None,
                    "metadata": {"transaction_id": transaction_id}
                }

            rows = exec_resp.get("rows", []) or exec_resp.get("data", [])
            if not rows:
                return {
                    "status": "error",
                    "message": "No comparison data returned for KPI",
                    "comparison_value": None,
                    "metadata": {"transaction_id": transaction_id}
                }

            first_row = rows[0]
            if isinstance(first_row, dict) and first_row:
                first_col = next(iter(first_row.keys()))
                comparison_value = first_row[first_col]
            elif isinstance(first_row, (list, tuple)) and first_row:
                comparison_value = first_row[0]
            else:
                comparison_value = first_row

            return {
                "status": "success",
                "message": "Comparison KPI data retrieved successfully",
                "comparison_value": comparison_value,
                "metadata": {
                    "transaction_id": transaction_id,
                    "row_count": len(rows),
                    "columns": exec_resp.get("columns", []),
                    "execution_time": exec_resp.get("execution_time", 0)
                }
            }
        except Exception as e:
            self.logger.error(f"[TXN:{transaction_id}] get_kpi_comparison_data error: {str(e)}\n{traceback.format_exc()}")
            return {
                "status": "error",
                "message": f"Error retrieving KPI comparison data: {str(e)}",
                "comparison_value": None,
                "metadata": {"transaction_id": transaction_id}
            }

    # ------------------------------------------------------------------
    # KPI Query Validation (Phase 2)
    # ------------------------------------------------------------------

    async def validate_kpi_queries(
        self, request: ValidateKPIQueriesRequest
    ) -> ValidateKPIQueriesResponse:
        """
        Validate KPI queries by executing them against the data source.
        
        This method executes each KPI query and returns:
        - Success/failure status
        - First 5 rows of results (if successful)
        - Error messages and categorization (if failed)
        - Execution time metrics
        
        Args:
            request: Validation request with KPIs and connection details
            
        Returns:
            Validation response with results for each KPI
        """
        request_id = request.request_id
        self.logger.info(f"[{request_id}] Starting KPI query validation for {len(request.kpis)} KPIs")
        
        validation_timestamp = datetime.datetime.utcnow().isoformat() + "Z"
        results = []
        passed_count = 0
        failed_count = 0
        
        # Prepare database manager for validation
        validation_manager = None
        manager_connected = False
        
        try:
            # Build connection settings for validation
            source_system = request.source_system.lower() if request.source_system else "duckdb"
            
            settings = {
                "source_system": source_system,
                "schema": request.schema,
                "project": request.database,
                "connection_overrides": request.connection_overrides or {},
                "connection_config": {},
                "connection_params": {},
            }
            
            # Build connection config for manager factory
            if source_system == "duckdb":
                db_path = settings["connection_overrides"].get("path") or self.db_path
                settings["connection_config"] = {"type": "duckdb", "path": db_path}
            elif source_system == "bigquery":
                settings["connection_config"] = {
                    "type": "bigquery",
                    "project": settings["project"],
                    "dataset": settings["schema"],
                }
                # Add service account path if provided
                if settings["connection_overrides"].get("service_account_json_path"):
                    settings["connection_params"]["service_account_json_path"] = settings["connection_overrides"]["service_account_json_path"]
            
            # Create and connect validation manager
            validation_manager, manager_connected = await self._prepare_inspection_manager(settings)
            
            if not manager_connected:
                self.logger.error(f"[{request_id}] Failed to connect to {source_system}")
                return ValidateKPIQueriesResponse(
                    request_id=request_id,
                    status="error",
                    error_message=f"Failed to connect to {source_system} for validation",
                    results=[],
                    overall_status="validation_error",
                    validation_timestamp=validation_timestamp,
                    can_proceed_to_governance=False,
                    summary={
                        "total": len(request.kpis),
                        "passed": 0,
                        "failed": 0,
                        "errors": len(request.kpis),
                    }
                )
            
            # Validate each KPI query
            for kpi in request.kpis:
                result = await self._validate_single_kpi_query(
                    kpi=kpi,
                    validation_manager=validation_manager,
                    timeout_seconds=request.timeout_seconds,
                    request_id=request_id
                )
                results.append(result)
                
                if result.status == "success":
                    passed_count += 1
                else:
                    failed_count += 1
            
            # Determine overall status
            if passed_count == len(request.kpis):
                overall_status = "all_passed"
            elif failed_count == len(request.kpis):
                overall_status = "all_failed"
            else:
                overall_status = "some_failed"
            
            # Governance Gate: Block if any validation fails
            # All KPIs must be valid to proceed to governance
            can_proceed = (failed_count == 0)
            
            self.logger.info(
                f"[{request_id}] Validation complete: {passed_count} passed, {failed_count} failed. Proceed={can_proceed}"
            )
            
            return ValidateKPIQueriesResponse(
                request_id=request_id,
                status="success",
                results=results,
                overall_status=overall_status,
                validation_timestamp=validation_timestamp,
                can_proceed_to_governance=can_proceed,
                summary={
                    "total": len(request.kpis),
                    "passed": passed_count,
                    "failed": failed_count,
                    "errors": failed_count,
                }
            )
            
        except Exception as e:
            self.logger.error(
                f"[{request_id}] Error during KPI validation: {str(e)}\n{traceback.format_exc()}"
            )
            return ValidateKPIQueriesResponse(
                request_id=request_id,
                status="error",
                error_message=f"Validation error: {str(e)}",
                results=results,
                overall_status="validation_error",
                validation_timestamp=validation_timestamp,
                can_proceed_to_governance=False,
                summary={
                    "total": len(request.kpis),
                    "passed": passed_count,
                    "failed": failed_count,
                    "errors": len(request.kpis) - len(results),
                }
            )
        finally:
            # Cleanup: disconnect validation manager if it's not the main db_manager
            if validation_manager and validation_manager != self.db_manager:
                try:
                    await validation_manager.disconnect()
                    self.logger.info(f"[{request_id}] Validation manager disconnected")
                except Exception as cleanup_err:
                    self.logger.warning(f"[{request_id}] Error disconnecting validation manager: {cleanup_err}")

    async def _validate_single_kpi_query(
        self,
        kpi: Any,
        validation_manager: Any,
        timeout_seconds: int,
        request_id: str
    ) -> KPIQueryValidationResult:
        """
        Validate a single KPI query by executing it.
        
        Args:
            kpi: KPI definition with sql_query
            validation_manager: Database manager to use for execution
            timeout_seconds: Query timeout in seconds
            request_id: Request ID for logging
            
        Returns:
            Validation result for the KPI
        """
        kpi_id = kpi.id
        kpi_name = kpi.name
        sql_query = kpi.sql_query
        
        self.logger.info(f"[{request_id}] Validating KPI {kpi_id}: {kpi_name}")
        
        start_time = time.time()
        
        try:
            # Execute query with timeout
            result = await asyncio.wait_for(
                validation_manager.execute_query(sql_query),
                timeout=timeout_seconds
            )
            
            execution_time_ms = int((time.time() - start_time) * 1000)
            
            # Handle DataFrame response (BigQuery, DuckDB return DataFrames)
            import pandas as pd
            if isinstance(result, pd.DataFrame):
                # Empty DataFrame indicates 0 rows (success), errors are raised as exceptions now
                
                # Convert DataFrame to list of dicts
                row_count = len(result)
                sample_rows = result.head(5).to_dict('records') if not result.empty else []
                
            # Handle dict response (legacy format)
            elif isinstance(result, dict):
                if not result.get("success", False):
                    error_msg = result.get("error", "Unknown error")
                    raise RuntimeError(error_msg)
                
                # Extract rows from dict format
                rows = result.get("rows", []) or result.get("data", [])
                row_count = len(rows)
                sample_rows = rows[:5] if rows else []
                
                # Convert rows to list of dicts if needed
                if sample_rows and not isinstance(sample_rows[0], dict):
                    columns = result.get("columns", [])
                    if columns:
                        sample_rows = [
                            {col: val for col, val in zip(columns, row)}
                            for row in sample_rows
                        ]
            else:
                # Unknown result type
                raise RuntimeError(f"Unexpected result type: {type(result)}")

            return KPIQueryValidationResult(
                kpi_id=kpi_id,
                kpi_name=kpi_name,
                status="success",
                execution_time_ms=execution_time_ms,
                row_count=row_count,
                sample_rows=sample_rows
            )

        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            error_msg = str(e)
            error_type = self._categorize_error(error_msg)
            
            self.logger.warning(f"[{request_id}] KPI {kpi_id} failed: {error_msg}")
            
            return KPIQueryValidationResult(
                kpi_id=kpi_id,
                kpi_name=kpi_name,
                status="error",
                execution_time_ms=execution_time_ms,
                error_message=error_msg,
                error_type=error_type,
            )
            
        except asyncio.TimeoutError:
            execution_time_ms = int((time.time() - start_time) * 1000)
            self.logger.warning(f"[{request_id}] KPI {kpi_id} timed out after {timeout_seconds}s")
            
            return KPIQueryValidationResult(
                kpi_id=kpi_id,
                kpi_name=kpi_name,
                status="timeout",
                execution_time_ms=execution_time_ms,
                error_message=f"Query execution timed out after {timeout_seconds} seconds",
                error_type="timeout",
            )
            
        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            error_msg = str(e)
            error_type = self._categorize_error(error_msg)
            
            self.logger.error(
                f"[{request_id}] KPI {kpi_id} error: {error_msg}\n{traceback.format_exc()}"
            )
            
            return KPIQueryValidationResult(
                kpi_id=kpi_id,
                kpi_name=kpi_name,
                status="error",
                execution_time_ms=execution_time_ms,
                error_message=error_msg,
                error_type=error_type,
            )

    def _categorize_error(self, error_message: str) -> str:
        """
        Categorize error message into a type for better UX.
        
        Args:
            error_message: Error message from query execution
            
        Returns:
            Error category: syntax, column_not_found, permission, timeout, connection, unknown
        """
        error_lower = error_message.lower()
        
        # Column/table not found (Generic + BigQuery specific)
        if any(phrase in error_lower for phrase in [
            "column", "not found", "does not exist", "unknown column",
            "invalid column", "no such column", "table or view not found",
            "unrecognized name", "not found: table", "not found: dataset"
        ]):
            return "column_not_found"
        
        # Syntax errors
        if any(phrase in error_lower for phrase in [
            "syntax error", "parse error", "invalid syntax", "unexpected token"
        ]):
            return "syntax"
        
        # Permission errors
        if any(phrase in error_lower for phrase in [
            "permission denied", "access denied", "insufficient privileges",
            "not authorized", "forbidden"
        ]):
            return "permission"
        
        # Connection errors
        if any(phrase in error_lower for phrase in [
            "connection", "connect", "network", "timeout", "unreachable"
        ]):
            return "connection"
        
        # Timeout
        if "timeout" in error_lower or "timed out" in error_lower:
            return "timeout"
        
        return "unknown"
