
import pytest
# arch-allow-direct-agent-construction
import pytest_asyncio
import os
import json
from unittest.mock import MagicMock, patch, mock_open

from src.registry.factory import RegistryFactory
from src.registry.bootstrap import RegistryBootstrap
from src.agents.new.a9_kpi_assistant_agent import A9_KPI_Assistant_Agent, KPIFinalizeRequest
from src.registry.models.kpi import KPI
from src.database.manager_factory import DatabaseManagerFactory
from src.database.duckdb_manager import DuckDBManager

@pytest.fixture
def mock_env_vars(monkeypatch):
    """Set up environment variables for database registry"""
    monkeypatch.setenv("KPI_REGISTRY_BACKEND", "database")
    monkeypatch.setenv("DATABASE_URL", "duckdb://:memory:")
    # We need to make sure we don't accidentally use real keys if they exist
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_SERVICE_ROLE_KEY", raising=False)

@pytest_asyncio.fixture
async def setup_registry(mock_env_vars):
    """Initialize registry with DuckDB backend"""
    # Reset singletons
    RegistryFactory._instance = None
    RegistryBootstrap._initialized = False
    RegistryBootstrap._factory = None
    RegistryBootstrap._db_manager = None
    
    # 1. Manually create Database Manager
    db_config = {"database_path": ":memory:"}
    db_manager = DuckDBManager(db_config)
    await db_manager.connect()
    
    # 2. Create tables BEFORE initialization
    # Hybrid schema: id, name, domain, definition (json)
    create_sql = """
    CREATE TABLE kpis (
        id VARCHAR PRIMARY KEY,
        name VARCHAR,
        domain VARCHAR,
        owner_role VARCHAR,
        definition VARCHAR
    )
    """
    await db_manager.execute_query(create_sql)
    
    # 3. Inject manager into RegistryBootstrap
    RegistryBootstrap._db_manager = db_manager
    
    # 4. Initialize Bootstrap (will use injected manager and load from existing empty table)
    await RegistryBootstrap.initialize()
    
    # Get the factory
    factory = RegistryFactory()
    provider = factory.get_kpi_provider()
    
    # Check if we got the DatabaseRegistryProvider
    from src.registry.providers.database_provider import DatabaseRegistryProvider
    if not isinstance(provider, DatabaseRegistryProvider):
        # Fallback if init failed (e.g. imports) or config didn't take
        pytest.fail(f"Failed to initialize DatabaseRegistryProvider. Got {type(provider)}")
    
    yield factory
    
    # Cleanup
    await db_manager.disconnect()
    RegistryBootstrap._db_manager = None

@pytest.mark.asyncio
async def test_kpi_persistence_flow(setup_registry):
    """
    Integration test: A9_KPI_Assistant_Agent -> DatabaseRegistryProvider -> DuckDB
    """
    factory = setup_registry
    
    # Initialize Agent
    # We mock the LLM part since we are testing persistence
    agent = A9_KPI_Assistant_Agent()
    
    # Mock internal agent methods that rely on file system or LLM
    # We want to test finalize_kpis -> _trigger_registry_updates
    
    # Sample KPI data
    kpi_id = "test_persistence_kpi"
    kpi_data = {
        "id": kpi_id,
        "name": "Test Persistence KPI",
        "domain": "Test",
        "description": "A KPI to test database persistence",
        "unit": "Count",
        "data_product_id": "dp_test",
        "sql_query": "SELECT 1",
        "owner_role": "Test User",
        "metadata": {
            "line": "top_line", 
            "altitude": "strategic",
            "profit_driver_type": "revenue",
            "lens_affinity": "test"
        }
    }
    
    request = KPIFinalizeRequest(
        data_product_id="dp_test",
        kpis=[kpi_data],
        extend_mode=True,
        principal_id="tester"
    )
    
    # Mock file operations to avoid writing to real disk
    # Use AsyncMock for async methods
    with patch("src.agents.new.a9_kpi_assistant_agent.os.path.exists", return_value=True), \
         patch("src.agents.new.a9_kpi_assistant_agent.open", mock_open(read_data="data_product_id: dp_test\nkpis: []")), \
         patch.object(agent, "_save_contract_yaml", new_callable=MagicMock) as mock_save, \
         patch.object(agent, "_load_contract_yaml", new_callable=MagicMock) as mock_load:
        
        # Configure async mocks
        async def async_load(*args, **kwargs):
            return "data_product_id: dp_test\nkpis: []"
        mock_load.side_effect = async_load
        
        async def async_save(*args, **kwargs):
            return None
        mock_save.side_effect = async_save
        
        # Run finalize
        response = await agent.finalize_kpis(request)
        
        if response.status == "error":
            print(f"Agent Error Message: {getattr(response, 'error_message', response)}")
            
        assert response.status == "success"
        assert kpi_id in response.registry_updates["success"]
        
        # VERIFY: Check if data is in the database
        provider = factory.get_kpi_provider()
        
        # Verify via provider.get() (which checks cache)
        # Note: DatabaseRegistryProvider implementation caches on write
        retrieved_kpi = provider.get(kpi_id)
        assert retrieved_kpi is not None
        assert retrieved_kpi.name == "Test Persistence KPI"
        
        # VERIFY: Check directly in DB (bypass cache) to ensure persistence
        db_manager = provider.db_manager
        result_df = await db_manager.execute_query(f"SELECT * FROM kpis WHERE id = '{kpi_id}'")
        
        assert len(result_df) == 1
        row = result_df.iloc[0]
        assert row["id"] == kpi_id
        assert row["name"] == "Test Persistence KPI"
        
        # Check definition JSON
        definition = json.loads(row["definition"])
        assert definition["id"] == kpi_id
        assert definition["metadata"]["altitude"] == "strategic"
