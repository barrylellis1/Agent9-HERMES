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
    CFO = "cfo_001"  # Updated to match registry ID with suffix
    CEO = "ceo_001"  # Updated to match registry ID with suffix
    COO = "coo_001"  # Updated to match registry ID with suffix
    CHRO = "chro"
    CMO = "cmo"
    CIO = "cio"
    FINANCE_MANAGER = "finance_manager"  # Added to match registry ID
    CDO = "cdo"
