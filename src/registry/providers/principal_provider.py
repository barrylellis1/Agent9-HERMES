"""
Principal Profile Registry Provider

Concrete implementation of the registry provider for principal profiles.
This provider supports loading principal profiles from various sources
and provides a unified API for accessing them.
"""

import importlib
import logging
from typing import Any, Dict, List, Optional, Type


from src.registry.models.principal import PrincipalProfile, DEFAULT_PRINCIPALS
from src.registry.providers.registry_provider import RegistryProvider

logger = logging.getLogger(__name__)


class PrincipalProfileProvider(RegistryProvider[PrincipalProfile]):
    """
    Provider for principal profile registry data.
    
    This provider supports loading principal profiles from Python modules,
    YAML files, or JSON files, and provides a unified API for accessing them.
    """
    
    def __init__(self, source_path: str = None, storage_format: str = "python"):
        """
        Initialize the principal profile provider.
        
        Args:
            source_path: Path to the principal profile data source
            storage_format: Format of the data source (python, yaml, json)
        """
        self.source_path = source_path
        self.storage_format = storage_format
        self._profiles: Dict[str, PrincipalProfile] = {}
        self._profiles_by_name: Dict[str, PrincipalProfile] = {}
        self._profiles_by_title: Dict[str, PrincipalProfile] = {}
    
    async def load(self) -> None:
        """
        Load principal profiles from the configured data source.
        
        This method supports loading from Python modules, YAML files,
        or JSON files, depending on the configured storage format.
        """
        logger.info(f"Loading principal profiles from {self.source_path} ({self.storage_format})")
        
        if not self.source_path:
            # Default to built-in profiles if no source path provided
            self._load_default_profiles()
            return
        
        if self.storage_format == "python":
            self._load_from_python_module()
        elif self.storage_format == "yaml":
            await self._load_from_yaml()
        elif self.storage_format == "json":
            await self._load_from_json()
        else:
            logger.error(f"Unsupported storage format: {self.storage_format}")
            # Fall back to default profiles
            self._load_default_profiles()
        
        logger.info(f"Loaded {len(self._profiles)} principal profiles")
    
    def _load_default_profiles(self) -> None:
        """Load the default principal profiles."""
        for profile in DEFAULT_PRINCIPALS:
            self._add_profile(profile)
    
    def _load_from_python_module(self) -> None:
        """Load principal profiles from a Python module."""
        try:
            module_name = self.source_path
            module = importlib.import_module(module_name)
            
            # Look for profile objects in the module
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                
                # Check for lists of PrincipalProfile objects
                if isinstance(attr, list) and attr and hasattr(attr[0], 'id') and hasattr(attr[0], 'name'):
                    for item in attr:
                        try:
                            # Try to convert to PrincipalProfile if it's not already
                            if not isinstance(item, PrincipalProfile):
                                profile = PrincipalProfile(**(item.model_dump() if hasattr(item, 'model_dump') else vars(item)))
                            else:
                                profile = item
                            self._add_profile(profile)
                        except Exception as e:
                            logger.warning(f"Failed to convert item to PrincipalProfile: {e}")
                
                # Check for dictionaries that might be profile registries
                elif isinstance(attr, dict) and attr:
                    for key, value in attr.items():
                        try:
                            if hasattr(value, 'id') and hasattr(value, 'name'):
                                # Try to convert to PrincipalProfile if it's not already
                                if not isinstance(value, PrincipalProfile):
                                    profile = PrincipalProfile(**(value.model_dump() if hasattr(value, 'model_dump') else vars(value)))
                                else:
                                    profile = value
                                self._add_profile(profile)
                        except Exception as e:
                            logger.warning(f"Failed to convert dict item to PrincipalProfile: {e}")
            
            # If no profiles were found, look for older profile format
            if not self._profiles:
                self._extract_profiles_from_module(module)
                
        except (ImportError, AttributeError) as e:
            logger.error(f"Error loading principal profiles from {self.source_path}: {e}")
            self._load_default_profiles()
    
    def _extract_profiles_from_module(self, module) -> None:
        """
        Extract principal profiles from a module with older format.
        
        This method looks for principal profile definitions in the module and
        converts them to PrincipalProfile objects.
        """
        # Look for common profile attributes in the module
        principal_ids = set()
        
        # Try to find direct profile objects
        for attr_name in dir(module):
            if "profile" in attr_name.lower() or "principal" in attr_name.lower():
                try:
                    attr = getattr(module, attr_name)
                    
                    # Try to extract principal ID
                    principal_id = None
                    if hasattr(attr, "id"):
                        principal_id = attr.id
                    elif hasattr(attr, "name"):
                        principal_id = attr.name.lower().replace(" ", "_")
                    elif "cfo" in attr_name.lower():
                        principal_id = "cfo"
                    elif "ceo" in attr_name.lower():
                        principal_id = "ceo"
                    elif "finance" in attr_name.lower():
                        principal_id = "finance_manager"
                    
                    if principal_id:
                        principal_ids.add(principal_id)
                        
                        # Try to create a profile
                        profile_data = {
                            "id": principal_id,
                            "name": attr.name if hasattr(attr, "name") else attr_name.replace("_", " ").title(),
                            "title": attr.title if hasattr(attr, "title") else attr_name.replace("_", " ").title(),
                            "business_processes": attr.business_processes if hasattr(attr, "business_processes") else [],
                            "kpis": attr.kpis if hasattr(attr, "kpis") else []
                        }
                        
                        profile = PrincipalProfile(**profile_data)
                        self._add_profile(profile)
                except Exception as e:
                    logger.warning(f"Failed to extract profile from attribute {attr_name}: {e}")
        
        # If no profiles found, create minimal ones based on default
        if not self._profiles:
            logger.warning("No profiles found, using defaults")
            self._load_default_profiles()
    
    async def _load_from_yaml(self) -> None:
        """Load principal profiles from a YAML file."""
        try:
            import yaml
            with open(self.source_path, "r") as file:
                data = yaml.safe_load(file)
                
                principals_loaded = False
                roles_by_id = {}
                principal_by_role = {}
                
                # First, load the roles section if it exists to build a role ID mapping
                if isinstance(data, dict) and 'roles' in data:
                    roles_data = data['roles']
                    logger.info(f"Found {len(roles_data)} roles in YAML under 'roles' key")
                    
                    if isinstance(roles_data, list):
                        for role in roles_data:
                            if isinstance(role, dict) and 'id' in role and 'name' in role:
                                role_id = role['id']
                                roles_by_id[role_id] = role
                                logger.debug(f"Registered role: {role_id} - {role['name']}")
                
                # Handle registry format with 'principals' key
                if isinstance(data, dict) and 'principals' in data:
                    logger.info(f"Found {len(data['principals'])} principal profiles in YAML under 'principals' key")
                    principals_data = data['principals']
                    
                    if isinstance(principals_data, list):
                        for item in principals_data:
                            if isinstance(item, dict):
                                try:
                                    # Filter out fields not in the PrincipalProfile model
                                    filtered_item = {}
                                    for field in PrincipalProfile.__annotations__.keys():
                                        if field in item:
                                            filtered_item[field] = item[field]
                                    
                                    profile = PrincipalProfile(**filtered_item)
                                    self._add_profile(profile)
                                    
                                    # Track profiles by role for additional role ID lookups
                                    if 'role' in item:
                                        role_name = item['role']
                                        principal_by_role[role_name] = profile.id
                                        logger.debug(f"Mapped role name {role_name} to principal ID {profile.id}")
                                    
                                    logger.info(f"Registered principal: {profile.id} - {profile.name}")
                                    principals_loaded = True
                                except Exception as e:
                                    logger.warning(f"Failed to create PrincipalProfile from YAML item: {e}")
                
                # Now add role IDs as profile IDs to support looking up by role ID
                for role_id, role_data in roles_by_id.items():
                    role_name = role_data.get('name')
                    
                    # Check if we already have this profile by role name
                    if role_name in principal_by_role:
                        principal_id = principal_by_role[role_name]
                        profile = self._profiles.get(principal_id)
                        
                        if profile:
                            # Clone the profile with the role ID to allow lookup by role ID
                            role_profile_data = profile.model_dump()
                            role_profile_data['id'] = role_id
                            role_profile = PrincipalProfile(**role_profile_data)
                            self._add_profile(role_profile)
                            logger.info(f"Added role ID mapping: {role_id} -> {profile.name}")
                
                if principals_loaded:
                    return
                
                # Fall back to original format handling if no 'principals' key
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict):
                            try:
                                profile = PrincipalProfile(**item)
                                self._add_profile(profile)
                                principals_loaded = True
                            except Exception as e:
                                logger.warning(f"Failed to create PrincipalProfile from YAML item: {e}")
                elif isinstance(data, dict):
                    for key, value in data.items():
                        if isinstance(value, dict):
                            try:
                                profile_data = {**value, "id": key}
                                if "name" not in profile_data:
                                    profile_data["name"] = key.replace("_", " ").title()
                                profile = PrincipalProfile(**profile_data)
                                self._add_profile(profile)
                                principals_loaded = True
                            except Exception as e:
                                logger.warning(f"Failed to create PrincipalProfile from YAML item: {e}")
                
        except (ImportError, FileNotFoundError, yaml.YAMLError) as e:
            logger.error(f"Error loading principal profiles from {self.source_path}: {e}")
            self._load_default_profiles()
    
    async def _load_from_json(self) -> None:
        """Load principal profiles from a JSON file."""
        try:
            import json
            with open(self.source_path, "r") as file:
                data = json.load(file)
                
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict):
                            try:
                                profile = PrincipalProfile(**item)
                                self._add_profile(profile)
                            except Exception as e:
                                logger.warning(f"Failed to create PrincipalProfile from JSON item: {e}")
                elif isinstance(data, dict):
                    for key, value in data.items():
                        if isinstance(value, dict):
                            try:
                                profile_data = {**value, "id": key}
                                if "name" not in profile_data:
                                    profile_data["name"] = key.replace("_", " ").title()
                                profile = PrincipalProfile(**profile_data)
                                self._add_profile(profile)
                            except Exception as e:
                                logger.warning(f"Failed to create PrincipalProfile from JSON item: {e}")
                
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Error loading principal profiles from {self.source_path}: {e}")
            self._load_default_profiles()
    
    def _remove_profile_indexes(self, profile: PrincipalProfile) -> None:
        """Remove cached lookups for the provided principal profile."""
        self._profiles_by_name.pop(profile.name, None)
        self._profiles_by_title.pop(profile.title, None)

    def _add_profile(self, profile: PrincipalProfile) -> None:
        """
        Add a principal profile to the internal dictionaries.
        
        Args:
            profile: The principal profile to add
        """
        existing = self._profiles.get(profile.id)
        if existing:
            self._remove_profile_indexes(existing)
        self._profiles[profile.id] = profile
        self._profiles_by_name[profile.name] = profile
        self._profiles_by_title[profile.title] = profile

    def upsert(self, profile: PrincipalProfile) -> PrincipalProfile:
        """Create or replace a principal profile entry."""
        self._add_profile(profile)
        return profile

    def delete(self, profile_id: str) -> bool:
        """Delete a principal profile by ID."""
        existing = self._profiles.pop(profile_id, None)
        if not existing:
            return False
        self._remove_profile_indexes(existing)
        return True
    
    def get(self, id_or_name: str) -> Optional[PrincipalProfile]:
        """
        Get a principal profile by ID, name, or title.
        
        Args:
            id_or_name: The ID, name, or title of the principal profile
            
        Returns:
            The principal profile if found, None otherwise
        """
        # Try to find by ID
        if id_or_name in self._profiles:
            return self._profiles[id_or_name]
        
        # Try to find by name
        if id_or_name in self._profiles_by_name:
            return self._profiles_by_name[id_or_name]
        
        # Try to find by title
        if id_or_name in self._profiles_by_title:
            return self._profiles_by_title[id_or_name]
        
        # Try case-insensitive match
        id_lower = id_or_name.lower()
        for key, profile in self._profiles.items():
            if key.lower() == id_lower:
                return profile
        
        for key, profile in self._profiles_by_name.items():
            if key.lower() == id_lower:
                return profile
                
        for key, profile in self._profiles_by_title.items():
            if key.lower() == id_lower:
                return profile
        
        return None
    
    def get_all(self) -> List[PrincipalProfile]:
        """
        Get all principal profiles.
        
        Returns:
            List of all principal profiles
        """
        return list(self._profiles.values())
    
    def find_by_attribute(self, attr_name: str, attr_value: Any) -> List[PrincipalProfile]:
        """
        Find principal profiles by a specific attribute value.
        
        Args:
            attr_name: The name of the attribute to search by
            attr_value: The value to search for
            
        Returns:
            List of matching principal profiles
        """
        results = []
        
        for profile in self._profiles.values():
            if hasattr(profile, attr_name):
                value = getattr(profile, attr_name)
                
                # Handle list attributes (e.g., business_processes, kpis)
                if isinstance(value, list) and attr_value in value:
                    results.append(profile)
                # Handle string/simple attributes
                elif value == attr_value:
                    results.append(profile)
        
        return results
    
    def find_by_business_process(self, business_process_id: str) -> List[PrincipalProfile]:
        """
        Find principal profiles by business process.
        
        Args:
            business_process_id: The business process ID to search for
            
        Returns:
            List of principal profiles responsible for the specified business process
        """
        return self.find_by_attribute("business_processes", business_process_id)
    
    def find_by_kpi(self, kpi_id: str) -> List[PrincipalProfile]:
        """
        Find principal profiles by KPI.
        
        Args:
            kpi_id: The KPI ID to search for
            
        Returns:
            List of principal profiles monitoring the specified KPI
        """
        return self.find_by_attribute("kpis", kpi_id)
    
    def register(self, item: PrincipalProfile) -> bool:
        """
        Register a new principal profile.
        
        Args:
            item: The principal profile to register
            
        Returns:
            True if registration succeeded, False otherwise
        """
        if item.id in self._profiles:
            logger.warning(f"Principal profile with ID {item.id} already exists")
            return False
        
        self._add_profile(item)
        logger.info(f"Registered principal profile: {item.id} - {item.name}")
        return True


