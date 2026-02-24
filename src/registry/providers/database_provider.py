"""
Database Registry Provider

A generic registry provider that persists data to a SQL database using the DatabaseManager.
It supports the "Hybrid Schema" pattern where core identity columns are first-class,
and the full object definition can be stored in a generic JSON/Text column.
"""

import logging
import json
from typing import Any, Dict, List, Optional, Type, TypeVar, Generic

from pydantic import BaseModel

from src.database.manager_interface import DatabaseManager
from src.registry.providers.registry_provider import RegistryProvider

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

class DatabaseRegistryProvider(RegistryProvider[T]):
    """
    Generic provider that persists registry items to a database table.
    """

    def __init__(
        self,
        db_manager: DatabaseManager,
        table_name: str,
        model_class: Type[T],
        key_fields: List[str] = None,
        json_column: str = "definition",
        client_id: Optional[str] = None
    ):
        """
        Initialize the database registry provider.

        Args:
            db_manager: Configured DatabaseManager instance (Postgres, DuckDB, etc.)
            table_name: Name of the database table to persist to
            model_class: Pydantic model class for deserialization
            key_fields: List of column names that form the unique key (default: ["id"] or ["client_id","id"])
            json_column: Name of the column to store the full JSON payload (default: "definition")
            client_id: If set, only load/write records for this client. Also changes default key_fields
                       to ["client_id", "id"] for composite PK upserts.
        """
        super().__init__()
        self.db_manager = db_manager
        self.table_name = table_name
        self.model_class = model_class
        self.client_id = client_id
        # When client_id is provided, default key_fields to composite PK
        self.key_fields = key_fields or (["client_id", "id"] if client_id else ["id"])
        self.json_column = json_column

        self._items: Dict[str, T] = {}

    async def load(self) -> None:
        """
        Load items from the database into memory.
        If client_id is set, only loads records for that client.
        """
        logger.info(
            f"Loading {self.model_class.__name__} items from table {self.table_name}"
            + (f" (client_id={self.client_id})" if self.client_id else "")
        )

        try:
            filters = {"client_id": self.client_id} if self.client_id else None
            records = await self.db_manager.fetch_records(self.table_name, filters=filters)

            loaded_count = 0
            for record in records:
                try:
                    item = self._deserialize_record(record)
                    self._cache_item(item)
                    loaded_count += 1
                except Exception as e:
                    logger.warning(f"Failed to deserialize record from {self.table_name}: {e}")
            
            logger.info(f"Loaded {loaded_count} items from {self.table_name}")
            
        except Exception as e:
            logger.error(f"Failed to load items from database: {e}")
            # Do not raise, just log, so fallback mechanisms can work if implemented at factory level

    def _deserialize_record(self, record: Dict[str, Any]) -> T:
        """
        Convert a DB record to a Pydantic model.
        Prioritizes the 'definition' JSON column if present, then merges/overrides with explicit columns.
        """
        data = {}
        
        # 1. Try to load from JSON column
        if self.json_column in record and record[self.json_column]:
            val = record[self.json_column]
            if isinstance(val, str):
                try:
                    data = json.loads(val)
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON in {self.json_column} column")
            elif isinstance(val, dict):
                data = val
        
        # 2. Merge explicit columns (they take precedence or fill gaps)
        # We exclude the json_column itself from the top-level fields
        for k, v in record.items():
            if k != self.json_column and v is not None:
                # Basic type conversion if needed (e.g. timestamps) could happen here
                data[k] = v
                
        # 3. Create model
        return self.model_class(**data)

    def _serialize_item(self, item: T) -> Dict[str, Any]:
        """
        Convert a Pydantic model to a DB record dict.
        Stores full dump in json_column, and specific fields as top-level columns.
        """
        model_dump = item.model_dump()
        
        # Start with the full payload in the JSON column
        record = {
            self.json_column: json.dumps(model_dump, default=str)
        }
        
        # Promote top-level fields to columns if they exist in the model
        # NOTE: In a real "Hybrid Schema", we only promote columns that actually exist in the DB table.
        # Since we don't know the DB schema schema here, we might rely on the DB manager to ignore extra keys
        # OR we rely on the specific provider subclass to know which columns to promote.
        # For this generic implementation, we will promote ID and basic metadata fields 
        # that are common across our tables (id, name, domain, etc).
        
        common_fields = ["id", "client_id", "name", "domain", "owner", "owner_role", "title", "version"]
        for field in common_fields:
            if field in model_dump:
                record[field] = model_dump[field]
                
        # Also promote key fields to ensure upsert works
        for field in self.key_fields:
            if field in model_dump:
                record[field] = model_dump[field]
                
        return record

    def _cache_item(self, item: T) -> None:
        """Add item to internal cache, keyed by composite (client_id:id) when client_id is present."""
        if not hasattr(item, "id"):
            return
        client_prefix = getattr(item, "client_id", None)
        key = f"{client_prefix}:{item.id}" if client_prefix else item.id
        self._items[key] = item

    def get(self, id_or_name: str) -> Optional[T]:
        """Get an item by ID. Tries composite key (client_id:id) first, then plain id."""
        if self.client_id:
            result = self._items.get(f"{self.client_id}:{id_or_name}")
            if result is not None:
                return result
        return self._items.get(id_or_name)

    def get_all(self) -> List[T]:
        """Get all items."""
        return list(self._items.values())

    def find_by_attribute(self, attr_name: str, attr_value: Any) -> List[T]:
        """Find items by attribute."""
        results = []
        for item in self._items.values():
            if hasattr(item, attr_name) and getattr(item, attr_name) == attr_value:
                results.append(item)
            # Check list attributes
            elif hasattr(item, attr_name):
                val = getattr(item, attr_name)
                if isinstance(val, list) and attr_value in val:
                    results.append(item)
        return results

    def register(self, item: T) -> bool:
        """
        Register (Upsert) an item to the database.
        Note: This method is sync in the base class but we need async for DB.
        The base class `register` signature is `def register(self, item: T) -> bool`.
        We cannot make it async without breaking the interface or requiring callers to await.
        
        However, Supabase providers already implemented `async def register` which violated the type hint 
        but worked because callers awaited it (or checked isawaitable).
        
        We will implement `register` as async (compatible with our refactored callers).
        """
        # Update cache immediately (optimistic)
        self._cache_item(item)
        
        # We need to schedule the DB write. 
        # Since we are in a sync context if following strict base class, 
        # but we know our application uses async.
        # We will return a Coroutine.
        return self._register_async(item)

    async def _register_async(self, item: T) -> bool:
        """Async implementation of register."""
        try:
            record = self._serialize_item(item)
            success = await self.db_manager.upsert_record(
                self.table_name, 
                record, 
                self.key_fields
            )
            if success:
                logger.info(f"Persisted {item.id} to {self.table_name}")
            else:
                logger.error(f"Failed to persist {item.id} to {self.table_name}")
            return success
        except Exception as e:
            logger.error(f"Error persisting item {item.id}: {e}")
            return False

    def upsert(self, item: T) -> bool:
        """Alias for register."""
        return self.register(item)
    
    def delete(self, item_id: str) -> bool:
        """
        Delete an item.
        Returns coroutine.
        """
        if item_id in self._items:
            del self._items[item_id]
        return self._delete_async(item_id)

    async def _delete_async(self, item_id: str) -> bool:
        try:
            # Assuming single key field for deletion for now
            key_col = self.key_fields[0]
            success = await self.db_manager.delete_record(self.table_name, key_col, item_id)
            return success
        except Exception as e:
            logger.error(f"Error deleting item {item_id}: {e}")
            return False
