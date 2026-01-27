"""
Business Process Registry Provider

Concrete implementation of the registry provider for business processes.
This provider supports loading business processes from various sources
and provides a unified API for accessing them.
"""

import importlib
import logging
from typing import Any, Dict, List, Optional, Type

from src.registry.models.business_process import BusinessProcess, FINANCE_BUSINESS_PROCESSES
from src.registry.providers.registry_provider import RegistryProvider

logger = logging.getLogger(__name__)


class BusinessProcessProvider(RegistryProvider[BusinessProcess]):
    """
    Provider for business process registry data.
    
    This provider supports loading business processes from Python modules,
    YAML files, or JSON files, and provides a unified API for accessing them.
    """
    
    def __init__(self, source_path: str = None, storage_format: str = "python"):
        """
        Initialize the business process provider.
        
        Args:
            source_path: Path to the business process data source
            storage_format: Format of the data source (python, yaml, json)
        """
        self.source_path = source_path
        self.storage_format = storage_format
        self._processes: Dict[str, BusinessProcess] = {}
        self._processes_by_name: Dict[str, BusinessProcess] = {}
        self._processes_by_legacy_id: Dict[str, BusinessProcess] = {}
    
    async def load(self) -> None:
        """
        Load business processes from the configured data source.
        
        This method supports loading from Python modules, YAML files,
        or JSON files, depending on the configured storage format.
        """
        logger.info(f"Loading business processes from {self.source_path} ({self.storage_format})")
        
        if not self.source_path:
            # Default to built-in processes if no source path provided
            self._load_default_processes()
            return
        
        if self.storage_format == "python":
            self._load_from_python_module()
        elif self.storage_format == "yaml":
            await self._load_from_yaml()
        elif self.storage_format == "json":
            await self._load_from_json()
        else:
            logger.error(f"Unsupported storage format: {self.storage_format}")
            # Fall back to default processes
            self._load_default_processes()
        
        logger.info(f"Loaded {len(self._processes)} business processes")
    
    def _load_default_processes(self) -> None:
        """Load the default finance business processes."""
        for process in FINANCE_BUSINESS_PROCESSES:
            self._add_process(process)
    
    def _load_from_python_module(self) -> None:
        """Load business processes from a Python module."""
        try:
            module_name = self.source_path
            module = importlib.import_module(module_name)
            
            # Look for business processes in the module
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                
                # Check for lists of BusinessProcess objects
                if isinstance(attr, list) and all(isinstance(item, BusinessProcess) for item in attr):
                    for process in attr:
                        self._add_process(process)
                
                # Check for individual BusinessProcess objects
                elif isinstance(attr, BusinessProcess):
                    self._add_process(attr)
            
            # If no processes were found, try to extract from enum or string values
            if not self._processes:
                self._extract_processes_from_module(module)
                
        except (ImportError, AttributeError) as e:
            logger.error(f"Error loading business processes from {self.source_path}: {e}")
            self._load_default_processes()
    
    def _extract_processes_from_module(self, module) -> None:
        """
        Extract business processes from a module that doesn't explicitly define them.
        
        This method looks for enum values or string constants that might represent
        business processes and converts them to BusinessProcess objects.
        """
        # Look for business process strings in principal profiles
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            
            # Check if it's a profile object with business processes
            if hasattr(attr, "business_processes") and isinstance(attr.business_processes, list):
                for process_str in attr.business_processes:
                    if process_str and isinstance(process_str, str):
                        # Convert string to BusinessProcess
                        process = BusinessProcess.from_enum_value(process_str)
                        self._add_process(process)
    
    async def _load_from_yaml(self) -> None:
        """Load business processes from a YAML file."""
        try:
            import yaml
            with open(self.source_path, 'r') as f:
                data = yaml.safe_load(f)
                
            logger.info(f"Loaded YAML data from {self.source_path}, found {len(data) if isinstance(data, list) else 0} processes")
                
            if isinstance(data, list):
                # New format: YAML file is a list of business processes
                for item in data:
                    # Remove any KPIs field if it exists (legacy support)
                    if "kpis" in item:
                        logger.warning(f"Found legacy 'kpis' field in business process {item.get('id')} - ignoring as KPIs are now defined in KPI registry")
                        item.pop("kpis")
                    
                    process = BusinessProcess(**item)
                    self._add_process(process)
                    logger.debug(f"Added business process: {process.id} ({process.domain}: {process.name})")
            elif isinstance(data, dict):
                if "processes" in data:
                    # Legacy format with processes key
                    for item in data["processes"]:
                        if "kpis" in item:
                            item.pop("kpis")
                        process = BusinessProcess(**item)
                        self._add_process(process)
                        logger.debug(f"Added business process from 'processes' key: {process.id}")
                else:
                    logger.warning(f"Unexpected YAML structure: dict without 'processes' key in {self.source_path}")
            else:
                logger.error(f"Unsupported YAML structure in {self.source_path}")
        except Exception as e:
            logger.error(f"Error loading business processes from YAML: {e}")
            self._load_default_processes()
    
    async def _load_from_json(self) -> None:
        """Load business processes from a JSON file."""
        try:
            import json
            with open(self.source_path, "r") as file:
                data = json.load(file)
                
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict):
                            process = BusinessProcess(**item)
                            self._add_process(process)
                
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Error loading business processes from {self.source_path}: {e}")
            self._load_default_processes()
    
    def _remove_process_indexes(self, process: BusinessProcess) -> None:
        """Remove cached lookups for the provided business process."""
        self._processes_by_name.pop(process.name, None)
        self._processes_by_legacy_id.pop(process.legacy_id, None)
        if hasattr(process, "display_name") and process.display_name:
            self._processes_by_name.pop(process.display_name, None)

    def _add_process(self, process: BusinessProcess) -> None:
        """
        Add a business process to the internal dictionaries.
        
        Args:
            process: The business process to add
        """
        existing = self._processes.get(process.id)
        if existing:
            self._remove_process_indexes(existing)
        self._processes[process.id] = process
        self._processes_by_name[process.name] = process
        self._processes_by_legacy_id[process.legacy_id] = process
        
        # Add by display_name if it exists
        if hasattr(process, 'display_name') and process.display_name:
            self._processes_by_name[process.display_name] = process

    def upsert(self, process: BusinessProcess) -> BusinessProcess:
        """Create or replace a business process entry."""
        self._add_process(process)
        return process

    def delete(self, process_id: str) -> bool:
        """Delete a business process by ID."""
        existing = self._processes.pop(process_id, None)
        if not existing:
            return False
        self._remove_process_indexes(existing)
        return True
    
    def get(self, id_or_name: str) -> Optional[BusinessProcess]:
        """
        Get a business process by ID, name, or legacy ID.
        
        Args:
            id_or_name: The ID, name, or legacy ID of the business process
            
        Returns:
            The business process if found, None otherwise
        """
        # Try to find by ID
        if id_or_name in self._processes:
            return self._processes[id_or_name]
        
        # Try to find by name
        if id_or_name in self._processes_by_name:
            return self._processes_by_name[id_or_name]
        
        # Try to find by legacy ID
        if id_or_name in self._processes_by_legacy_id:
            return self._processes_by_legacy_id[id_or_name]
        
        # Try to create from enum value
        try:
            process = BusinessProcess.from_enum_value(id_or_name)
            self._add_process(process)
            return process
        except:
            pass
        
        return None
    
    def get_all(self) -> List[BusinessProcess]:
        """
        Get all business processes.
        
        Returns:
            List of all business processes
        """
        return list(self._processes.values())
    
    def find_by_attribute(self, attr_name: str, attr_value: Any) -> List[BusinessProcess]:
        """
        Find business processes by a specific attribute value.
        
        Args:
            attr_name: The name of the attribute to search by
            attr_value: The value to search for
            
        Returns:
            List of matching business processes
        """
        results = []
        
        for process in self._processes.values():
            if hasattr(process, attr_name):
                value = getattr(process, attr_name)
                
                # Handle list attributes (e.g., tags, kpis)
                if isinstance(value, list) and attr_value in value:
                    results.append(process)
                # Handle string/simple attributes
                elif value == attr_value:
                    results.append(process)
        
        return results
    
    def find_by_domain(self, domain: str) -> List[BusinessProcess]:
        """
        Find business processes by domain.
        
        Args:
            domain: The domain to search for
            
        Returns:
            List of business processes in the specified domain
        """
        return self.find_by_attribute("domain", domain)
    
    def find_by_owner_role(self, role: str) -> List[BusinessProcess]:
        """
        Find business processes by owner role.
        
        Args:
            role: The owner role to search for
            
        Returns:
            List of business processes owned by the specified role
        """
        return self.find_by_attribute("owner_role", role)
    
    def register(self, item: BusinessProcess) -> bool:
        """
        Register a new business process.
        
        Args:
            item: The business process to register
            
        Returns:
            True if registration succeeded, False otherwise
        """
        if item.id in self._processes:
            logger.warning(f"Business process with ID {item.id} already exists")
            return False
        
        self._add_process(item)
        logger.info(f"Registered business process: {item.id} - {item.name}")
        return True


