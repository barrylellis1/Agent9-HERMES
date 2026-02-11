
import pytest
import asyncio
from typing import Dict, Any, List
from pydantic import BaseModel, Field

from src.database.duckdb_manager import DuckDBManager
from src.registry.providers.database_provider import DatabaseRegistryProvider

class TestModel(BaseModel):
    id: str
    name: str
    value: int
    tags: List[str] = Field(default_factory=list)

@pytest.mark.asyncio
async def test_database_registry_provider_crud():
    # 1. Setup In-Memory DuckDB
    db_config = {"database_path": ":memory:"}
    db_manager = DuckDBManager(db_config)
    await db_manager.connect()
    
    # Create a table for testing
    # In hybrid schema, we need at least the key columns and a definition column
    create_table_sql = """
    CREATE TABLE test_items (
        id VARCHAR PRIMARY KEY,
        name VARCHAR,
        definition VARCHAR
    )
    """
    await db_manager.execute_query(create_table_sql)
    
    # 2. Initialize Provider
    provider = DatabaseRegistryProvider(
        db_manager=db_manager,
        table_name="test_items",
        model_class=TestModel,
        key_fields=["id"],
        json_column="definition"
    )
    
    # 3. Test Register (Create)
    item1 = TestModel(id="item1", name="Test Item 1", value=100, tags=["a", "b"])
    success = await provider.register(item1)
    assert success is True
    
    # Verify persistence
    # Note: Provider caches items, so we should clear cache or check DB directly to be sure
    provider._items.clear() 
    await provider.load()
    loaded_item = provider.get("item1")
    assert loaded_item is not None
    assert loaded_item.name == "Test Item 1"
    assert loaded_item.value == 100
    assert loaded_item.tags == ["a", "b"]
    
    # 4. Test Update (Upsert)
    item1_updated = TestModel(id="item1", name="Test Item 1 Updated", value=200, tags=["a", "b", "c"])
    success = await provider.upsert(item1_updated)
    assert success is True
    
    provider._items.clear()
    await provider.load()
    updated_item = provider.get("item1")
    assert updated_item.name == "Test Item 1 Updated"
    assert updated_item.value == 200
    
    # 5. Test Get All
    item2 = TestModel(id="item2", name="Test Item 2", value=300)
    await provider.register(item2)
    
    provider._items.clear()
    await provider.load()
    all_items = provider.get_all()
    assert len(all_items) == 2
    
    # 6. Test Delete
    success = await provider.delete("item1")
    assert success is True
    
    provider._items.clear()
    await provider.load()
    assert provider.get("item1") is None
    assert provider.get("item2") is not None
    
    # Cleanup
    await db_manager.disconnect()

if __name__ == "__main__":
    asyncio.run(test_database_registry_provider_crud())
