"""
BigQuery Manager - Implementation of the database manager interface for Google BigQuery.

This module implements the DatabaseManager interface for Google BigQuery, providing
query execution and metadata helpers that the Agent9 Data Product Agent can use for
schema inspection and curated view profiling.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from src.database.manager_interface import DatabaseManager

try:  # pragma: no cover - dependency may be missing in some environments
    from google.cloud import bigquery  # type: ignore
    from google.oauth2 import service_account  # type: ignore
except Exception:  # pragma: no cover - dependency missing
    bigquery = None  # type: ignore
    service_account = None  # type: ignore


class BigQueryManager(DatabaseManager):
    """
    DatabaseManager implementation for Google BigQuery.
    Provides curated view discovery and SQL execution capabilities.
    """

    def __init__(self, config: Dict[str, Any], logger: Optional[logging.Logger] = None):
        self.config = config or {}
        self.logger = logger or logging.getLogger(__name__)
        self.client: Optional["bigquery.Client"] = None  # type: ignore[name-defined]
        self.project: Optional[str] = self.config.get("project")
        self.dataset: Optional[str] = self.config.get("dataset")

    async def connect(self, connection_params: Dict[str, Any]) -> bool:
        """
        Establish a BigQuery client using service-account credentials supplied via overrides.
        """
        if bigquery is None:
            self.logger.error("google-cloud-bigquery package is not installed")
            return False

        params = dict(self.config)
        params.update(connection_params or {})

        project = params.get("project") or self.project
        dataset = params.get("dataset") or params.get("schema") or self.dataset
        credentials = None

        try:
            if params.get("service_account_info"):
                if service_account is None:
                    raise RuntimeError("google-auth is required for service account usage")
                credentials = service_account.Credentials.from_service_account_info(
                    params["service_account_info"]
                )
            elif params.get("service_account_json_path"):
                if service_account is None:
                    raise RuntimeError("google-auth is required for service account usage")
                credentials = service_account.Credentials.from_service_account_file(
                    params["service_account_json_path"]
                )

            client_kwargs: Dict[str, Any] = {}
            if project:
                client_kwargs["project"] = project
            if credentials is not None:
                client_kwargs["credentials"] = credentials

            self.client = bigquery.Client(**client_kwargs)  # type: ignore[call-arg]
            self.project = project or self.client.project
            self.dataset = dataset

            self.logger.info(
                "Connected to BigQuery project '%s' (dataset=%s)",
                self.project,
                self.dataset,
            )
            return True
        except Exception as exc:
            self.logger.error("Failed to connect to BigQuery: %s", exc)
            self.client = None
            return False

    async def disconnect(self) -> bool:
        """
        Close the BigQuery client.
        """
        try:
            if self.client:
                await asyncio.to_thread(self.client.close)
                self.client = None
            return True
        except Exception as exc:
            self.logger.warning("Error closing BigQuery client: %s", exc)
            return False

    async def execute_query(
        self,
        sql: str,
        parameters: Optional[Dict[str, Any]] = None,
        transaction_id: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Execute a SQL query using BigQuery and return a pandas DataFrame.
        """
        if self.client is None:
            raise RuntimeError("BigQuery client is not connected")

        tx_id = transaction_id or "bq"
        try:
            job_config = bigquery.QueryJobConfig()  # type: ignore[name-defined]

            if self.dataset and self.project:
                job_config.default_dataset = f"{self.project}.{self.dataset}"

            query_parameters = []
            if parameters:
                for name, value in parameters.items():
                    if isinstance(value, float):
                        param_type = "FLOAT64"
                    elif isinstance(value, int):
                        param_type = "INT64"
                    else:
                        param_type = "STRING"
                    query_parameters.append(
                        bigquery.ScalarQueryParameter(name, param_type, value)  # type: ignore[name-defined]
                    )
                job_config.query_parameters = query_parameters

            def _run_query() -> pd.DataFrame:
                job = self.client.query(sql, job_config=job_config)
                result = job.result()
                return result.to_dataframe(create_bqstorage_client=False)

            df = await asyncio.to_thread(_run_query)
            self.logger.info("[TXN:%s] BigQuery query succeeded (rows=%s)", tx_id, len(df))
            return df
        except Exception as exc:
            import traceback
            self.logger.error("[TXN:%s] BigQuery query failed: %s", tx_id, exc)
            self.logger.error("[TXN:%s] Full traceback:\n%s", tx_id, traceback.format_exc())
            self.logger.error("[TXN:%s] Query was: %s", tx_id, sql)
            raise  # Re-raise the exception to allow caller to handle it

    async def create_view(
        self,
        view_name: str,
        sql: str,
        replace_existing: bool = True,
        transaction_id: Optional[str] = None,
    ) -> bool:
        """
        Creating views via the adapter is not supported for curated data products.
        """
        self.logger.warning("BigQueryManager.create_view is not supported")
        return False

    async def list_views(self, transaction_id: Optional[str] = None) -> List[str]:
        """
        List available views within the configured dataset.
        """
        if self.client is None or not self.dataset or not self.project:
            return []

        sql = (
            f"SELECT table_name FROM `{self.project}.{self.dataset}.INFORMATION_SCHEMA.VIEWS`"
        )
        df = await self.execute_query(sql, transaction_id=transaction_id)
        return df["table_name"].tolist() if not df.empty and "table_name" in df else []

    async def register_data_source(
        self,
        source_info: Dict[str, Any],
        transaction_id: Optional[str] = None,
    ) -> bool:
        """
        Registering external sources is out of scope for the BigQuery adapter.
        """
        self.logger.warning("BigQueryManager.register_data_source is not supported")
        return False

    async def validate_sql(self, sql: str) -> Tuple[bool, Optional[str]]:
        """
        Basic validation to ensure only read-only statements are executed.
        """
        normalized = " ".join(sql.strip().lower().split())
        if not (normalized.startswith("select") or normalized.startswith("with")):
            return False, "Only SELECT/WITH statements are permitted for BigQuery execution"
        disallowed = [
            " insert ",
            " update ",
            " delete ",
            " merge ",
            " create ",
            " alter ",
            " drop ",
            " truncate ",
        ]
        if any(token in normalized for token in disallowed):
            return False, "Mutation statements are not allowed"
        return True, None

    async def get_metadata(self) -> Dict[str, Any]:
        """
        Return basic metadata about the current connection.
        """
        if self.client is None:
            return {"status": "disconnected"}
        return {
            "status": "connected",
            "database_type": "bigquery",
            "project": self.project,
            "dataset": self.dataset,
        }

    def transform_sql(self, sql: str, dialect: str = None) -> str:
        """
        SQL transformation is not required; return the original statement.
        """
        return sql

    async def check_view_exists(self, view_name: str) -> bool:
        """
        Check whether a view exists in INFORMATION_SCHEMA.VIEWS.
        """
        if self.client is None or not self.dataset or not self.project:
            return False
        sql = (
            f"SELECT COUNT(*) AS cnt FROM `{self.project}.{self.dataset}.INFORMATION_SCHEMA.VIEWS` "
            f"WHERE table_name = @view_name"
        )
        df = await self.execute_query(sql, parameters={"view_name": view_name})
        return bool(not df.empty and df.iloc[0].get("cnt", 0))

    async def create_fallback_views(
        self,
        view_names: List[str],
        transaction_id: Optional[str] = None,
    ) -> Dict[str, bool]:
        """
        Fallback view creation is not supported for BigQuery.
        """
        self.logger.warning("BigQueryManager.create_fallback_views is not supported")
        return {name: False for name in view_names}

    async def upsert_record(
        self,
        table: str,
        record: Dict[str, Any],
        key_fields: List[str],
        transaction_id: Optional[str] = None,
    ) -> bool:
        """
        Upsert is not supported for BigQuery in this manager implementation.
        """
        self.logger.warning("BigQueryManager.upsert_record is not supported")
        return False

    async def get_record(
        self,
        table: str,
        key_field: str,
        key_value: Any,
        transaction_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve a single record by its key.
        """
        if self.client is None or not self.dataset or not self.project:
            return None

        sql = f"SELECT * FROM `{self.project}.{self.dataset}.{table}` WHERE {key_field} = @key_value LIMIT 1"
        df = await self.execute_query(
            sql,
            parameters={"key_value": key_value},
            transaction_id=transaction_id,
        )
        
        if not df.empty:
            return df.iloc[0].to_dict()
        return None

    async def delete_record(
        self,
        table: str,
        key_field: str,
        key_value: Any,
        transaction_id: Optional[str] = None,
    ) -> bool:
        """
        Delete is not supported for BigQuery in this manager implementation.
        """
        self.logger.warning("BigQueryManager.delete_record is not supported")
        return False

    async def fetch_records(
        self,
        table: str,
        filters: Optional[Dict[str, Any]] = None,
        transaction_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Fetch multiple records from a table, optionally filtered.
        """
        if self.client is None or not self.dataset or not self.project:
            return []

        sql = f"SELECT * FROM `{self.project}.{self.dataset}.{table}`"
        params = {}
        
        if filters:
            conditions = []
            for col, val in filters.items():
                param_name = f"filter_{col}"
                conditions.append(f"{col} = @{param_name}")
                params[param_name] = val
            
            if conditions:
                sql += " WHERE " + " AND ".join(conditions)
        
        df = await self.execute_query(
            sql,
            parameters=params,
            transaction_id=transaction_id,
        )
        
        return df.to_dict(orient="records") if not df.empty else []
