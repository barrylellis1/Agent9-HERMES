"""
KPI Registry Provider

Concrete implementation of the registry provider for KPIs.
This provider supports loading KPIs from various sources
and provides a unified API for accessing them.
"""

import importlib
import logging
from typing import Any, Dict, List, Optional, Type

from src.registry.models.kpi import KPI, ComparisonType
from src.registry.providers.registry_provider import RegistryProvider

logger = logging.getLogger(__name__)


class KPIProvider(RegistryProvider[KPI]):
    """
    Provider for KPI registry data.
    
    This provider supports loading KPIs from Python modules,
    YAML files, or JSON files, and provides a unified API for accessing them.
    """
    
    def __init__(self, source_path: str = None, storage_format: str = "python"):
        """
        Initialize the KPI provider.
        
        Args:
            source_path: Path to the KPI data source
            storage_format: Format of the data source (python, yaml, json)
        """
        self.source_path = source_path
        self.storage_format = storage_format
        self._kpis: Dict[str, KPI] = {}
        self._kpis_by_name: Dict[str, KPI] = {}
        self._kpis_by_legacy_id: Dict[str, KPI] = {}
    
    async def load(self) -> None:
        """
        Load KPIs from the configured data source.
        
        This method supports loading from Python modules, YAML files,
        or JSON files, depending on the configured storage format.
        """
        logger.info(f"Loading KPIs from {self.source_path} ({self.storage_format})")
        
        if not self.source_path:
            # Default to built-in KPIs if no source path provided
            self._load_default_kpis()
            return
        
        if self.storage_format == "python":
            self._load_from_python_module()
        elif self.storage_format == "yaml":
            await self._load_from_yaml()
        elif self.storage_format == "json":
            await self._load_from_json()
        else:
            logger.error(f"Unsupported storage format: {self.storage_format}")
            # Fall back to default KPIs
            self._load_default_kpis()
        
        logger.info(f"Loaded {len(self._kpis)} KPIs")
    
    def _load_default_kpis(self) -> None:
        """Load default KPIs if no source is available."""
        # These are just placeholders - real implementations would load from registry_references
        default_kpis = [
            KPI(
                id="gross_margin",
                name="Gross Margin",
                domain="Finance",
                description="Revenue minus cost of goods sold, divided by revenue",
                unit="%",
                data_product_id="finance_data",
                business_process_ids=["finance_profitability_analysis"],
                sql_query="SELECT * FROM kpi_gross_margin",
                thresholds=[
                    {
                        "comparison_type": ComparisonType.YOY,
                        "green_threshold": 5.0,
                        "yellow_threshold": 0.0,
                        "red_threshold": -5.0,
                        "inverse_logic": False
                    }
                ],
                owner_role="CFO"
            ),
            KPI(
                id="revenue_growth_rate",
                name="Revenue Growth Rate",
                domain="Finance",
                description="Year-over-year percentage change in revenue",
                unit="%",
                data_product_id="finance_data",
                business_process_ids=["finance_revenue_growth"],
                sql_query="SELECT * FROM kpi_revenue_growth_rate",
                thresholds=[
                    {
                        "comparison_type": ComparisonType.YOY,
                        "green_threshold": 10.0,
                        "yellow_threshold": 5.0,
                        "red_threshold": 0.0,
                        "inverse_logic": False
                    }
                ],
                owner_role="CFO"
            )
        ]
        
        for kpi in default_kpis:
            self._add_kpi(kpi)
    
    def _load_from_python_module(self) -> None:
        """Load KPIs from a Python module."""
        try:
            module_name = self.source_path
            module = importlib.import_module(module_name)
            
            # Look for KPI objects in the module
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                
                # Check for lists of KPI objects
                if isinstance(attr, list) and attr and hasattr(attr[0], 'id') and hasattr(attr[0], 'name'):
                    for item in attr:
                        try:
                            # Try to convert to KPI if it's not already
                            if not isinstance(item, KPI):
                                kpi = KPI(**item.dict() if hasattr(item, 'dict') else vars(item))
                            else:
                                kpi = item
                            self._add_kpi(kpi)
                        except Exception as e:
                            logger.warning(f"Failed to convert item to KPI: {e}")
                
                # Check for dictionaries that might be KPI registries
                elif isinstance(attr, dict) and attr:
                    for key, value in attr.items():
                        try:
                            if hasattr(value, 'id') and hasattr(value, 'name'):
                                # Try to convert to KPI if it's not already
                                if not isinstance(value, KPI):
                                    kpi = KPI(**value.dict() if hasattr(value, 'dict') else vars(value))
                                else:
                                    kpi = value
                                self._add_kpi(kpi)
                        except Exception as e:
                            logger.warning(f"Failed to convert dict item to KPI: {e}")
            
            # If no KPIs were found, try to extract from legacy registry format
            if not self._kpis:
                self._extract_kpis_from_module(module)
                
        except (ImportError, AttributeError) as e:
            logger.error(f"Error loading KPIs from {self.source_path}: {e}")
            self._load_default_kpis()
    
    def _extract_kpis_from_module(self, module) -> None:
        """
        Extract KPIs from a module that doesn't explicitly define them.
        
        This method looks for legacy KPI definitions in the module and
        converts them to KPI objects.
        """
        # Try to find KPI registry in the module
        registry_attr = None
        for attr_name in dir(module):
            if "registry" in attr_name.lower() or "kpi" in attr_name.lower():
                registry_attr = getattr(module, attr_name)
                break
        
        if registry_attr is None:
            logger.warning("No KPI registry found in module")
            return
        
        # Try different extraction strategies
        if isinstance(registry_attr, dict):
            for key, value in registry_attr.items():
                try:
                    # If the value is a dict, try to create a KPI from it
                    if isinstance(value, dict):
                        kpi_data = {**value, "id": key.lower()}
                        if "name" not in kpi_data:
                            kpi_data["name"] = " ".join(word.capitalize() for word in key.lower().split("_"))
                        kpi = KPI(**kpi_data)
                        self._add_kpi(kpi)
                    # If the value is a string, try to create a KPI from the key
                    elif isinstance(key, str):
                        kpi = KPI.from_enum_value(key)
                        self._add_kpi(kpi)
                except Exception as e:
                    logger.warning(f"Failed to extract KPI from registry item: {e}")
        elif isinstance(registry_attr, list):
            for item in registry_attr:
                try:
                    if isinstance(item, str):
                        kpi = KPI.from_enum_value(item)
                        self._add_kpi(kpi)
                    elif hasattr(item, 'id') and hasattr(item, 'name'):
                        kpi_data = item.dict() if hasattr(item, 'dict') else vars(item)
                        kpi = KPI(**kpi_data)
                        self._add_kpi(kpi)
                except Exception as e:
                    logger.warning(f"Failed to extract KPI from registry item: {e}")
    
    async def _load_from_yaml(self) -> None:
        """Load KPIs from a YAML file."""
        try:
            import yaml
            with open(self.source_path, "r") as file:
                data = yaml.safe_load(file)
                
                # Handle the specific structure of our KPI registry YAML
                if isinstance(data, dict) and "kpis" in data and isinstance(data["kpis"], list):
                    # Process the list of KPIs under the 'kpis' key
                    for item in data["kpis"]:
                        if isinstance(item, dict):
                            try:
                                kpi = KPI(**item)
                                self._add_kpi(kpi)
                            except Exception as e:
                                logger.warning(f"Failed to create KPI from YAML item: {e}")
                # Also keep the original handling for other formats
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict):
                            try:
                                kpi = KPI(**item)
                                self._add_kpi(kpi)
                            except Exception as e:
                                logger.warning(f"Failed to create KPI from YAML item: {e}")
                elif isinstance(data, dict):
                    for key, value in data.items():
                        if isinstance(value, dict):
                            try:
                                kpi_data = {**value, "id": key}
                                if "name" not in kpi_data:
                                    kpi_data["name"] = " ".join(word.capitalize() for word in key.split("_"))
                                kpi = KPI(**kpi_data)
                                self._add_kpi(kpi)
                            except Exception as e:
                                logger.warning(f"Failed to create KPI from YAML item: {e}")
                
        except (ImportError, FileNotFoundError, yaml.YAMLError) as e:
            logger.error(f"Error loading KPIs from {self.source_path}: {e}")
            self._load_default_kpis()
    
    async def _load_from_json(self) -> None:
        """Load KPIs from a JSON file."""
        try:
            import json
            with open(self.source_path, "r") as file:
                data = json.load(file)
                
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict):
                            try:
                                kpi = KPI(**item)
                                self._add_kpi(kpi)
                            except Exception as e:
                                logger.warning(f"Failed to create KPI from JSON item: {e}")
                elif isinstance(data, dict):
                    for key, value in data.items():
                        if isinstance(value, dict):
                            try:
                                kpi_data = {**value, "id": key}
                                if "name" not in kpi_data:
                                    kpi_data["name"] = " ".join(word.capitalize() for word in key.split("_"))
                                kpi = KPI(**kpi_data)
                                self._add_kpi(kpi)
                            except Exception as e:
                                logger.warning(f"Failed to create KPI from JSON item: {e}")
                
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Error loading KPIs from {self.source_path}: {e}")
            self._load_default_kpis()
    
    def _add_kpi(self, kpi: KPI) -> None:
        """
        Add a KPI to the internal dictionaries.
        
        Args:
            kpi: The KPI to add
        """
        self._kpis[kpi.id] = kpi
        self._kpis_by_name[kpi.name] = kpi
        self._kpis_by_legacy_id[kpi.legacy_id] = kpi
    
    def get(self, id_or_name: str) -> Optional[KPI]:
        """
        Get a KPI by ID, name, or legacy ID.
        
        Args:
            id_or_name: The ID, name, or legacy ID of the KPI
            
        Returns:
            The KPI if found, None otherwise
        """
        # Try to find by ID
        if id_or_name in self._kpis:
            return self._kpis[id_or_name]
        
        # Try to find by name
        if id_or_name in self._kpis_by_name:
            return self._kpis_by_name[id_or_name]
        
        # Try to find by legacy ID
        if id_or_name in self._kpis_by_legacy_id:
            return self._kpis_by_legacy_id[id_or_name]
        
        # Try to create from enum value
        try:
            kpi = KPI.from_enum_value(id_or_name)
            self._add_kpi(kpi)
            return kpi
        except:
            pass
        
        return None
    
    def get_all(self) -> List[KPI]:
        """
        Get all KPIs.
        
        Returns:
            List of all KPIs
        """
        return list(self._kpis.values())
    
    def find_by_attribute(self, attr_name: str, attr_value: Any) -> List[KPI]:
        """
        Find KPIs by a specific attribute value.
        
        Args:
            attr_name: The name of the attribute to search by
            attr_value: The value to search for
            
        Returns:
            List of matching KPIs
        """
        results = []
        
        for kpi in self._kpis.values():
            if hasattr(kpi, attr_name):
                value = getattr(kpi, attr_name)
                
                # Handle list attributes (e.g., tags, business_process_ids)
                if isinstance(value, list) and attr_value in value:
                    results.append(kpi)
                # Handle string/simple attributes
                elif value == attr_value:
                    results.append(kpi)
        
        return results
    
    def find_by_domain(self, domain: str) -> List[KPI]:
        """
        Find KPIs by domain.
        
        Args:
            domain: The domain to search for
            
        Returns:
            List of KPIs in the specified domain
        """
        return self.find_by_attribute("domain", domain)
    
    def find_by_business_process(self, business_process_id: str) -> List[KPI]:
        """
        Find KPIs by business process.
        
        Args:
            business_process_id: The business process ID to search for
            
        Returns:
            List of KPIs related to the specified business process
        """
        return self.find_by_attribute("business_process_ids", business_process_id)
    
    def find_by_owner_role(self, role: str) -> List[KPI]:
        """
        Find KPIs by owner role.
        
        Args:
            role: The owner role to search for
            
        Returns:
            List of KPIs owned by the specified role
        """
        return self.find_by_attribute("owner_role", role)
    
    def register(self, item: KPI) -> bool:
        """
        Register a new KPI.
        
        Args:
            item: The KPI to register
            
        Returns:
            True if registration succeeded, False otherwise
        """
        if item.id in self._kpis:
            logger.warning(f"KPI with ID {item.id} already exists")
            return False
        
        self._add_kpi(item)
        logger.info(f"Registered KPI: {item.id} - {item.name}")
        return True
