"""Pydantic models for the KPI Accountability registry table.

Each row maps one principal to one KPI (optionally scoped to a dimension/value)
with a role of 'accountable' or 'responsible'.

The unique constraint (client_id, kpi_id, scope_dimension, scope_value) is enforced
at the database level: only one principal can be *accountable* for a given KPI scope.
Use role='responsible' for secondary owners who can co-exist in the same scope.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional
from datetime import datetime

from pydantic import BaseModel


class AccountabilityRole(str, Enum):
    ACCOUNTABLE = "accountable"
    RESPONSIBLE = "responsible"


class KPIAccountability(BaseModel):
    id: str
    client_id: str
    kpi_id: str
    principal_id: str
    scope_dimension: Optional[str] = None
    scope_value: Optional[str] = None
    role: AccountabilityRole = AccountabilityRole.ACCOUNTABLE
    notes: Optional[str] = None
    created_by: str = "system"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
