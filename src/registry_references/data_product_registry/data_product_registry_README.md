# Data Product Registry Schema (CSV)

This registry defines the metadata for all SAP data products onboarded into Agent9. Each row represents a single data product. All fields are required unless marked optional.

| Column               | Description                                                                                 | Example                                      |
|----------------------|---------------------------------------------------------------------------------------------|----------------------------------------------|
| product_id           | Unique product identifier                                                                   | dp_20250421_001                              |
| name                 | Human-readable product name                                                                 | Finance Revenue View                         |
| domain               | Source system/domain                                                                        | SAP                                          |
| description          | Description of the data product                                                             | Revenue KPIs from SAP                        |
| tags                 | Semicolon-separated tags                                                                    | erp;finance;revenue;sap                      |
| last_updated         | Last updated date (YYYY-MM-DD)                                                              | 2025-05-16                                   |
| documentation        | Link to product documentation                                                               | https://docs.example.com/finance-revenue     |
| reviewed             | TRUE if reviewed and approved, else FALSE                                                    | TRUE                                         |
| join_keys            | Join keys for linking to lookup/text tables (format: field:target_file.target_field)        | customer_id:customers.csv.customer_id        |
| kpi_mappings         | KPI mappings for business Q&A (format: kpi_name:Column Name;...)                            | revenue:Revenue Amount;profit:Profit Amount  |
| filters              | Allowed/default filters for queries (semicolon-separated)                                    | region;fiscal_year                           |
| aggregation_methods  | Supported aggregation functions (semicolon-separated)                                       | sum;avg;count                                |

## Example Row
```
product_id,name,domain,description,tags,last_updated,documentation,reviewed,join_keys,kpi_mappings,filters,aggregation_methods
"dp_20250421_001","Finance Revenue View","SAP","Revenue KPIs from SAP","erp;finance;revenue;sap","2025-05-16","https://docs.example.com/finance-revenue",TRUE,"customer_id:customers.csv.customer_id","revenue:Revenue Amount;profit:Profit Amount","region;fiscal_year","sum;avg;count"
```

## Notes
- Use `;` to separate multiple tags, KPIs, filters, or aggregation methods.
- For join_keys and kpi_mappings, use `:` to map field names to targets.
- All SAP sample data products to be onboarded must be listed here and kept up to date.
