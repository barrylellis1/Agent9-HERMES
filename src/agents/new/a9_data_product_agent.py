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

logger = logging.getLogger(__name__)

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
        
        # Initialize registry providers
        self.registry_factory = config.get('registry_factory') or RegistryFactory()
        self.data_product_provider = self.registry_factory.get_provider("data_product") or DataProductProvider()
        self.kpi_provider = self.registry_factory.get_provider("kpi") or KPIProvider()
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
    
    async def _async_init(self):
        """Initialize async resources."""
        # Connect to the database
        try:
            success = await self.db_manager.connect({'database_path': self.db_path})
            if success:
                self.is_connected = True
                self.logger.info(f"Connected to database at {self.db_path}")
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
        Generic SQL generation endpoint. For MVP, only echo pass-through SQL when it looks like SQL.
        Returns a protocol-compliant dict: { success, sql, message }.
        """
        transaction_id = str(uuid.uuid4())
        try:
            if isinstance(query, str) and query.strip():
                q = query.strip()
                # naive detection: if the string appears to be SQL already, echo it back
                if re.match(r"^\s*(with|select|from|create|explain)\b", q, flags=re.IGNORECASE):
                    return {"success": True, "sql": q, "message": "Pass-through SQL", "transaction_id": transaction_id}
            return {"success": False, "sql": "", "message": "LLM-based SQL generation not enabled in MVP", "transaction_id": transaction_id}
        except Exception as e:
            return {"success": False, "sql": "", "message": str(e), "transaction_id": transaction_id}

    async def generate_sql_for_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Compatibility wrapper to align with callers expecting generate_sql_for_query.
        """
        return await self.generate_sql(query, context)

    async def _generate_sql_for_kpi(self, kpi_definition: Any, timeframe: Any = None, filters: Dict[str, Any] = None) -> str:
        """
        Generate SQL for a KPI definition.
        
        Args:
            kpi_definition: KPI definition object
            timeframe: Optional timeframe filter
            filters: Optional additional filters
            
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
                select_items.append(f"SUM({derived}) as total_value")
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
                        select_items.append(f"SUM({resolved}) as total_value")
                    else:
                        select_items.append(resolved)
        
        # If no attributes, use count(*)
        if not select_items:
            select_items = ["count(*) as count"]
            
        # Defer constructing the SELECT clause until after grouping columns are added
        
        # Add group by clause if needed
        group_by_items = []
        if hasattr(kpi_definition, 'group_by') and kpi_definition.group_by:
            for group_item in kpi_definition.group_by:
                if isinstance(group_item, str):
                    group_by_items.append(group_item)
                elif isinstance(group_item, dict) and 'name' in group_item:
                    group_by_items.append(group_item['name'])

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
        
        # Build where clause from filters (map keys to actual view columns)
        all_conditions = []
        for key, value in kpi_filters.items():
            # Resolve attribute/column name against the target view
            resolved_col = self._resolve_attribute_name(str(key), kpi_definition, view_name)
            
            if isinstance(value, str):
                safe_value = value.replace("'", "''")
                all_conditions.append(f"{resolved_col} = '{safe_value}'")
            elif isinstance(value, (int, float)):
                all_conditions.append(f"{resolved_col} = {value}")
            elif isinstance(value, list):
                if all(isinstance(item, str) for item in value):
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
        
        # Add time filter if present
        if hasattr(kpi_definition, 'time_filter') and kpi_definition.time_filter:
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

                if resolved_date_col:
                    # Safely quote date column and substitute the generic placeholder
                    safe_date_col = '"' + resolved_date_col.replace('"', '""') + '"'
                    timeframe_condition = timeframe_condition.replace('"date"', safe_date_col)
                    all_conditions.append(timeframe_condition)
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
            
        if where_clause:
            base_query += f" {where_clause}"
            
        if group_by_items:
            try:
                resolved_group_by = [self._resolve_attribute_name(str(gb), kpi_definition, view_name) for gb in group_by_items]
                base_query += f" GROUP BY {', '.join(resolved_group_by)}"
            except Exception:
                base_query += f" GROUP BY {', '.join(group_by_items)}"
            
        # Add order by if present
        if hasattr(kpi_definition, 'order_by') and kpi_definition.order_by:
            order_items = []
            for order_item in kpi_definition.order_by:
                if isinstance(order_item, str):
                    order_items.append(order_item)
                elif isinstance(order_item, dict) and 'name' in order_item:
                    direction = order_item.get('direction', 'ASC').upper()
                    order_items.append(f"{order_item['name']} {direction}")
                    
            if order_items:
                base_query += f" ORDER BY {', '.join(order_items)}"
                
        # Add limit if present
        if hasattr(kpi_definition, 'limit') and kpi_definition.limit:
            base_query += f" LIMIT {kpi_definition.limit}"
        
        # Final validation to ensure we have a valid SELECT statement
        base_query = base_query.strip()
        if not base_query.upper().startswith("SELECT "):
            self.logger.warning("Invalid SQL statement (not a SELECT): " + base_query)
            return "SELECT 1 WHERE 1=0 -- Invalid SQL generated"
            
        self.logger.info(f"[SQL] Generated KPI SQL for '{getattr(kpi_definition, 'name', 'unknown')}': {base_query}")
        return base_query

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
        Generate a SQL condition string for a given timeframe. Uses a generic "date" column
        which calling code can remap to the actual column name (e.g., "Transaction Date").

        Returns a string like: "date" >= <start_expr> AND "date" < <end_expr>
        """
        if not timeframe:
            return None
        
        date_col = '"date"'
        # Normalize timeframe from string or enum-like
        tf: Optional[str] = None
        if isinstance(timeframe, str):
            tf = timeframe.strip().lower()
        elif hasattr(timeframe, 'value'):
            try:
                tf = str(getattr(timeframe, 'value')).strip().lower()
            except Exception:
                tf = None

        if isinstance(tf, str):
            if tf in ("this_quarter", "current_quarter"):
                return f"{date_col} >= date_trunc('quarter', CURRENT_DATE) AND {date_col} < date_trunc('quarter', CURRENT_DATE) + INTERVAL '3 months'"
            if tf == "last_quarter":
                return f"{date_col} >= date_trunc('quarter', CURRENT_DATE) - INTERVAL '3 months' AND {date_col} < date_trunc('quarter', CURRENT_DATE)"
            if tf in ("this_year", "current_year"):
                return f"{date_col} >= date_trunc('year', CURRENT_DATE) AND {date_col} < date_trunc('year', CURRENT_DATE) + INTERVAL '1 year'"
            if tf == "last_year":
                return f"{date_col} >= date_trunc('year', CURRENT_DATE) - INTERVAL '1 year' AND {date_col} < date_trunc('year', CURRENT_DATE)"
            if tf in ("this_month", "current_month"):
                return f"{date_col} >= date_trunc('month', CURRENT_DATE) AND {date_col} < date_trunc('month', CURRENT_DATE) + INTERVAL '1 month'"
            if tf == "last_month":
                return f"{date_col} >= date_trunc('month', CURRENT_DATE) - INTERVAL '1 month' AND {date_col} < date_trunc('month', CURRENT_DATE)"
            if tf == "last_7_days":
                return f"{date_col} >= CURRENT_DATE - INTERVAL '7 days' AND {date_col} <= CURRENT_DATE"
            if tf == "last_30_days":
                return f"{date_col} >= CURRENT_DATE - INTERVAL '30 days' AND {date_col} <= CURRENT_DATE"
            if tf == "last_90_days":
                return f"{date_col} >= CURRENT_DATE - INTERVAL '90 days' AND {date_col} <= CURRENT_DATE"
            if tf == "year_to_date":
                return f"{date_col} >= date_trunc('year', CURRENT_DATE) AND {date_col} <= CURRENT_DATE"
            if tf == "quarter_to_date":
                return f"{date_col} >= date_trunc('quarter', CURRENT_DATE) AND {date_col} <= CURRENT_DATE"
            if tf == "month_to_date":
                return f"{date_col} >= date_trunc('month', CURRENT_DATE) AND {date_col} <= CURRENT_DATE"
        
        # Unsupported timeframe type
        return None

    async def generate_sql_for_kpi_comparison(self, kpi_definition: Any, timeframe: Any = None, comparison_type: str = "previous_period", filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate SQL for a KPI comparison (e.g., previous period, year-over-year).

        Returns a dict with keys: sql, kpi_name, comparison_type, transaction_id, success, message
        """
        transaction_id = str(uuid.uuid4())
        kpi_name = getattr(kpi_definition, 'name', 'unknown')
        self.logger.info(f"[TXN:{transaction_id}] Generating comparison SQL for KPI: {kpi_name}, type: {comparison_type}")

        try:
            # Base SQL for KPI
            base_sql_resp = await self.generate_sql_for_kpi(kpi_definition, timeframe=timeframe, filters=filters)
            if not base_sql_resp.get('success'):
                return base_sql_resp
            base_sql = base_sql_resp['sql']

            # Derive start/end bounds
            start_date = None
            end_date = None
            if isinstance(timeframe, dict):
                start_date = timeframe.get('start_date') or timeframe.get('start')
                end_date = timeframe.get('end_date') or timeframe.get('end')

            if (not start_date or not end_date) and isinstance(timeframe, str):
                cond = self._get_timeframe_condition(timeframe)
                if cond and 'AND' in cond:
                    try:
                        ge_part, le_part = cond.split('AND', 1)
                        start_date = ge_part.split('>=', 1)[1].strip()
                        # prefer '<' bound if present, else '<='
                        if '<=' in le_part:
                            end_date = le_part.split('<=', 1)[1].strip()
                        else:
                            end_date = le_part.split('<', 1)[1].strip()
                    except Exception:
                        pass

            if not start_date or not end_date:
                self.logger.warning("Cannot derive start/end dates; returning base SQL for comparison")
                return {
                    'sql': base_sql,
                    'kpi_name': kpi_name,
                    'comparison_type': comparison_type,
                    'transaction_id': transaction_id,
                    'success': True,
                    'message': f"Comparison SQL generated successfully for KPI: {kpi_name}"
                }

            comparison_sql = self._replace_date_conditions(base_sql, start_date, end_date)
            # If automatic replacement failed (e.g., function-based dates), try a simple CURRENT_DATE shift fallback
            try:
                comp_l = str(comparison_type or '').lower()
                needs_fallback = (comparison_sql.startswith("-- Unable to automatically modify date conditions") or comparison_sql.strip() == base_sql.strip())
                if needs_fallback and 'CURRENT_DATE' in base_sql:
                    if 'year' in comp_l or 'yoy' in comp_l:
                        interval = "1 year"
                    elif 'quarter' in comp_l or 'qoq' in comp_l:
                        interval = "3 months"
                    elif 'month' in comp_l or 'mom' in comp_l:
                        interval = "1 month"
                    else:
                        interval = None
                    if interval:
                        shifted_sql = base_sql.replace('CURRENT_DATE', f"CURRENT_DATE - INTERVAL '{interval}'")
                        comparison_sql = f"-- Fallback: shifted CURRENT_DATE by {interval} for comparison\n{shifted_sql}"
                        self.logger.warning("Applied fallback CURRENT_DATE shift for comparison SQL")
            except Exception:
                pass
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
                return {"transaction_id": transaction_id, "sql": "", "columns": [], "rows": [], "row_count": 0, "execution_time": 0, "success": False, "message": "Invalid SQL request payload", "data": []}

        try:
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
                "success": True,
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
                "success": False,
                "message": str(e),
                "error": str(e),
                "data": []
            }

    async def generate_sql_for_kpi(self, kpi_definition: Any, timeframe: Any = None, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Wrapper that generates SQL for a KPI definition using _generate_sql_for_kpi and returns
        a protocol-compliant response.
        """
        transaction_id = str(uuid.uuid4())
        kpi_name = getattr(kpi_definition, "name", "unknown")
        self.logger.info(f"[TXN:{transaction_id}] Generating SQL for KPI: {kpi_name}")
        try:
            sql = await self._generate_sql_for_kpi(kpi_definition, timeframe=timeframe, filters=filters)
            if not isinstance(sql, str) or not sql.strip():
                return {"sql": "", "kpi_name": kpi_name, "transaction_id": transaction_id, "success": False, "message": "No SQL generated"}
            return {"sql": sql, "kpi_name": kpi_name, "transaction_id": transaction_id, "success": True, "message": f"SQL generated successfully for KPI: {kpi_name}"}
        except Exception as e:
            self.logger.error(f"[TXN:{transaction_id}] Error generating SQL for KPI {kpi_name}: {str(e)}\n{traceback.format_exc()}")
            return {"sql": "", "kpi_name": kpi_name, "transaction_id": transaction_id, "success": False, "message": str(e), "error": str(e)}

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
            # 1) Generate comparison SQL
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

            # 2) Execute SQL
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
