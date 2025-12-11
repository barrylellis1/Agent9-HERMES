"""
Principal Context Agent

This agent manages principal context and relationships in business operations.
It handles registration, retrieval, and management of principal profiles as well
as mapping principals to business processes and KPIs.
"""

import os
import json
import uuid
import asyncio
import logging
from typing import Dict, List, Any, Optional

from src.registry.factory import RegistryFactory
from src.registry.providers.principal_provider import PrincipalProfileProvider
from src.registry.providers.business_process_provider import BusinessProcessProvider
from src.agents.models.data_product_onboarding_models import (
    PrincipalOwnershipRequest,
    PrincipalOwnershipResponse,
    OwnershipChainEntry,
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
        self.principal_profiles = {}
        self._setup_logging()
        # Use a single canonical attribute name for registry factory
        self.registry_factory = None
        self._principal_provider = None
        
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
        self.logger.info(f"Initializing {self.__class__.__name__}")
    
    async def connect(self, orchestrator=None):
        """
        Connect to dependencies and initialize required resources.
        
        Args:
            orchestrator: Optional orchestrator agent for service discovery
        """
        try:
            # Store orchestrator reference for service discovery
            if orchestrator:
                self.orchestrator = orchestrator
                self.logger.info("Orchestrator reference stored for service discovery")
            
            # Initialize registry factory and providers
            self.registry_factory = RegistryFactory()
            self._principal_provider = None
            self._business_process_provider = None
            
            # Try to get the principal profile provider from the registry factory
            try:
                self._principal_provider = self.registry_factory.get_principal_profile_provider()
                if not self._principal_provider:
                    self.logger.warning("Principal profile provider not found, creating default provider")
                    self._principal_provider = PrincipalProfileProvider()
                    self.registry_factory.register_provider("principal_profile", self._principal_provider)
                    # Explicitly load the provider data
                    await self._principal_provider.load()
                    # Mark as initialized in factory so UI status checks pass
                    if hasattr(self.registry_factory, "_provider_initialization_status"):
                        self.registry_factory._provider_initialization_status["principal_profile"] = True
                else:
                    # If provider exists but not marked initialized, load now
                    init = getattr(self.registry_factory, "_provider_initialization_status", {})
                    if not init.get("principal_profile", False):
                        self.logger.info("Principal profile provider exists but not initialized; loading now")
                        await self._principal_provider.load()
                        if hasattr(self.registry_factory, "_provider_initialization_status"):
                            self.registry_factory._provider_initialization_status["principal_profile"] = True
                # Log how many profiles are available
                try:
                    loaded = self._principal_provider.get_all() or []
                    self.logger.info(f"Principal profile provider ready with {len(loaded)} profiles")
                except Exception:
                    pass
                self.logger.info("Successfully retrieved principal profile provider from registry factory")
            except Exception as e:
                self.logger.warning(f"Failed to get principal profile provider: {str(e)}")
                self.logger.info("Initializing default principal profile provider")
                self._principal_provider = PrincipalProfileProvider()
                # Load default profiles
                await self._principal_provider.load()
                
            # Get the business process provider from the registry factory
            # The factory will create a default provider if none exists
            try:
                self._business_process_provider = self.registry_factory.get_business_process_provider()
                if self._business_process_provider:
                    # Ensure the provider is loaded
                    if not self.registry_factory._provider_initialization_status.get("business_process", False):
                        self.logger.info("Loading business process provider data")
                        await self._business_process_provider.load()
                        self.registry_factory._provider_initialization_status["business_process"] = True
                    self.logger.info("Successfully retrieved business process provider from registry factory")
                else:
                    self.logger.error("Failed to get or create business process provider from registry factory")
            except Exception as e:
                self.logger.error(f"Error initializing business process provider: {str(e)}")
                # No fallback needed as the factory already handles creation
            
            # Load all principal profiles
            await self._load_principal_profiles()
            
            self.logger.info("Connected to dependencies")
        except Exception as e:
            self.logger.error(f"Error connecting to dependencies: {str(e)}")
    
    async def disconnect(self):
        """
        Disconnect from dependencies and clean up resources.
        """
        self.logger.info("Disconnected from dependencies")
    
    async def _load_principal_profiles(self):
        """
        Load principal profiles from the registry.
        """
        try:
            # Check if provider exists
            if not self._principal_provider:
                self.logger.error("Cannot load principal profiles: principal provider is None")
                # Initialize default profiles
                self.principal_profiles = self._get_default_profiles()
                return
                
            # Get all principal profiles
            profiles = self._principal_provider.get_all() or {}
            if not profiles:
                self.logger.warning("No principal profiles found in registry, attempting to load from file")
                # Try to load from file
                try:
                    import yaml
                    import os
                    
                    # Try to load from the standard registry location
                    registry_path = os.path.join("src", "registry", "principal", "principal_registry.yaml")
                    if os.path.exists(registry_path):
                        with open(registry_path, 'r') as file:
                            yaml_data = yaml.safe_load(file)
                            if yaml_data and "principals" in yaml_data and isinstance(yaml_data["principals"], list):
                                # Register profiles with provider
                                for profile in yaml_data["principals"]:
                                    self._principal_provider.register(profile)
                                
                                # Try to get profiles again
                                profiles = self._principal_provider.get_all() or {}
                                if profiles:
                                    self.logger.info(f"Successfully loaded {len(profiles)} profiles from file")
                except Exception as e:
                    self.logger.error(f"Error loading profiles from file: {str(e)}")
                
                # If still no profiles, use defaults
                if not profiles:
                    self.logger.warning("Still no profiles found, using default profiles")
                    self.principal_profiles = self._get_default_profiles()
                    return
            
            # Ensure profiles is in the correct format
            if isinstance(profiles, list):
                self.logger.info(f"Loaded {len(profiles)} principal profiles (list format) from registry")
                self.principal_profiles = profiles
                try:
                    sample = profiles[0] if profiles else None
                    self.logger.debug(f"Sample profile (list): {getattr(sample, 'id', getattr(sample, 'name', str(sample)))})")
                except Exception:
                    pass
            elif isinstance(profiles, dict):
                self.logger.info(f"Loaded {len(profiles)} principal profiles (dict format) from registry")
                self.principal_profiles = profiles
                try:
                    self.logger.debug(f"Profile keys: {list(profiles.keys())[:10]}")
                except Exception:
                    pass
            else:
                self.logger.warning(f"Unexpected principal profiles format: {type(profiles)}")
                self.principal_profiles = {}
        except Exception as e:
            self.logger.error(f"Error loading principal profiles: {str(e)}")
            # Initialize default profiles
            self.principal_profiles = self._get_default_profiles()
            
    def _get_default_profiles(self):
        """
        Get default principal profiles when registry loading fails.
        
        Returns:
            Dict of default principal profiles
        """
        self.logger.info("Using default principal profiles")
        return {
            "CFO": {
                "id": "cfo_001",
                "name": "Chief Financial Officer",
                "role": "CFO",
                "business_processes": ["Finance: Profitability Analysis", "Finance: Revenue Growth Analysis"],
                "default_filters": {},
                "persona_profile": {
                    "decision_style": "Analytical"
                },
                "communication_style": "Concise"
            },
            "Finance Manager": {
                "id": "finance_mgr_001",
                "name": "Finance Manager",
                "role": "Finance Manager",
                "business_processes": ["Finance: Budget Planning", "Finance: Cost Management"],
                "default_filters": {},
                "persona_profile": {
                    "decision_style": "Methodical"
                },
                "communication_style": "Detailed"
            }
        }
    
    async def set_principal_context(self, principal_id: str, context_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Set principal context.
        
        Args:
            principal_id: Identifier of the principal.
            context_data: Additional context data.
            
        Returns:
            Principal context information.
        """
        try:
            # Get principal profile
            profile = await self.fetch_principal_profile(principal_id)
            if not profile:
                self.logger.warning(f"Principal profile not found: {principal_id}")
                return {}
                
            # Merge with context data
            if context_data:
                # Update profile with context data
                # This would be expanded in a full implementation
                pass
                
            return profile
        except Exception as e:
            self.logger.error(f"Error setting principal context: {str(e)}")
            return {}
    
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
            
            # Try to get the profile directly from the provider
            profile = self._principal_provider.get(principal_id)
            
            if profile:
                # Convert Pydantic model to dict if needed (prefer Pydantic v2 API)
                if hasattr(profile, 'model_dump'):
                    profile_dict = profile.model_dump()
                elif hasattr(profile, '__dict__'):
                    profile_dict = vars(profile)
                else:
                    profile_dict = {}
                
                return {
                    "principal_id": profile_dict.get("id", principal_id),
                    "name": profile_dict.get("name", principal_id),
                    "business_processes": profile_dict.get("business_processes", []),
                    "default_filters": profile_dict.get("default_filters", {}),
                    "communication_style": profile_dict.get("communication_style", "direct"),
                    "decision_timeframe": profile_dict.get("decision_timeframe", "monthly")
                }
            
            # Fall back to checking self.principal_profiles if provider lookup failed
            if principal_id in self.principal_profiles:
                profile = self.principal_profiles[principal_id]
                return {
                    "principal_id": principal_id,
                    "name": profile.get("name", principal_id),
                    "business_processes": profile.get("business_processes", []),
                    "default_filters": profile.get("default_filters", {}),
                    "communication_style": profile.get("communication_style", "direct"),
                    "decision_timeframe": profile.get("decision_timeframe", "monthly")
                }
            else:
                self.logger.warning(f"Principal profile not found: {principal_id}")
                # Return a default profile instead of empty dict
                return {
                    "principal_id": principal_id,
                    "name": principal_id.replace('_', ' ').title(),
                    "business_processes": ["Finance: Profitability Analysis", "Finance: Revenue Growth Analysis"],
                    "default_filters": {},
                    "communication_style": "direct",
                    "decision_timeframe": "monthly"
                }
        except Exception as e:
            self.logger.error(f"Error fetching principal profile: {str(e)}")
            return {"principal_id": principal_id, "name": principal_id.replace('_', ' ').title()}

    async def identify_data_product_owner(
        self, request: PrincipalOwnershipRequest
    ) -> PrincipalOwnershipResponse:
        """Resolve the accountable principal for a newly onboarded data product."""

        request_id = request.request_id
        notes: List[str] = []
        ownership_chain: List[OwnershipChainEntry] = []
        owner_principal_id: Optional[str] = None
        owner_profile: Dict[str, Any] = {}

        def _record_chain(principal_id: str, role: Optional[str], reason: str) -> None:
            ownership_chain.append(
                OwnershipChainEntry(
                    principal_id=principal_id,
                    role=role,
                    reason=reason,
                )
            )

        # 1. Direct nominee lookup by principal ID
        if self._principal_provider and request.candidate_owner_ids:
            for candidate_id in request.candidate_owner_ids:
                if not candidate_id:
                    continue
                try:
                    provider_profile = self._principal_provider.get(candidate_id)
                except Exception as err:
                    self.logger.warning(f"Candidate lookup failed for {candidate_id}: {err}")
                    provider_profile = None
                if provider_profile:
                    owner_profile = self._normalize_profile_data(provider_profile)
                    owner_principal_id = owner_profile.get("id", candidate_id)
                    owner_profile.setdefault("principal_id", owner_principal_id)
                    _record_chain(owner_principal_id, owner_profile.get("role"), "Direct nominee match")
                    notes.append(f"Matched nominated owner '{owner_principal_id}'.")
                    break

        # 2. Fallback to role-based resolution when no direct nominee found
        if not owner_principal_id and request.fallback_roles:
            for role in request.fallback_roles:
                profile = self._get_profile_case_insensitive(role)
                if profile:
                    owner_profile = self._normalize_profile_data(profile)
                    owner_principal_id = owner_profile.get("id") or owner_profile.get("principal_id") or role
                    owner_profile.setdefault("principal_id", owner_principal_id)
                    _record_chain(owner_principal_id, owner_profile.get("role", role), "Role-based fallback match")
                    notes.append(f"Selected role-based fallback '{owner_principal_id}'.")
                    break

        # 3. Examine business process context for the best available owner
        if not owner_principal_id and request.business_process_context:
            target_processes = {bp.lower() for bp in request.business_process_context if bp}
            best_candidate: Optional[Dict[str, Any]] = None
            best_match_count = 0
            for profile_data in self._iter_principal_profiles():
                business_processes = profile_data.get("business_processes", []) or []
                overlap = target_processes.intersection({bp.lower() for bp in business_processes})
                if overlap and len(overlap) > best_match_count:
                    best_candidate = profile_data
                    best_match_count = len(overlap)
            if best_candidate:
                owner_profile = best_candidate
                owner_principal_id = best_candidate.get("id") or best_candidate.get("principal_id")
                owner_profile.setdefault("principal_id", owner_principal_id)
                _record_chain(
                    owner_principal_id or "unknown",
                    owner_profile.get("role"),
                    "Matched via business process context",
                )
                notes.append(
                    "Matched owner based on business process overlap: "
                    + ", ".join(request.business_process_context)
                )

        # 4. Last-resort fallback to the first available profile
        if not owner_principal_id:
            fallback_profile = next(self._iter_principal_profiles(), None)
            if fallback_profile:
                owner_profile = fallback_profile
                owner_principal_id = fallback_profile.get("id") or fallback_profile.get("principal_id")
                owner_profile.setdefault("principal_id", owner_principal_id)
                _record_chain(
                    owner_principal_id or "unknown",
                    owner_profile.get("role"),
                    "Default registry fallback",
                )
                notes.append("Applied default principal registry fallback.")

        if owner_principal_id:
            owner_profile.setdefault("principal_id", owner_principal_id)
            return PrincipalOwnershipResponse.success(
                request_id=request_id,
                owner_principal_id=owner_principal_id,
                owner_profile=owner_profile,
                ownership_chain=ownership_chain,
                notes=notes,
            )

        notes.append("No owner could be resolved automatically; manual assignment required.")
        return PrincipalOwnershipResponse.pending(
            request_id=request_id,
            owner_principal_id=None,
            owner_profile={},
            ownership_chain=ownership_chain,
            notes=notes,
        )
    
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
        
    def _get_profile_case_insensitive(self, role_key: str) -> Dict[str, Any]:
        """
        Get a profile using case-insensitive matching with multiple format attempts.
        
        Args:
            role_key: The role key to look up (can be in any case format)
            
        Returns:
            The profile if found, or None if not found
        """
        if not role_key:
            return None
            
        # Try different formats of the role key
        formats_to_try = [
            role_key,                              # Original format
            role_key.lower(),                      # lowercase
            role_key.upper(),                      # UPPERCASE
            role_key.replace(" ", "_").upper(),     # UPPERCASE_WITH_UNDERSCORES
            role_key.title(),                      # Title Case
            role_key.replace("_", " ").title(),     # Title Case With Spaces
        ]
        
        # Try each format against profile keys and role values
        for fmt in formats_to_try:
            # Direct key match
            if fmt in self.principal_profiles:
                return self.principal_profiles[fmt]
                
            # Check lowercase keys - ensure principal_profiles is a dictionary
            if isinstance(self.principal_profiles, dict):
                for key, profile in self.principal_profiles.items():
                    # Match against key
                    if key.lower() == fmt.lower():
                        return profile
                        
                    # Match against role attribute if it exists
                    if hasattr(profile, 'get') and profile.get('role', '').lower() == fmt.lower():
                        return profile
            elif isinstance(self.principal_profiles, list):
                # Handle case where principal_profiles is a list
                for profile in self.principal_profiles:
                    # Try to get a key or identifier from the profile
                    if hasattr(profile, 'get'):
                        profile_role = profile.get('role', '')
                        if profile_role.lower() == fmt.lower():
                            return profile
                    
        # No match found
        return None
        
    def _get_role_string(self, role):
        """
        Ensure role is a string.
        
        Args:
            role: Role string or enum value
            
        Returns:
            Role as a string
        """
        # If it has a value attribute (like an enum), get the value
        if hasattr(role, 'value'):
            return role.value
        
        # Otherwise convert to string
        return str(role)
        
    async def _map_business_processes_to_strings(self, business_processes: List[Any]) -> List[str]:
        """
        Convert business process objects to string values.
        
        Args:
            business_processes: List of business process objects or strings
            
        Returns:
            List of business process strings
        """
        result = []
        
        for bp in business_processes:
            if isinstance(bp, str):
                # Already a string, use directly
                result.append(bp)
            elif hasattr(bp, 'display_name') and bp.display_name:
                # Business process object with display_name
                result.append(bp.display_name)
            elif hasattr(bp, 'name') and bp.name:
                # Business process object with name
                result.append(bp.name)
            else:
                # Try to convert to string
                try:
                    result.append(str(bp))
                except Exception as e:
                    self.logger.warning(f"Could not convert business process to string: {e}")
        
        # Filter out None values
        return [bp for bp in result if bp is not None]
        
    async def get_principal_context(self, principal_role) -> Dict[str, Any]:
        """
        Get principal context for a given role.
        
        Args:
            principal_role: Role of the principal (string or PrincipalRole enum value)
            
        Returns:
            Principal context containing preferences and relevant business processes
        """
        from src.agents.models.situation_awareness_models import PrincipalContext, TimeFrame
        
        try:
            # Log the request
            self.logger.info(f"Getting principal context for role: {principal_role}")
            
            # First try to load from registry if not already loaded
            if not self.principal_profiles:
                await self._load_principal_profiles()
            
            # Convert enum to string if needed
            role_str = self._get_role_string(principal_role)
            
            # Try to find profile by role string
            profile = None
            
            # Try to find profile with matching role
            if isinstance(self.principal_profiles, list):
                for p in self.principal_profiles:
                    if isinstance(p, dict) and p.get('role', '').lower() == role_str.lower():
                        profile = p
                        break
            elif isinstance(self.principal_profiles, dict):
                for p in self.principal_profiles.values():
                    if isinstance(p, dict) and p.get('role', '').lower() == role_str.lower():
                        profile = p
                        break
            
            # If no profile found by direct match, try case-insensitive lookup
            if not profile:
                profile = self._get_profile_case_insensitive(role_str)
            
            if profile:
                # Create and return PrincipalContext
                business_processes = []
                
                # If profile is a dictionary and has business_processes
                if hasattr(profile, 'get') and profile.get('business_processes'):
                    for bp in profile.get('business_processes', []):
                        # Add business process as string
                        business_processes.append(bp)
                
                # Get role string from profile
                role_str = profile.get('role', 'CFO')
                
                # Create context with defaults if values are missing
                principal_context = PrincipalContext(
                    role=role_str,  # Use role string directly
                    principal_id=profile.get('id', role_str.lower().replace(' ', '_')),
                    business_processes=business_processes or [],
                    default_filters=profile.get('default_filters', {}) if hasattr(profile, 'get') else {},
                    decision_style=profile.get('decision_style', "Analytical") if hasattr(profile, 'get') else "Analytical",
                    communication_style=profile.get('communication_style', "Concise") if hasattr(profile, 'get') else "Concise",
                    preferred_timeframes=[TimeFrame.CURRENT_QUARTER, TimeFrame.YEAR_TO_DATE]
                )
                
                # Return as dictionary for JSON serialization
                return principal_context.model_dump()
            
            # If no matching profile is found, return a default context
            self.logger.warning(f"No principal profile found for role {principal_role}, using default")
            # Use the input role string or default to CFO
            default_role = "CFO"
            default_id = role_str.lower().replace(' ', '_') if 'role_str' in locals() else "cfo_001"
            
            principal_context = PrincipalContext(
                role=default_role,
                principal_id=default_id,
                business_processes=[],
                default_filters={},
                decision_style="Analytical",
                communication_style="Concise",
                preferred_timeframes=[TimeFrame.CURRENT_QUARTER, TimeFrame.YEAR_TO_DATE]
            )
            
            return principal_context.model_dump()
            
        except Exception as e:
            self.logger.error(f"Error in get_principal_context: {str(e)}")
            raise
            
    async def get_business_process_by_name(self, name: str) -> Dict[str, Any]:
        """
        Get a business process by name from the registry.
        
        Args:
            name: Name of the business process
            
        Returns:
            Business process object as a dictionary
        """
        try:
            # Log the request
            self.logger.info(f"Getting business process by name: {name}")
            
            # Get the business process provider
            if self.registry_factory is None:
                self.logger.error("Registry factory is not initialized")
                return None
                
            business_process_provider = self.registry_factory.get_provider("business_process")
            if business_process_provider is None:
                self.logger.error("Business process provider not found in registry factory")
                return None
            
            # Try to find the business process by name
            business_process = business_process_provider.get_by_name(name)
            if business_process is None:
                # Try by display name
                business_process = business_process_provider.get_by_display_name(name)
            
            if business_process is None:
                # Try by ID
                business_process = business_process_provider.get_by_id(name)
                
            if business_process is None:
                self.logger.warning(f"Business process not found: {name}")
                # Return the name directly as a string
                business_process = name
            
            # Convert to dictionary
            if hasattr(business_process, 'model_dump'):
                return business_process.model_dump()
            else:
                return business_process
                
        except Exception as e:
            self.logger.error(f"Error in get_business_process_by_name: {str(e)}")
            return None
            
    async def get_principal_context_by_id(self, principal_id: str) -> Dict[str, Any]:
        """
        Get principal context for a given principal ID.
        
        Args:
            principal_id: ID of the principal
            
        Returns:
            Principal context containing preferences and relevant business processes
        """
        from src.agents.models.situation_awareness_models import PrincipalContext, TimeFrame
        from src.agents.models.principal_context_models import PrincipalProfileResponse
        
        try:
            # Log the request
            self.logger.info(f"Getting principal context for ID: {principal_id}")
            
            # First try to load from registry if not already loaded
            if not self.principal_profiles:
                await self._load_principal_profiles()
            
            # Try to get profile directly from the provider first
            profile_data = None
            if self._principal_provider:
                profile_obj = self._principal_provider.get(principal_id)
                if profile_obj:
                    # Convert to dict if it's a model (prefer Pydantic v2 API)
                    if hasattr(profile_obj, 'model_dump'):
                        profile_data = profile_obj.model_dump()
                    elif hasattr(profile_obj, '__dict__'):
                        profile_data = vars(profile_obj)
                    else:
                        profile_data = {}
                    
                    self.logger.info(f"Found profile for {principal_id} in provider")
            
            # If not found in provider, check principal_profiles
            if not profile_data:
                # Check if principal_profiles is a list or dict and handle accordingly
                if isinstance(self.principal_profiles, list):
                    for p in self.principal_profiles:
                        if isinstance(p, dict) and p.get('id') == principal_id:
                            profile_data = p
                            break
                elif isinstance(self.principal_profiles, dict):
                    if principal_id in self.principal_profiles:
                        profile_data = self.principal_profiles[principal_id]
            
            if profile_data:
                # Create and return PrincipalContext
                business_processes = []
                
                # Extract business processes
                bp_list = profile_data.get('business_processes', [])
                for bp in bp_list:
                    # Try to get the business process from the registry provider
                    if self._business_process_provider:
                        bp_obj = self._business_process_provider.get(bp)
                        if bp_obj:
                            business_processes.append(bp_obj)
                        else:
                            # Try to find by display name or similar name
                            found = False
                            for process in self._business_process_provider.get_all():
                                if bp.lower() in process.name.lower() or \
                                   (process.display_name and bp.lower() in process.display_name.lower()):
                                    business_processes.append(process)
                                    found = True
                                    self.logger.info(f"Found similar business process: {process.name} for {bp}")
                                    break
                            
                            if not found:
                                self.logger.warning(f"Unknown business process: {bp} for principal {principal_id}")
                                # Add the business process as a string directly
                                business_processes.append(bp)
                    else:
                        # Fallback to using the string directly
                        self.logger.warning(f"No business process provider available, using string directly: {bp}")
                        business_processes.append(bp)
                
                # Get role string from profile; YAML to model conversion may omit 'role'
                # Fallback to 'title' or 'name' before defaulting to 'CFO'
                role_str = profile_data.get('role') or profile_data.get('title') or profile_data.get('name') or 'CFO'
                
                # Convert business process objects to string values directly
                string_business_processes = []
                for bp in business_processes:
                    if isinstance(bp, str):
                        string_business_processes.append(bp)
                    elif hasattr(bp, 'display_name') and bp.display_name:
                        string_business_processes.append(bp.display_name)
                    elif hasattr(bp, 'name') and bp.name:
                        string_business_processes.append(bp.name)
                    else:
                        try:
                            string_business_processes.append(str(bp))
                        except Exception as e:
                            self.logger.warning(f"Could not convert business process to string: {e}")
                
                # Filter out None values
                string_business_processes = [bp for bp in string_business_processes if bp is not None]
                
                # Create context with defaults if values are missing
                principal_context = PrincipalContext(
                    role=role_str,  # Use role string directly
                    principal_id=principal_id,
                    business_processes=string_business_processes,
                    default_filters=profile_data.get('default_filters', {}),
                    decision_style=profile_data.get('persona_profile', {}).get('decision_style', "Analytical") 
                        if isinstance(profile_data.get('persona_profile'), dict) else "Analytical",
                    communication_style=profile_data.get('communication_style', "Concise"),
                    preferred_timeframes=[TimeFrame.CURRENT_QUARTER, TimeFrame.YEAR_TO_DATE]
                )
                # Build and return a protocol-compliant response immediately
                try:
                    import uuid as _uuid
                    from src.agents.models.principal_context_models import PrincipalProfileResponse as _PPR
                    response = _PPR(
                        request_id=str(_uuid.uuid4()),
                        status="success",
                        profile=profile_data,
                        context=principal_context.model_dump()
                    )
                    return response.model_dump()
                except Exception:
                    # Fallback to dict if model construction fails
                    return {
                        "request_id": str(_uuid.uuid4()) if '_uuid' in locals() else "",
                        "status": "success",
                        "profile": profile_data,
                        "context": principal_context.model_dump()
                    }
            
            # Create a default profile
            default_profile = {
                "id": principal_id,
                "name": principal_id.replace('_', ' ').title(),
                "role": "CFO",
                "business_processes": ["Finance: Profitability Analysis", "Finance: Revenue Growth Analysis"]
            }
            
            # Create default context with business processes as strings
            default_business_processes = [
                "Finance: Profitability Analysis",
                "Finance: Revenue Growth Analysis",
                "Finance: Expense Management",
                "Finance: Cash Flow Management",
                "Finance: Budget vs. Actuals"
            ]
            
            principal_context = PrincipalContext(
                role="CFO",  # Default role as string
                principal_id=principal_id,
                business_processes=default_business_processes,
                default_filters={},
                decision_style="Analytical",
                communication_style="Concise",
                preferred_timeframes=[TimeFrame.CURRENT_QUARTER, TimeFrame.YEAR_TO_DATE]
            )
            
            # Create response object
            import uuid
            response = PrincipalProfileResponse(
                request_id=str(uuid.uuid4()),
                status="success",
                profile=default_profile,
                context=principal_context.model_dump()
            )
            
            return response.model_dump()
            
        except Exception as e:
            self.logger.error(f"Error in get_principal_context_by_id: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            
            # Return a minimal valid response even in case of error
            default_profile = {"id": principal_id, "name": principal_id.replace('_', ' ').title(), "role": "CFO"}
            
            # Try to get some business processes from registry for the error case
            default_business_processes = []
            try:
                if self._business_process_provider:
                    # Get a couple of finance processes if available
                    finance_processes = self._business_process_provider.find_by_domain("Finance")
                    if finance_processes:
                        # Convert business process objects to strings
                        for bp in finance_processes[:2]:  # Just use 2 in error case
                            if hasattr(bp, 'display_name') and bp.display_name:
                                default_business_processes.append(bp.display_name)
                            elif hasattr(bp, 'name') and bp.name:
                                default_business_processes.append(bp.name)
                            else:
                                default_business_processes.append(str(bp))
            except Exception:
                # Ignore any errors in the error handler
                pass
                
            # Fallback to hardcoded strings if we couldn't get any
            if not default_business_processes:
                default_business_processes = [
                    "Finance: Profitability Analysis",
                    "Finance: Revenue Growth Analysis"
                ]
                
            principal_context = PrincipalContext(
                role="CFO",
                principal_id=principal_id,
                business_processes=default_business_processes,
                default_filters={},
                decision_style="Analytical",
                communication_style="Concise",
                preferred_timeframes=[TimeFrame.CURRENT_QUARTER]
            )
            response = PrincipalProfileResponse(
                request_id=str(uuid.uuid4()),
                status="success",
                profile=default_profile, 
                context=principal_context
            )
            return response.model_dump()
