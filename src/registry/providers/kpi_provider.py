"""
KPI Registry Provider

Concrete implementation of the registry provider for KPIs.
This provider supports loading KPIs from various sources
and provides a unified API for accessing them.
"""

import importlib
import os
import logging
from typing import Any, Dict, List, Optional, Type

from src.registry.models.kpi import KPI, ComparisonType
from src.registry.providers.registry_provider import RegistryProvider

logger = logging.getLogger(__name__)


class KPIProvider(RegistryProvider[KPI]):
    """
    Provider for KPI registry data.
    
    This provider supports loading KPIs from Python modules,
    YAML files, or JSON files, and provides a unified API for accessing them.
    """
    
    def __init__(self, source_path: str = None, storage_format: str = "python"):
        """
        Initialize the KPI provider.
        
        Args:
            source_path: Path to the KPI data source
            storage_format: Format of the data source (python, yaml, json)
        """
        self.source_path = source_path
        self.storage_format = storage_format
        self._kpis: Dict[str, KPI] = {}
        self._kpis_by_name: Dict[str, KPI] = {}
        self._kpis_by_legacy_id: Dict[str, KPI] = {}
    
    async def load(self) -> None:
        """
        Load KPIs from the configured data source.
        
        This method supports loading from Python modules, YAML files,
        or JSON files, depending on the configured storage format.
        """
        logger.info(f"Loading KPIs from {self.source_path} ({self.storage_format})")
        
        if not self.source_path:
            # Default to built-in KPIs if no source path provided
            self._load_default_kpis()
            return
        
        if self.storage_format == "python":
            self._load_from_python_module()
        elif self.storage_format == "yaml":
            await self._load_from_yaml()
        elif self.storage_format == "json":
            await self._load_from_json()
        else:
            logger.error(f"Unsupported storage format: {self.storage_format}")
            # Fall back to default KPIs
            self._load_default_kpis()
        
        logger.info(f"Loaded {len(self._kpis)} KPIs")
    
    def _load_default_kpis(self) -> None:
        """Load default KPIs if no source is available."""
        # These are just placeholders - real implementations would load from registry_references
        default_kpis = [
            KPI(
                id="gross_margin",
                name="Gross Margin",
                domain="Finance",
                description="Revenue minus cost of goods sold, divided by revenue",
                unit="%",
                data_product_id="finance_data",
                business_process_ids=["finance_profitability_analysis"],
                sql_query="SELECT * FROM kpi_gross_margin",
                thresholds=[
                    {
                        "comparison_type": ComparisonType.YOY,
                        "green_threshold": 5.0,
                        "yellow_threshold": 0.0,
                        "red_threshold": -5.0,
                        "inverse_logic": False
                    }
                ],
                owner_role="CFO"
            ),
            KPI(
                id="revenue_growth_rate",
                name="Revenue Growth Rate",
                domain="Finance",
                description="Year-over-year percentage change in revenue",
                unit="%",
                data_product_id="finance_data",
                business_process_ids=["finance_revenue_growth"],
                sql_query="SELECT * FROM kpi_revenue_growth_rate",
                thresholds=[
                    {
                        "comparison_type": ComparisonType.YOY,
                        "green_threshold": 10.0,
                        "yellow_threshold": 5.0,
                        "red_threshold": 0.0,
                        "inverse_logic": False
                    }
                ],
                owner_role="CFO"
            )
        ]
        
        for kpi in default_kpis:
            self._add_kpi(kpi)
    
    def _load_from_python_module(self) -> None:
        """Load KPIs from a Python module."""
        try:
            module_name = self.source_path
            module = importlib.import_module(module_name)
            
            # Look for KPI objects in the module
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                
                # Check for lists of KPI objects
                if isinstance(attr, list) and attr and hasattr(attr[0], 'id') and hasattr(attr[0], 'name'):
                    for item in attr:
                        try:
                            # Try to convert to KPI if it's not already
                            if not isinstance(item, KPI):
                                kpi = KPI(**(item.model_dump() if hasattr(item, 'model_dump') else vars(item)))
                            else:
                                kpi = item
                            self._add_kpi(kpi)
                        except Exception as e:
                            logger.warning(f"Failed to convert item to KPI: {e}")
                
                # Check for dictionaries that might be KPI registries
                elif isinstance(attr, dict) and attr:
                    for key, value in attr.items():
                        try:
                            if hasattr(value, 'id') and hasattr(value, 'name'):
                                # Try to convert to KPI if it's not already
                                if not isinstance(value, KPI):
                                    kpi = KPI(**(value.model_dump() if hasattr(value, 'model_dump') else vars(value)))
                                else:
                                    kpi = value
                                self._add_kpi(kpi)
                        except Exception as e:
                            logger.warning(f"Failed to convert dict item to KPI: {e}")
            
            # If no KPIs were found, try to extract from legacy registry format
            if not self._kpis:
                self._extract_kpis_from_module(module)
                
        except (ImportError, AttributeError) as e:
            logger.error(f"Error loading KPIs from {self.source_path}: {e}")
            self._load_default_kpis()
    
    def _extract_kpis_from_module(self, module) -> None:
        """
        Extract KPIs from a module that doesn't explicitly define them.
        
        This method looks for legacy KPI definitions in the module and
        converts them to KPI objects.
        """
        # Try to find KPI registry in the module
        registry_attr = None
        for attr_name in dir(module):
            if "registry" in attr_name.lower() or "kpi" in attr_name.lower():
                registry_attr = getattr(module, attr_name)
                break
        
        if registry_attr is None:
            logger.warning("No KPI registry found in module")
            return
        
        # Try different extraction strategies
        if isinstance(registry_attr, dict):
            for key, value in registry_attr.items():
                try:
                    # If the value is a dict, try to create a KPI from it
                    if isinstance(value, dict):
                        kpi_data = {**value, "id": key.lower()}
                        if "name" not in kpi_data:
                            kpi_data["name"] = " ".join(word.capitalize() for word in key.lower().split("_"))
                        kpi = KPI(**kpi_data)
                        self._add_kpi(kpi)
                    # If the value is a string, try to create a KPI from the key
                    elif isinstance(key, str):
                        kpi = KPI.from_enum_value(key)
                        self._add_kpi(kpi)
                except Exception as e:
                    logger.warning(f"Failed to extract KPI from registry item: {e}")
        elif isinstance(registry_attr, list):
            for item in registry_attr:
                try:
                    if isinstance(item, str):
                        kpi = KPI.from_enum_value(item)
                        self._add_kpi(kpi)
                    elif hasattr(item, 'id') and hasattr(item, 'name'):
                        kpi_data = item.model_dump() if hasattr(item, 'model_dump') else vars(item)
                        kpi = KPI(**kpi_data)
                        self._add_kpi(kpi)
                except Exception as e:
                    logger.warning(f"Failed to extract KPI from registry item: {e}")
    
    async def _load_from_yaml(self) -> None:
        """Load KPIs from a YAML file."""
        try:
            import yaml
            with open(self.source_path, "r") as file:
                data = yaml.safe_load(file)
                # Load optional enrichment file from same directory
                enrichment_top_dims: Dict[str, Any] = {}
                enrichment_dim_scores: Dict[str, Any] = {}
                try:
                    if isinstance(self.source_path, str):
                        enrich_path = os.path.join(os.path.dirname(self.source_path), "kpi_enrichment.yaml")
                        if os.path.exists(enrich_path):
                            with open(enrich_path, "r", encoding="utf-8") as ef:
                                enrich_doc = yaml.safe_load(ef) or {}
                                enrichment_top_dims = (enrich_doc.get("top_dimensions") or {})
                                enrichment_dim_scores = (enrich_doc.get("dimension_scores") or {})
                except Exception:
                    # Non-fatal; continue without enrichment
                    enrichment_top_dims, enrichment_dim_scores = {}, {}
                
                # Handle the specific structure of our KPI registry YAML
                if isinstance(data, dict) and "kpis" in data and isinstance(data["kpis"], list):
                    # Extract defaults (optional)
                    defaults = data.get("kpi_defaults", {}) if isinstance(data, dict) else {}
                    dp_defaults = (defaults.get("by_data_product_id") or {}) if isinstance(defaults, dict) else {}

                    def _merge_defaults(item: dict) -> dict:
                        """Return a new KPI dict merged with defaults by data_product_id.
                        - Merges 'filters' (shallow) and 'dimensions' (by 'name' dedupe)
                        """
                        try:
                            if not isinstance(item, dict):
                                return item
                            dp_id = item.get("data_product_id")
                            if not (isinstance(dp_id, str) and dp_id in dp_defaults):
                                return item
                            dflt = dp_defaults.get(dp_id) or {}
                            merged = dict(item)
                            # Merge filters
                            dflt_filters = dflt.get("filters") or {}
                            if dflt_filters:
                                mf = dict(dflt_filters)
                                if isinstance(merged.get("filters"), dict):
                                    mf.update(merged["filters"])  # KPI-specific overrides take precedence
                                merged["filters"] = mf
                            # Merge dimensions
                            dflt_dims = dflt.get("dimensions") or []
                            if dflt_dims:
                                existing = merged.get("dimensions") or []
                                # Build map by lowercased name for dedupe
                                def _norm_name(d):
                                    if isinstance(d, dict):
                                        n = d.get("name") or d.get("field") or str(d)
                                    else:
                                        n = str(d)
                                    return str(n).strip().lower()
                                emap = { _norm_name(d): d for d in existing }
                                for d in dflt_dims:
                                    key = _norm_name(d)
                                    if key not in emap:
                                        existing.append(d)
                                merged["dimensions"] = existing
                            return merged
                        except Exception:
                            return item

                    # Process the list of KPIs under the 'kpis' key
                    for item in data["kpis"]:
                        if isinstance(item, dict):
                            try:
                                # Apply defaults before model creation
                                merged_item = _merge_defaults(item)
                                kpi = KPI(**merged_item)
                                # Merge enrichment into KPI.metadata (non-destructive)
                                try:
                                    if not isinstance(kpi.metadata, dict):
                                        kpi.metadata = {}
                                    # by name, id, or legacy id
                                    td = (
                                        enrichment_top_dims.get(kpi.name)
                                        or enrichment_top_dims.get(kpi.id)
                                        or enrichment_top_dims.get(getattr(kpi, "legacy_id", None))
                                    )
                                    if td is not None:
                                        # ensure string
                                        td_str = ", ".join(td) if isinstance(td, list) else str(td)
                                        kpi.metadata.setdefault("top_dimensions", td_str)
                                    ds = (
                                        enrichment_dim_scores.get(kpi.name)
                                        or enrichment_dim_scores.get(kpi.id)
                                        or enrichment_dim_scores.get(getattr(kpi, "legacy_id", None))
                                    )
                                    if ds is not None:
                                        # ensure JSON string for scores
                                        try:
                                            import json as _json
                                            ds_str = ds if isinstance(ds, str) else _json.dumps(ds)
                                        except Exception:
                                            ds_str = str(ds)
                                        kpi.metadata.setdefault("dimension_scores", ds_str)
                                except Exception:
                                    pass
                                self._add_kpi(kpi)
                            except Exception as e:
                                logger.warning(f"Failed to create KPI from YAML item: {e}")
                # Also keep the original handling for other formats
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict):
                            try:
                                kpi = KPI(**item)
                                self._add_kpi(kpi)
                            except Exception as e:
                                logger.warning(f"Failed to create KPI from YAML item: {e}")
                elif isinstance(data, dict):
                    for key, value in data.items():
                        if isinstance(value, dict):
                            try:
                                kpi_data = {**value, "id": key}
                                if "name" not in kpi_data:
                                    kpi_data["name"] = " ".join(word.capitalize() for word in key.split("_"))
                                kpi = KPI(**kpi_data)
                                self._add_kpi(kpi)
                            except Exception as e:
                                logger.warning(f"Failed to create KPI from YAML item: {e}")
                
        except (ImportError, FileNotFoundError, yaml.YAMLError) as e:
            logger.error(f"Error loading KPIs from {self.source_path}: {e}")
            self._load_default_kpis()
    
    async def _load_from_json(self) -> None:
        """Load KPIs from a JSON file."""
        try:
            import json
            with open(self.source_path, "r") as file:
                data = json.load(file)
                
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict):
                            try:
                                kpi = KPI(**item)
                                self._add_kpi(kpi)
                            except Exception as e:
                                logger.warning(f"Failed to create KPI from JSON item: {e}")
                elif isinstance(data, dict):
                    for key, value in data.items():
                        if isinstance(value, dict):
                            try:
                                kpi_data = {**value, "id": key}
                                if "name" not in kpi_data:
                                    kpi_data["name"] = " ".join(word.capitalize() for word in key.split("_"))
                                kpi = KPI(**kpi_data)
                                self._add_kpi(kpi)
                            except Exception as e:
                                logger.warning(f"Failed to create KPI from JSON item: {e}")
                
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Error loading KPIs from {self.source_path}: {e}")
            self._load_default_kpis()
    
    def _add_kpi(self, kpi: KPI) -> None:
        """Add a KPI to the internal dictionaries with case-insensitive names."""
        if not getattr(kpi, "id", None):
            raise ValueError("KPI must have an id")

        self._kpis[kpi.id] = kpi

        name = getattr(kpi, "name", None)
        if isinstance(name, str):
            stripped = name.strip()
            if stripped:
                self._kpis_by_name[stripped] = kpi
                self._kpis_by_name[stripped.lower()] = kpi

        legacy_id = getattr(kpi, "legacy_id", None)
        if isinstance(legacy_id, str):
            clean_legacy = legacy_id.strip()
            if clean_legacy:
                self._kpis_by_legacy_id[clean_legacy] = kpi

    def get(self, id_or_name: str) -> Optional[KPI]:
        """Return a KPI by id, legacy id, or name (case-insensitive)."""
        if not isinstance(id_or_name, str):
            return None

        key = id_or_name.strip()
        if not key:
            return None

        match = self._kpis.get(key)
        if match:
            return match

        match = self._kpis_by_legacy_id.get(key)
        if match:
            return match

        match = self._kpis_by_name.get(key)
        if match:
            return match

        return self._kpis_by_name.get(key.lower())

    def get_all(self) -> List[KPI]:
        """Return all KPIs currently cached."""
        return list(self._kpis.values())
    
    def find_by_attribute(self, attr_name: str, attr_value: Any) -> List[KPI]:
        """
        Find KPIs by a specific attribute value.
        
        Args:
            attr_name: The name of the attribute to search by
            attr_value: The value to search for
            
        Returns:
            List of matching KPIs
        """
        results = []
        
        for kpi in self._kpis.values():
            if hasattr(kpi, attr_name):
                value = getattr(kpi, attr_name)
                
                # Handle list attributes (e.g., tags, business_process_ids)
                if isinstance(value, list) and attr_value in value:
                    results.append(kpi)
                # Handle string/simple attributes
                elif value == attr_value:
                    results.append(kpi)
        
        return results
    
    def find_by_domain(self, domain: str) -> List[KPI]:
        """
        Find KPIs by domain.
        
        Args:
            domain: The domain to search for
            
        Returns:
            List of KPIs in the specified domain
        """
        return self.find_by_attribute("domain", domain)
    
    def find_by_business_process(self, business_process_id: str) -> List[KPI]:
        """
        Find KPIs by business process.
        
        Args:
            business_process_id: The business process ID to search for
            
        Returns:
            List of KPIs related to the specified business process
        """
        return self.find_by_attribute("business_process_ids", business_process_id)
    
    def find_by_owner_role(self, role: str) -> List[KPI]:
        """
        Find KPIs by owner role.
        
        Args:
            role: The owner role to search for
            
        Returns:
            List of KPIs owned by the specified role
        """
        return self.find_by_attribute("owner_role", role)
    
    def register(self, item: KPI) -> bool:
        """
        Register a new KPI.
        
        Args:
            item: The KPI to register
            
        Returns:
            True if registration succeeded, False otherwise
        """
        if item.id in self._kpis:
            logger.warning(f"KPI with ID {item.id} already exists")
            return False
        
        self._add_kpi(item)
        logger.info(f"Registered KPI: {item.id} - {item.name}")
        return True


