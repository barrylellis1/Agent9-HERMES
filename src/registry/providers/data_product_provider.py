"""
Data Product Registry Provider

Concrete implementation of the registry provider for data products.
This provider supports loading data products from various sources
and provides a unified API for accessing them.
"""

import importlib
import logging
import os
from typing import Any, Dict, List, Optional, Type

from src.registry.models.data_product import DataProduct
from src.registry.providers.registry_provider import RegistryProvider

logger = logging.getLogger(__name__)


class DataProductProvider(RegistryProvider[DataProduct]):
    """
    Provider for data product registry data.
    
    This provider supports loading data products from YAML contracts,
    Python modules, JSON files, or CSV files, and provides a unified
    API for accessing them.
    """
    
    def __init__(self, source_path: str = None, storage_format: str = "yaml"):
        """
        Initialize the data product provider.
        
        Args:
            source_path: Path to the data product data source
            storage_format: Format of the data source (yaml, python, json, csv)
        """
        self.source_path = source_path
        self.storage_format = storage_format
        self._data_products: Dict[str, DataProduct] = {}
        self._data_products_by_name: Dict[str, DataProduct] = {}
        self._data_products_by_legacy_id: Dict[str, DataProduct] = {}
    
    async def load(self) -> None:
        """
        Load data products from the configured data source.
        
        This method supports loading from YAML contracts, Python modules,
        JSON files, or CSV files, depending on the configured storage format.
        """
        logger.info(f"Loading data products from {self.source_path} ({self.storage_format})")
        
        if not self.source_path:
            # Default to built-in data products if no source path provided
            self._load_default_data_products()
            return
        
        if self.storage_format == "yaml":
            await self._load_from_yaml()
        elif self.storage_format == "python":
            self._load_from_python_module()
        elif self.storage_format == "json":
            await self._load_from_json()
        elif self.storage_format == "csv":
            await self._load_from_csv()
        else:
            logger.error(f"Unsupported storage format: {self.storage_format}")
            # Fall back to default data products
            self._load_default_data_products()
        
        logger.info(f"Loaded {len(self._data_products)} data products")
    
    def _load_default_data_products(self) -> None:
        """Load default data products if no source is available."""
        # Default finance data product
        finance_data = DataProduct(
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
            views={
                "revenue_by_department": {
                    "name": "revenue_by_department",
                    "description": "Revenue aggregated by department",
                    "sql_definition": """
                    SELECT department, SUM(amount) as total_revenue
                    FROM financial_transactions
                    WHERE category = 'Revenue'
                    GROUP BY department
                    """
                }
            },
            related_business_processes=[
                "finance_profitability_analysis",
                "finance_revenue_growth",
                "finance_expense_management"
            ]
        )
        
        self._add_data_product(finance_data)
    
    def _load_from_python_module(self) -> None:
        """Load data products from a Python module."""
        try:
            module_name = self.source_path
            module = importlib.import_module(module_name)
            
            # Look for data product objects in the module
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                
                # Check for lists of DataProduct objects
                if isinstance(attr, list) and attr and hasattr(attr[0], 'id') and hasattr(attr[0], 'name'):
                    for item in attr:
                        try:
                            # Try to convert to DataProduct if it's not already
                            if not isinstance(item, DataProduct):
                                data_product = DataProduct(**(item.model_dump() if hasattr(item, 'model_dump') else vars(item)))
                            else:
                                data_product = item
                            self._add_data_product(data_product)
                        except Exception as e:
                            logger.warning(f"Failed to convert item to DataProduct: {e}")
                
                # Check for dictionaries that might be data product registries
                elif isinstance(attr, dict) and attr:
                    for key, value in attr.items():
                        try:
                            if hasattr(value, 'id') and hasattr(value, 'name'):
                                # Try to convert to DataProduct if it's not already
                                if not isinstance(value, DataProduct):
                                    data_product = DataProduct(**(value.model_dump() if hasattr(value, 'model_dump') else vars(value)))
                                else:
                                    data_product = value
                                self._add_data_product(data_product)
                        except Exception as e:
                            logger.warning(f"Failed to convert dict item to DataProduct: {e}")
                
        except (ImportError, AttributeError) as e:
            logger.error(f"Error loading data products from {self.source_path}: {e}")
            self._load_default_data_products()
    
    def load_from_yaml(self, yaml_path: str) -> None:
        """
        Load data products from a YAML file.
        
        Args:
            yaml_path: Path to the YAML file or directory
        """
        try:
            import yaml
            
            # Save the original source path
            original_source_path = self.source_path
            
            # Set the new source path
            self.source_path = yaml_path
            
            # If the source path is a directory, load all YAML files in it
            if os.path.isdir(yaml_path):
                for filename in os.listdir(yaml_path):
                    if filename.endswith('.yaml') or filename.endswith('.yml'):
                        file_path = os.path.join(yaml_path, filename)
                        self._load_yaml_file_sync(file_path, yaml)
            else:
                # Load a single YAML file
                self._load_yaml_file_sync(yaml_path, yaml)
            
            # Restore the original source path
            self.source_path = original_source_path
                
        except (ImportError, FileNotFoundError) as e:
            logger.error(f"Error loading data products from {yaml_path}: {e}")
            self._load_default_data_products()
    
    async def _load_from_yaml(self) -> None:
        """
        Load data products from YAML files.
        
        This method handles both single YAML files and directories of YAML files.
        """
        try:
            import yaml
            
            # If the source path is a directory, load all YAML files in it
            if os.path.isdir(self.source_path):
                for filename in os.listdir(self.source_path):
                    if filename.endswith('.yaml') or filename.endswith('.yml'):
                        file_path = os.path.join(self.source_path, filename)
                        await self._load_yaml_file(file_path, yaml)
            else:
                # Load a single YAML file
                await self._load_yaml_file(self.source_path, yaml)
                
        except (ImportError, FileNotFoundError) as e:
            logger.error(f"Error loading data products from {self.source_path}: {e}")
            self._load_default_data_products()
    
    def _load_yaml_file_sync(self, file_path: str, yaml_module) -> None:
        """
        Load a single YAML file as a data product (synchronous version).
        
        Args:
            file_path: Path to the YAML file
            yaml_module: The imported yaml module
        """
        try:
            with open(file_path, "r") as file:
                data = yaml_module.safe_load(file)
                
                if data:
                    # Use filename without extension as data product ID if not specified
                    data_product_id = os.path.splitext(os.path.basename(file_path))[0]
                    
                    # Create data product from YAML contract
                    data_product = DataProduct.from_yaml_contract(data, data_product_id)
                    self._add_data_product(data_product)
                    
        except (yaml_module.YAMLError, Exception) as e:
            logger.error(f"Error loading data product from {file_path}: {e}")
    
    async def _load_yaml_file(self, file_path: str, yaml_module) -> None:
        """
        Load a single YAML file as a data product.
        
        Args:
            file_path: Path to the YAML file
            yaml_module: The imported yaml module
        """
        try:
            with open(file_path, "r") as file:
                data = yaml_module.safe_load(file)
                
                if data:
                    # Use filename without extension as data product ID if not specified
                    data_product_id = os.path.splitext(os.path.basename(file_path))[0]
                    
                    # Create data product from YAML contract
                    data_product = DataProduct.from_yaml_contract(data, data_product_id)
                    self._add_data_product(data_product)
                    
        except (yaml_module.YAMLError, Exception) as e:
            logger.error(f"Error loading data product from {file_path}: {e}")
    
    async def _load_from_json(self) -> None:
        """
        Load data products from JSON files.
        
        This method handles both single JSON files and directories of JSON files.
        """
        try:
            import json
            
            # If the source path is a directory, load all JSON files in it
            if os.path.isdir(self.source_path):
                for filename in os.listdir(self.source_path):
                    if filename.endswith('.json'):
                        file_path = os.path.join(self.source_path, filename)
                        await self._load_json_file(file_path, json)
            else:
                # Load a single JSON file
                await self._load_json_file(self.source_path, json)
                
        except (FileNotFoundError) as e:
            logger.error(f"Error loading data products from {self.source_path}: {e}")
            self._load_default_data_products()
    
    async def _load_json_file(self, file_path: str, json_module) -> None:
        """
        Load a single JSON file as a data product.
        
        Args:
            file_path: Path to the JSON file
            json_module: The imported json module
        """
        try:
            with open(file_path, "r") as file:
                data = json_module.load(file)
                
                if isinstance(data, dict):
                    # Use filename without extension as data product ID if not specified
                    data_product_id = os.path.splitext(os.path.basename(file_path))[0]
                    
                    # If it's in YAML contract format, use from_yaml_contract method
                    if "metadata" in data and "tables" in data:
                        data_product = DataProduct.from_yaml_contract(data, data_product_id)
                    else:
                        # Otherwise assume it's direct DataProduct format
                        if "id" not in data:
                            data["id"] = data_product_id
                        data_product = DataProduct(**data)
                    
                    self._add_data_product(data_product)
                    
                elif isinstance(data, list):
                    # Handle list of data products
                    for item in data:
                        if isinstance(item, dict):
                            data_product = DataProduct(**item)
                            self._add_data_product(data_product)
                    
        except (json_module.JSONDecodeError, Exception) as e:
            logger.error(f"Error loading data product from {file_path}: {e}")
    
    async def _load_from_csv(self) -> None:
        """
        Load data products from CSV files.
        
        This method handles a CSV file that lists data products.
        """
        try:
            import csv
            
            with open(self.source_path, "r") as file:
                reader = csv.DictReader(file)
                for row in reader:
                    try:
                        # Extract required fields
                        data_product_id = row.get("id", "").strip()
                        name = row.get("name", "").strip()
                        domain = row.get("domain", "").strip()
                        owner = row.get("owner", "").strip()
                        
                        if data_product_id and name and domain and owner:
                            # Create minimal data product from CSV
                            data_product = DataProduct(
                                id=data_product_id,
                                name=name,
                                domain=domain,
                                owner=owner,
                                description=row.get("description", ""),
                                version=row.get("version", "1.0.0")
                            )
                            self._add_data_product(data_product)
                    except Exception as e:
                        logger.warning(f"Failed to create data product from CSV row: {e}")
                
        except (FileNotFoundError, Exception) as e:
            logger.error(f"Error loading data products from {self.source_path}: {e}")
            self._load_default_data_products()
    
    def _remove_data_product_indexes(self, data_product) -> None:
        """Remove cached lookups for the provided data product."""
        name = getattr(data_product, "name", None)
        legacy_id = getattr(data_product, "legacy_id", None)
        if name:
            self._data_products_by_name.pop(name, None)
        if legacy_id:
            self._data_products_by_legacy_id.pop(legacy_id, None)

    def _add_data_product(self, data_product) -> None:
        """
        Add a data product to the internal dictionaries.
        
        Args:
            data_product: The data product to add (DataProduct object or dict)
        """
        # Handle both DataProduct objects and dictionaries
        if isinstance(data_product, dict):
            # For dictionaries, create a simple wrapper that mimics DataProduct
            class DictWrapper:
                def __init__(self, data):
                    self.__dict__.update(data)
                    # Ensure required attributes exist
                    if not hasattr(self, 'id') and 'product_id' in data:
                        self.id = data['product_id']
                    if not hasattr(self, 'legacy_id'):
                        self.legacy_id = getattr(self, 'id', '')
                    if not hasattr(self, 'name'):
                        self.name = f"Product {getattr(self, 'id', 'unknown')}"
            
            # Create a wrapper object
            wrapper = DictWrapper(data_product)
            existing = self._data_products.get(wrapper.id)
            if existing:
                self._remove_data_product_indexes(existing)
            
            # Add to dictionaries
            self._data_products[wrapper.id] = data_product
            self._data_products_by_name[wrapper.name] = data_product
            self._data_products_by_legacy_id[wrapper.legacy_id] = data_product
        else:
            existing = self._data_products.get(data_product.id)
            if existing:
                self._remove_data_product_indexes(existing)
            # For DataProduct objects
            self._data_products[data_product.id] = data_product
            self._data_products_by_name[data_product.name] = data_product
            self._data_products_by_legacy_id[data_product.legacy_id] = data_product

    def upsert(self, data_product: DataProduct) -> DataProduct:
        """Create or replace a data product entry."""
        self._add_data_product(data_product)
        return data_product

    def delete(self, data_product_id: str) -> bool:
        """Delete a data product by ID."""
        existing = self._data_products.pop(data_product_id, None)
        if not existing:
            return False
        self._remove_data_product_indexes(existing)
        return True
    
    def get(self, id_or_name: str) -> Optional[DataProduct]:
        """
        Get a data product by ID, name, or legacy ID.
        
        Args:
            id_or_name: The ID, name, or legacy ID of the data product
            
        Returns:
            The data product if found, None otherwise
        """
        # Try to find by ID
        if id_or_name in self._data_products:
            return self._data_products[id_or_name]
        
        # Try to find by name
        if id_or_name in self._data_products_by_name:
            return self._data_products_by_name[id_or_name]
        
        # Try to find by legacy ID
        if id_or_name in self._data_products_by_legacy_id:
            return self._data_products_by_legacy_id[id_or_name]
        
        # Try to create from enum value
        try:
            data_product = DataProduct.from_enum_value(id_or_name)
            self._add_data_product(data_product)
            return data_product
        except:
            pass
        
        return None
    
    def get_all(self) -> List[DataProduct]:
        """
        Get all data products.
        
        Returns:
            List of all data products
        """
        return list(self._data_products.values())
    
    def find_by_attribute(self, attr_name: str, attr_value: Any) -> List[DataProduct]:
        """
        Find data products by a specific attribute value.
        
        Args:
            attr_name: The name of the attribute to search by
            attr_value: The value to search for
            
        Returns:
            List of matching data products
        """
        results = []
        
        for data_product in self._data_products.values():
            if hasattr(data_product, attr_name):
                value = getattr(data_product, attr_name)
                
                # Handle list attributes (e.g., related_business_processes, tags)
                if isinstance(value, list) and attr_value in value:
                    results.append(data_product)
                # Handle string/simple attributes
                elif value == attr_value:
                    results.append(data_product)
            
            # Special case for checking if a table or view exists
            elif attr_name == "has_table" and attr_value in data_product.tables:
                results.append(data_product)
            elif attr_name == "has_view" and attr_value in data_product.views:
                results.append(data_product)
        
        return results
    
    def find_by_domain(self, domain: str) -> List[DataProduct]:
        """
        Find data products by domain.
        
        Args:
            domain: The domain to search for
            
        Returns:
            List of data products in the specified domain
        """
        return self.find_by_attribute("domain", domain)
    
    def find_by_business_process(self, business_process_id: str) -> List[DataProduct]:
        """
        Find data products by related business process.
        
        Args:
            business_process_id: The business process ID to search for
            
        Returns:
            List of data products related to the specified business process
        """
        return self.find_by_attribute("related_business_processes", business_process_id)
    
    def find_by_table(self, table_name: str) -> List[DataProduct]:
        """
        Find data products containing a specific table.
        
        Args:
            table_name: The table name to search for
            
        Returns:
            List of data products containing the specified table
        """
        return self.find_by_attribute("has_table", table_name)
    
    def find_by_view(self, view_name: str) -> List[DataProduct]:
        """
        Find data products containing a specific view.
        
        Args:
            view_name: The view name to search for
            
        Returns:
            List of data products containing the specified view
        """
        return self.find_by_attribute("has_view", view_name)
    
    def register(self, item: DataProduct) -> bool:
        """
        Register a new data product.
        
        Args:
            item: The data product to register
            
        Returns:
            True if registration succeeded, False otherwise
        """
        if item.id in self._data_products:
            # Instead of warning, just log at debug level since this is expected during reloads
            logger.debug(f"Data product with ID {item.id} already exists, skipping registration")
            return True  # Return True to indicate no error occurred
        
        self._add_data_product(item)
        logger.info(f"Registered data product: {item.id} - {item.name}")
        return True
