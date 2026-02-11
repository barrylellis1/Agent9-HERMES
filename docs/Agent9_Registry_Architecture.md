# Agent9 Registry-Driven Architecture

## Overview

This document outlines the registry-driven architecture for Agent9, including the Unified Registry Access Layer, MVP Agents, and Decision Studio UI integration. The registry architecture provides a flexible, extensible, and professional approach to managing business metadata, replacing hardcoded enums and scattered business logic.

## Table of Contents

1. [Registry Architecture](#registry-architecture)
   - [Core Components](#core-components)
   - [Registry Providers](#registry-providers)
   - [Data Models](#data-models)
   - [Registry Factory](#registry-factory)
2. [Integration Patterns](#integration-patterns)
   - [Initialization Sequence](#initialization-sequence)
   - [Agent Integration](#agent-integration)
   - [UI Integration](#ui-integration)
3. [MVP Agents](#mvp-agents)
   - [Situation Awareness Agent](#situation-awareness-agent)
   - [Data Product MCP Service Agent](#data-product-mcp-service-agent)
   - [NLP Interface Agent](#nlp-interface-agent)
   - [Principal Context Agent](#principal-context-agent)
   - [Orchestrator Agent](#orchestrator-agent)
4. [Decision Studio UI](#decision-studio-ui)
   - [UI Components](#ui-components)
   - [Registry Integration](#registry-integration)
5. [Extension Points](#extension-points)
   - [Custom Providers](#custom-providers)
   - [Data Model Extension](#data-model-extension)
6. [Migration Guide](#migration-guide)
   - [Enum to Registry Migration](#enum-to-registry-migration)
   - [Backward Compatibility](#backward-compatibility)

## Registry Architecture

### Core Components

The Agent9 Registry Architecture consists of several core components:

1. **Registry Module**: The central access point for all registry functionality
2. **Registry Factory**: Creates and manages registry providers
3. **Registry Providers**: Supply registry data from various sources
4. **Data Models**: Define the structure of registry data
5. **Configuration System**: Controls registry initialization and behavior

```
┌─────────────────────┐     ┌─────────────────────┐
│                     │     │                     │
│    Agent9 Agents    │     │  Decision Studio UI │
│                     │     │                     │
└─────────┬───────────┘     └──────────┬──────────┘
          │                            │
          │                            │
          ▼                            ▼
┌─────────────────────────────────────────────────┐
│                                                 │
│              Registry Module                    │
│                                                 │
│  ┌─────────────────────────────────────────┐    │
│  │                                         │    │
│  │            Registry Factory             │    │
│  │                                         │    │
│  └───┬──────────────┬───────────────┬──────┘    │
│      │              │               │           │
│      ▼              ▼               ▼           │
│  ┌─────────┐    ┌─────────┐     ┌─────────┐     │
│  │Business │    │   KPI   │     │  Data   │     │
│  │Process  │    │Provider │     │Product  │     │
│  │Provider │    │         │     │Provider │     │
│  └─────────┘    └─────────┘     └─────────┘     │
│                                                 │
└─────────────────────────────────────────────────┘
```

### Registry Providers

Registry Providers are responsible for loading, storing, and providing access to registry data. Each provider specializes in a specific type of registry data:

1. **Business Process Provider**: Manages business process definitions
2. **KPI Provider**: Manages KPI definitions and evaluation logic
3. **Principal Profile Provider**: Manages principal (user) profiles and preferences
4. **Data Product Provider**: Manages data product definitions and schema information
5. **Database Registry Provider**: A generic provider for database-backed persistence (Postgres, DuckDB, etc.)

Each provider implements the `RegistryProvider[T]` interface, which defines common methods:

```python
class RegistryProvider[T]:
    async def load(self) -> None: ...
    def get(self, id_or_name: str) -> Optional[T]: ...
    def get_all(self) -> List[T]: ...
    def find_by_attribute(self, attr_name: str, attr_value: Any) -> List[T]: ...
    def register(self, item: T) -> bool: ...
```

Providers support multiple storage formats, including:
- Python modules
- YAML files
- JSON files
- CSV files
- Database records (via `DatabaseRegistryProvider`)

### Database Persistence (Hybrid Schema)

Agent9 supports a "Hybrid Schema" pattern for database persistence, enabling "Bring Your Own Database" (BYODB) for enterprise deployments. This decoupling allows the registry to run on Postgres, DuckDB, or other SQL-compliant backends.

**Key Features:**
- **Database Agnostic**: Uses `DatabaseManager` interface to support multiple backends (e.g., `PostgresManager`, `DuckDBManager`).
- **Hybrid Storage**:
  - **Core Columns**: First-class SQL columns for identity and search (`id`, `name`, `domain`).
  - **JSON Payload**: Full object definition stored in a JSON/Text column (`definition`) to avoid schema drift and frequent migrations.
- **Generic Provider**: `DatabaseRegistryProvider` handles CRUD operations for any Pydantic model.

**Configuration:**
To enable database persistence for a specific registry (e.g., KPIs), set the environment variable:
```bash
KPI_REGISTRY_BACKEND=database
DATABASE_URL=postgresql://user:pass@host:5432/db
```

### Data Models


The registry is built around well-defined data models that capture the business domain:

#### Business Process Model

```python
class BusinessProcess(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    domain: str
    owner: str
    kpis: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, str] = Field(default_factory=dict)
```

#### KPI Model

```python
class KPI(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    domain: str
    business_processes: List[str] = Field(default_factory=list)
    unit: Optional[str] = None
    thresholds: Dict[str, float] = Field(default_factory=dict)
    comparison_methods: List[str] = Field(default_factory=list)
    metadata: Dict[str, str] = Field(default_factory=dict)
    
    def evaluate(self, value: float, comparison_type: str = None) -> KPIEvaluationStatus:
        # KPI evaluation logic
        ...
```

#### Principal Profile Model

```python
class PrincipalProfile(BaseModel):
    id: str
    name: str
    title: str
    description: Optional[str] = None
    business_processes: List[str] = Field(default_factory=list)
    kpis: List[str] = Field(default_factory=list)
    preferences: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, str] = Field(default_factory=dict)
```

#### Data Product Model

```python
class DataProduct(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    domain: str
    owner: str
    version: str = "1.0.0"
    tables: Dict[str, TableDefinition] = Field(default_factory=dict)
    views: Dict[str, ViewDefinition] = Field(default_factory=dict)
    related_business_processes: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, str] = Field(default_factory=dict)
```

### Registry Factory

The Registry Factory is responsible for creating, initializing, and providing access to registry providers:

```python
class RegistryFactory:
    def register_provider(self, provider_type: str, provider: RegistryProvider[Any]) -> None: ...
    def get_provider(self, provider_type: str) -> RegistryProvider[Any]: ...
    async def initialize(self) -> None: ...
```

## Integration Patterns

### Initialization Sequence

The registry system follows a specific initialization sequence:

1. Application startup initiates registry initialization
2. Registry configuration is loaded
3. Registry providers are created and registered
4. Provider data sources are loaded
5. Registry is ready for use by agents and UI components

```python
# Example initialization
async def startup():
    # Create registry configuration
    config = RegistryConfig(
        providers={
            "data_product": ProviderConfig(
                enabled=True,
                source_path="src/contracts/fi_star_schema.yaml",
                storage_format="yaml"
            ),
            "business_process": ProviderConfig(
                enabled=True,
                source_path="src/registry/data/business_processes.py",
                storage_format="python"
            ),
            # ... other providers
        }
    )
    
    # Initialize registry
    await initialize_registry(config)
```

### Agent Integration

Agents interact with the registry through a consistent pattern:

1. Access the registry through the `get_registry()` function
2. Retrieve the appropriate provider
3. Use provider methods to access registry data

```python
async def process_request(self, request):
    # Get registry providers
    registry = get_registry()
    business_process_provider = registry.get_provider("business_process")
    kpi_provider = registry.get_provider("kpi")
    
    # Use registry data
    process = business_process_provider.get(request.process_id)
    kpis = kpi_provider.find_by_business_process(process.id)
    
    # Process request using registry data
    ...
```

### UI Integration

The Decision Studio UI integrates with the registry to provide context-aware visualizations and interactions:

1. React components access registry data through an API layer
2. Registry data drives UI components like dropdowns, filters, and visualizations
3. User actions can trigger registry updates

## MVP Agents

### Situation Awareness Agent

The Situation Awareness Agent uses the registry to:

1. Identify relevant business processes based on principal profile
2. Assess KPIs associated with those business processes
3. Detect situations requiring attention
4. Present findings in context of the principal's role

**Registry Integration Points**:
- Retrieves principal profile from Principal Profile Provider
- Gets business processes from Business Process Provider
- Accesses KPI definitions and thresholds from KPI Provider
- Uses Data Product Provider to identify data sources for analysis

### Data Product MCP Service Agent

The Data Product MCP Service Agent uses the registry to:

1. Discover data products from YAML contracts
2. Register tables and views in the database
3. Provide context-aware query capabilities
4. Connect data products to business processes and KPIs

**Registry Integration Points**:
- Loads data product definitions from Data Product Provider
- Retrieves schema and source information for tables and views
- Maps queries to appropriate data products
- Provides business context for query results

### NLP Interface Agent

The NLP Interface Agent uses the registry to:

1. Map natural language terms to business terminology
2. Identify entities in user queries
3. Connect queries to relevant business processes and KPIs
4. Generate context-aware responses

**Registry Integration Points**:
- Uses Business Process Provider for process terminology
- Accesses KPI Provider for metric terminology
- Leverages Data Product Provider for schema information
- Retrieves Principal Profile for personalization

### Principal Context Agent

The Principal Context Agent uses the registry to:

1. Load and manage principal profiles
2. Customize experiences based on role
3. Prioritize information based on responsibilities
4. Maintain preference history

**Registry Integration Points**:
- Manages Principal Profile Provider data
- Updates profiles based on user interactions
- Maps principals to business processes and KPIs

### Orchestrator Agent

The Orchestrator Agent uses the registry to:

1. Route requests to appropriate agents
2. Coordinate multi-agent workflows
3. Maintain context across agent interactions
4. Ensure protocol compliance

**Registry Integration Points**:
- Uses all providers to understand request context
- Selects appropriate agents based on business process and KPI context
- Ensures data product compatibility across agent boundaries

## Decision Studio UI

### UI Components

The Decision Studio UI includes several key components:

1. **Principal Selector**: Allows users to switch between principal perspectives
2. **KPI Dashboard**: Displays relevant KPIs based on principal profile
3. **Situation Cards**: Shows detected situations requiring attention
4. **Query Interface**: Provides natural language query capabilities
5. **Data Explorer**: Allows exploration of data products and visualization

### Registry Integration

The UI integrates with the registry through:

1. **API Layer**: Provides registry access to frontend components
2. **Context Providers**: React context providers that expose registry data
3. **Registry-Aware Components**: UI components that adapt based on registry data

```typescript
// Example React component using registry data
function KPIDashboard({ principalId }) {
  const [kpis, setKpis] = useState([]);
  
  useEffect(() => {
    // Fetch KPIs for the principal from registry
    async function fetchKPIs() {
      const response = await fetch(`/api/registry/principals/${principalId}/kpis`);
      const data = await response.json();
      setKpis(data.kpis);
    }
    
    fetchKPIs();
  }, [principalId]);
  
  return (
    <div className="kpi-dashboard">
      {kpis.map(kpi => (
        <KPICard 
          key={kpi.id}
          kpi={kpi}
          status={kpi.status}
          value={kpi.value}
        />
      ))}
    </div>
  );
}
```

## Extension Points

### Custom Providers

The registry architecture supports custom providers through:

1. **Provider Interface**: Implementing the `RegistryProvider[T]` interface
2. **Factory Registration**: Registering custom providers with the factory
3. **Custom Storage Formats**: Adding support for new storage formats

### Data Model Extension

Data models can be extended through:

1. **Metadata Fields**: Using the `metadata` dictionary for custom attributes
2. **Model Inheritance**: Creating specialized model classes
3. **Provider Extensions**: Extending provider capabilities for custom models

## Migration Guide

### Enum to Registry Migration

Migrating from enum-based approaches to the registry system:

1. **Identify Enums**: Locate hardcoded enums in the codebase
2. **Create Models**: Define appropriate registry models
3. **Implement Provider**: Create a provider for the models
4. **Update Code**: Replace enum references with registry calls
5. **Test Compatibility**: Ensure behavior is preserved

### Backward Compatibility

The registry system maintains backward compatibility through:

1. **Legacy ID Support**: Registry models provide `legacy_id` properties
2. **from_enum_value Methods**: Convert enum values to registry models
3. **Fallback Logic**: Providers attempt to handle legacy identifiers

```python
# Example of backward compatibility
# Old code
kpi_status = calculate_kpi_status(KPI_ENUM.GROSS_MARGIN, value)

# New code (works with both new and old approaches)
kpi = kpi_provider.get("GROSS_MARGIN")  # Works with both enum values and registry IDs
kpi_status = kpi.evaluate(value)
```

## Conclusion

The Agent9 Registry Architecture transforms the system from a collection of hardcoded rules and scattered logic to a flexible, extensible, and professional registry system. This architecture enables:

1. **Customer-Driven Extensibility**: Customers can add their own business processes, KPIs, and data products
2. **Consistent Access Patterns**: All agents use the same registry API
3. **Rich Business Context**: Registry data models capture relationships between business concepts
4. **Simplified Maintenance**: Business logic is centralized in the registry
5. **Enhanced Personalization**: Principal profiles drive context-aware experiences

By implementing this architecture, Agent9 positions itself as a robust application suitable for investor demonstrations and customer deployments.
