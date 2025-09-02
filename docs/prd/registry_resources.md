# Agent9 Registry Resources

This document provides a comprehensive overview of the registry resources available in the Agent9 system. These registries serve as the central source of truth for various components of the system, including principal profiles, business processes, KPIs, data products, and business glossary terms.

## Registry Structure

The Agent9 registry is organized into the following main categories:

1. **Principal Registry** - Contains principal profiles and role definitions
2. **Business Process Registry** - Contains business process definitions across domains
3. **KPI Registry** - Contains key performance indicators and their definitions
4. **Data Product Registry** - Contains data product definitions and metadata
5. **Business Glossary** - Contains business terms and their technical mappings

## Principal Registry

Located at: `src/registry/principal/principal_registry.yaml`

The Principal Registry contains detailed profiles for organizational principals (executives, managers, etc.) and their associated roles. Each principal profile includes:

- **Basic Information**: ID, name, title, role, department
- **Responsibilities**: List of key responsibilities
- **Business Processes**: Associated business processes
- **Default Filters**: Default dimensional filters for data views
- **Timeframes**: Typical timeframes for analysis
- **Groups**: Principal group memberships
- **Persona Profile**: Decision style, risk tolerance, communication style, values
- **Preferences**: UI and communication preferences
- **Permissions**: Access control permissions
- **Communication**: Detail level, format preferences, emphasis areas

### Available Principals

The registry currently includes profiles for:

- Chief Financial Officer (CFO)
- Chief Executive Officer (CEO)
- Chief Operating Officer (COO)

### Role Definitions

The registry also includes standardized role definitions with:
- Role ID
- Name
- Description
- Associated permissions

## Business Process Registry

Located at: `src/registry/business_process/business_process_registry.yaml`

The Business Process Registry contains definitions of business processes across multiple domains. Each business process includes:

- **ID**: Unique identifier
- **Name**: Process name
- **Domain**: Business domain (Finance, HR, Marketing, etc.)
- **Description**: Detailed description of the process
- **Owner Role**: Principal role responsible for the process
- **Stakeholder Roles**: Other roles with interest in the process
- **Display Name**: Formatted name for display
- **Tags**: Categorization tags

### Available Domains

The registry includes business processes across multiple domains:

1. **Finance**: Profitability Analysis, Revenue Growth Analysis, Expense Management, Cash Flow Management, Budget vs. Actuals, Investor Relations Reporting
2. **Strategy**: Market Share Analysis, EBITDA Growth Tracking, Capital Allocation Efficiency
3. **Operations**: Order-to-Cash Cycle Optimization, Inventory Turnover Analysis, Manufacturing Efficiency
4. **Supply Chain**: Logistics Efficiency
5. **HR**: Employee Attrition Rate Analysis, Talent Acquisition Effectiveness, Compensation Ratio Analysis, Workforce Diversity Reporting
6. **Marketing**: Customer Acquisition Cost, Brand Sentiment Analysis, Campaign ROI Tracking
7. **IT**: Project Spend vs. Budget, System Uptime/Downtime Analysis, Cybersecurity Incident Rate, Digital Transformation ROI
8. **Data**: Data Quality Score Tracking, Data Access Compliance Audits, Analytics Adoption Rate, Self-Service BI Usage
9. **Team**: Productivity Metrics, Project Milestone Tracking, Budget Adherence

## KPI Registry

Located at: `src/registry/kpi/kpi_registry.yaml`

The KPI Registry contains definitions of key performance indicators. Each KPI includes:

- **ID**: Unique identifier
- **Name**: KPI name
- **Domain**: Business domain
- **Description**: Detailed description
- **Unit**: Measurement unit (e.g., $, %)
- **Data Product ID**: Associated data product
- **Business Process IDs**: Associated business processes
- **SQL Query**: Query to calculate the KPI
- **Thresholds**: Performance thresholds (green, yellow, red) for different comparison types
- **Dimensions**: Available dimensions for analysis
- **Tags**: Categorization tags
- **Owner Role**: Principal role responsible for the KPI
- **Stakeholder Roles**: Other roles with interest in the KPI

### Available KPIs

The registry currently focuses on Finance KPIs:

1. **Gross Revenue**: Total gross revenue recognized in the period
2. **Cost of Goods Sold**: Total cost of goods sold in the period
3. **Gross Margin**: Calculated as Gross Revenue minus Cost of Goods Sold
4. **Utilities Expense**: Total utilities expense
5. **Office Expense**: Total office expense
6. **Payroll**: Total payroll expense

## Data Product Registry

Located at: `src/registry/data_product/data_product_registry.yaml`

The Data Product Registry contains definitions of data products available in the system. Each data product includes:

- **Product ID**: Unique identifier
- **Name**: Data product name
- **Domain**: Business domain
- **Description**: Detailed description
- **Tags**: Categorization tags
- **Last Updated**: Date of last update
- **Documentation**: Additional documentation
- **Reviewed**: Review status
- **Language**: Data language
- **Output Path**: Path to output data
- **YAML Contract Path**: Path to YAML contract definition

### Available Data Products

The registry includes data products across multiple domains:

1. **Finance**: FI Star Schema with Account Hierarchy, GL Accounts
2. **HR**: Employee Headcount, Employee Performance, Employee Personal Data
3. **Sales**: Sales Orders, Sales Order Items

## Business Glossary

Located at: `src/registry/data/business_glossary.yaml`

The Business Glossary contains definitions of business terms and their technical mappings. Each term includes:

- **Name**: Term name
- **Synonyms**: Alternative names
- **Description**: Detailed description
- **Technical Mappings**: Mappings to technical systems (e.g., SAP, DuckDB)

### Available Terms

The glossary currently includes:

1. **Revenue**: Total income generated from sales
2. **Profit Margin**: Percentage of profit relative to revenue
3. **Expense**: Money spent on goods, services, or operations
4. **Customer Satisfaction**: Measure of how satisfied customers are with products or services

## Registry Access

The registries are accessed through provider classes in the `src/registry/providers` directory:

- `principal_provider.py`: Access to principal profiles
- `business_process_provider.py`: Access to business processes
- `kpi_provider.py`: Access to KPIs
- `data_product_provider.py`: Access to data products
- `business_glossary_provider.py`: Access to business glossary terms

These providers are instantiated through the `RegistryFactory` class in `src/registry/factory.py`.

## Registry Models

The registry data structures are defined as Pydantic models in the `src/registry/models` directory:

- `principal.py`: Principal profile models
- `business_process.py`: Business process models
- `kpi.py`: KPI models
- `data_product.py`: Data product models

These models ensure type safety and validation for registry data.