class SupabaseBusinessProcessProvider(BusinessProcessProvider):
    """
    Supabase-backed business process provider.
    
    Fetches business processes from Supabase REST API and falls back to YAML if unavailable.
    """
    
    def __init__(
        self,
        supabase_url: str,
        service_key: str,
        table: str = 'business_processes',
        schema: str = 'public',
        source_path: str = None,
    ):
        """
        Initialize Supabase business process provider.
        
        Args:
            supabase_url: Supabase project URL
            service_key: Service role key for authentication
            table: Table name (default: business_processes)
            schema: Schema name (default: public)
            source_path: Fallback YAML path if Supabase fails
        """
        super().__init__(source_path=source_path, storage_format='yaml')
        self.supabase_url = supabase_url
        self.service_key = service_key
        self.table = table
        self.schema = schema
    
    async def load(self) -> None:
        """Load business processes from Supabase, with YAML fallback."""
        try:
            await self._load_from_supabase()
        except Exception as e:
            logger.warning(f'Failed to load from Supabase: {e}. Falling back to YAML.')
            if self.source_path:
                await self._load_from_yaml()
            else:
                self._load_default_processes()
    
    async def _load_from_supabase(self) -> None:
        """Fetch business processes from Supabase REST API."""
        import requests
        import json
        from requests.exceptions import RequestException, ConnectionError, Timeout
        
        url = f'{self.supabase_url}/rest/v1/{self.table}'
        headers = {
            'apikey': self.service_key,
            'Authorization': f'Bearer {self.service_key}',
        }
        
        params = {'select': '*'}
        
        try:
            # Set a timeout to avoid hanging
            response = requests.get(url, headers=headers, params=params, timeout=5)
            response.raise_for_status()
            
            rows = json.loads(response.text)
            
            for row in rows:
                bp = self._row_to_business_process(row)
                self._add_process(bp)
            
            logger.info(f'Loaded {len(self._processes)} business processes from Supabase')
            
        except ConnectionError:
            raise Exception("Connection refused - Supabase may be down or unreachable")
        except Timeout:
            raise Exception("Connection timed out - Supabase is slow or unreachable")
        except RequestException as e:
            raise Exception(f"Supabase request failed: {e}")
    
    def _row_to_business_process(self, row: dict) -> BusinessProcess:
        """Convert Supabase row to BusinessProcess Pydantic object."""
        return BusinessProcess(
            id=row['id'],
            name=row['name'],
            domain=row['domain'],
            description=row.get('description'),
            tags=row.get('tags', []),
            owner_role=row.get('owner_role'),
            stakeholder_roles=row.get('stakeholder_roles', []),
            display_name=row.get('display_name'),
            metadata=row.get('metadata', {}),
        )
