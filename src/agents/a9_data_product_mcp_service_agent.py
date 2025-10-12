"""
DEPRECATION WARNING
This module is deprecated and will be removed after 2025-11-30.
Reason: SQL generation/execution must occur exclusively in the MCP Service per PRD.
Replacement: Use MCP client/service via `src/agents/new/a9_data_product_agent.py` and `src/database/backends/`.
arch-allow-db-in-agent file

A9_Data_Product_MCP_Service_Agent - Centralized data access for SAP Datasphere data.

This agent provides a standardized interface for data access operations,
acting as the single authoritative layer for all dynamic SQL generation
using registry-driven SELECT, JOIN, GROUP BY, and aggregation SQL.

It is designed to provide business-ready, summarized, filtered, and pre-joined
data products to other agents and services within the system.

Protocol compliance:
- All request/response models inherit from A9AgentBaseModel
- Factory method pattern for orchestrator-driven lifecycle
- Standardized error handling and logging
- Protocol-compliant request/response models
"""

import asyncio
import datetime
import json
import time
import logging
import os
import re
import sys
import traceback
import uuid
from pathlib import Path
from typing import Any, ClassVar, Dict, List, Optional, Tuple, Union

import pandas as pd
import yaml

# Import database manager components
# Note: Agent is designed for orchestrator-driven registry pattern per PRD
from src.database.manager_factory import DatabaseManagerFactory
from src.database.manager_interface import DatabaseManager

# Import shared models
from src.agents.shared.a9_agent_base_model import (
    A9AgentBaseModel, A9AgentBaseRequest, A9AgentBaseResponse
)

# Import config models
from src.agents.agent_config_models import A9_Data_Product_MCP_Service_Config

# Import registry components
from src.registry.factory import RegistryFactory
from src.registry.providers.principal_provider import PrincipalProfileProvider as PrincipalProvider
from src.registry.providers.business_process_provider import BusinessProcessProvider
from src.registry.models.data_product import DataProduct
from src.registry.providers.registry_provider import RegistryProvider
from src.registry.providers.kpi_provider import KPIProvider as KpiProvider
from src.registry.models.data_product import DataProduct

# Protocol-Compliant Request/Response Models
class SQLExecutionRequest(A9AgentBaseRequest):
    """Request model for SQL execution with protocol compliance"""
    sql: str
    context: Optional[Dict[str, Any]] = None
    principal_context: Optional[Dict[str, Any]] = None
    yaml_contract_text: Optional[str] = None


class SQLExecutionResponse(A9AgentBaseResponse):
    """Response model for SQL execution results with protocol compliance"""
    columns: List[str] = []
    rows: List[List[Any]] = []
    row_count: int = 0
    query_time_ms: Optional[float] = None
    human_action_required: bool = False
    human_action_type: Optional[str] = None
    human_action_context: Optional[Dict[str, Any]] = None
    
    @classmethod
    def from_result(cls, request_id: str, result: Dict[str, Any]) -> 'SQLExecutionResponse':
        """Create successful response from DuckDB execution result"""
        columns = result.get('columns', [])
        rows = result.get('rows', [])
        
        return cls.success(
            request_id=request_id,
            message="SQL execution successful",
            columns=columns,
            rows=rows,
            row_count=len(rows),
            query_time_ms=result.get('query_time_ms')
        )
    
    @classmethod
    def success(cls, request_id: str, message: str = "SQL execution successful", **kwargs) -> 'SQLExecutionResponse':
        """Create a successful response with the provided fields"""
        return cls(
            status="success",
            request_id=request_id,
            message=message,
            **kwargs
        )
    
    @classmethod
    def error(cls, request_id: str, error_message: str, **kwargs) -> 'SQLExecutionResponse':
        """Create an error response with the provided fields"""
        return cls(
            status="error",
            request_id=request_id,
            message=error_message,
            error=error_message,
            error_message=error_message,
            columns=[],
            rows=[],
            row_count=0,
            **kwargs
        )


class DataProductRequest(A9AgentBaseRequest):
    """Request model for data product operations with protocol compliance"""
    product_id: str
    filters: Optional[Dict[str, Any]] = None
    aggregation_level: Optional[str] = None
    format: str = "json"
    limit: Optional[int] = None
    yaml_contract_text: Optional[str] = None
    sql_query: Optional[str] = None


class DataProductResponse(A9AgentBaseResponse):
    """Response model for data product operations with protocol compliance"""
    product_id: str
    columns: List[str] = []
    rows: List[List[Any]] = []
    row_count: int = 0
    query_time_ms: Optional[float] = None
    human_action_required: bool = False
    human_action_type: Optional[str] = None
    human_action_context: Optional[Dict[str, Any]] = None
    data_governance_metadata: Optional[Dict[str, Any]] = None
    
    @classmethod
    def from_result(cls, request_id: str, product_id: str, result: Dict[str, Any]) -> 'DataProductResponse':
        """Create successful response from data product result"""
        columns = result.get('columns', [])
        rows = result.get('rows', [])
        
        # Format success message based on row count
        row_count = len(rows)
        if row_count == 1:
            message = f"Successfully retrieved 1 row for data product: {product_id}"
        else:
            message = f"Successfully retrieved {row_count} rows for data product: {product_id}"
        
        # Add governance metadata if available
        governance_metadata = None
        if 'governance_metadata' in result:
            governance_metadata = result['governance_metadata']
        
        return cls.success(
            request_id=request_id,
            product_id=product_id,
            message=message,
            columns=columns,
            rows=rows,
            row_count=row_count,
            query_time_ms=result.get('query_time_ms'),
            data_governance_metadata=governance_metadata
        )
    
    @classmethod
    def success(cls, request_id: str, product_id: str, message: str = "Data product retrieved successfully", **kwargs) -> 'DataProductResponse':
        """Create a successful response with the provided fields"""
        return cls(
            status="success",
            request_id=request_id,
            product_id=product_id,
            message=message,
            **kwargs
        )
    
    @classmethod
    def error(cls, request_id: str, error_message: str, product_id: str = "", **kwargs) -> 'DataProductResponse':
        """Create an error response with the provided fields"""
        return cls(
            status="error",
            request_id=request_id,
            product_id=product_id,
            message=error_message,
            error=error_message,
            error_message=error_message,
            columns=[],
            rows=[],
            row_count=0,
            **kwargs
        )


