"""
Data Product Models

Defines the data structures for data products in the registry system.
This replaces hardcoded data product references with a flexible, data-driven model.
"""

from enum import Enum
from typing import Dict, List, Optional, Union, Any
from pydantic import BaseModel, Field


class DataSourceType(str, Enum):
    """Types of data sources supported for data products."""
    CSV = "csv"
    DATABASE = "database"
    API = "api"
    SERVICE = "service"
    OTHER = "other"


class TableDefinition(BaseModel):
    """
    Definition of a table within a data product.
    
    This includes schema information and source details.
    """
    
    name: str = Field(..., description="Name of the table")
    description: Optional[str] = Field(None, description="Description of the table")
    data_source_type: DataSourceType = Field(..., description="Type of data source")
    data_source_path: Optional[str] = Field(None, description="Path to the data source file/endpoint")
    column_schema: Dict[str, str] = Field(default_factory=dict, description="Schema definition (column name to type)")
    primary_keys: List[str] = Field(default_factory=list, description="List of primary key columns")
    foreign_keys: Dict[str, str] = Field(default_factory=dict, description="Foreign key relationships")
    sample_data: Optional[List[Dict[str, Any]]] = Field(None, description="Sample data for this table")


class ViewDefinition(BaseModel):
    """
    Definition of a view within a data product.
    
    Views are derived from tables or other views through SQL queries.
    """
    
    name: str = Field(..., description="Name of the view")
    description: Optional[str] = Field(None, description="Description of the view")
    sql_definition: str = Field(..., description="SQL query defining the view")
    depends_on: List[str] = Field(default_factory=list, description="Tables or views this view depends on")


