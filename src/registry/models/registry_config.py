"""
Registry Configuration Models

Defines the configuration models for the registry system.
"""

from enum import Enum
from typing import Dict, List, Optional, Union
from pydantic import BaseModel, Field


class StorageFormat(str, Enum):
    """Supported storage formats for registry data."""
    YAML = "yaml"
    JSON = "json"
    CSV = "csv"
    PYTHON = "python"
    DATABASE = "database"


class RegistryProviderConfig(BaseModel):
    """Configuration for a single registry provider."""
    name: str = Field(..., description="Name of the registry provider")
    storage_format: StorageFormat = Field(..., description="Storage format for the registry data")
    source_path: str = Field(..., description="Path to the registry data source")
    model_class: str = Field(..., description="Fully qualified name of the model class for this registry")
    enabled: bool = Field(True, description="Whether this registry provider is enabled")
    options: Dict[str, Union[str, int, bool, List[str]]] = Field(
        default_factory=dict,
        description="Additional options for the registry provider"
    )


class RegistryConfig(BaseModel):
    """Configuration for the registry system."""
    providers: Dict[str, RegistryProviderConfig] = Field(
        default_factory=dict,
        description="Configured registry providers"
    )
    
    def __init__(self, **data):
        """Initialize with default configurations."""
        super().__init__(**data)
        
        # Add default configurations if not present
        if not self.providers:
            self._add_default_configs()
    
    def _add_default_configs(self):
        """Add default provider configurations."""
        # Business Process Registry (Python format initially)
        self.providers["business_process"] = RegistryProviderConfig(
            name="business_process",
            storage_format=StorageFormat.PYTHON,
            source_path="src.registry_references.principal_registry.principal_profiles",
            model_class="src.registry.models.business_process.BusinessProcess",
            enabled=True,
            options={"extract_from_profiles": True}
        )
        
        # KPI Registry (Python format initially)
        self.providers["kpi"] = RegistryProviderConfig(
            name="kpi",
            storage_format=StorageFormat.PYTHON,
            source_path="src.registry_references.kpi_registry.kpi_registry",
            model_class="src.registry.models.kpi.KPI",
            enabled=True,
        )
        
        # Principal Profile Registry (Python format initially)
        self.providers["principal_profile"] = RegistryProviderConfig(
            name="principal_profile",
            storage_format=StorageFormat.PYTHON,
            source_path="src.registry_references.principal_registry.principal_profiles",
            model_class="src.registry.models.principal.PrincipalProfile",
            enabled=True,
        )
        
        # Data Product Registry (CSV format)
        self.providers["data_product"] = RegistryProviderConfig(
            name="data_product",
            storage_format=StorageFormat.CSV,
            source_path="src.registry_references.data_product_registry.data_product_registry.csv",
            model_class="src.registry.models.data_product.DataProduct",
            enabled=True,
        )
