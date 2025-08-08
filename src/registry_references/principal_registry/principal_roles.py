"""
Principal roles for A9 agents
"""

from enum import Enum

class PrincipalRole(Enum):
    """Enum for principal roles"""
    EMPLOYEE = "employee"
    MANAGER = "manager"
    EXECUTIVE = "executive"
    DATA_OWNER = "data_owner"
    DATA_STEWARD = "data_steward"
    DATA_CUSTODIAN = "data_custodian"
    CFO = "cfo"
    CEO = "ceo"
    COO = "coo"
    CHRO = "chro"
    CMO = "cmo"
    CIO = "cio"
    CDO = "cdo"