class DataProduct(BaseModel):
    """
    Represents a data product in the registry.
    
    A data product is a collection of related tables and views that serve
    a specific business purpose, along with metadata about the product.
    """
    
    id: str = Field(..., description="Unique identifier for the data product")
    name: str = Field(..., description="Human-readable name of the data product")
    description: Optional[str] = Field(None, description="Description of the data product")
    domain: str = Field(..., description="Business domain this data product belongs to")
    owner: str = Field(..., description="Owner of the data product (team or role)")
    version: str = Field("1.0.0", description="Version of the data product")
    tables: Dict[str, TableDefinition] = Field(default_factory=dict, description="Tables in this data product")
    views: Dict[str, ViewDefinition] = Field(default_factory=dict, description="Views in this data product")
    related_business_processes: List[str] = Field(default_factory=list, 
                                               description="Business processes related to this data product")
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
    source_system: str = Field(
        "duckdb",
        description="Primary source system (duckdb, bigquery, etc.) for the curated data product",
    )
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata for extensions")
    
    @classmethod
    def from_enum_value(cls, enum_value: str, domain: str = "Finance") -> "DataProduct":
        """
        Create a DataProduct instance from a legacy enum value.
        
        This method provides backward compatibility with enum-based approaches.
        
        Args:
            enum_value: The enum value string (e.g., "FINANCE_DATA")
            domain: The business domain this data product belongs to
            
        Returns:
            A DataProduct instance
        """
        # Create a normalized name from the enum value
        name = " ".join(word.capitalize() for word in enum_value.lower().split("_"))
        
        # Create a normalized ID from the enum value
        data_product_id = enum_value.lower()
        
        return cls(
            id=data_product_id,
            name=name,
            domain=domain,
            owner=f"{domain} Team",
            description=f"{name} data product for {domain}",
        )
    
    def to_dict(self) -> Dict:
        """Convert to dictionary representation."""
        return self.model_dump()
    
    @property
    def legacy_id(self) -> str:
        """
        Get the legacy enum ID for backward compatibility.
        
        This property allows seamless migration from enum-based code.
        
        Returns:
            The legacy enum ID as a string (e.g., "FINANCE_DATA")
        """
        return self.name.upper().replace(" ", "_").replace("-", "_")
    
    @classmethod
    def from_yaml_contract(cls, yaml_data: Dict[str, Any], data_product_id: str = None) -> "DataProduct":
        """
        Create a DataProduct from a YAML contract definition.
        
        Args:
            yaml_data: The parsed YAML data
            data_product_id: Optional ID override
            
        Returns:
            A DataProduct instance
        """
        # Extract metadata
        metadata = yaml_data.get("metadata", {})
        # Surface top-level fallback_group_by_dimensions into metadata for downstream use
        try:
            fgbd = yaml_data.get("fallback_group_by_dimensions")
            if isinstance(fgbd, list):
                # Keep existing metadata entries and add fallback dims
                metadata = {**metadata, "fallback_group_by_dimensions": fgbd}
        except Exception:
            pass
        name = metadata.get("name", "Unnamed Data Product")
        domain = metadata.get("domain", "Finance")
        owner = metadata.get("owner", f"{domain} Team")
        description = metadata.get("description", f"Data product for {domain}")
        version = metadata.get("version", "1.0.0")
        source_system = metadata.get("source_system") or yaml_data.get("source_system") or "duckdb"
        
        # Use provided ID or generate from name
        if not data_product_id:
            data_product_id = name.lower().replace(" ", "_").replace("-", "_")
        
        raw_tables = yaml_data.get("tables", {}) or {}
        if isinstance(raw_tables, list):
            tables_iterable = {}
            for entry in raw_tables:
                name = entry.get("name") if isinstance(entry, dict) else None
                if name:
                    tables_iterable[name] = entry
            raw_tables = tables_iterable

        tables = {}
        for table_name, table_def in raw_tables.items():
            # Convert schema format to dict
            schema_definition = {}
            for column in table_def.get("columns", []) if isinstance(table_def, dict) else []:
                col_name = column.get("name")
                col_type = column.get("type")
                if col_name and col_type:
                    schema_definition[col_name] = col_type

            # Create table definition
            tables[table_name] = TableDefinition(
                name=table_name,
                description=table_def.get("description", f"Table {table_name}") if isinstance(table_def, dict) else f"Table {table_name}",
                data_source_type=table_def.get("data_source_type", DataSourceType.CSV) if isinstance(table_def, dict) else DataSourceType.CSV,
                data_source_path=table_def.get("data_source_path") if isinstance(table_def, dict) else None,
                column_schema=schema_definition,
                primary_keys=table_def.get("primary_keys", []) if isinstance(table_def, dict) else [],
                foreign_keys=table_def.get("foreign_keys", {}) if isinstance(table_def, dict) else {}
            )

        # Extract views
        raw_views = yaml_data.get("views", {}) or {}
        if isinstance(raw_views, list):
            views_iterable = {}
            for entry in raw_views:
                name = entry.get("name") if isinstance(entry, dict) else None
                if name:
                    views_iterable[name] = entry
            raw_views = views_iterable

        views = {}
        for view_name, view_def in raw_views.items():
            views[view_name] = ViewDefinition(
                name=view_name,
                description=view_def.get("description", f"View {view_name}") if isinstance(view_def, dict) else f"View {view_name}",
                sql_definition=view_def.get("sql_definition", f"SELECT * FROM {view_name}") if isinstance(view_def, dict) else f"SELECT * FROM {view_name}",
                depends_on=view_def.get("depends_on", []) if isinstance(view_def, dict) else []
            )
        
        # Create data product
        return cls(
            id=data_product_id,
            name=name,
            description=description,
            domain=domain,
            owner=owner,
            version=version,
            tables=tables,
            views=views,
            tags=metadata.get("tags", []),
            related_business_processes=metadata.get("related_business_processes", []),
            source_system=source_system,
            metadata={k: v for k, v in metadata.items() 
                    if k not in ["name", "domain", "owner", "description", "version", "tags"]}
        )
