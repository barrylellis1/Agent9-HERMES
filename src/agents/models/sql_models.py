"""
Shared SQL execution request/response models for Agent9.
These models are used across agents (LLM Service -> DP Agent -> Execution backend).
"""
from typing import Any, Dict, List, Optional
from src.agents.shared.a9_agent_base_model import (
    A9AgentBaseRequest,
    A9AgentBaseResponse,
)


class SQLExecutionRequest(A9AgentBaseRequest):
    """Protocol-compliant request model for SQL execution."""
    sql: str
    context: Optional[Dict[str, Any]] = None
    principal_context: Optional[Dict[str, Any]] = None
    yaml_contract_text: Optional[str] = None


class SQLExecutionResponse(A9AgentBaseResponse):
    """Protocol-compliant response model for SQL execution results."""
    columns: List[str] = []
    rows: List[List[Any]] = []
    row_count: int = 0
    query_time_ms: Optional[float] = None
    human_action_required: bool = False
    human_action_type: Optional[str] = None
    human_action_context: Optional[Dict[str, Any]] = None

    @classmethod
    def from_result(cls, request_id: str, result: Dict[str, Any]) -> "SQLExecutionResponse":
        columns = result.get("columns", [])
        rows = result.get("rows", [])
        return cls.success(
            request_id=request_id,
            message="SQL execution successful",
            columns=columns,
            rows=rows,
            row_count=len(rows),
            query_time_ms=result.get("query_time_ms"),
        )

    @classmethod
    def success(
        cls, request_id: str, message: str = "SQL execution successful", **kwargs
    ) -> "SQLExecutionResponse":
        return cls(status="success", request_id=request_id, message=message, **kwargs)

    @classmethod
    def error(
        cls, request_id: str, error_message: str, **kwargs
    ) -> "SQLExecutionResponse":
        return cls(
            status="error",
            request_id=request_id,
            message=error_message,
            error_message=error_message,
            columns=[],
            rows=[],
            row_count=0,
            **kwargs,
        )
