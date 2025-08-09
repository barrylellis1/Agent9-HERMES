"""
Adapter module to bridge the gap between registry references and agent models.
This provides compatibility with existing registry files that import this module.
"""

from typing import Dict, List, Optional, Any


class A9PrincipalContextProfile:
    """
    Principal profile model used by the registry.
    This adapter class mimics the structure expected by the registry references.
    """
    
    def __init__(
        self,
        user_id: str,
        first_name: str,
        last_name: str,
        role: str,
        department: str,
        responsibilities: List[str],
        business_processes: List[str],
        default_filters: Dict[str, Any],
        typical_timeframes: List[str],
        principal_groups: List[str],
        persona_profile: Dict[str, Any],
        preferences: Dict[str, str],
        permissions: List[str],
        source: str,
        description: str
    ):
        self.user_id = user_id
        self.first_name = first_name
        self.last_name = last_name
        self.role = role
        self.department = department
        self.responsibilities = responsibilities
        self.business_processes = business_processes
        self.default_filters = default_filters
        self.typical_timeframes = typical_timeframes
        self.principal_groups = principal_groups
        self.persona_profile = persona_profile
        self.preferences = preferences
        self.permissions = permissions
        self.source = source
        self.description = description
