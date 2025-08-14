"""
Registry Provider Interface

Defines the interface for all registry providers, regardless of data source.
This ensures a consistent API for accessing registry data across the system.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, TypeVar, Generic, Type

from pydantic import BaseModel

T = TypeVar('T', bound=BaseModel)


class RegistryProvider(ABC, Generic[T]):
    """
    Abstract base class for all registry providers.
    
    A registry provider is responsible for loading, validating, and providing
    access to a specific type of registry data (e.g., business processes,
    KPIs, principal profiles, etc.).
    
    Each provider handles one specific registry type but can load from
    different storage formats (YAML, JSON, CSV, Python objects).
    """
    
    _registry_base_path = "src/registry_references"
    
    @classmethod
    def get_registry_path(cls, relative_path: str = "") -> str:
        """
        Get the absolute path to a registry reference file or directory.
        
        Args:
            relative_path: Relative path within the registry references directory
            
        Returns:
            Absolute path to the registry reference
        """
        if relative_path:
            return f"{cls._registry_base_path}/{relative_path}"
        return cls._registry_base_path
    
    @classmethod
    def initialize(cls, registry_base_path: str = "src/registry_references") -> None:
        """
        Initialize the registry provider with the base path.
        
        Args:
            registry_base_path: Base path to registry reference files
        """
        cls._registry_base_path = registry_base_path
    
    @abstractmethod
    async def load(self) -> None:
        """
        Load all registry items from the data source.
        Must be implemented by concrete providers.
        """
        pass
    
    @abstractmethod
    def get(self, id_or_name: str) -> Optional[T]:
        """
        Get a registry item by ID or name.
        
        Args:
            id_or_name: The ID or name of the registry item to retrieve
            
        Returns:
            The registry item if found, None otherwise
        """
        pass
    
    @abstractmethod
    def get_all(self) -> List[T]:
        """
        Get all registry items.
        
        Returns:
            List of all registry items
        """
        pass
    
    @abstractmethod
    def find_by_attribute(self, attr_name: str, attr_value: Any) -> List[T]:
        """
        Find registry items by a specific attribute value.
        
        Args:
            attr_name: The name of the attribute to search by
            attr_value: The value to search for
            
        Returns:
            List of matching registry items
        """
        pass
    
    @abstractmethod
    def register(self, item: T) -> bool:
        """
        Register a new item in the registry.
        
        Args:
            item: The item to register
            
        Returns:
            True if registration succeeded, False otherwise
        """
        pass


class BusinessProcessProvider(RegistryProvider[T]):
    """Provider specifically for business process registry data."""
    pass


class KPIProvider(RegistryProvider[T]):
    """Provider specifically for KPI registry data."""
    pass


class PrincipalProfileProvider(RegistryProvider[T]):
    """Provider specifically for principal profile registry data."""
    pass


class DataProductProvider(RegistryProvider[T]):
    """Provider specifically for data product registry data."""
    pass
