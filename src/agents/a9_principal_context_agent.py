"""
Principal Context Agent

This agent manages principal context and relationships in business operations.
It handles registration, retrieval, and management of principal profiles as well
as mapping principals to business processes and KPIs.
"""

import asyncio
import datetime
import logging
import os
import uuid
import yaml
from typing import Dict, List, Any, Optional, Union

from pydantic import BaseModel

from src.registry.factory import RegistryFactory
from src.registry.providers.principal_provider import PrincipalProfileProvider
from src.agents.agent_provider_connector import AgentProviderConnector
from src.registry.bootstrap import RegistryBootstrap
from src.agents.models.principal_context_models import (
    PrincipalProfileRequest, PrincipalProfileResponse,
    SetPrincipalContextRequest, SetPrincipalContextResponse,
    ExtractFiltersRequest, ExtractFiltersResponse, ExtractedFilter
)
from src.agents.models.situation_awareness_models import (
    PrincipalRole, BusinessProcess, TimeFrame, PrincipalContext
)

logger = logging.getLogger(__name__)


class A9_Principal_Context_Agent:
    """
    Principal Context Agent responsible for managing principal profiles and context.
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the Principal Context Agent.
        
        Args:
            config: Configuration dictionary.
        """
        self.config = config or {}
        self.principal_profiles = {}  # Dictionary of principal profiles keyed by role (lowercase)
        self.principal_profiles_by_id = {}  # Dictionary of principal profiles keyed by ID
        self.role_to_id_map = {}  # Mapping from role name to principal ID
        self._setup_logging()
        self._registry_factory = None
        self._principal_provider = None
        self._provider_connector = None
        
    @classmethod
    async def create(cls, config: Dict[str, Any] = None) -> 'A9_Principal_Context_Agent':
        """
        Create a new instance of the Principal Context Agent.
        
        Args:
            config: Configuration dictionary.
            
        Returns:
            Initialized Principal Context Agent instance.
        """
        agent = cls(config)
        await agent.connect()
        return agent

    def _setup_logging(self):
        """Set up logging for the agent."""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Set up structured logging format
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            
        self.logger.info(f"Initializing {self.__class__.__name__}")
        
    def _log_error(self, method_name: str, error: Exception, context: Dict[str, Any] = None) -> str:
        """Log an error with context and return an error ID."""
        error_id = str(uuid.uuid4())[:8]
        error_msg = f"Error in {method_name}: {str(error)} (ID: {error_id})"
        error_context = {
            "error_id": error_id,
            "method": method_name,
            "error_type": type(error).__name__,
            "error_message": str(error),
            **context
        } if context else {
            "error_id": error_id,
            "method": method_name,
            "error_type": type(error).__name__,
            "error_message": str(error)
        }
        
        self.logger.error(error_msg, extra=error_context)
        return error_id
        
    def _get_profile_by_id(self, principal_id: str) -> Optional[Dict[str, Any]]:
        """Get principal profile by ID.
        
        Args:
            principal_id: The unique principal ID to look up
            
        Returns:
            The principal profile dict or None if not found
        """
        if not principal_id:
            return None
            
        # Direct lookup by ID (case-sensitive)
        if principal_id in self.principal_profiles_by_id:
            return self.principal_profiles_by_id[principal_id]
                
        return None
        
    def _get_profile_case_insensitive(self, role: Union[str, PrincipalRole]) -> Optional[Dict[str, Any]]:
        """Get a principal profile with case-insensitive lookup.
        
        Args:
            role: Role name or PrincipalRole enum
            
        Returns:
            Profile dictionary or None if not found
        """
        if not role:
            return None
            
        # Convert role to string if it's an enum
        role_name = str(role) if isinstance(role, PrincipalRole) else str(role)
            
        # Try different formats of the role name
        formats_to_try = [
            role_name,  # Original format
            role_name.lower(),  # lowercase
            role_name.upper(),  # UPPERCASE
            role_name.replace(' ', '_').upper(),  # UPPERCASE_WITH_UNDERSCORES
            ' '.join(word.capitalize() for word in role_name.replace('_', ' ').split()),  # Title Case With Spaces
            ''.join(word.capitalize() for word in role_name.replace('_', ' ').split()),  # TitleCaseNoSpaces
        ]
        
        # Try each format
        for fmt in formats_to_try:
            if fmt in self.principal_profiles:
                return self.principal_profiles[fmt]
                
        # Try partial matches as last resort
        role_lower = role_name.lower()
        for key, profile in self.principal_profiles.items():
            if role_lower in key.lower() or key.lower() in role_lower:
                return profile
                
        return None
        
    async def connect(self):
        """
        Connect to dependencies and initialize required resources.
        """
        try:
            # Initialize registry factory
            self._registry_factory = RegistryFactory()
            
            # Set up provider connector for robust provider access
            self._provider_connector = AgentProviderConnector(self._registry_factory)
            
            # Ensure registry providers are initialized using the bootstrap
            base_path = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
            config = {
                "base_path": base_path,
                "registry_path": os.path.join(base_path, "registry")
            }
            await RegistryBootstrap.initialize(config)
            
            # Get principal provider through connector
            self._principal_provider = self._provider_connector.get_provider('principal_profile')
            if not self._principal_provider:
                self.logger.warning("Principal profile provider not available, attempting to create")
                # Try to ensure provider exists with config
                principal_path = os.path.join(base_path, "registry", "principal", "principal_registry.yaml")
                self._principal_provider = await self._provider_connector.ensure_provider(
                    'principal_profile',
                    {"source_path": principal_path, "storage_format": "yaml"}
                )
                
            # Load all principal profiles
            await self._load_principal_profiles()
            
            self.logger.info("Connected to dependencies")
        except Exception as e:
            error_id = self._log_error("connect", e, {"config": self.config})
            # Always initialize default profiles as a fallback
            self._load_default_profiles()
            self.logger.warning(f"Using default profiles due to connection error {error_id}")
    
    async def disconnect(self):
        """
        Disconnect from dependencies and clean up resources.
        """
        self.logger.info("Disconnected from dependencies")
    
    async def _load_principal_profiles(self):
        """Load principal profiles from registry."""
        try:
            # Try to get principal profiles from registry
            if not self._principal_provider:
                self.logger.warning("Principal profile provider not initialized")
                self._load_default_profiles()
                return
                
            # Get all profiles from the provider
            registry_data = self._principal_provider.get_all()
            self.logger.info(f"Loaded {len(registry_data) if registry_data else 0} principal profiles from registry")
            
            # Debug the registry data
            if not registry_data:
                self.logger.warning("No principal profiles found in registry")
                self._load_default_profiles()
                return
                
            if not isinstance(registry_data, list):
                self.logger.warning(f"Registry data is not a list: {type(registry_data)}")
                self._load_default_profiles()
                return
                
            # Debug: Log all profiles to see their structure
            for i, profile in enumerate(registry_data):
                self.logger.info(f"Profile {i}: id={getattr(profile, 'id', 'unknown')}, "
                                f"role={getattr(profile, 'role', 'unknown')}, "
                                f"title={getattr(profile, 'title', 'unknown')}, "
                                f"name={getattr(profile, 'name', 'unknown')}")
            
            # Convert to our internal dictionary format keyed by ID and role
            normalized_by_role = {}
            normalized_by_id = {}
            role_to_id = {}
            
            for principal in registry_data:
                # Use attribute access for Pydantic models instead of dictionary-style access
                principal_id = getattr(principal, 'id', None)
                role = getattr(principal, 'role', None)
                title = getattr(principal, 'title', None)
                
                self.logger.info(f"Processing principal: id={principal_id}, role={role}, title={title}")
                
                if not principal_id:
                    self.logger.warning(f"Principal missing ID: {getattr(principal, 'name', 'Unknown')} - {role or title}")
                    continue
                    
                # Create profile object
                profile = {
                    "id": principal_id,
                    "role": role or title,  # Use title as role if role is not available
                    "name": getattr(principal, 'name', None),
                    "title": title,
                    "business_processes": getattr(principal, 'business_processes', []),
                    "default_filters": getattr(principal, 'default_filters', {}),
                    "decision_style": getattr(getattr(principal, 'persona_profile', {}), 'decision_style', 'Analytical'),
                    "communication_style": getattr(getattr(principal, 'persona_profile', {}), 'communication_style', 'Concise'),
                    "description": getattr(principal, 'description', ''),
                    "timeframes": getattr(principal, 'typical_timeframes', [])
                }
                
                # Store by ID (primary index)
                normalized_by_id[principal_id] = profile
                self.logger.info(f"Added profile by ID: {principal_id}")
                
                # Store by role (secondary index for backward compatibility)
                if role:
                    # Store using exact role name
                    normalized_by_role[role] = profile
                    role_to_id[role] = principal_id
                    self.logger.info(f"Added profile by role (exact): {role}")
                    
                    # Also store using lowercase role name
                    role_lower = role.lower()
                    normalized_by_role[role_lower] = profile
                    role_to_id[role_lower] = principal_id
                    self.logger.info(f"Added profile by role (lowercase): {role_lower}")
                
                # Also store by title for additional lookup options
                if title:
                    # Store using exact title
                    normalized_by_role[title] = profile
                    role_to_id[title] = principal_id
                    self.logger.info(f"Added profile by title (exact): {title}")
                    
                    # Also store using lowercase title
                    title_lower = title.lower()
                    normalized_by_role[title_lower] = profile
                    role_to_id[title_lower] = principal_id
                    self.logger.info(f"Added profile by title (lowercase): {title_lower}")
            
            if normalized_by_id:
                self.principal_profiles = normalized_by_role
                self.principal_profiles_by_id = normalized_by_id
                self.role_to_id_map = role_to_id
                self.logger.info(f"Loaded {len(self.principal_profiles_by_id)} principal profiles by ID from registry")
                self.logger.info(f"Loaded {len(self.principal_profiles)} principal profiles by role from registry")
                self.logger.info(f"Available profile IDs: {list(self.principal_profiles_by_id.keys())}")
                self.logger.info(f"Available role keys: {list(self.principal_profiles.keys())}")
                return
            
            # Fallback to default profiles if no valid profiles were loaded
            self.logger.warning("No valid profiles found in registry, using defaults")
            self._load_default_profiles()
        except Exception as e:
            error_id = self._log_error("_load_principal_profiles", e)
            self._load_default_profiles()
            self.logger.warning(f"Using default profiles due to loading error {error_id}")
    
    def _load_default_profiles(self):
        """Load default principal profiles when registry is unavailable."""
        from src.agents.models.situation_awareness_models import PrincipalRole, BusinessProcess
        import yaml
        import os
        
        # Clear existing profiles
        self.principal_profiles = {}
        self.principal_profiles_by_id = {}
        self.role_to_id_map = {}
        
        # Try to load from the existing registry file
        registry_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                    "registry", "principal", "principal_registry.yaml")
        
        try:
            if os.path.exists(registry_path):
                with open(registry_path, 'r') as f:
                    registry_data = yaml.safe_load(f)
                
                # Convert registry format to our internal format
                principals = registry_data.get('principals', [])
                
                if principals:
                    self.logger.info(f"Found {len(principals)} principals in registry file")
                    
                    for principal in principals:
                        principal_id = principal.get('id')
                        role = principal.get('role')
                        title = principal.get('title')
                        
                        if not principal_id:
                            self.logger.warning(f"Principal missing ID in registry file: {principal.get('name')} - {role}")
                            continue
                            
                        # Create profile object
                        profile = {
                            "id": principal_id,
                            "role": role,
                            "name": principal.get('name'),
                            "title": title,
                            "business_processes": principal.get('business_processes', []),
                            "default_filters": principal.get('default_filters', {}),
                            "decision_style": principal.get('persona_profile', {}).get('decision_style', 'Analytical'),
                            "communication_style": principal.get('persona_profile', {}).get('communication_style', 'Concise'),
                            "description": principal.get('description', ''),
                            "timeframes": principal.get('typical_timeframes', [])
                        }
                        
                        # Store by ID (primary index)
                        self.principal_profiles_by_id[principal_id] = profile
                        
                        # Store by role with multiple formats for robust lookup
                        if role:
                            # Original role name
                            self.principal_profiles[role] = profile
                            self.role_to_id_map[role] = principal_id
                            
                            # Lowercase role name
                            role_lower = role.lower()
                            self.principal_profiles[role_lower] = profile
                            self.role_to_id_map[role_lower] = principal_id
                            
                            # Role name with underscores
                            role_with_underscores = role.replace(' ', '_')
                            self.principal_profiles[role_with_underscores] = profile
                            self.role_to_id_map[role_with_underscores] = principal_id
                            
                            # Uppercase role name with underscores (enum format)
                            role_enum_format = role.replace(' ', '_').upper()
                            self.principal_profiles[role_enum_format] = profile
                            self.role_to_id_map[role_enum_format] = principal_id
                        
                        # Also store by title for additional lookup options
                        if title:
                            # Original title
                            self.principal_profiles[title] = profile
                            self.role_to_id_map[title] = principal_id
                            
                            # Lowercase title
                            title_lower = title.lower()
                            self.principal_profiles[title_lower] = profile
                            self.role_to_id_map[title_lower] = principal_id
                    
                    self.logger.info(f"Loaded {len(self.principal_profiles_by_id)} principal profiles from registry file")
                    return
        except Exception as e:
            self.logger.warning(f"Error loading profiles from registry file: {str(e)}")
        
        # If we get here, either the registry file doesn't exist, is empty, or had an error
        # Create default hardcoded profiles
        self.logger.info("Creating default hardcoded principal profiles")
        
        # Create default profiles
        default_profiles = {
            "CFO": {
                "id": "cfo_001",
                "role": "CFO",
                "name": "Default CFO",
                "title": "Chief Financial Officer",
                "business_processes": [
                    "Finance: Profitability Analysis",
                    "Finance: Revenue Growth Analysis",
                    "Finance: Expense Management",
                    "Finance: Cash Flow Management",
                    "Finance: Budget vs. Actuals"
                ],
                "default_filters": {
                    "profit_center_hierarchyid": ["Total"]
                },
                "decision_style": "Analytical",
                "communication_style": "Concise",
                "description": "Chief Financial Officer responsible for financial performance",
                "timeframes": ["Monthly", "Quarterly", "Annual"]
            },
            "CEO": {
                "id": "ceo_001",
                "role": "CEO",
                "name": "Default CEO",
                "title": "Chief Executive Officer",
                "business_processes": [
                    "Executive: Strategic Planning",
                    "Executive: Performance Management",
                    "Executive: Risk Management"
                ],
                "default_filters": {
                    "profit_center_hierarchyid": ["Total"]
                },
                "decision_style": "Decisive",
                "communication_style": "Concise",
                "description": "Chief Executive Officer responsible for overall company performance",
                "timeframes": ["Quarterly", "Annual", "YTD"]
            },
            "COO": {
                "id": "coo_001",
                "role": "COO",
                "name": "Default COO",
                "title": "Chief Operating Officer",
                "business_processes": [
                    "Operations: Supply Chain Management",
                    "Operations: Production Efficiency",
                    "Operations: Quality Control"
                ],
                "default_filters": {
                    "profit_center_hierarchyid": ["Total"]
                },
                "decision_style": "Analytical",
                "communication_style": "Detailed",
                "description": "Chief Operating Officer responsible for operations and supply chain",
                "timeframes": ["Monthly", "Quarterly"]
            },
            "Finance Manager": {
                "id": "finance_mgr_001",
                "role": "Finance Manager",
                "name": "Default Finance Manager",
                "title": "Finance Manager",
                "business_processes": [
                    "Finance: Budget Planning",
                    "Finance: Financial Reporting",
                    "Finance: Cost Analysis"
                ],
                "default_filters": {
                    "profit_center_hierarchyid": ["Total"]
                },
                "decision_style": "Analytical",
                "communication_style": "Detailed",
                "description": "Finance Manager responsible for financial reporting and analysis",
                "timeframes": ["Monthly", "Quarterly"]
            }
        }
        
        # Add default profiles to dictionaries with multiple lookup keys
        for role, profile in default_profiles.items():
            # Store by ID (primary index)
            self.principal_profiles_by_id[profile["id"]] = profile
            
            # Store by role name (multiple formats for robust lookup)
            # Original role name
            self.principal_profiles[role] = profile
            self.role_to_id_map[role] = profile["id"]
            
            # Lowercase role name
            role_lower = role.lower()
            self.principal_profiles[role_lower] = profile
            self.role_to_id_map[role_lower] = profile["id"]
            
            # Role name with underscores
            role_with_underscores = role.replace(' ', '_')
            self.principal_profiles[role_with_underscores] = profile
            self.role_to_id_map[role_with_underscores] = profile["id"]
            
            # Uppercase role name with underscores (enum format)
            role_enum_format = role.replace(' ', '_').upper()
            self.principal_profiles[role_enum_format] = profile
            self.role_to_id_map[role_enum_format] = profile["id"]
            
            # Also store by title if available
            if "title" in profile and profile["title"]:
                title = profile["title"]
                title_lower = title.lower()
                
                self.principal_profiles[title] = profile
                self.role_to_id_map[title] = profile["id"]
                
                self.principal_profiles[title_lower] = profile
                self.role_to_id_map[title_lower] = profile["id"]
        
        self.logger.info(f"Loaded {len(default_profiles)} default principal profiles")
        self.logger.info(f"Available profile IDs: {list(self.principal_profiles_by_id.keys())}")
        self.logger.info(f"Available role keys: {list(self.principal_profiles.keys())}")
        self.logger.info("Default profiles loaded successfully")
        self.logger.info(f"Loaded {len(self.principal_profiles_by_id)} hardcoded default principal profiles")
    
    async def set_principal_context(self, request: Union[SetPrincipalContextRequest, Dict[str, Any]]) -> SetPrincipalContextResponse:
        """
        Set principal context.
        
        Args:
            request: SetPrincipalContextRequest or dict with principal_id and optional context_data
            
        Returns:
            SetPrincipalContextResponse with updated profile and extracted responsibilities/filters
        """
        try:
            # Convert dict to Pydantic model if needed
            if isinstance(request, dict):
                principal_id = request.get('principal_id')
                context_data = request.get('context_data')
                request_id = request.get('request_id', str(uuid.uuid4()))
                request = SetPrincipalContextRequest(
                    request_id=request_id,
                    principal_id=principal_id,
                    context_data=context_data
                )
            
            # Get principal profile
            profile = await self.fetch_principal_profile(request.principal_id)
            if not profile:
                self.logger.warning(f"Principal profile not found: {request.principal_id}")
                return SetPrincipalContextResponse(
                    request_id=request.request_id,
                    status="error",
                    message=f"Principal profile not found: {request.principal_id}",
                    profile={},
                    responsibilities=[],
                    filters={}
                )
                
            # Merge with context data
            if request.context_data:
                # Update profile with context data
                # This would be expanded in a full implementation
                pass
            
            # Extract responsibilities from business processes
            responsibilities = []
            if "business_processes" in profile:
                for bp in profile["business_processes"]:
                    # Convert business process to responsibility description
                    if isinstance(bp, str) and bp.startswith("Finance:"):
                        responsibilities.append(bp.replace("Finance: ", ""))
            
            # Extract filters
            filters = profile.get("default_filters", {})
                
            return SetPrincipalContextResponse(
                request_id=request.request_id,
                status="success",
                message=f"Principal context set for {request.principal_id}",
                profile=profile,
                responsibilities=responsibilities,
                filters=filters
            )
        except Exception as e:
            error_id = self._log_error("set_principal_context", e, {
                "request_id": getattr(request, 'request_id', None),
                "principal_id": getattr(request, 'principal_id', None) if not isinstance(request, dict) else request.get('principal_id')
            })
            return SetPrincipalContextResponse(
                request_id=getattr(request, 'request_id', str(uuid.uuid4())),
                status="error",
                message=f"Error setting principal context: {str(e)} (error ID: {error_id})",
                profile={},
                responsibilities=[],
                filters={}
            )
    
    async def fetch_principal_profile(self, principal_id: str) -> Dict[str, Any]:
        """
        Fetch principal profile.
        
        Args:
            principal_id: Identifier of the principal.
            
        Returns:
            Principal profile information.
        """
        try:
            if not self._principal_provider:
                self.logger.warning("Principal profile provider not initialized")
                return {}
                
            # Convert principal_id to lowercase for case-insensitive matching
            principal_id_lower = principal_id.lower() if isinstance(principal_id, str) else str(principal_id).lower()
            
            # First try to find by exact ID in the principal_profiles_by_id dictionary
            if principal_id in self.principal_profiles_by_id:
                profile = self.principal_profiles_by_id[principal_id]
                return self._format_profile_response(profile, principal_id)
            
            # Try case-insensitive ID lookup
            for pid, profile in self.principal_profiles_by_id.items():
                if str(pid).lower() == principal_id_lower:
                    return self._format_profile_response(profile, principal_id)
            
            # Try by role in principal_profiles (backward compatibility)
            if principal_id_lower in self.principal_profiles:
                profile = self.principal_profiles[principal_id_lower]
                return self._format_profile_response(profile, principal_id)
            
            # Try by role with different case variations
            profile = self._get_profile_case_insensitive(principal_id)
            if profile:
                return self._format_profile_response(profile, principal_id)
            
            # Log the failure and return empty dict
            self.logger.warning(f"Principal profile not found: {principal_id} (tried ID: {principal_id})")
            return {}
        except Exception as e:
            error_id = self._log_error("fetch_principal_profile", e, {"principal_id": principal_id})
            self.logger.warning(f"Failed to fetch principal profile for {principal_id} (error {error_id})")
            return {}
    
    def _get_profile_case_insensitive(self, role_name: str) -> Dict[str, Any]:
        """
        Try to find a profile using different case variations of the role name.
        
        Args:
            role_name: The role name to look up (e.g., 'CFO', 'cfo', 'Chief Financial Officer')
            
        Returns:
            The profile dictionary if found, otherwise an empty dictionary
        """
        if not role_name:
            self.logger.warning("Empty role name provided to _get_profile_case_insensitive")
            return {}
        
        self.logger.info(f"Looking up profile with case-insensitive search for: '{role_name}'")
        self.logger.debug(f"Available profile keys: {list(self.principal_profiles.keys())}")
            
        # Try different case variations
        variations = [
            role_name,  # Original
            role_name.lower(),  # lowercase
            role_name.upper(),  # UPPERCASE
            role_name.upper().replace(' ', '_'),  # UPPERCASE_WITH_UNDERSCORES
            ' '.join(word.capitalize() for word in role_name.replace('_', ' ').split()),  # Title Case With Spaces
            '_'.join(word.lower() for word in role_name.replace(' ', '_').split('_')),  # snake_case
        ]
        
        # Add common role name variations
        if role_name.lower() in ['cfo', 'chief financial officer']:
            variations.extend(['cfo', 'CFO', 'Chief Financial Officer'])
        elif role_name.lower() in ['ceo', 'chief executive officer']:
            variations.extend(['ceo', 'CEO', 'Chief Executive Officer'])
        elif role_name.lower() in ['coo', 'chief operating officer']:
            variations.extend(['coo', 'COO', 'Chief Operating Officer'])
        elif role_name.lower() in ['finance manager', 'finance_manager']:
            variations.extend(['finance manager', 'Finance Manager', 'FINANCE_MANAGER'])
        
        # Remove duplicates while preserving order
        variations = list(dict.fromkeys(variations))
        
        self.logger.debug(f"Trying variations: {variations}")
        
        # First try direct dictionary lookup
        for variation in variations:
            if variation in self.principal_profiles:
                self.logger.info(f"Found profile with key: '{variation}'")
                return self.principal_profiles[variation]
        
        # Then try matching by title or role attribute
        for profile in self.principal_profiles.values():
            profile_role = profile.get("role", "")
            profile_title = profile.get("title", "")
            
            for variation in variations:
                # Check both role and title
                if (profile_role and str(profile_role).lower() == variation.lower()) or \
                   (profile_title and str(profile_title).lower() == variation.lower()):
                    self.logger.info(f"Found profile by attribute match: '{profile.get('id', 'unknown')}' with role/title: '{profile_role or profile_title}'")
                    return profile
        
        # If we get here, we couldn't find a match
        self.logger.warning(f"Principal profile not found for any variation of: '{role_name}'")
        self.logger.debug(f"Available profiles: {[p.get('role', 'unknown') for p in self.principal_profiles.values()]}")
        return {}
        
    def _format_profile_response(self, profile: Dict[str, Any], principal_id: str) -> Dict[str, Any]:
        """
        Format the profile response consistently.
        """
        return {
            "name": profile.get("name", principal_id),
            "title": profile.get("title", ""),
            "business_processes": profile.get("business_processes", []),
            "default_filters": profile.get("default_filters", {}),
            "decision_style": profile.get("decision_style", "Analytical"),
            "communication_style": profile.get("communication_style", "Concise"),
            "timeframes": profile.get("timeframes", ["Monthly", "Quarterly"]),
            "description": profile.get("description", "")
        }
    
    async def get_context_recommendations(self) -> List[Dict[str, Any]]:
        """
        Get context-based recommendations.
        
        Returns:
            List of recommendations.
        """
        # This would be implemented in a full version
        return []
    
    async def get_context_history(self) -> List[Dict[str, Any]]:
        """
        Get context history.
        
        Returns:
            List of context history items.
        """
        # This would be implemented in a full version
        return []
    
    async def clear_context(self) -> None:
        """
        Clear current context.
        """
        # This would be implemented in a full version
        pass
        
    async def extract_filters(self, request: Union[ExtractFiltersRequest, Dict[str, Any], str]) -> ExtractFiltersResponse:
        """
        Extract dimensional filters from job description or responsibility text.
        
        Args:
            request: ExtractFiltersRequest, dict with description, or string with description text
            
        Returns:
            ExtractFiltersResponse with extracted filters
        """
        try:
            # Handle different input types
            if isinstance(request, str):
                description = request
                request_id = str(uuid.uuid4())
            elif isinstance(request, dict):
                # Try job_description first, fall back to description
                description = request.get('job_description', request.get('description', ''))
                request_id = request.get('request_id', str(uuid.uuid4()))
            else:
                # Try job_description first, fall back to description
                description = getattr(request, 'job_description', None)
                if description is None:
                    description = getattr(request, 'description', '')
                request_id = request.request_id
            
            self.logger.info(f"Extracting filters from description: {description[:50]}...")
            
            # Initialize extracted filters
            extracted_filters = []
            
            # Simple rule-based extraction for common dimensions
            # In a full implementation, this would use NLP or LLM techniques
            
            # Extract region filters
            regions = [
                "Global", "Americas", "EMEA", "APAC", "North America", "Europe", 
                "Asia", "Africa", "Latin America", "Middle East"
            ]
            for region in regions:
                if region.lower() in description.lower():
                    extracted_filters.append(ExtractedFilter(
                        dimension="region",
                        value=region,
                        confidence=0.8,
                        extraction_method="rule_based"
                    ))
            
            # Extract time period filters
            time_periods = [
                "monthly", "quarterly", "annual", "yearly", "YTD", "QTD", "MTD",
                "year-to-date", "quarter-to-date", "month-to-date"
            ]
            for period in time_periods:
                if period.lower() in description.lower():
                    extracted_filters.append(ExtractedFilter(
                        dimension="time_period",
                        value=period,
                        confidence=0.8,
                        extraction_method="rule_based"
                    ))
            
            # Extract business unit filters if mentioned
            business_units = [
                "Sales", "Marketing", "Finance", "HR", "Operations", "IT", 
                "R&D", "Customer Service", "Best Run U"
            ]
            for unit in business_units:
                if unit.lower() in description.lower():
                    extracted_filters.append(ExtractedFilter(
                        dimension="business_unit",
                        value=unit,
                        confidence=0.7,
                        extraction_method="rule_based"
                    ))
            
            # Convert extracted filters to a dictionary format
            filter_dict = {}
            for filter_item in extracted_filters:
                if filter_item.dimension not in filter_dict:
                    filter_dict[filter_item.dimension] = []
                filter_dict[filter_item.dimension].append(filter_item.value)
            
            return ExtractFiltersResponse(
                request_id=request_id,
                status="success",
                message=f"Extracted {len(extracted_filters)} filters from description",
                filters=filter_dict,
                extracted_filters=extracted_filters
            )
        except Exception as e:
            error_id = self._log_error("extract_filters", e, {
                "request_id": request_id if 'request_id' in locals() else None,
                "description_length": len(description) if 'description' in locals() else 0
            })
            return ExtractFiltersResponse(
                request_id=request_id if 'request_id' in locals() else str(uuid.uuid4()),
                status="error",
                message=f"Error extracting filters: {str(e)} (error ID: {error_id})",
                filters={},
                extracted_filters=[]
            )
        
    async def get_principal_context(self, request_data: Union[PrincipalProfileRequest, Dict[str, Any], str]) -> PrincipalProfileResponse:
        """
        Get principal context for a given principal.
        
        Args:
            request_data: PrincipalProfileRequest, dict with principal_role or principal_id, or string with role name or ID
            
        Returns:
            PrincipalProfileResponse: Response with principal context
        """
        # Extract request ID, principal ID, and principal role from request data
        request_id = str(uuid.uuid4())  # Default request ID
        principal_id = None
        principal_role = None
        profile = {}
        
        try:
            # Parse the request data
            if isinstance(request_data, dict):
                # Extract from dictionary
                if 'request_id' in request_data:
                    request_id = request_data['request_id']
                if 'principal_id' in request_data:
                    principal_id = request_data['principal_id']
                elif 'principal_role' in request_data:
                    principal_role = request_data['principal_role']
            elif isinstance(request_data, str):
                # Try to determine if it's an ID or role
                if request_data in self.principal_profiles_by_id:
                    principal_id = request_data
                else:
                    principal_role = request_data
            elif isinstance(request_data, PrincipalRole):
                # Handle PrincipalRole enum directly - convert to string for lookup
                self.logger.info(f"Converting PrincipalRole enum to string for lookup: {request_data}")
                # Use the enum name (e.g., 'CFO', 'CEO') for profile lookup
                principal_role = request_data.name
            
            # Try to get profile by ID first
            if principal_id:
                profile = await self.fetch_principal_profile(principal_id)
                if not profile:
                    self.logger.warning(f"Principal profile not found for ID: {principal_id}")
            
            # If no profile found by ID, try by role
            if not profile and principal_role:
                self.logger.info(f"Looking up profile by role: {principal_role}")
                profile = self._get_profile_case_insensitive(principal_role)
                if profile:
                    self.logger.info(f"Found profile by role: {principal_role}")
                    principal_id = profile.get('id', '')
                else:
                    self.logger.warning(f"Principal profile not found for role: {principal_role}")
                    profile = {}  # Ensure profile is a dictionary even if lookup failed
            
            # If still no profile, use default
            if not profile:
                self.logger.info(f"Using default principal ID: default_id")
                principal_id = "default_id"
                profile = self._get_default_profile()
            
            # Get role string from profile
            role_str = profile.get('role', '')
            if not role_str and profile.get('title'):
                role_str = profile.get('title')
            
            # Map role string to PrincipalRole enum
            try:
                # Try direct mapping if it's already a valid enum value
                enum_role = PrincipalRole(role_str)
                self.logger.info(f"Mapped role directly to enum: {role_str} -> {enum_role}")
            except (ValueError, TypeError):
                # Map common role names to enum values
                role_mapping = {
                    "cfo": PrincipalRole.CFO,
                    "chief financial officer": PrincipalRole.CFO,
                    "finance manager": PrincipalRole.FINANCE_MANAGER,
                    "ceo": PrincipalRole.CEO,
                    "chief executive officer": PrincipalRole.CEO,
                    "coo": PrincipalRole.COO,
                    "chief operating officer": PrincipalRole.COO,
                    "finance director": PrincipalRole.FINANCE_MANAGER,
                }
                
                # Try to map the role string to an enum value
                role_key = role_str.lower() if isinstance(role_str, str) else "cfo"
                enum_role = role_mapping.get(role_key, PrincipalRole.CFO)
                self.logger.info(f"Mapped role '{role_key}' to enum value '{enum_role}'")
            
            # Extract timeframes from profile
            timeframes = []
            for tf in profile.get('timeframes', ['Quarterly']):
                try:
                    timeframes.append(TimeFrame(tf))
                except (ValueError, TypeError):
                    # Map common timeframe strings to enum values
                    tf_mapping = {
                        "quarterly": TimeFrame.CURRENT_QUARTER,
                        "qtd": TimeFrame.CURRENT_QUARTER,
                        "ytd": TimeFrame.YEAR_TO_DATE,
                        "year to date": TimeFrame.YEAR_TO_DATE,
                        "mtd": TimeFrame.CURRENT_MONTH,
                        "month to date": TimeFrame.CURRENT_MONTH,
                    }
                    tf_key = tf.lower() if isinstance(tf, str) else ""
                    if tf_key in tf_mapping:
                        timeframes.append(tf_mapping[tf_key])
            
            # Ensure we have at least one timeframe
            if not timeframes:
                timeframes = [TimeFrame.CURRENT_QUARTER, TimeFrame.YEAR_TO_DATE]
            
            # Ensure we have a principal ID
            if not principal_id:
                principal_id = profile.get('id', f"{enum_role.name.lower()}_default")
                self.logger.info(f"Using principal ID from profile: {principal_id}")
            
            # Map business processes to enum values
            business_processes = []
            bp_mapping = {
                "finance: profitability analysis": BusinessProcess.PROFITABILITY_ANALYSIS,
                "finance: revenue growth analysis": BusinessProcess.REVENUE_GROWTH,
                "finance: expense management": BusinessProcess.EXPENSE_MANAGEMENT,
                "finance: cash flow management": BusinessProcess.CASH_FLOW,
                "finance: budget vs. actuals": BusinessProcess.BUDGET_VS_ACTUALS,
                "finance_expense_management": BusinessProcess.EXPENSE_MANAGEMENT,
                "finance_cash_flow": BusinessProcess.CASH_FLOW,
                "finance_budget_vs_actuals": BusinessProcess.BUDGET_VS_ACTUALS,
                "profitability analysis": BusinessProcess.PROFITABILITY_ANALYSIS,
                "revenue growth analysis": BusinessProcess.REVENUE_GROWTH,
                "expense management": BusinessProcess.EXPENSE_MANAGEMENT,
                "cash flow management": BusinessProcess.CASH_FLOW,
                "budget vs. actuals": BusinessProcess.BUDGET_VS_ACTUALS,
            }
            
            # Process each business process string
            for bp in profile.get('business_processes', []):
                try:
                    # Try direct enum conversion first
                    business_processes.append(BusinessProcess(bp))
                except (ValueError, TypeError):
                    # Try normalized lookup
                    bp_lower = str(bp).lower() if bp else ""
                    if bp_lower in bp_mapping:
                        business_processes.append(bp_mapping[bp_lower])
                    else:
                        self.logger.warning(f"Unknown business process format: {bp}")
            
            # If no valid business processes found, use all enum values
            if not business_processes:
                business_processes = list(BusinessProcess)
            
            # Create principal context object
            principal_context = PrincipalContext(
                role=enum_role,
                principal_id=principal_id,
                business_processes=business_processes,
                default_filters=profile.get('default_filters', {}),
                decision_style=profile.get('decision_style', 'Analytical'),
                communication_style=profile.get('communication_style', 'Concise'),
                preferred_timeframes=timeframes
            )
            
            return PrincipalProfileResponse(
                request_id=request_id,
                status="success",
                message="Principal context retrieved successfully",
                profile=self._format_profile_response(profile, principal_id),
                responsibilities=profile.get('responsibilities', []),
                filters=profile.get('default_filters', {}),
                context=principal_context
            )
            
        except Exception as e:
            error_id = self._log_error("get_principal_context", e, request_data)
            self.logger.error(f"Error in get_principal_context: {str(e)} (ID: {error_id})")
            
            # Return a default response with error status
            default_profile = self._get_default_profile()
            default_context = PrincipalContext(
                role=PrincipalRole.CFO,
                principal_id="cfo_default",
                business_processes=list(BusinessProcess),
                default_filters={},
                decision_style="Analytical",
                communication_style="Concise",
                preferred_timeframes=[TimeFrame.CURRENT_QUARTER, TimeFrame.YEAR_TO_DATE]
            )
            
            return PrincipalProfileResponse(
                request_id=request_id,
                status="error",
                message=f"Error getting principal context: {str(e)} (error ID: {error_id})",
                profile=self._format_profile_response(default_profile, "default_id"),
                responsibilities=[],
                filters={},
                context=default_context
            )
