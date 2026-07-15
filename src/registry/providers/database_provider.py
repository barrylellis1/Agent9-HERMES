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
            key_fields: List of column names that form the unique key (default: ["client_id", "id"])
            json_column: Name of the column to store the full JSON payload (default: "definition")
            client_id: If set, only load/write records for this client. Does NOT affect key_fields —
                       every table this provider manages has a composite (client_id, id) primary key
                       regardless of whether this instance loads one tenant or all of them (bootstrap
                       loads with client_id=None to serve all tenants from one cache, but writes still
                       need the real composite key or ON CONFLICT has no matching constraint to target).
        """
        super().__init__()
        self.db_manager = db_manager
        self.table_name = table_name
        self.model_class = model_class
        self.client_id = client_id
        self.key_fields = key_fields or ["client_id", "id"]
        self.json_column = json_column
        self._columns_cache: Optional[set] = None

        self._items: Dict[str, T] = {}

    async def _get_columns(self) -> set:
        """Introspect the table's real columns (cached after first call).

        Infra A2: writes must only include keys that exist as real columns —
        these tables are fully columnar (no generic JSON blob column), so
        blindly including every model_dump() key fails with "column ... does
        not exist". table_name is a fixed constructor argument (never user
        input), so inlining it into the SQL string here is safe.
        """
        if self._columns_cache is None:
            df = await self.db_manager.execute_query(
                f"SELECT column_name FROM information_schema.columns WHERE table_name = '{self.table_name}'"
            )
            columns = set(df["column_name"]) if not df.empty else set()
            if not columns:
                raise RuntimeError(
                    f"DatabaseRegistryProvider: table '{self.table_name}' has no columns "
                    "(introspection failed or table does not exist) — refusing to write blind"
                )
            self._columns_cache = columns
        return self._columns_cache

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
            if self.client_id and hasattr(self.db_manager, "fetch_records_scoped"):
                # Infra B3: client-scoped load runs under the RLS tenant role so the
                # database itself enforces isolation, not just the filter below.
                records = await self.db_manager.fetch_records_scoped(
                    self.table_name, self.client_id
                )
            else:
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

    async def _serialize_item(self, item: T) -> Dict[str, Any]:
        """
        Convert a Pydantic model to a DB record dict.

        These tables are fully columnar (kpis, principal_profiles,
        data_products, business_processes, business_glossary_terms all have
        typed columns for every field, verified against
        information_schema.columns — none has a generic JSON blob column).
        The previous "hybrid schema" design assumed a `definition` blob column
        that doesn't exist on any of them (and on business_glossary_terms,
        `definition` is a real, unrelated column holding the term's own
        definition text) — writing to it always failed with "column
        ... does not exist", silently swallowed by register()'s try/except.
        Only include keys that are real columns on this table.
        """
        model_dump = item.model_dump(mode="json")
        columns = await self._get_columns()
        return {k: v for k, v in model_dump.items() if k in columns}

    def _cache_item(self, item: T) -> None:
        """Add item to internal cache, keyed by composite (client_id:id) when client_id is present."""
        if not hasattr(item, "id"):
            return
        client_prefix = getattr(item, "client_id", None)
        key = f"{client_prefix}:{item.id}" if client_prefix else item.id
        self._items[key] = item

    def get(self, id_or_name: str) -> Optional[T]:
        """Get an item by ID. Tries composite key (client_id:id) first, then plain id,
        then a bare-id linear scan for items cached under a different client prefix
        (e.g. shared records stored with client_id='default')."""
        if self.client_id:
            result = self._items.get(f"{self.client_id}:{id_or_name}")
            if result is not None:
                return result
        result = self._items.get(id_or_name)
        if result is not None:
            return result
        # Fallback: scan for matching bare id — handles items stored under a client_id
        # prefix different from the lookup context (e.g. shared records with client_id='default')
        for item in self._items.values():
            if getattr(item, "id", None) == id_or_name:
                return item
        return None

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

    async def register(self, item: T) -> bool:
        """
        Register (Upsert) an item to the database.

        Async — callers MUST await this. Historically this returned an
        unawaited coroutine (the DB write was silently a no-op for every
        caller that didn't await it); it is now a real async method so a
        missing `await` fails loudly (unawaited-coroutine warning / wrong
        type) instead of silently dropping the write.
        """
        # Update cache immediately (optimistic)
        self._cache_item(item)

        try:
            record = await self._serialize_item(item)
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

    async def upsert(self, item: T) -> bool:
        """Alias for register."""
        return await self.register(item)

    async def delete(self, item_id: str) -> bool:
        """Delete an item. Async — callers MUST await this."""
        if item_id in self._items:
            del self._items[item_id]
        return await self._delete_async(item_id)

    async def _delete_async(self, item_id: str) -> bool:
        try:
            # Handle composite keys: when multiple key_fields are present, item_id is in format "field1_value:field2_value:..."
            if len(self.key_fields) > 1:
                # Parse composite key (format: "{field0_value}:{field1_value}:...")
                parts = item_id.split(":", len(self.key_fields) - 1)
                if len(parts) != len(self.key_fields):
                    logger.error(f"Composite key {item_id} does not match expected {len(self.key_fields)} fields")
                    return False
                # Infra B3: delete must match ALL key fields. Deleting by the bare id
                # alone removes the same-id row of every other tenant.
                keys = dict(zip(self.key_fields, parts))
                if hasattr(self.db_manager, "delete_record_multi"):
                    return await self.db_manager.delete_record_multi(self.table_name, keys)
                # Fallback for managers without composite delete: last key field (id)
                success = await self.db_manager.delete_record(self.table_name, self.key_fields[-1], parts[-1])
                return success
            else:
                # Single key field: delete by that field
                key_col = self.key_fields[0]
                success = await self.db_manager.delete_record(self.table_name, key_col, item_id)
                return success
        except Exception as e:
            logger.error(f"Error deleting item {item_id}: {e}")
            return False