class A9_Data_Product_MCP_Service_Agent:
    """
    Agent for centralized data access operations with DuckDB backend.
    
    This agent handles all data access operations for Agent9, providing:
    - Centralized SQL execution with DuckDB backend
    - Registry-driven data product access
    - Protocol-compliant request/response handling
    - Logging and auditability
    - Orchestrator integration via async factory pattern
    
    Implementation is fully A9 Agent Design Standards compliant:
    - Async factory method for orchestrator-driven lifecycle
    - Protocol-compliant request/response models
    - Structured error handling and logging
    - Business term translation via registry
    - Orchestrator-provided logging
    - Selective async pattern (only API and I/O methods)
    """
    
    # Class reference for registration
    _instance: ClassVar[Optional['A9_Data_Product_MCP_Service_Agent']] = None
    
    @classmethod
    async def create(cls, config: Union[A9_Data_Product_MCP_Service_Config, Dict[str, Any]], logger=None) -> 'A9_Data_Product_MCP_Service_Agent':
        """
        Async factory method to create a Data Product MCP Service Agent instance.
        This follows the A9 Agent Design Standards for orchestrator-driven lifecycle.
        
        Args:
            config: Configuration for the agent, either as config model or dict
            logger: Orchestrator-provided logger instance (optional)
            
        Returns:
            Initialized Data Product MCP Service Agent instance
        """
        # Use provided logger or create a default one if none is provided
        if logger:
            agent_logger = logger
        else:
            agent_logger = logging.getLogger(__name__)
            if not agent_logger.hasHandlers():
                agent_logger.setLevel(logging.INFO)
                handler = logging.StreamHandler(sys.stdout)
                handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
                agent_logger.addHandler(handler)
        
        agent_logger.info("Creating Data Product MCP Service Agent instance")
        
        try:
            # Create a new instance if one doesn't exist or force refresh requested
            if cls._instance is None:
                cls._instance = cls(config, logger=agent_logger)
                await cls._instance._async_init()
                agent_logger.info("Data Product MCP Service Agent instance created successfully")
            else:
                agent_logger.info("Reusing existing Data Product MCP Service Agent instance")
            
            return cls._instance
            
        except Exception as e:
            stack_trace = traceback.format_exc()
            error_msg = f"Failed to create Data Product MCP Service Agent: {str(e)}"
            agent_logger.error(f"{error_msg}\n{stack_trace}")
            raise RuntimeError(error_msg) from e
    
    def __init__(self, config: Union[A9_Data_Product_MCP_Service_Config, Dict[str, Any]], logger=None):
        """
        Initialize the Data Product MCP service agent with configuration.
        
        Note: Do not instantiate directly. Use create() factory method instead.
        
        Args:
            config: Configuration for the agent, either as config model or dict
            logger: Orchestrator-provided logger (optional)
        """
        if isinstance(config, dict):
            self.config = A9_Data_Product_MCP_Service_Config(**config)
        else:
            self.config = config
            
        # Initialize properties
        self.db_manager = None
        self.registry = {}
        self.duckdb_conn = None
        self.principal_context = None
        self.data_directory = None
        self.data_product_views = {}
        
        # Setup logging
        if logger:
            self.logger = logger
        else:
            import logging
            self.logger = logging.getLogger(__name__)
            
        # Handle data_directory as an alias for sap_data_path if needed
        if not hasattr(self.config, 'data_directory'):
            setattr(self.config, 'data_directory', self.config.sap_data_path)
            
        # Assign data_directory from config to instance attribute
        self.data_directory = self.config.data_directory
        
        # Set the data_product_registry path using the registry_path from config
        if hasattr(self.config, 'registry_path') and hasattr(self.config, 'data_product_registry'):
            # Handle the transition to new registry location
            if self.config.registry_path == "src/registry_references" and os.path.exists("src/registry"):
                # Use new registry structure if available
                self.data_product_registry = os.path.join(
                    "src/registry/data_product", os.path.basename(self.config.data_product_registry)
                )
                self.logger.info(f"Using new registry structure path: {self.data_product_registry}")
            else:
                # Use configured path
                self.data_product_registry = os.path.join(
                    self.config.registry_path, self.config.data_product_registry
                )
                self.logger.info(f"Using configured registry path: {self.data_product_registry}")
        else:
            # Fallback to default
            self.data_product_registry = "src/registry/data_product/data_product_registry.csv"
            self.logger.warning(f"No registry path configured, using fallback: {self.data_product_registry}")
    
        # Log initialization
        self.logger.info(f"Data Product MCP Service Agent initialized with data_directory: {self.data_directory} and registry path: {self.data_product_registry}")
        
    async def _async_init(self):
        """
        Async initialization steps that need to be performed after instance creation.
        This method is called by the factory method and should not be called directly.
        """
        return await self._async_initialize()
    
    async def _async_initialize(self):
        """Async initialization logic"""
        self.logger.info("Initializing Data Product MCP Service Agent")
        
        # Run all async initialization tasks
        await self._initialize_database_connection()
        
        # Initialize registry providers for principal and KPI awareness
        self._initialize_registry_providers()
        
        # Initialize duckdb connection for tests
        if hasattr(self, 'db_manager') and self.db_manager and hasattr(self.db_manager, 'connection'):
            self.duckdb_conn = self.db_manager.connection
        
        # Load registry data
        self.registry = {}
        await self._load_registry_data()
        
        self.logger.info(f"Data Product MCP Service Agent initialized with {len(self.registry.get('data_products', []))} data products")
        self.logger.info("Async initialization for Data Product MCP Service Agent completed successfully")
        return True
    
    async def _load_registry_data(self):
        """Load data product registry from YAML file"""
        transaction_id = str(uuid.uuid4())
        self.logger.info(f"[TXN:{transaction_id}] Loading data product registry from: {self.data_product_registry}")
        
        # Initialize registry data structure if needed
        if not hasattr(self, 'registry') or self.registry is None:
            self.registry = {}
        
        # Initialize data products list and status flag
        self.registry['data_products'] = []
        
        try:
            # Check if registry path is a YAML file or determine YAML path from CSV path
            yaml_registry_path = self.data_product_registry
            if yaml_registry_path.endswith('.csv'):
                yaml_registry_path = yaml_registry_path.replace('.csv', '.yaml')
            
            self.logger.info(f"[TXN:{transaction_id}] Attempting to load from YAML registry: {yaml_registry_path}")
            
            # Check if YAML file exists
            if os.path.exists(yaml_registry_path):
                with open(yaml_registry_path, 'r') as file:
                    yaml_data = yaml.safe_load(file)
                
                if yaml_data and 'data_products' in yaml_data and isinstance(yaml_data['data_products'], list):
                    # Load data products from YAML
                    data_products = []
                    
                    for product_data in yaml_data['data_products']:
                        try:
                            # Create DataProduct from YAML data
                            product = DataProduct(**product_data)
                            data_products.append(product)
                            
                            # If product has yaml_contract_path, load detailed definition from contract
                            if hasattr(product, 'yaml_contract_path') and product.yaml_contract_path:
                                try:
                                    contract_path = product.yaml_contract_path
                                    self.logger.info(f"[TXN:{transaction_id}] Loading contract for {product.id} from {contract_path}")
                                    
                                    if os.path.exists(contract_path):
                                        with open(contract_path, 'r') as contract_file:
                                            contract_data = yaml.safe_load(contract_file)
                                            
                                        # Enrich product with contract data
                                        if contract_data:
                                            # Add tables from contract if available
                                            if 'tables' in contract_data:
                                                product.tables = contract_data['tables']
                                            
                                            # Add views from contract if available 
                                            if 'views' in contract_data:
                                                product.views = contract_data['views']
                                    else:
                                        self.logger.warning(f"[TXN:{transaction_id}] Contract file not found: {contract_path}")
                                except Exception as contract_error:
                                    self.logger.error(f"[TXN:{transaction_id}] Error loading contract for {product.id}: {str(contract_error)}")
                        except Exception as product_error:
                            self.logger.error(f"[TXN:{transaction_id}] Error processing data product: {str(product_error)}\n{traceback.format_exc()}")
                    
                    # Store products in registry
                    self.registry['data_products'] = data_products
                    
                    # Set the flag if we have any products
                    if len(data_products) > 0:
                        self.registry['has_data_products'] = True
                        self.logger.info(f"[TXN:{transaction_id}] Loaded {len(data_products)} data products from YAML registry")
                    else:
                        self.registry['has_data_products'] = False
                        self.logger.warning(f"[TXN:{transaction_id}] No data products found in YAML registry")
                else:
                    self.logger.warning(f"[TXN:{transaction_id}] Invalid YAML registry format or missing data_products section")
                    self.registry['has_data_products'] = False
            else:
                self.logger.warning(f"[TXN:{transaction_id}] YAML registry not found at: {yaml_registry_path}")
                self.registry['has_data_products'] = False
                
                # Try to fall back to CSV if YAML not found
                await self._try_load_legacy_csv_registry()
            
            # If no data products loaded from YAML or CSV, load defaults
            if not self.registry.get('has_data_products', False):
                self._load_default_data_products()
        
        except Exception as e:
            self.logger.error(f"[TXN:{transaction_id}] Error loading registry data: {str(e)}\n{traceback.format_exc()}")
            self.registry['has_data_products'] = False
            self._load_default_data_products()
        
        # Log registry status
        self.logger.info(f"[TXN:{transaction_id}] Registry status: registry={type(self.registry)}, has_data_products={self.registry.get('has_data_products', False)}")
        return self.registry
    
    async def _try_load_legacy_csv_registry(self):
        """Try to load data products from legacy CSV registry if available"""
        transaction_id = str(uuid.uuid4())
        
        try:
            # Check if we have a CSV registry path
            csv_registry_path = None
            if hasattr(self, 'data_product_registry') and self.data_product_registry.endswith('.csv'):
                csv_registry_path = self.data_product_registry
            else:
                # Try to construct CSV path from YAML path
                if hasattr(self, 'data_product_registry'):
                    csv_registry_path = self.data_product_registry.replace('.yaml', '.csv')
            
            if csv_registry_path and os.path.exists(csv_registry_path):
                self.logger.info(f"[TXN:{transaction_id}] Attempting to load legacy CSV registry from: {csv_registry_path}")
                
                # Load CSV into DataFrame
                import pandas as pd
                df = pd.read_csv(csv_registry_path)
                
                if not df.empty:
                    # Convert DataFrame to list of DataProduct objects
                    data_products = []
                    
                    for _, row in df.iterrows():
                        try:
                            # Create dictionary from row
                            product_dict = row.to_dict()
                            
                            # Clean up dictionary (convert NaN to None)
                            product_dict = {k: None if pd.isna(v) else v for k, v in product_dict.items()}
                            
                            # Create DataProduct object
                            product = DataProduct(**product_dict)
                            data_products.append(product)
                            
                        except Exception as product_error:
                            self.logger.error(f"[TXN:{transaction_id}] Error processing CSV data product: {str(product_error)}")
                    
                    # Store products in registry
                    self.registry['data_products'] = data_products
                    
                    # Set flag if we have products
                    if len(data_products) > 0:
                        self.registry['has_data_products'] = True
                        self.logger.info(f"[TXN:{transaction_id}] Loaded {len(data_products)} data products from legacy CSV registry")
                        return True
                    else:
                        self.registry['has_data_products'] = False
                        self.logger.warning(f"[TXN:{transaction_id}] No data products found in legacy CSV registry")
                else:
                    self.logger.warning(f"[TXN:{transaction_id}] Empty CSV registry file")
            else:
                self.logger.warning(f"[TXN:{transaction_id}] Legacy CSV registry not found")
        
        except Exception as e:
            self.logger.error(f"[TXN:{transaction_id}] Error loading legacy CSV registry: {str(e)}")
        
        return False
    
    def _load_default_data_products(self):
        """Load default data products when no registry is available"""
        transaction_id = str(uuid.uuid4())
        self.logger.warning(f"[TXN:{transaction_id}] Loading default data products as fallback")
        
        # Create a single default data product
        try:
            # Define default data product attributes
            product_data = {
                "product_id": "dp_fi_20250516_001",
                "name": "Financial Transactions (Default)",
                "domain": "FI",
                "description": "Default financial transactions data product",
                "tags": ["finance", "default"],
                "last_updated": datetime.now().strftime("%Y-%m-%d")
            }
            
            # Create DataProduct object
            default_product = DataProduct(**product_data)
            
            # Store in registry
            self.registry['data_products'] = [default_product]
            self.registry['has_data_products'] = True
            
            self.logger.info(f"[TXN:{transaction_id}] Loaded default data product: {default_product.id}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"[TXN:{transaction_id}] Error creating default data product: {str(e)}")
            self.registry['has_data_products'] = False
            return False
        
    def _initialize_registry_providers(self):
        """Initialize registry providers for principal and KPI-aware operations"""
        try:
            # Create registry factory instance
            self.registry_factory = RegistryFactory()
            
            # Initialize principal provider
            self.principal_provider = PrincipalProvider()
            
            # Initialize KPI provider
            self.kpi_provider = KpiProvider()
            
            self.logger.info("Registry providers initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize registry providers: {str(e)}")
            
    async def _load_registry_data(self):
        """Load data product registry data from YAML file"""
        self.logger.info(f"Loading data product registry from: {self.data_product_registry}")
        
        # Update the path to use the YAML file instead of CSV
        yaml_registry_path = self.data_product_registry.replace('.csv', '.yaml')
        
        # Initialize the registry data structure
        self.registry['data_products'] = []
        self.registry['has_data_products'] = False
        
        try:
            # Check if the YAML registry file exists
            if os.path.exists(yaml_registry_path):
                self.logger.info(f"Found YAML data product registry at {yaml_registry_path}")
                try:
                    # Load data products from YAML registry
                    with open(yaml_registry_path, 'r') as file:
                        registry_data = yaml.safe_load(file)
                        
                        if registry_data and 'data_products' in registry_data:
                            for product_data in registry_data['data_products']:
                                # Convert each product entry to a DataProduct object
                                product = DataProduct(
                                    id=product_data.get('product_id'),
                                    name=product_data.get('name'),
                                    domain=product_data.get('domain'),
                                    description=product_data.get('description', ''),
                                    owner=product_data.get('domain', 'Unknown'),  # Default to domain if owner not specified
                                    tags=product_data.get('tags', []),
                                )
                                
                                # Add any additional attributes if present
                                if 'yaml_contract_path' in product_data and product_data['yaml_contract_path']:
                                    # If product has a YAML contract, try to load tables/views from it
                                    contract_path = product_data['yaml_contract_path']
                                    if os.path.exists(contract_path):
                                        try:
                                            with open(contract_path, 'r') as contract_file:
                                                contract_data = yaml.safe_load(contract_file)
                                                # Process contract data for tables and views if available
                                                if contract_data:
                                                    if 'tables' in contract_data:
                                                        product.tables = contract_data['tables']
                                                    if 'views' in contract_data:
                                                        product.views = contract_data['views']
                                                    
                                                self.logger.info(f"Loaded contract data for {product.id} from {contract_path}")
                                        except Exception as e:
                                            self.logger.warning(f"Failed to load contract for {product.id}: {str(e)}")
                                
                                # Add the product to the registry
                                self.registry['data_products'].append(product)
                                
                            # Set the flag if we have any products
                            if len(self.registry['data_products']) > 0:
                                self.registry['has_data_products'] = True
                                self.logger.info(f"Loaded {len(self.registry['data_products'])} data products from YAML registry")
                            else:
                                self.logger.warning("No data products found in YAML registry")
                        else:
                            self.logger.warning(f"YAML registry at {yaml_registry_path} does not contain data_products list")
                            
                except Exception as e:
                    self.logger.error(f"Error loading YAML data product registry: {str(e)}")
                    # Fall back to CSV if YAML fails (for backward compatibility)
                    await self._try_load_legacy_csv_registry()
            else:
                self.logger.warning(f"YAML data product registry not found at {yaml_registry_path}, trying CSV fallback")
                # Try to load from CSV as fallback (legacy support)
                await self._try_load_legacy_csv_registry()
                
            # If still no data products, load defaults
            if not self.registry['has_data_products']:
                self._load_default_data_products()
                
        except Exception as e:
            self.logger.error(f"Failed to load data product registry: {str(e)}")
            self._load_default_data_products()
    
    async def _try_load_legacy_csv_registry(self):
        """Try to load data products from legacy CSV registry"""
        try:
            # Check if CSV file exists
            if os.path.exists(self.data_product_registry):
                import csv
                with open(self.data_product_registry, 'r') as file:
                    reader = csv.DictReader(file)
                    for row in reader:
                        try:
                            # Create DataProduct from CSV row
                            product = DataProduct(
                                id=row.get('product_id'),
                                name=row.get('name'),
                                domain=row.get('domain'),
                                description=row.get('description', ''),
                                owner=row.get('domain', 'Unknown'),  # Default to domain
                            )
                            
                            # Handle tags if present
                            if 'tags' in row and row['tags']:
                                product.tags = [tag.strip() for tag in row['tags'].split(';')] if row['tags'] else []
                            
                            # Handle yaml contract if present
                            if 'yaml_contract_path' in row and row['yaml_contract_path']:
                                contract_path = row['yaml_contract_path']
                                if os.path.exists(contract_path):
                                    try:
                                        with open(contract_path, 'r') as contract_file:
                                            contract_data = yaml.safe_load(contract_file)
                                            # Process contract data for tables and views if available
                                            if contract_data:
                                                if 'tables' in contract_data:
                                                    product.tables = contract_data['tables']
                                                if 'views' in contract_data:
                                                    product.views = contract_data['views']
                                                
                                                self.logger.info(f"Loaded contract data for {product.id} from {contract_path}")
                                    except Exception as e:
                                        self.logger.warning(f"Failed to load contract for {product.id}: {str(e)}")
                                        
                            # Add product to registry
                            self.registry['data_products'].append(product)
                            
                        except Exception as e:
                            self.logger.warning(f"Failed to process CSV row: {str(e)}")
                    
                    # Set the flag if we have any products
                    if len(self.registry['data_products']) > 0:
                        self.registry['has_data_products'] = True
                        self.logger.info(f"Loaded {len(self.registry['data_products'])} data products from CSV registry")
                    else:
                        self.logger.warning("No data products found in CSV registry")
            else:
                self.logger.warning(f"CSV data product registry not found at {self.data_product_registry}")
        except Exception as e:
            self.logger.error(f"Error loading CSV data product registry: {str(e)}")
            
    def _load_default_data_products(self):
        """Load default data products when no registry data is available"""
        self.logger.warning("Loading default data products as fallback")
        
        # Create a default finance data product
        finance_product = DataProduct(
            id="finance_data",
            name="Finance Data",
            domain="Finance",
            owner="Finance Team",
            description="Core financial data product including financial transactions and dimensions",
            tables={
                "financial_transactions": {
                    "name": "financial_transactions",
                    "description": "Financial transactions including revenue, expenses, etc.",
                    "data_source_type": "csv",
                    "data_source_path": "data/finance/financial_transactions.csv",
                    "schema": {
                        "transaction_id": "string",
                        "date": "date",
                        "amount": "float",
                        "category": "string",
                        "department": "string"
                    },
                    "primary_keys": ["transaction_id"]
                }
            },
        )
        
        # Add to registry
        self.registry['data_products'] = [finance_product]
        self.registry['has_data_products'] = True
        
        self.logger.info("Loaded 1 default data product")
            
    async def _load_registry_data(self):
        """Load data product registry from configured sources"""
        try:
            transaction_id = str(uuid.uuid4())
            self.logger.info(f"[TXN:{transaction_id}] Loading data product registry")
            
            # Initialize registry structure if not already done
            if not hasattr(self, 'registry'):
                self.registry = {}
                
            # Load data products from registry path if available
            data_products = []
            registry_path = self.data_product_registry if hasattr(self, 'data_product_registry') else None
            
            if registry_path:
                self.logger.info(f"[TXN:{transaction_id}] Loading data product registry from {registry_path}")
                try:
                    # Load registry from CSV, YAML, or other sources based on extension
                    if registry_path.endswith('.csv'):
                        if os.path.exists(registry_path):
                            df = pd.read_csv(registry_path)
                            data_products = df.to_dict('records')
                            self.logger.info(f"[TXN:{transaction_id}] Loaded {len(data_products)} data products from CSV")
                        else:
                            self.logger.warning(f"[TXN:{transaction_id}] Data product registry CSV not found at {registry_path}")
                    elif registry_path.endswith('.yaml') or registry_path.endswith('.yml'):
                        if os.path.exists(registry_path):
                            with open(registry_path, 'r') as f:
                                import yaml
                                data_products = yaml.safe_load(f)
                                self.logger.info(f"[TXN:{transaction_id}] Loaded {len(data_products)} data products from YAML")
                        else:
                            self.logger.warning(f"[TXN:{transaction_id}] Data product registry YAML not found at {registry_path}")
                    else:
                        self.logger.warning(f"[TXN:{transaction_id}] Unsupported registry format for {registry_path}")
                except Exception as e:
                    self.logger.error(f"[TXN:{transaction_id}] Error loading data product registry: {str(e)}")
            else:
                self.logger.warning(f"[TXN:{transaction_id}] No data product registry path configured")
                
            # Store in registry
            self.registry['data_products'] = data_products
            self.logger.info(f"[TXN:{transaction_id}] Registry status: registry={type(self.registry)}, has data_products={len(data_products) > 0}")
            return self.registry
        except Exception as e:
            self.logger.error(f"Error loading registry data: {str(e)}")
            self.registry = {'data_products': []}
            return self.registry
    
    async def _initialize_database_connection(self):
        """
        Initialize the database connection using the DatabaseManagerFactory.
        This creates a database manager instance based on the agent's configuration.
        """
        try:
            self.logger.info("Initializing database connection")
            
            # Default to DuckDB if no database type is specified
            db_type = getattr(self.config, 'database_type', 'duckdb')
            self.logger.info(f"Using database type: {db_type}")
            
            # Log all available modules for debugging
            self.logger.debug(f"Available modules: {', '.join(sys.modules.keys())}")
            
            # Verify DatabaseManagerFactory import
            from src.database.manager_factory import DatabaseManagerFactory
            self.logger.info(f"DatabaseManagerFactory class: {DatabaseManagerFactory}")
            self.logger.info(f"Registered backends: {DatabaseManagerFactory.get_supported_backends()}")
            
            # Verify DatabaseManager interface
            from src.database.manager_interface import DatabaseManager
            self.logger.info(f"DatabaseManager interface: {DatabaseManager}")
            
            # Convert config to dictionary for database manager factory
            # This is required as the factory expects a Dict[str, Any]
            config_dict = {}
            if hasattr(self.config, "model_dump"):
                # Pydantic v2 model
                config_dict = self.config.model_dump()
            elif hasattr(self.config, "__dict__"):
                # Fallback to __dict__ if no dict() method
                config_dict = self.config.__dict__
            else:
                # Last resort, try to convert to dict directly
                config_dict = dict(self.config)
                
            self.logger.info(f"Database config: {config_dict}")
            
            # Import and check DuckDBManager
            if db_type.lower() == 'duckdb':
                try:
                    from src.database.backends.duckdb_manager import DuckDBManager
                    self.logger.info(f"DuckDBManager class: {DuckDBManager}")
                except ImportError as ie:
                    self.logger.error(f"Failed to import DuckDBManager: {str(ie)}")
                    raise
            
            # Create database manager from factory
            self.logger.info("Creating database manager from factory...")
            self.db_manager = DatabaseManagerFactory.create_manager(
                db_type=db_type,
                config=config_dict,
                logger=self.logger
            )
            
            self.logger.info(f"Created database manager: {self.db_manager}")
            
            # Initialize the database manager
            self.logger.info("Initializing database manager...")
            await self.db_manager.initialize()
            
            self.logger.info(f"Successfully initialized {db_type} database manager")
            return self.db_manager
            
        except ImportError as ie:
            error_msg = f"Module import error during database initialization: {str(ie)}"
            self.logger.error(error_msg)
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            raise RuntimeError(error_msg)
        except AttributeError as ae:
            error_msg = f"Attribute error during database initialization: {str(ae)}"
            self.logger.error(error_msg)
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            raise RuntimeError(error_msg)
        except Exception as e:
            error_msg = f"Error initializing database connection: {str(e)}"
            self.logger.error(error_msg)
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            raise RuntimeError(error_msg)
        
    # _load_registry_data method implementation is now consolidated at line ~476
    
    @classmethod
    async def create_from_registry(cls, config_dict: Dict[str, Any], logger=None) -> 'A9_Data_Product_MCP_Service_Agent':
        """
        Create an instance from registry configuration asynchronously.
        This is the factory method used by the orchestrator.
        
        Args:
            config_dict: Configuration dictionary from registry
            logger: Orchestrator-provided logger (optional)
            
        Returns:
            Instance of A9_Data_Product_MCP_Service_Agent
        """
        # Use provided logger or fall back to default
        agent_logger = logger or default_logger
        
        # Check if instance already exists for singleton pattern
        if cls._instance is None:
            agent_logger.info("Creating new A9_Data_Product_MCP_Service_Agent instance")
            cls._instance = cls(config_dict, logger=agent_logger)
            await cls._instance._async_init()
        return cls._instance
    
    @classmethod
    def get_instance(cls) -> Optional['A9_Data_Product_MCP_Service_Agent']:
        """
        Get the current instance if it exists.
        
        Returns:
            The current agent instance or None if not initialized
        """
        return cls._instance
    
    # Legacy _initialize_duckdb_connection method removed - replaced by _initialize_database_connection
    
    # First implementation of _register_csv_files removed.
    # The consolidated implementation at line 2127 should be used instead.
    # This version uses the database_manager abstraction which is database-agnostic.
    # All remaining fragments from first _register_csv_files implementation removed
            
    # Remaining code from first _register_csv_files implementation removed
    
    async def _register_contract_views(self, transaction_id: str = None) -> bool:
        """
        Creates necessary views as defined in the YAML contract.
        Uses the consolidated _create_views method.
        """
        tx_id = transaction_id or str(uuid.uuid4())
        self.logger.info(f"[TXN:{tx_id}] Registering contract views using consolidated method")
        
        # Call the consolidated method with 'yaml_contract' source
        success = await self._create_views(transaction_id=tx_id, source='yaml_contract')
        
        if success:
            self.logger.info(f"[TXN:{tx_id}] Successfully created views from contract")
        else:
            self.logger.warning(f"[TXN:{tx_id}] Failed to create some or all views from contract")
            
        return success
    
    async def _load_registry_data(self) -> Dict[str, Any]:
        """
        Load registry data from files and star schema contract asynchronously
        
        Returns:
            Dictionary containing registry data
        """
        try:
            self.logger.info("Loading registry data from files and star schema contract")
            start_time = time.time()
            
            # Initialize registry dictionary with empty structures
            registry = {
                'data_products': [],
                'kpis': [],
                'relationships': [],
                'business_terms': {},
                'views': []  # Add views section to registry
            }
            
            # Define default data products to ensure registry always has valid content
            # These will be used if no products are found in the contract
            default_data_products = [
                {
                    'product_id': 'financial_transactions_data',
                    'primary_table': 'FinancialTransactions',
                    'description': 'Default SAP Financial Transactions Data Product',
                    'governance_level': 'department'
                },
                {
                    'product_id': 'accounting_documents_data',
                    'primary_table': 'AccountingDocuments',
                    'description': 'Default SAP Accounting Documents Data Product',
                    'governance_level': 'department'
                }
            ]
            
            # Load FI star schema contract from YAML file
            star_schema_path = Path(self.config.contracts_path) / "fi_star_schema.yaml"
            star_schema = {}
            
            if not star_schema_path.exists():
                self.logger.warning(f"Star schema contract file not found: {star_schema_path}")
                self.logger.info("Using default data products instead")
            else:
                try:
                    # Load YAML file asynchronously
                    import yaml
                    import aiofiles
                    
                    try:
                        async with aiofiles.open(star_schema_path, 'r') as f:
                            content = await f.read()
                            star_schema = yaml.safe_load(content)
                            
                        self.logger.info(f"Loaded star schema contract from {star_schema_path}")
                        
                    except ImportError:
                        # Fall back to synchronous loading if aiofiles is not available
                        self.logger.warning("aiofiles not available, falling back to synchronous file loading")
                        with open(star_schema_path, 'r') as f:
                            star_schema = yaml.safe_load(f)
                except Exception as e:
                    self.logger.error(f"Error loading star schema contract: {str(e)}")
                    self.logger.info("Using default data products instead")
            
            # Extract data products from the contract
            data_products = []
            if star_schema and 'data_product' in star_schema:
                # Add the main data product
                data_products.append({
                    'product_id': star_schema['data_product'],
                    'primary_table': 'FinancialTransactions',  # Fact table in the star schema
                    'description': star_schema.get('description', 'SAP FI Star Schema'),
                    'governance_level': star_schema.get('governance_level', 'department')
                })
                
            # Add table-specific data products
            if star_schema and 'tables' in star_schema:
                for table in star_schema['tables']:
                    data_products.append({
                        'product_id': f"{table['name'].lower()}_data",
                        'primary_table': table['name'],
                        'description': f"Data from {table['name']} table",
                        'governance_level': table.get('governance_level', 'department')
                    })
            
            # Add KPI-specific data products
            if star_schema and 'kpis' in star_schema:
                for kpi in star_schema['kpis']:
                    data_products.append({
                        'product_id': f"{kpi['name'].lower().replace(' ', '_')}",
                        'primary_table': 'FinancialTransactions',  # Most KPIs are based on the fact table
                        'description': kpi.get('description', f"{kpi['name']} KPI"),
                        'kpi_definition': kpi,
                        'governance_level': kpi.get('governance_level', 'enterprise')
                    })
                    
            # Extract views from the contract
            views = []
            if star_schema and 'views' in star_schema:
                self.logger.info(f"Found {len(star_schema['views'])} views in contract")
                for view in star_schema['views']:
                    if 'name' in view and 'sql' in view:
                        views.append({
                            'name': view['name'],
                            'sql': view['sql']
                        })
                        # Also create a corresponding data product for each view
                        view_product_id = view['name'].lower()
                        data_products.append({
                            'product_id': view_product_id,
                            'primary_table': view['name'],
                            'description': f"View: {view['name']}",
                            'governance_level': 'department',
                            'is_view': True
                        })
                        self.logger.info(f"Added view {view['name']} to registry")
                    else:
                        self.logger.warning(f"View is missing required fields (name or sql): {view}")
                registry['views'] = views
            
            # If no data products were extracted from contract, use defaults
            if not data_products:
                self.logger.warning("No data products found in contract, using default data products")
                data_products = default_data_products
                
            # Log the number of data products found
            self.logger.info(f"Found {len(data_products)} data products")
            
            # Store data products in registry - always ensure a DataFrame is created
            registry['data_products'] = pd.DataFrame(data_products)
            
            # Store KPIs in registry
            if star_schema and 'kpis' in star_schema:
                registry['kpis'] = star_schema['kpis']
            
            # Store relationships in registry
            if star_schema and 'relationships' in star_schema:
                registry['relationships'] = star_schema['relationships']
                
            # Store business terms in registry
            if star_schema and 'business_terms' in star_schema:
                registry['business_terms'] = star_schema['business_terms']
                
            # Log success with timing information
            elapsed_time = time.time() - start_time
            
            # Log detailed information about loaded registry
            self.logger.info(f"Registry loaded successfully in {elapsed_time:.2f} seconds")
            self.logger.info(f"Registry keys: {list(registry.keys())}")
            self.logger.info(f"Data products DataFrame shape: {registry['data_products'].shape}")
            
            # Store full schema for reference
            registry['schema'] = star_schema
            
            # Log comprehensive information about loaded data
            self.logger.info(f"Registry data loaded successfully in {elapsed_time:.2f}s")
            self.logger.info(f"Loaded FI star schema with {len(data_products)} data products and {len(registry.get('kpis', []))} KPIs")
            
            return registry
            
        except Exception as e:
            stack_trace = traceback.format_exc()
            self.logger.error(f"Error loading registry data: {str(e)}\n{stack_trace}")
            
            # Instead of empty registry, create default registry with fallback data products
            # This ensures protocol compliance and prevents downstream errors
            default_data_products = [
                {
                    'product_id': 'financial_transactions_data',
                    'primary_table': 'FinancialTransactions',
                    'description': 'Fallback SAP Financial Transactions Data Product',
                    'governance_level': 'department'
                },
                {
                    'product_id': 'accounting_documents_data',
                    'primary_table': 'AccountingDocuments',
                    'description': 'Fallback SAP Accounting Documents Data Product',
                    'governance_level': 'department'
                }
            ]
            
            self.logger.info("Using fallback data products due to error in registry loading")
            
            # Return a valid registry with default data products
            return {
                'data_products': pd.DataFrame(default_data_products),
                'kpis': [],
                'relationships': [],
                'business_terms': {},
                'error': str(e)
            }
    
    async def _create_views_from_registry(self, transaction_id=None):
        """
        Create views defined in the registry using the consolidated method.
        
        Args:
            transaction_id: Optional transaction ID for logging
            
        Returns:
            bool: True if successful, False otherwise
        """
        tx_id = transaction_id or str(uuid.uuid4())
        self.logger.info(f"[TXN:{tx_id}] Creating views from registry using consolidated method")
        
        # Call the consolidated method with 'registry' source
        success = await self._create_views(transaction_id=tx_id, source='registry')
        
        if success:
            self.logger.info(f"[TXN:{tx_id}] Successfully created views from registry")
        else:
            self.logger.warning(f"[TXN:{tx_id}] Failed to create some or all views from registry")
            
        return success
                
    async def _create_views(self, transaction_id: str = None, source: str = 'all') -> bool:
        """
        Centralized method to create all required views in DuckDB.
        This consolidated method handles view creation from all sources including:
        - YAML contract
        - Registry data
        - Required test views
        
        Args:
            transaction_id: Optional transaction ID for logging
            source: Source of views to create ('all', 'contract', 'registry', 'test')
                    Default 'all' creates views from all sources
                    
        Returns:
            bool: True if successful, False otherwise
        """
        tx_id = transaction_id or str(uuid.uuid4())
        self.logger.info(f"[TXN:{tx_id}] Creating views from source: {source}")
        
        try:
            # 1. Ensure DatabaseManager is initialized (no direct duckdb usage here)
            if not getattr(self, 'db_manager', None):
                try:
                    loop = asyncio.get_running_loop()
                    if loop.is_running():
                        loop.create_task(self._initialize_database_connection())
                    else:
                        asyncio.run(self._initialize_database_connection())
                except RuntimeError:
                    asyncio.run(self._initialize_database_connection())
            
            # Expose underlying connection for legacy tests if available
            if hasattr(self, 'db_manager') and hasattr(self.db_manager, 'connection'):
                self.duckdb_conn = self.db_manager.connection
            
            # Optionally create views from YAML contract using consolidated method
            try:
                loop = asyncio.get_running_loop()
                if loop.is_running():
                    loop.create_task(self._create_views(source='yaml_contract'))
                else:
                    asyncio.run(self._create_views(source='yaml_contract'))
            except RuntimeError:
                asyncio.run(self._create_views(source='yaml_contract'))
            
            self.logger.info("Database connection ensured via DatabaseManager")
        
        except Exception as e:
            self.logger.error(f"Error ensuring DuckDB connection: {str(e)}")
            raise RuntimeError(f"Failed to initialize DuckDB connection: {str(e)}") from e
            
    def _create_views_from_yaml_contract(self):
        """
        Create views based on the YAML contract using the consolidated async method.
        This avoids direct DB calls in the agent and delegates to the DatabaseManager.
        """
        try:
            try:
                loop = asyncio.get_running_loop()
                if loop.is_running():
                    loop.create_task(self._create_views(source='yaml_contract'))
                else:
                    asyncio.run(self._create_views(source='yaml_contract'))
            except RuntimeError:
                asyncio.run(self._create_views(source='yaml_contract'))
        except Exception as e:
            self.logger.error(f"Error creating views from YAML contract: {str(e)}")
            # Do not raise here; allow agent to continue even if view creation fails
            
    # _validate_sql_statement method implementation is now consolidated at line ~1624
    
    async def execute_sql(self, request: SQLExecutionRequest) -> SQLExecutionResponse:
        """
        Execute SQL query on the data product source with protocol compliance.
        Only SELECT statements are allowed for security reasons.
        
        Args:
            request: SQLRequest object containing SQL to execute
            
        Returns:
            SQLExecutionResponse with results or error information
        """
        transaction_id = str(uuid.uuid4())
        self.logger.info(f"[TXN:{transaction_id}] Executing SQL: {request.sql[:100]}...")
        
        # Validate request object
        if not request or not request.sql:
            self.logger.error(f"[TXN:{transaction_id}] Invalid request: {request}")
            return SQLExecutionResponse.error(
                request_id=getattr(request, 'request_id', 'unknown'),
                error_message="Invalid or empty SQL request",
                transaction_id=transaction_id
            )
        
        # Validate SQL statement for security
        if not self._validate_sql_statement(request.sql):
            self.logger.error(f"[TXN:{transaction_id}] Invalid SQL statement: {request.sql}")
            return SQLExecutionResponse.error(
                request_id=request.request_id,
                error_message="Invalid SQL statement: only SELECT statements are allowed",
                transaction_id=transaction_id
            )
        
        try:
            start_time = time.time()
            
            # Execute SQL with DuckDB through async wrapper
            # Since DuckDB doesn't support async natively, we'll use a wrapper
            import asyncio as _asyncio
            self.logger.info(f"[TXN:{transaction_id}] [MCP] Starting DB execution via DuckDBManager")
            try:
                result_df = await _asyncio.wait_for(
                    self._execute_sql_async(request.sql, transaction_id),
                    timeout=4
                )
                query_time_ms = (time.time() - start_time) * 1000
                self.logger.info(f"[TXN:{transaction_id}] [MCP] DB execution finished in {query_time_ms:.2f}ms")
            except _asyncio.TimeoutError:
                self.logger.warning(f"[TXN:{transaction_id}] [MCP] DB execution timeout after 4s")
                return SQLExecutionResponse.error(
                    request_id=request.request_id,
                    error_message="MCP DB execution timeout",
                    transaction_id=transaction_id
                )
            
            # Convert result to list format
            columns = list(result_df.columns)
            rows = result_df.values.tolist() if not result_df.empty else []
            
            self.logger.info(f"[TXN:{transaction_id}] SQL executed successfully: {len(rows)} rows returned in {query_time_ms:.2f}ms")
            # Extra visibility: log columns and first row if available
            try:
                if columns:
                    self.logger.info(f"[TXN:{transaction_id}] Columns: {columns}")
                if rows:
                    first_row_preview = rows[0]
                    self.logger.info(f"[TXN:{transaction_id}] First row: {first_row_preview}")
                else:
                    self.logger.info(f"[TXN:{transaction_id}] No rows returned for SQL result")
            except Exception:
                pass
            
            # Create structured result dict for response helper with metadata
            result_dict = {
                'columns': columns,
                'rows': rows,
                'query_time_ms': query_time_ms,
                'row_count': len(rows),
                'timestamp': datetime.datetime.now().isoformat(),
                'transaction_id': transaction_id,
                'truncated': len(rows) >= request.limit if hasattr(request, 'limit') and request.limit else False
            }
            
            # Get principal context from request or registry if available
            principal_context = {}
            principal_id = None
            
            # Extract principal context from request
            if hasattr(request, 'principal_context') and request.principal_context:
                principal_context = request.principal_context
                principal_id = principal_context.get('principal_id')
                self.logger.info(f"[TXN:{transaction_id}] Using principal context from request for principal ID: {principal_id}")
            # If no principal context in request but principal_id is available, try to get from registry
            elif hasattr(request, 'principal_id') and request.principal_id and self.principal_provider:
                principal_id = request.principal_id
                try:
                    principal = self.principal_provider.get_principal_by_id(principal_id)
                    if principal:
                        # Convert principal model to dictionary
                        principal_context = {
                            'principal_id': principal_id,
                            'role': getattr(principal, 'role', None),
                            'business_processes': getattr(principal, 'business_processes', []),
                            'default_filters': getattr(principal, 'default_filters', {}),
                            'governance_level': getattr(principal, 'governance_level', 'department')
                        }
                        self.logger.info(f"[TXN:{transaction_id}] Retrieved principal context from registry for ID: {principal_id}")
                except Exception as e:
                    self.logger.warning(f"[TXN:{transaction_id}] Failed to get principal from registry: {str(e)}")
            
            # Create response with protocol compliance and enhanced principal context
            return SQLExecutionResponse.from_result(
                request_id=request.request_id,
                result=result_dict,
                transaction_id=transaction_id,
                metadata={
                    'source': 'duckdb',
                    'principal_id': principal_id,
                    'principal_context': principal_context,
                    'governance_level': principal_context.get('governance_level', 'department')
                }
            )
            
        except Exception as e:
            error_msg = str(e)
            stack_trace = traceback.format_exc()
            self.logger.error(f"[TXN:{transaction_id}] Error executing SQL: {error_msg}\n{stack_trace}")
            
            # Enhanced error response with protocol compliance
            return SQLExecutionResponse.error(
                request_id=request.request_id,
                error_message=f"Error executing SQL: {error_msg}",
                transaction_id=transaction_id,
                error_code='SQL_EXECUTION_ERROR',
                human_action_required=self._needs_human_action(error_msg),
                human_action_type='data_correction' if self._needs_human_action(error_msg) else None,
                human_action_context={
                    'sql': request.sql,
                    'error': error_msg,
                    'transaction_id': transaction_id
                } if self._needs_human_action(error_msg) else None
            )
        except Exception as e:
            error_msg = str(e)
            stack_trace = traceback.format_exc()
            self.logger.error(f"[TXN:{transaction_id}] Error executing SQL: {error_msg}\n{stack_trace}")
            
            # Enhanced error response with protocol compliance
            return SQLExecutionResponse.error(
                request_id=request.request_id,
                error_message=f"Error executing SQL: {error_msg}",
                transaction_id=transaction_id,
                error_code='SQL_EXECUTION_ERROR',
                human_action_required=self._needs_human_action(error_msg),
                human_action_type='data_correction' if self._needs_human_action(error_msg) else None,
                human_action_context={
                    'sql': request.sql,
                    'error': error_msg,
                    'transaction_id': transaction_id
                } if self._needs_human_action(error_msg) else None
            )
        
    def _needs_human_action(self, error_msg: str) -> bool:
        """
        Determine if an error requires human action based on the error message
        
        Args:
            error_msg: Error message to analyze
            
        Returns:
            True if human action is required, False otherwise
        """
        # These error patterns typically require human intervention
        human_action_patterns = [
            "no such table",
            "no such column", 
            "undefined column",
            "permission denied",
            "ambiguous column name",
            "invalid input syntax",
            "could not convert"
        ]
        
        return any(pattern in error_msg.lower() for pattern in human_action_patterns)
        
    async def get_data_product(self, request: DataProductRequest) -> DataProductResponse:
        """
        Get data product based on registry configuration and star schema contract
        with protocol compliance.
        
        Args:
            request: DataProductRequest with product ID and filters
            
        Returns:
            DataProductResponse with data or error
        """
    def _needs_human_action(self, error_msg: str) -> bool:
        """
        Determine if an error requires human action based on the error message
        
        Args:
            error_msg: Error message to analyze
            
        Returns:
            True if human action is required, False otherwise
        """
        # These error patterns typically require human intervention
        human_action_patterns = [
            "no such table",
            "no such column", 
            "undefined column",
            "permission denied",
            "ambiguous column name",
            "invalid input syntax",
            "could not convert"
        ]
        
        return any(pattern in error_msg.lower() for pattern in human_action_patterns)
        
    async def get_data_product(self, request: DataProductRequest) -> DataProductResponse:
        """
        Get data product based on registry configuration and star schema contract
        with protocol compliance.
        
        Args:
            request: DataProductRequest with product ID and filters
            
        Returns:
            DataProductResponse with data or error
        """
        transaction_id = str(uuid.uuid4())
        self.logger.info(f"[TXN:{transaction_id}] Getting data product: {request.product_id} with filters: {request.filters}")
        
        try:
            start_time = time.time()
            
            # Validate request
            if not request or not request.product_id:
                self.logger.error(f"[TXN:{transaction_id}] Invalid data product request: {request}")
                return DataProductResponse.error(
                    request_id=getattr(request, 'request_id', 'unknown'),
                    error_message="Invalid data product request: missing product ID",
                    product_id=getattr(request, 'product_id', 'unknown'),
                    transaction_id=transaction_id,
                    error_code='INVALID_REQUEST'
                )
            
            # Check if yaml_contract_text is provided and should be used
            if hasattr(request, 'yaml_contract_text') and request.yaml_contract_text:
                self.logger.info(f"[TXN:{transaction_id}] Using provided YAML contract text for data product")
                # In a full implementation, we would parse and use the YAML contract here
                # For now, we'll continue with our existing registry
            
            # Detailed inspection of registry state
            self.logger.info(f"[TXN:{transaction_id}] Registry status: registry={type(self.registry)}, has data_products={'data_products' in self.registry}")
            if hasattr(self, 'registry') and self.registry:
                self.logger.info(f"[TXN:{transaction_id}] Registry keys: {list(self.registry.keys())}")
                if 'data_products' in self.registry:
                    self.logger.info(f"[TXN:{transaction_id}] Data products DataFrame empty: {self.registry['data_products'].empty}")
                    self.logger.info(f"[TXN:{transaction_id}] Data products DataFrame shape: {self.registry['data_products'].shape}")
                    self.logger.info(f"[TXN:{transaction_id}] Data products columns: {self.registry['data_products'].columns.tolist() if not self.registry['data_products'].empty else 'N/A'}")
            
            # Check if product exists in registry
            if not hasattr(self, 'registry') or self.registry is None or 'data_products' not in self.registry or self.registry['data_products'].empty:
                self.logger.error(f"[TXN:{transaction_id}] Data product registry not loaded")
                return DataProductResponse.error(
                    request_id=request.request_id,
                    error_message="Data product registry not loaded",
                    product_id=request.product_id,
                    transaction_id=transaction_id,
                    error_code='REGISTRY_NOT_LOADED',
                    human_action_required=True,
                    human_action_type='configuration',
                    human_action_context={
                        'message': 'Data product registry is not loaded. Please check the agent configuration.'
                    }
                )
            
            # Check if principal_id is available, either from request or principal context
            principal_id = None
            principal_context = {}
            
            # Extract principal context from request if available
            if hasattr(request, 'principal_context') and request.principal_context:
                principal_context = request.principal_context
                principal_id = principal_context.get('principal_id')
                self.logger.info(f"[TXN:{transaction_id}] Using principal context from request for principal ID: {principal_id}")
            # If no principal context but principal_id is available, try to get from provider
            elif hasattr(request, 'principal_id') and request.principal_id and self.principal_provider:
                principal_id = request.principal_id
                try:
                    principal = self.principal_provider.get_principal_by_id(principal_id)
                    if principal:
                        # Convert principal model to dictionary
                        principal_context = {
                            'principal_id': principal_id,
                            'role': getattr(principal, 'role', None),
                            'business_processes': getattr(principal, 'business_processes', []),
                            'default_filters': getattr(principal, 'default_filters', {}),
                            'governance_level': getattr(principal, 'governance_level', 'department')
                        }
                        self.logger.info(f"[TXN:{transaction_id}] Retrieved principal context from registry for ID: {principal_id}")
                except Exception as e:
                    self.logger.warning(f"[TXN:{transaction_id}] Failed to get principal from registry: {str(e)}")

            # In the refactored architecture, we expect the SQL to be provided in the request
            # as it's now generated by the LLM Service Agent
            if not hasattr(request, 'sql_query') or not request.sql_query:
                self.logger.error(f"[TXN:{transaction_id}] Missing SQL query in request")
                return DataProductResponse.error(
                    request_id=request.request_id,
                    error_message="Missing SQL query in request. Per updated architecture, SQL should be generated by LLM Service Agent.",
                    product_id=request.product_id,
                    transaction_id=transaction_id
                )
            
            # Get product definition from registry (for metadata only)
            product_row = None
            try:
                product_row = self.registry['data_products'][self.registry['data_products']['product_id'] == request.product_id].iloc[0].to_dict()
            except (IndexError, KeyError):
                self.logger.warning(f"[TXN:{transaction_id}] Product metadata not found in registry: {request.product_id}")
                # Continue execution even if product metadata is not found
                # We still have the SQL to execute
            
            # Use the SQL query provided in the request (generated by LLM Service Agent)
            # Clean and parse the SQL to handle potential LLM output formatting issues
            sql = request.sql_query
            
            # Process the SQL for potential LLM formatting issues
            try:
                # If SQL is a string representation of a JSON object, parse it
                if isinstance(sql, str) and sql.strip().startswith('{'):
                    try:
                        sql_obj = json.loads(sql)
                        if isinstance(sql_obj, dict) and 'sql' in sql_obj:
                            sql = sql_obj['sql']
                        elif isinstance(sql_obj, dict) and 'query' in sql_obj:
                            sql = sql_obj['query']
                        self.logger.info(f"[TXN:{transaction_id}] Extracted SQL from JSON object: {sql[:100]}...")
                    except json.JSONDecodeError:
                        # Not valid JSON, continue with sql as is
                        self.logger.info(f"[TXN:{transaction_id}] SQL is not valid JSON, using as is")
                
                # Improved cleaning of SQL string to handle JSON fragments
                if isinstance(sql, str):
                    # First check if SQL has JSON structure within it
                    sql = sql.strip()
                    
                    # Look for common JSON ending pattern in SQL (often LLM includes trailing JSON)
                    json_endings = ['",', '"}']
                    for ending in json_endings:
                        if ending in sql:
                            # Truncate at first JSON marker
                            sql = sql.split(ending, 1)[0]
                            self.logger.info(f"[TXN:{transaction_id}] Truncated SQL at JSON marker")
                    
                    # Remove any trailing quotes and commas
                    sql = sql.strip().rstrip('"').rstrip("'").rstrip(',').strip()
                    
                    self.logger.info(f"[TXN:{transaction_id}] Cleaned SQL: {sql}")
                    
                    # Remove surrounding quotes if present
                    if (sql.startswith('"') and sql.endswith('"')) or (sql.startswith('\'') and sql.endswith('\'')):
                        sql = sql[1:-1]
                        self.logger.info(f"[TXN:{transaction_id}] Removed surrounding quotes from SQL")
                    
                    # Fix escaped quotes inside SQL
                    sql = sql.replace("\\\"", '"').replace("\\\''", "'")
                    
                    # Fix any other common escape sequences
                    sql = sql.replace("\\n", " ").replace("\\t", " ")
                    
                    # For now, just do basic cleanup of common formatting issues
                    sql = sql.strip()
                    self.logger.info(f"[TXN:{transaction_id}] Cleaned SQL: {sql}")
                
                self.logger.info(f"[TXN:{transaction_id}] Final SQL after cleaning: {sql}")
            except Exception as e:
                self.logger.error(f"[TXN:{transaction_id}] Error cleaning SQL: {str(e)}")
                # Continue with original SQL as fallback
                sql = request.sql_query
            
            # Validate SQL for security
            if not self._validate_sql_statement(sql):
                self.logger.error(f"[TXN:{transaction_id}] Invalid SQL statement: {sql}")
                return DataProductResponse.error(
                    request_id=request.request_id,
                    error_message="Invalid SQL statement",
                    product_id=request.product_id,
                    transaction_id=transaction_id
                )
            
            try:
                # Execute SQL with asynchronous wrapper
                start_time = time.time()
                result_df = await self._execute_sql_query(sql, transaction_id)
                query_time_ms = (time.time() - start_time) * 1000
                
                # Convert to response format
                columns = list(result_df.columns)
                rows = result_df.values.tolist() if not result_df.empty else []
                
                self.logger.info(f"[TXN:{transaction_id}] Data product retrieved successfully: {len(rows)} rows in {query_time_ms:.2f}ms")
                
                # Create result dict for response helper
                result_dict = {
                    'columns': columns,
                    'rows': rows,
                    'query_time_ms': query_time_ms,
                    'row_count': len(rows),
                    'timestamp': datetime.datetime.now().isoformat(),
                    'transaction_id': transaction_id,
                    'truncated': len(rows) >= request.limit if hasattr(request, 'limit') and request.limit else False
                }
                
                # Create metadata from product_row if available, otherwise use defaults
                metadata = {
                    'source': 'duckdb',
                    'principal_id': getattr(request, 'principal_id', None),
                }
                
                if product_row:
                    metadata.update({
                        'product_type': product_row.get('product_type', 'table'),
                        'governance_level': product_row.get('governance_level', 'department')
                    })
                
                # Create and return response using helper method with protocol compliance
                return DataProductResponse.from_result(
                    request_id=request.request_id,
                    product_id=request.product_id,
                    result=result_dict,
                    transaction_id=transaction_id,
                    metadata=metadata
                )
            
            except Exception as e:
                # Handle SQL execution errors with comprehensive error response
                error_msg = str(e)
                stack_trace = traceback.format_exc()
                self.logger.error(f"[TXN:{transaction_id}] Error executing SQL for data product: {error_msg}\n{stack_trace}")
                
                # Check if human action is required based on error message
                human_action_required = self._needs_human_action(error_msg)
                
                return DataProductResponse.error(
                    request_id=request.request_id,
                    error_message=f"Error executing SQL for data product: {error_msg}",
                    product_id=request.product_id,
                    transaction_id=transaction_id,
                    error_code='SQL_EXECUTION_ERROR',
                    human_action_required=human_action_required,
                    human_action_type='data_correction' if human_action_required else None,
                    human_action_context={
                        'sql': sql,
                        'error': error_msg,
                        'transaction_id': transaction_id
                    } if human_action_required else None
                )
                
        except Exception as e:
            stack_trace = traceback.format_exc()
            error_msg = str(e)
            self.logger.error(f"[TXN:{transaction_id}] Error in data product retrieval: {error_msg}\n{stack_trace}")
            
            return DataProductResponse.error(
                request_id=getattr(request, 'request_id', 'unknown'),
                error_message=f"Error in data product retrieval: {error_msg}",
                product_id=getattr(request, 'product_id', 'unknown'),
                transaction_id=transaction_id,
                error_code='DATA_PRODUCT_RETRIEVAL_ERROR'
            )
    
    # Legacy method removed: _build_data_product_sql
    # SQL generation now fully handled by LLM Service Agent per updated PRDs
    
    # Legacy method removed: _get_kpi_data_product
    # KPI SQL generation now handled by LLM Service Agent per updated PRDs
    
    # Legacy method removed: _build_kpi_sql
    # KPI SQL generation now handled by LLM Service Agent per updated PRDs
    
    async def _initialize_database_connection(self):
        """
        Initialize database connection using the appropriate manager based on config.
        This method uses the DatabaseManagerFactory to create the correct backend
        implementation based on the configured database type.
        """
        try:
            # Get database type from config, default to duckdb
            db_type = getattr(self.config, 'database_type', 'duckdb')
            self.logger.info(f"Initializing database connection for type: {db_type}")
            
            # Create appropriate database manager through existing factory
            self.db_manager = DatabaseManagerFactory.create_manager(
                db_type=db_type,
                config=self.config.__dict__ if hasattr(self.config, '__dict__') else self.config,
                logger=self.logger
            )
            
            # Connect to the database
            connection_params = {
                'database_path': getattr(self.config, 'database_path', ':memory:'),
                'data_directory': self.data_directory
            }
            
            # Connect to database
            connect_result = await self.db_manager.connect(connection_params)
            
            if not connect_result:
                self.logger.error("Failed to connect to database")
                raise RuntimeError("Database connection failed")
                
            # Get database metadata for logging
            self.logger.info(f"Database connection established successfully for {db_type}")
            
            # For DuckDB backend, also store the connection directly on the agent for test compatibility
            if db_type == 'duckdb' and hasattr(self.db_manager, 'duckdb_conn'):
                self.duckdb_conn = self.db_manager.duckdb_conn
                self.logger.info("DuckDB connection stored on agent for test compatibility")
            
        except Exception as e:
            error_msg = f"Error initializing database connection: {str(e)}"
            self.logger.error(f"{error_msg}\n{traceback.format_exc()}")
            raise RuntimeError(error_msg) from e
            
    async def _register_csv_files(self):
        """
        Register all CSV files in the data directory with DuckDB.
        This is a minimal implementation that delegates to the database manager.
        """
        try:
            if not self.db_manager:
                await self._initialize_database_connection()
                
            if not self.data_directory:
                self.logger.error("No data directory specified")
                return
                
            self.logger.info(f"Registering CSV files from {self.data_directory}")
            
            # Get all CSV files in the data directory
            csv_files = []
            for root, _, files in os.walk(self.data_directory):
                for file in files:
                    if file.lower().endswith('.csv'):
                        csv_files.append(os.path.join(root, file))
            
            # Register each CSV file
            num_files = 0
            for csv_file in csv_files:
                # Extract table name from file name (without extension)
                table_name = os.path.splitext(os.path.basename(csv_file))[0]
                
                # Register the CSV file using the database manager
                source_info = {
                    'type': 'csv',
                    'path': csv_file,
                    'schema': 'sap',  # Use 'sap' schema for all tables as per test expectations
                    'table_name': table_name
                }
                
                result = await self.db_manager.register_data_source(source_info)
                if result:
                    num_files += 1
                    self.logger.info(f"Registered CSV file: {csv_file} as sap.{table_name}")
                    
            self.logger.info(f"Successfully registered {num_files} CSV files")
            return num_files
            
        except Exception as e:
            error_msg = f"Error registering CSV files: {str(e)}"
            self.logger.error(f"{error_msg}\n{traceback.format_exc()}")
            raise RuntimeError(error_msg) from e

    async def _execute_sql_async(self, sql: str, transaction_id: str = None) -> pd.DataFrame:
        """
        Execute SQL asynchronously using the database manager.
        
        Args:
            sql: SQL statement to execute
            transaction_id: Optional transaction ID for logging
            
        Returns:
            DataFrame with query results
            
        Raises:
            RuntimeError: If database connection is not initialized or query fails
        """
        if not transaction_id:
            transaction_id = str(uuid.uuid4())
            
        if not self.db_manager:
            error_msg = "Database connection not initialized"
            self.logger.error(f"[TXN:{transaction_id}] {error_msg}")
            raise RuntimeError(error_msg)
        
        try:
            self.logger.info(f"[TXN:{transaction_id}] Executing SQL: {sql[:100]}...")
            # Pass transaction_id as part of parameters if the manager expects it that way
            parameters = {'transaction_id': transaction_id} if transaction_id else None
            result_df = await self.db_manager.execute_query(sql, parameters=parameters)
            self.logger.info(f"[TXN:{transaction_id}] SQL execution successful, rows: {len(result_df)}")
            return result_df
        except Exception as e:
            error_msg = f"Error executing SQL: {str(e)}"
            self.logger.error(f"[TXN:{transaction_id}] {error_msg}\n{traceback.format_exc()}")
            raise RuntimeError(error_msg) from e
    
    def _validate_sql_statement(self, sql: str) -> bool:
        """
        Validate SQL statement for security.
        Delegates to the database manager for dialect-specific validation.
        
        Args:
            sql: SQL statement to validate
            
        Returns:
            True if SQL is valid and safe, False otherwise
        """
        if not sql or not isinstance(sql, str):
            return False
            
        # Normalize SQL for basic validation
        sql = sql.strip().lower()
        
        # Basic check - must start with SELECT
        if not sql.startswith('select '):
            self.logger.warning(f"Invalid SQL (not SELECT): {sql[:50]}...")
            return False
        
        # Check for potentially dangerous operations
        dangerous_keywords = [
            'drop', 'truncate', 'delete', 'update', 'insert', 'create', 'alter',
            'grant', 'revoke', 'exec', 'execute', 'call'
        ]
        
        for keyword in dangerous_keywords:
            pattern = r'\b' + keyword + r'\b'
            if re.search(pattern, sql):
                self.logger.warning(f"SQL contains dangerous keyword '{keyword}': {sql[:50]}...")
                return False
        
        # If we have a database manager, use its validation if available
        if self.db_manager and hasattr(self.db_manager, 'validate_sql'):
            try:
                # Use a non-blocking wrapper since this might not be async
                loop = asyncio.get_event_loop()
                result = asyncio.run_coroutine_threadsafe(
                    self.db_manager.validate_sql(sql), loop
                ).result()
                
                # Handle different return formats (tuple vs bool)
                if isinstance(result, tuple) and len(result) == 2:
                    is_valid, error = result
                    if not is_valid:
                        self.logger.warning(f"SQL validation failed: {error}")
                        return False
                elif isinstance(result, bool) and not result:
                    self.logger.warning("SQL validation failed (no details available)")
                    return False
            except Exception as e:
                self.logger.error(f"Error in SQL validation: {str(e)}")
                # Continue with basic validation if manager validation fails
        
        return True

    async def _create_views_from_definitions(self, product_id: str, view_definitions: List[Dict[str, Any]], transaction_id: str = None) -> bool:
        """
        Create database views based on the provided view definitions.
        Delegates to the appropriate database manager for dialect-specific view creation.
        
        Args:
            product_id: The data product ID associated with these views
            view_definitions: List of view definition dictionaries with name, query, description fields
            transaction_id: Optional transaction ID for logging
            
        Returns:
            True if all views were created successfully, False otherwise
        """
        if not transaction_id:
            transaction_id = str(uuid.uuid4())
            
        if not self.db_manager:
            self.logger.error(f"[TXN:{transaction_id}] Cannot create views: Database connection not initialized")
            return False
            
        try:
            self.logger.info(f"[TXN:{transaction_id}] Creating {len(view_definitions)} views for product {product_id}")
            
            # Track success for all views
            all_success = True
            for view_def in view_definitions:
                try:
                    view_name = view_def.get('name')
                    view_query = view_def.get('query')
                    
                    if not view_name or not view_query:
                        self.logger.warning(f"[TXN:{transaction_id}] Invalid view definition: missing name or query")
                        all_success = False
                        continue
                    
                    # Execute view creation through database manager
                    create_view_sql = f"CREATE OR REPLACE VIEW {view_name} AS {view_query}"
                    await self.db_manager.execute_query(create_view_sql, transaction_id=transaction_id)
                    self.logger.info(f"[TXN:{transaction_id}] Created view {view_name}")
                except Exception as e:
                    self.logger.error(f"[TXN:{transaction_id}] Error creating view {view_def.get('name', 'unknown')}: {str(e)}")
                    all_success = False
            
            return all_success
        except Exception as e:
            self.logger.error(f"[TXN:{transaction_id}] Error creating views: {str(e)}\n{traceback.format_exc()}")
            return False
    
    async def _register_csv_files_async(self, csv_files: List[Dict[str, Any]], transaction_id: str = None) -> Dict[str, bool]:
        """
        Register CSV files with the database manager (async implementation).
        
        Args:
            csv_files: List of CSV file definitions with file_path, table_name, and options
            transaction_id: Optional transaction ID for logging
            
        Returns:
            Dictionary mapping table names to registration success (True/False)
        """
        if not transaction_id:
            transaction_id = str(uuid.uuid4())
            
        if not self.db_manager:
            error_msg = "Database connection not initialized"
            self.logger.error(f"[TXN:{transaction_id}] {error_msg}")
            raise RuntimeError(error_msg)
            
        results = {}
        
        self.logger.info(f"[TXN:{transaction_id}] Registering {len(csv_files)} CSV files")
        
        for csv_file in csv_files:
            file_path = csv_file.get('file_path')
            table_name = csv_file.get('table_name')
            options = csv_file.get('options', {})
            
            if not file_path or not table_name:
                self.logger.warning(f"[TXN:{transaction_id}] Invalid CSV file definition: missing path or table name")
                results[table_name if table_name else 'unknown'] = False
                continue
                
            # Check if file exists
            full_path = os.path.join(self.data_directory, file_path) if not os.path.isabs(file_path) else file_path
            
            if not os.path.exists(full_path):
                self.logger.error(f"[TXN:{transaction_id}] CSV file not found: {full_path}")
                results[table_name] = False
                continue
                
            try:
                # Check if database manager has dedicated import_csv method
                if hasattr(self.db_manager, 'import_csv'):
                    try:
                        # Try with direct method first
                        self.logger.info(f"[TXN:{transaction_id}] Using import_csv method for {table_name}: {full_path}")
                        success = await self.db_manager.import_csv(
                            file_path=full_path,
                            table_name=table_name,
                            options=options,
                            transaction_id=transaction_id
                        )
                    except TypeError:
                        # Fall back to parameter dict approach if signature differs
                        params = {
                            'file_path': full_path,
                            'table_name': table_name,
                            'options': options,
                            'transaction_id': transaction_id
                        }
                        success = await self.db_manager.import_csv(params)
                else:
                    # Fallback to direct SQL import if no import_csv method exists
                    self.logger.info(f"[TXN:{transaction_id}] Using SQL fallback for CSV import: {table_name}: {full_path}")
                    
                    # Build import SQL based on options
                    delimiter = options.get('delimiter', ',')
                    header = options.get('header', True)
                    auto_detect = options.get('auto_detect', True)
                    
                    # Normalize file path for SQL
                    sql_path = full_path.replace("\\", "/")
                    
                    # Use appropriate import SQL
                    import_sql = f"""
                        CREATE TABLE IF NOT EXISTS {table_name} AS 
                        SELECT * FROM read_csv_auto(
                            '{sql_path}',
                            delim='{delimiter}',
                            header={str(header).lower()},
                            auto_detect={str(auto_detect).lower()}
                        )
                    """
                    
                    # Execute import SQL
                    await self.db_manager.execute_query(import_sql)
                    success = True  # Assume success if no exception raised
                
                results[table_name] = success
                
                if success:
                    self.logger.info(f"[TXN:{transaction_id}] Successfully imported CSV to table {table_name}")
                else:
                    self.logger.error(f"[TXN:{transaction_id}] Failed to import CSV to table {table_name}")
                    
            except Exception as e:
                self.logger.error(f"[TXN:{transaction_id}] Error importing CSV file {file_path} to table {table_name}: {str(e)}\n{traceback.format_exc()}")
                results[table_name] = False
                
        return results

    async def _register_csv_files(self):
        """Register CSV files from the configured data directory into the database.
        This is a thin wrapper method maintained for backward compatibility with tests.
        The actual implementation is delegated to the database manager.
        """
        # Generate a transaction ID for logging
        transaction_id = str(uuid.uuid4())
        self.logger.info(f"[TXN:{transaction_id}] Registering CSV files from {self.data_directory}")
        
        # Ensure database connection is established
        if not hasattr(self, 'db_manager') or self.db_manager is None:
            self.logger.info(f"[TXN:{transaction_id}] Database manager not initialized, initializing now")
            # Initialize database connection if missing
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
            if loop.is_running():
                await self._initialize_database_connection()
            else:
                loop.run_until_complete(self._initialize_database_connection())
        
        # Validate that initialization succeeded
        if not hasattr(self, 'db_manager') or self.db_manager is None:
            self.logger.error(f"[TXN:{transaction_id}] Failed to initialize database manager")
            return []
            
        # Set duckdb_conn reference for backward compatibility with tests
        if hasattr(self.db_manager, 'connection'):
            self.duckdb_conn = self.db_manager.connection
        
        # Find all CSV files in the data directory
        csv_files = []
        try:
            self.logger.info(f"[TXN:{transaction_id}] Scanning for CSV files in {self.data_directory}")
            for root, _, files in os.walk(self.data_directory):
                for file in files:
                    if file.endswith('.csv'):
                        full_path = os.path.join(root, file)
                        table_name = os.path.splitext(file)[0]
                        # Ensure table name is SQL-safe and prepend schema if needed
                        if not table_name.startswith('sap.'):
                            table_name = f"sap.{table_name}"
                            
                        # Schedule CSV import through the database manager
                        csv_files.append({
                            'file_path': full_path,
                            'table_name': table_name,
                            'options': {
                                'schema': 'sap',
                                'header': True
                            }
                        })
            
            # Process the CSV files using the async implementation
            results = await self._register_csv_files_async(csv_files, transaction_id)
            
            # Extract successful tables for return value to match original method's contract
            tables = [table_name for table_name, success in results.items() if success]
            self.logger.info(f"[TXN:{transaction_id}] Registered {len(tables)} tables from CSV files")
            return tables
        except Exception as e:
            self.logger.error(f"[TXN:{transaction_id}] Error registering CSV files: {str(e)}\n{traceback.format_exc()}")
            return []

    def close(self):
        """Close database connection when agent is destroyed"""
        if self.db_manager:
            try:
                # Try to get the current event loop
                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    # No event loop exists, create a new one
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                
                # Run disconnect in the appropriate way based on loop state
                if loop.is_running():
                    asyncio.create_task(self.db_manager.disconnect())
                else:
                    loop.run_until_complete(self.db_manager.disconnect())
            except Exception as e:
                # Log error but continue cleanup
                self.logger.error(f"Error during disconnect: {str(e)}")
            finally:
                self.db_manager = None
