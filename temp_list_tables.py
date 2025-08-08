from src.agents.utils.a9_duckdb_utils import get_table_schema
import pprint

if __name__ == "__main__":
    table_name = "kpi_values"
    schema = get_table_schema(table_name)
    if schema:
        print(f"Schema for table '{table_name}':")
        # pprint is great for printing lists of tuples nicely
        pprint.pprint(schema)
    else:
        print(f"Could not retrieve schema for table '{table_name}'.")