class SupabaseKPIProvider(KPIProvider):
    """Supabase-backed implementation of the KPI provider."""

    def __init__(
        self,
        *,
        supabase_url: str,
        service_key: str,
        table: str = "kpis",
        schema: str = "public",
        timeout: float = 10.0,
        source_path: Optional[str] = None,
    ) -> None:
        """
        Initialize Supabase KPI provider.
        
        Args:
            supabase_url: Supabase project URL
            service_key: Service role key for admin access
            table: Table name (default: kpis)
            schema: Schema name (default: public)
            timeout: HTTP timeout in seconds
            source_path: Optional fallback YAML path
        """
        super().__init__(source_path=source_path, storage_format="yaml")
        self.supabase_url = supabase_url.rstrip("/")
        self.service_key = service_key
        self.table = table
        self.schema = schema
        self.timeout = timeout

    async def load(self) -> None:
        """Fetch KPIs from Supabase REST endpoint."""
        import httpx
        
        endpoint = f"{self.supabase_url}/rest/v1/{self.table}"
        headers = {
            "apikey": self.service_key,
            "Authorization": f"Bearer {self.service_key}",
            "Accept": "application/json",
            "Prefer": "return=representation",
        }
        if self.schema:
            headers["Accept-Profile"] = self.schema

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(endpoint, params={"select": "*"}, headers=headers)
                response.raise_for_status()
                # Use explicit JSON parsing to avoid Pydantic v1 API lint issues
                import json as _json
                records = _json.loads(response.text)
        except (httpx.HTTPStatusError, httpx.RequestError) as http_err:
            logger.warning(
                "Supabase KPI fetch failed: %s. Falling back to YAML.",
                str(http_err)
            )
            # Fall back to YAML loading
            if self.source_path:
                await super().load()
            return
        except Exception as exc:
            logger.error("Unexpected error fetching Supabase KPIs: %s", exc)
            logger.warning("Falling back to YAML-based KPI provider")
            # Fall back to YAML loading
            if self.source_path:
                await super().load()
            return

        # Clear existing KPIs
        self._kpis.clear()
        self._kpis_by_name.clear()
        self._kpis_by_legacy_id.clear()

        loaded = 0
        for record in records:
            kpi_id = (record.get("id") or "").strip()
            if not kpi_id:
                continue

            try:
                # Build KPI from Supabase row
                # Map Supabase columns to KPI fields
                kpi = KPI(
                    id=kpi_id,
                    name=record.get("name") or kpi_id,
                    domain=record.get("domain") or "Finance",
                    description=record.get("description"),
                    unit=record.get("unit"),
                    data_product_id=record.get("data_product_id") or "unknown",
                    business_process_ids=record.get("business_process_ids") or [],  # Normalized IDs
                    sql_query=record.get("sql_query"),
                    filters=record.get("filters") or {},
                    thresholds=record.get("thresholds") or [],
                    dimensions=record.get("dimensions") or [],
                    tags=record.get("tags") or [],
                    owner_role=record.get("owner_role"),
                    stakeholder_roles=record.get("stakeholder_roles") or [],
                    metadata=record.get("metadata") or {},
                )
            except Exception as kpi_err:
                logger.warning(
                    "Skipping Supabase KPI row due to validation error: %s",
                    kpi_err
                )
                continue

            self._add_kpi(kpi)
            loaded += 1

        logger.info(f"Loaded {loaded} KPIs from Supabase")


def create_supabase_kpi_provider(config: Dict[str, Any]) -> SupabaseKPIProvider:
    """
    Factory function to create a Supabase KPI Provider.
    
    Args:
        config: Configuration dictionary with Supabase credentials
        
    Returns:
        SupabaseKPIProvider instance
    """
    return SupabaseKPIProvider(
        supabase_url=config["url"],
        service_key=config["service_key"],
        table=config.get("kpi_table", "kpis"),
        schema=config.get("schema", "public"),
        timeout=config.get("timeout", 10.0),
        source_path=config.get("fallback_yaml_path"),
    )
