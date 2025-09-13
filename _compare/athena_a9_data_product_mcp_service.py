# src/services/a9_data_product_mcp_service.py
import os
import glob
import duckdb
import pandas as pd
from typing import Dict, Any

from src.models.yaml_data_product_loader import load_yaml_data_product
from src.agents.utils.a9_shared_logger import a9_logger

class A9_Data_Product_MCP_Service:
    """
    Service responsible for loading and querying data products via DuckDB.
    This is not an agent, but a backend service for data operations.
    """

    def __init__(self):
        self.project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        self.data_product_registry_dir = os.path.join(self.project_root, "src", "registry_references", "data_product_registry")
        
        self.db_connection = duckdb.connect(database=':memory:', read_only=False)
        self.data_products = {}
        self._validate_path()
        self.load_data_products()
        a9_logger.info(f"A9_Data_Product_MCP_Service initialized with in-memory DuckDB.")

    def _validate_path(self) -> None:
        """Validates that the data product registry directory exists."""
        if not os.path.isdir(self.data_product_registry_dir):
            raise FileNotFoundError(f"Data product registry directory not found at: {self.data_product_registry_dir}")

    def load_data_products(self):
        """Loads all data product tables from YAML files found in the registry directory."""
        search_path = os.path.join(self.data_product_registry_dir, "data_products", "*.yaml")
        contract_files = glob.glob(search_path)

        if not contract_files:
            a9_logger.warning(f"No data product contracts found in {search_path}")
            return

        for contract_path in contract_files:
            try:
                data_product = load_yaml_data_product(contract_path)
                self.data_products[data_product.data_product] = data_product
                a9_logger.info(f"Loading data product: {data_product.data_product}")

                # The CSV base dir is relative to the project root
                # The base path for CSVs is defined in the data product's YAML contract itself.
            # It's a relative path from the project root.
                for table in data_product.tables:
                    if not table.data_source_path:
                        a9_logger.warning(f"Skipping table '{table.name}' in data product '{data_product.data_product}' because it has no data_source_path defined.")
                        continue

                    table_name = table.name
                    # Determine the full path to the CSV file.
                    # The data_source_path can be an absolute path to the file or directory,
                    # or a relative path from the project root.
                    raw_path = table.data_source_path
                    a9_logger.info(f"[DEBUG] Table '{table_name}': read data_source_path from YAML: '{raw_path}'")

                    if not os.path.isabs(raw_path):
                        raw_path = os.path.join(self.project_root, raw_path)
                    a9_logger.info(f"[DEBUG] Table '{table_name}': resolved raw_path: '{raw_path}'")

                    # Check if the resolved path is a file or a directory
                    if os.path.isfile(raw_path):
                        csv_path = raw_path
                    else:
                        # If it's a directory, append the standard CSV filename
                        csv_filename = f"{table_name}.csv"
                        csv_path = os.path.join(raw_path, csv_filename)
                    a9_logger.info(f"[DEBUG] Table '{table_name}': final constructed csv_path: '{csv_path}'")
                    if os.path.exists(csv_path):
                        a9_logger.info(f"Loading table '{table_name}' from {csv_path}")
                        # Use absolute path for read_csv_auto and handle backslashes on Windows
                        safe_csv_path = csv_path.replace('\\', '/')
                        self.db_connection.execute(f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM read_csv_auto('{safe_csv_path}')")
                    else:
                        a9_logger.warning(f"CSV file for table '{table_name}' not found at {csv_path}")

                # After loading tables, create the views
                if data_product.views:
                    for view in data_product.views:
                        a9_logger.info(f"Creating view '{view.name}' for data product '{data_product.data_product}'")
                        try:
                            create_view_sql = f"CREATE OR REPLACE VIEW \"{view.name}\" AS {view.sql}"
                            self.db_connection.execute(create_view_sql)
                            a9_logger.info(f"Successfully created view '{view.name}'.")
                        except Exception as e:
                            a9_logger.error(f"Failed to create view '{view.name}': {e}")
            except Exception as e:
                a9_logger.error(f"Failed to load data product from {contract_path}: {e}")

    def execute_query(self, query: str) -> pd.DataFrame:
        """Executes a SQL query against the DuckDB database."""
        try:
            a9_logger.info(f"Executing query: {query}")
            result = self.db_connection.execute(query).fetchdf()
            return result
        except duckdb.Error as e:
            a9_logger.error(f"DuckDB error executing query: {e}")
            a9_logger.error(f"Failed query: {query}")
            return pd.DataFrame() # Return empty dataframe on error

    def get_kpi_data(self, kpi_name: str, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Queries a KPI from the loaded data product.
        """
        kpi_found = None
        for dp in self.data_products.values():
            for kpi in dp.kpis:
                if kpi.name == kpi_name:
                    kpi_found = kpi
                    break
            if kpi_found:
                break

        if not kpi_found:
            a9_logger.error(f"KPI '{kpi_name}' not found in any loaded data product.")
            return {}

        query = kpi_found.query
        a9_logger.info(f"Retrieved query for KPI '{kpi_name}' from data product: {query}")
        if filters:
            a9_logger.warning(f"Filters provided to MCP service but will be ignored: {filters}")

        result_df = self.execute_query(query)

        if result_df.empty:
            return {"kpi_name": kpi_name, "current_value": 0, "previous_value": 0, "trend": "flat"}
        
        kpi_data = result_df.to_dict('records')[0]
        kpi_data['kpi_name'] = kpi_name
        kpi_data['data_source'] = 'duckdb'
        kpi_data['trend'] = 'up' if kpi_data.get('current_value', 0) > kpi_data.get('previous_value', 0) else 'down'
        return kpi_data

    def get_kpi_base_query(self, kpi_name: str) -> str:
        """Constructs a base SQL query for a given KPI using the FI_Star_View."""
        target_kpi = None
        for dp in self.data_products.values():
            for kpi in dp.kpis:
                if kpi.name == kpi_name:
                    target_kpi = kpi
                    break
            if target_kpi:
                break

        if not target_kpi:
            a9_logger.error(f"KPI '{kpi_name}' not found in any loaded data product.")
            return ""

        # Per architecture, all queries must target the main view.
        from_clause = "FI_Star_View"

        # Use the KPI definition to build the query
        aggregation = target_kpi.aggregation
        base_column = f'"{target_kpi.base_column}"'
        
        # Build the final query. The WHERE clause will be added by the NLP agent.
        query = f"SELECT {aggregation}({base_column}) AS current_value FROM {from_clause}"

        a9_logger.info(f"Constructed base query for KPI '{kpi_name}': {query}")
        return query

    def get_kpi_permanent_filters(self, kpi_name: str) -> Dict[str, Any]:
        """Returns the permanent filters defined for a KPI in the YAML contract."""
        target_kpi = None
        for dp in self.data_products.values():
            for kpi in dp.kpis:
                if kpi.name == kpi_name:
                    target_kpi = kpi
                    break
            if target_kpi:
                break

        if not target_kpi:
            a9_logger.error(f"KPI '{kpi_name}' not found when trying to get filters.")
            return {}

        kpi_filters = {}
        if target_kpi.filters:
            for f in target_kpi.filters:
                kpi_filters[f.column] = f.value
        
        a9_logger.info(f"Retrieved permanent filters for KPI '{kpi_name}': {kpi_filters}")
        return kpi_filters

    def get_kpis_for_business_processes(self, business_processes: list[str]) -> list[str]:
        """Returns a list of KPI names associated with the given business processes."""
        relevant_kpis = []
        for dp in self.data_products.values():
            for kpi in dp.kpis:
                # A KPI is relevant if any of its business_terms match the principal's processes
                if kpi.business_terms and any(bp in business_processes for bp in kpi.business_terms):
                    relevant_kpis.append(kpi.name)
        a9_logger.info(f"Found {len(relevant_kpis)} KPIs for business processes {business_processes}: {relevant_kpis}")
        return relevant_kpis

    def get_kpi_definition(self, kpi_name: str):
        """Finds and returns the KPI definition model for a given KPI name."""
        for dp in self.data_products.values():
            for kpi in dp.kpis:
                if kpi.name == kpi_name:
                    a9_logger.info(f"Found KPI definition for '{kpi_name}' in data product '{dp.data_product}'.")
                    return kpi
        a9_logger.warning(f"KPI definition for '{kpi_name}' not found in any loaded data product.")
        return None

    def get_schema(self, table_name: str) -> Dict[str, str]:
        """
        Retrieves the schema (column names and types) for a given table or view.
        """
        a9_logger.info(f"Retrieving schema for table/view: {table_name}")
        try:
            # Using DESCRIBE is a standard way to get schema info
            schema_df = self.execute_query(f"DESCRIBE {table_name}")
            if schema_df.empty:
                a9_logger.warning(f"Schema for '{table_name}' is empty or table does not exist.")
                return {}
            
            # The result of DESCRIBE has 'column_name' and 'column_type' columns
            schema = dict(zip(schema_df['column_name'], schema_df['column_type']))
            a9_logger.info(f"Successfully retrieved schema for '{table_name}': {schema}")
            return schema
        except Exception as e:
            a9_logger.error(f"Failed to retrieve schema for '{table_name}': {e}")
            return {}
