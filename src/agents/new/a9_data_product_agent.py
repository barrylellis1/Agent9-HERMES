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
                        # Request LLM Service Agent with OpenAI config so factory creates it with the right provider
                        self.llm_service_agent = await self.orchestrator.get_agent(
                            "A9_LLM_Service_Agent",
                            {"provider": "openai", "model_name": "gpt-4-turbo", "api_key_env_var": "OPENAI_API_KEY"}
                        )
                    except Exception:
                        self.llm_service_agent = None
                    if not getattr(self, 'llm_service_agent', None):
                        try:
                            from src.agents.a9_llm_service_agent import A9_LLM_Service_Agent
                            # Switch provider to OpenAI and use OPENAI_API_KEY
                            self.llm_service_agent = await A9_LLM_Service_Agent.create({
                                "provider": "openai",
                                "model_name": "gpt-4-turbo",
                                "api_key_env_var": "OPENAI_API_KEY"
                            })
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
                CREATE TABLE IF NOT EXISTS time_dim AS
                WITH bounds AS (
                    SELECT DATE '2021-01-01' AS start_date, DATE '2026-12-31' AS end_date
                ), series AS (
                    SELECT start_date + gs*INTERVAL 1 DAY AS dt
                    FROM bounds, generate_series(0, DATEDIFF('day', start_date, end_date)) AS s(gs)
                )
                SELECT
                    dt AS "date",
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
                ok = await self.db_manager.register_data_source({
                    "type": "csv",
                    "path": csv_path,
                    "schema": schema,
                    "table_name": table_name
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
            # Derive primary measure column
            derived = self._resolve_measure_from_kpi(kpi_definition)
            if not derived:
                # Pragmatic fallback for FI_Star_Schema
                try:
                    dp_id = getattr(kpi_definition, 'data_product_id', None)
                    if isinstance(dp_id, str) and dp_id.strip().lower() == 'fi_star_schema':
                        derived = '"Transaction Value Amount"'
                except Exception:
                    derived = None
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
        
        # Interim default: ensure Version filter defaults to 'Actual' for FI Star Schema if unspecified
        try:
            dp_id = getattr(kpi_definition, 'data_product_id', None)
            has_version = any(str(k).strip().lower() == 'version' for k in kpi_filters.keys()) if isinstance(kpi_filters, dict) else False
            if isinstance(dp_id, str) and dp_id.strip().lower() == 'fi_star_schema' and not has_version:
                kpi_filters['Version'] = 'Actual'
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

                # Product-aware fallback: if KPI belongs to FI_Star_Schema and no explicit date column,
                # use the canonical view column "Transaction Date" from FI_Star_View.
                if not resolved_date_col:
                    try:
                        dp_id = getattr(kpi_definition, 'data_product_id', None)
                        if isinstance(dp_id, str) and dp_id.strip().lower() == 'fi_star_schema':
                            resolved_date_col = 'Transaction Date'
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

    def _contract_path(self) -> str:
        """Resolve the FI Star contract path similarly to Deep Analysis Agent."""
        try:
            here = os.path.dirname(__file__)
            # From src/agents/new -> src
            src_dir = os.path.abspath(os.path.join(here, "..", ".."))
            candidate = os.path.join(src_dir, "contracts", "fi_star_schema.yaml")
            if os.path.exists(candidate):
                return candidate
            # Fallback: from project root -> src/contracts/...
            proj_root = os.path.abspath(os.path.join(here, "..", "..", ".."))
            alt2 = os.path.join(proj_root, "contracts", "fi_star_schema.yaml")
            if os.path.exists(alt2):
                return alt2
            # Fallback: CWD-based absolute
            cwd_alt = os.path.abspath(os.path.join(os.getcwd(), "src", "contracts", "fi_star_schema.yaml"))
            if os.path.exists(cwd_alt):
                return cwd_alt
            # Last resort: repo-relative string (may still work if cwd = project root)
            return "src/contracts/fi_star_schema.yaml"
        except Exception:
            return "src/contracts/fi_star_schema.yaml"

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

                    # Pragmatic product-specific fallback: if KPI belongs to FI_Star_Schema,
                    # use the canonical measure alias used in FI_Star_View.
                    try:
                        dp_id = getattr(kpi_definition, 'data_product_id', None)
                        if isinstance(dp_id, str) and dp_id.strip().lower() == 'fi_star_schema':
                            return '"Transaction Value Amount"'
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

            if isinstance(base_col, str) and base_col.strip():
                bc = base_col.strip()
                if bc.startswith('[') and bc.endswith(']') and len(bc) > 2:
                    bc = bc[1:-1].strip()
                safe_bc = bc.replace('"', '""')
                return f'"{safe_bc}"'

            # Pragmatic product-specific fallback: if KPI belongs to FI_Star_Schema,
            # use the canonical measure alias used in FI_Star_View.
            try:
                dp_id = getattr(kpi_definition, 'data_product_id', None)
                if isinstance(dp_id, str) and dp_id.strip().lower() == 'fi_star_schema':
                    return '"Transaction Value Amount"'
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

            # Neutral default
            base = str(kpi_name or 'unknown').strip().lower().replace(' ', '_')
            return f"view_{base}"
        except Exception:
            return "view_unknown"
    
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

    async def execute_sql(self, sql_query: Union[str, 'SQLExecutionRequest'], parameters: Optional[Dict[str, Any]] = None, principal_context=None) -> Dict[str, Any]:
        """
        Execute a SQL query using the embedded DuckDBManager. Returns a protocol-compliant dict
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
        self.logger.info(f"[TXN:{transaction_id}] Generating SQL for KPI: {kpi_name}")
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
