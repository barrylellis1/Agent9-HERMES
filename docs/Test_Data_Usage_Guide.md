# Agent9 Test Data Usage Guide

## Overview

This guide explains how to use the SAP DataSphere test data for the Agent9 LLM Hackathon. The test data is maintained in an external location to ensure consistency across all implementations and to avoid duplicating large data files.

## Test Data Location

The test data is located at:
```
C:\Users\barry\Documents\Agent 9\SAP DataSphere Data\datasphere-content-1.7\datasphere-content-1.7\SAP_Sample_Content\CSV
```

This directory contains CSV files from SAP DataSphere that represent realistic business data for testing the Agent9 workflows.

## Accessing the Test Data

### For Local Development

When developing locally, you can access the test data directly from its location. Use the following approach in your code:

```python
import os
import pandas as pd

# Define the path to the test data
TEST_DATA_PATH = os.environ.get(
    "AGENT9_TEST_DATA_PATH", 
    r"C:\Users\barry\Documents\Agent 9\SAP DataSphere Data\datasphere-content-1.7\datasphere-content-1.7\SAP_Sample_Content\CSV"
)

# Load a specific test data file
def load_test_data(filename):
    """Load a test data file from the external test data location."""
    file_path = os.path.join(TEST_DATA_PATH, filename)
    return pd.read_csv(file_path)

# Example usage
sales_data = load_test_data("SALES_DATA.csv")
```

### Environment Variable Configuration

To make your code more portable, set the `AGENT9_TEST_DATA_PATH` environment variable in your `.env` file:

```
AGENT9_TEST_DATA_PATH=C:\Users\barry\Documents\Agent 9\SAP DataSphere Data\datasphere-content-1.7\datasphere-content-1.7\SAP_Sample_Content\CSV
```

This allows each developer or LLM to configure their own path to the test data without modifying the code.

## Available Test Data Files

The test data directory contains various CSV files representing different business data domains. Here are some of the key files:

- `SALES_DATA.csv` - Sales transactions and order data
- `CUSTOMER_DATA.csv` - Customer information and profiles
- `PRODUCT_DATA.csv` - Product catalog and details
- `INVENTORY_DATA.csv` - Inventory levels and warehouse information
- `FINANCIAL_DATA.csv` - Financial transactions and accounting data

> Note: The actual filenames may differ. Please check the test data directory for the exact filenames.

## Using Test Data with DuckDB

Agent9 uses DuckDB for data processing. Here's how to load the test data into DuckDB:

```python
import duckdb
import os

# Define the path to the test data
TEST_DATA_PATH = os.environ.get(
    "AGENT9_TEST_DATA_PATH", 
    r"C:\Users\barry\Documents\Agent 9\SAP DataSphere Data\datasphere-content-1.7\datasphere-content-1.7\SAP_Sample_Content\CSV"
)

# Connect to DuckDB (in-memory database)
conn = duckdb.connect(database=':memory:')

# Load a CSV file into a DuckDB table
def load_csv_to_duckdb(filename, table_name):
    """Load a CSV file into a DuckDB table."""
    file_path = os.path.join(TEST_DATA_PATH, filename)
    conn.execute(f"CREATE TABLE {table_name} AS SELECT * FROM read_csv_auto('{file_path}')")
    
# Example usage
load_csv_to_duckdb("SALES_DATA.csv", "sales")
```

## Data Contracts

The `src/contracts` directory contains YAML data contracts that define the expected schema and format for each data file. These contracts should be used to validate the test data before processing.

Example of using a data contract:

```python
import yaml
import os
import pandas as pd
from pydantic import BaseModel, create_model, ValidationError

# Load a data contract
def load_data_contract(contract_name):
    """Load a data contract from the contracts directory."""
    contract_path = os.path.join("src/contracts", f"{contract_name}.yaml")
    with open(contract_path, 'r') as file:
        return yaml.safe_load(file)

# Validate data against a contract
def validate_data(data, contract_name):
    """Validate data against a contract."""
    contract = load_data_contract(contract_name)
    
    # Create a Pydantic model from the contract
    fields = {}
    for field_name, field_type in contract["fields"].items():
        fields[field_name] = (eval(field_type["type"]), ...)
    
    DataModel = create_model(contract["name"], **fields)
    
    # Validate each row
    errors = []
    for index, row in data.iterrows():
        try:
            DataModel(**row.to_dict())
        except ValidationError as e:
            errors.append(f"Row {index}: {str(e)}")
    
    return len(errors) == 0, errors
```

## Best Practices

1. **Never hardcode the test data path** - Always use environment variables or configuration files.
2. **Validate data before processing** - Use the data contracts to validate the test data.
3. **Handle missing data gracefully** - The test data may contain missing values or edge cases.
4. **Document data dependencies** - If your implementation requires specific test data files, document these dependencies.
5. **Use relative paths within the test data directory** - This makes your code more portable.

## Troubleshooting

### Common Issues

1. **File not found errors**:
   - Check that the `AGENT9_TEST_DATA_PATH` environment variable is set correctly
   - Verify that the file exists in the test data directory
   - Ensure file paths use the correct directory separators for your OS

2. **Data format errors**:
   - Verify that the CSV file format matches your expectations
   - Check for header rows, delimiters, and encoding issues
   - Use pandas' `read_csv` parameters to handle special cases

3. **Performance issues with large files**:
   - Consider using DuckDB's streaming capabilities
   - Process data in chunks using pandas' `chunksize` parameter
   - Use appropriate indexing for faster lookups

## Support

If you encounter issues with the test data, please document them in your implementation notes or contact the hackathon organizers.
