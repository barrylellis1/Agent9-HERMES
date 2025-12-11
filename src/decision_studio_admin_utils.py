"""Utility functions supporting Decision Studio administrative workflows."""

from __future__ import annotations

import json
import uuid
from typing import Any, Dict, Iterable, List, Optional

from src.agents.models.data_product_onboarding_models import (
    DataProductOnboardingWorkflowRequest,
)


def _parse_csv(value: Optional[str]) -> List[str]:
    """Parse a comma or newline separated string into a list of trimmed values."""
    if not value:
        return []
    items: Iterable[str]
    if isinstance(value, str):
        separators = ",\n"
        for sep in separators:
            value = value.replace(sep, ",")
        items = value.split(",")
    else:
        return []
    return [item.strip() for item in items if item.strip()]


def _parse_json_dict(value: Optional[str]) -> Dict[str, Any]:
    """Parse a JSON string into a dictionary, returning an empty dict on failure."""
    if value is None:
        return {}
    text = str(value).strip()
    if not text:
        return {}
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def build_onboarding_workflow_request(form_data: Dict[str, Any]) -> DataProductOnboardingWorkflowRequest:
    """Construct a workflow request model from raw admin form inputs."""

    request_id = form_data.get("request_id") or str(uuid.uuid4())

    tables = form_data.get("tables")
    if isinstance(tables, list):
        table_list = [str(table).strip() for table in tables if str(table).strip()]
    else:
        table_list = _parse_csv(tables)

    candidate_owner_ids = form_data.get("candidate_owner_ids")
    fallback_roles = form_data.get("fallback_roles")
    business_process_context = form_data.get("business_process_context")
    qa_checks = form_data.get("qa_checks")

    tags = form_data.get("data_product_tags")
    if isinstance(tags, list):
        tag_list = [str(tag).strip() for tag in tags if str(tag).strip()]
    else:
        tag_list = _parse_csv(tags)

    connection_overrides = form_data.get("connection_overrides")
    if isinstance(connection_overrides, dict):
        connection_overrides_dict = connection_overrides
    else:
        connection_overrides_dict = _parse_json_dict(connection_overrides)

    contract_overrides = form_data.get("contract_overrides")
    additional_metadata = form_data.get("additional_metadata")
    owner_metadata = form_data.get("owner_metadata")
    qa_additional_context = form_data.get("qa_additional_context")

    request = DataProductOnboardingWorkflowRequest(
        request_id=request_id,
        principal_id=form_data.get("principal_id", "admin_console"),
        data_product_id=form_data["data_product_id"],
        source_system=form_data.get("source_system", "duckdb"),
        database=form_data.get("database") or None,
        schema=form_data.get("schema") or None,
        tables=table_list or None,
        inspection_depth=form_data.get("inspection_depth", "standard"),
        include_samples=bool(form_data.get("include_samples", False)),
        environment=form_data.get("environment", "dev"),
        connection_overrides=connection_overrides_dict or None,
        contract_output_path=form_data.get("contract_output_path") or None,
        data_product_name=form_data.get("data_product_name") or None,
        data_product_domain=form_data.get("data_product_domain") or None,
        data_product_description=form_data.get("data_product_description") or None,
        data_product_tags=tag_list,
        contract_overrides=_parse_json_dict(contract_overrides),
        additional_metadata=_parse_json_dict(additional_metadata),
        owner_metadata=_parse_json_dict(owner_metadata),
        kpi_entries=form_data.get("kpi_entries") or [],
        overwrite_existing_kpis=bool(form_data.get("overwrite_existing_kpis", False)),
        business_process_mappings=form_data.get("business_process_mappings") or [],
        overwrite_existing_mappings=bool(form_data.get("overwrite_existing_mappings", False)),
        candidate_owner_ids=_parse_csv(candidate_owner_ids),
        fallback_roles=_parse_csv(fallback_roles),
        business_process_context=_parse_csv(business_process_context),
        qa_enabled=bool(form_data.get("qa_enabled", False)),
        qa_checks=_parse_csv(qa_checks),
        qa_additional_context=_parse_json_dict(qa_additional_context),
    )

    return request
