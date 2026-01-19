"""
Registry Bootstrap

This module is responsible for initializing and registering all registry providers
with the RegistryFactory, ensuring they are available to agents and services.

Provides standardized initialization of registry providers and agent factories.
"""

import os
import logging
from typing import Dict, Any, Optional

from src.registry.factory import RegistryFactory
from src.registry.providers.principal_provider import (
    PrincipalProfileProvider,
    SupabasePrincipalProfileProvider,
)
from src.agents.agent_bootstrap import AgentBootstrap
from src.registry.providers.data_product_provider import (
    DataProductProvider,
    SupabaseDataProductProvider,
)
from src.registry.providers.kpi_provider import (
    KPIProvider,
    SupabaseKPIProvider,
)
from src.registry.providers.business_glossary_provider import (
    BusinessGlossaryProvider,
    SupabaseBusinessGlossaryProvider,
)
from src.registry.providers.business_process_provider import (
    BusinessProcessProvider,
    SupabaseBusinessProcessProvider,
)

logger = logging.getLogger(__name__)

class RegistryBootstrap:
    """
    Bootstrap class for registry initialization.
    
    This class is responsible for properly initializing and registering
    all registry providers with the RegistryFactory, ensuring they are
    available to agents and services.
    """
    
    _initialized = False
    _factory = None
    
    @classmethod
    async def initialize(cls, config: Dict[str, Any] = None) -> bool:
        """
        Initialize the registry bootstrap system, register required providers,
        and initialize agent factories.
        
        Args:
            config: Configuration dictionary (base_path, registry_path, etc.)
            
        Returns:
            bool: True if initialization was successful, False otherwise
        """
        try:
            if cls._initialized:
                cls._factory = cls._factory or RegistryFactory()
                missing_providers = []
                expected = ("principal_profile", "business_glossary", "data_product", "kpi")
                for provider_name in expected:
                    provider = cls._factory.get_provider(provider_name)
                    if provider is None or not cls._factory._provider_initialization_status.get(provider_name, False):
                        missing_providers.append(provider_name)

                if not missing_providers:
                    logger.info("Registry bootstrap already initialized")
                    return True

                logger.info(
                    "Registry bootstrap re-running to finish provider initialization for: %s",
                    ", ".join(missing_providers),
                )
            config = config or {}
            base_path = config.get('base_path', os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
            registry_path = config.get('registry_path', os.path.join(base_path, "registry"))
            registry_base_path = os.getenv("REGISTRY_BASE_PATH")
            if registry_base_path:
                registry_base_path = os.path.abspath(registry_base_path)
            else:
                registry_base_path = registry_path

            logger.info("Registry base path resolved to: %s", registry_base_path)
            registry_references_path = os.path.join(base_path, "registry_references")
            
            # Initialize registry factory
            cls._factory = RegistryFactory()
            
            # Configure base paths
            # base_path = config.get("base_path", os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
            # registry_path = config.get("registry_path", os.path.join(base_path, "registry"))
            
            # Initialize and register principal provider
            existing_principal_provider = cls._factory.get_provider('principal_profile')
            if existing_principal_provider is None:
                backend_choice = (os.getenv('PRINCIPAL_PROFILE_BACKEND', 'yaml') or 'yaml').lower()
                supabase_config = (config or {}).get('supabase', {})
                supabase_url = supabase_config.get('url') or os.getenv('SUPABASE_URL')
                supabase_service_key = supabase_config.get('service_key') or os.getenv('SUPABASE_SERVICE_ROLE_KEY')

                principal_provider = None
                principal_path = os.path.join(registry_base_path, "principal", "principal_registry.yaml")

                if backend_choice == 'supabase' and supabase_url and supabase_service_key:
                    try:
                        logger.info('Initializing Supabase principal profile provider')
                        principal_provider = SupabasePrincipalProfileProvider(
                            supabase_url=supabase_url,
                            service_key=supabase_service_key,
                            table=supabase_config.get('principal_table', 'principal_profiles'),
                            schema=supabase_config.get('schema', 'public'),
                            source_path=principal_path,  # Fallback YAML path
                        )
                        await principal_provider.load()
                        cls._factory.register_provider('principal_profile', principal_provider)
                        cls._factory._provider_initialization_status['principal_profile'] = True
                        profiles = principal_provider.get_all() or []
                        logger.info(f'Supabase principal provider initialized successfully with {len(profiles)} profiles')
                    except Exception as supabase_err:
                        logger.warning(
                            'Falling back to YAML principal provider due to Supabase error: %s',
                            supabase_err,
                        )
                        principal_provider = None

                if principal_provider is None:
                    logger.info("Initializing YAML principal profile provider")
                    if os.path.exists(principal_path):
                        principal_provider = PrincipalProfileProvider(
                            source_path=principal_path,
                            storage_format="yaml"
                        )
                        cls._factory.register_provider('principal_profile', principal_provider)
                        await principal_provider.load()
                        cls._factory._provider_initialization_status['principal_profile'] = True
                        profiles = principal_provider.get_all() or []
                        logger.info(f"Initialized principal provider with {len(profiles)} profiles")
                    else:
                        logger.warning(f"Principal registry file not found at {principal_path}")
                        # Create with default profiles
                        principal_provider = PrincipalProfileProvider()
                        principal_provider._load_default_profiles()
                        cls._factory.register_provider('principal_profile', principal_provider)
                        cls._factory._provider_initialization_status['principal_profile'] = True
                        logger.info("Using default principal profiles (registry file not found)")
            else:
                logger.info("Principal profile provider already registered, using existing instance")
            
            # Initialize and register business glossary provider
            existing_glossary_provider = cls._factory.get_provider('business_glossary')
            if existing_glossary_provider is None:
                backend_choice = (os.getenv('BUSINESS_GLOSSARY_BACKEND', 'yaml') or 'yaml').lower()
                supabase_config = (config or {}).get('supabase', {})
                supabase_url = supabase_config.get('url') or os.getenv('SUPABASE_URL')
                supabase_service_key = supabase_config.get('service_key') or os.getenv('SUPABASE_SERVICE_ROLE_KEY')

                glossary_provider = None

                if backend_choice == 'supabase' and supabase_url and supabase_service_key:
                    try:
                        logger.info('Initializing Supabase business glossary provider')
                        glossary_provider = SupabaseBusinessGlossaryProvider(
                            supabase_url=supabase_url,
                            service_key=supabase_service_key,
                            table=supabase_config.get('glossary_table', 'business_glossary_terms'),
                            schema=supabase_config.get('schema', 'public'),
                            glossary_path=os.path.join(registry_base_path, 'data', 'business_glossary.yaml'),
                        )
                        await glossary_provider.load()
                        cls._factory.register_provider('business_glossary', glossary_provider)
                        cls._factory._provider_initialization_status['business_glossary'] = True
                        logger.info('Supabase glossary provider initialized successfully')
                    except Exception as supabase_err:
                        logger.warning(
                            'Falling back to YAML glossary provider due to Supabase error: %s',
                            supabase_err,
                        )
                        glossary_provider = None

                if glossary_provider is None:
                    logger.info("Initializing YAML business glossary provider")
                    glossary_path = os.path.join(registry_base_path, "data", "business_glossary.yaml")
                    glossary_provider = BusinessGlossaryProvider(glossary_path=glossary_path)
                    cls._factory.register_provider('business_glossary', glossary_provider)
                    cls._factory._provider_initialization_status['business_glossary'] = True
                    logger.info(
                        "Initialized business glossary provider with %s terms",
                        len(glossary_provider.get_all()),
                    )
            
            # Initialize and register data product provider
            existing_data_product_provider = cls._factory.get_provider('data_product')
            if existing_data_product_provider is None:
                backend_choice = (os.getenv('DATA_PRODUCT_BACKEND', 'yaml') or 'yaml').lower()
                supabase_config = (config or {}).get('supabase', {})
                supabase_url = supabase_config.get('url') or os.getenv('SUPABASE_URL')
                supabase_service_key = supabase_config.get('service_key') or os.getenv('SUPABASE_SERVICE_ROLE_KEY')

                data_product_provider = None
                data_product_path = os.path.join(registry_base_path, "data_product", "data_product_registry.yaml")
                data_product_reference_dir = None
                if not os.getenv("REGISTRY_BASE_PATH"):
                    candidate_reference_dir = os.path.join(registry_references_path, "data_product_registry", "data_products")
                    if os.path.isdir(candidate_reference_dir):
                        data_product_reference_dir = candidate_reference_dir
                data_product_source = data_product_reference_dir or data_product_path

                if backend_choice == 'supabase' and supabase_url and supabase_service_key:
                    try:
                        logger.info('Initializing Supabase data product provider')
                        data_product_provider = SupabaseDataProductProvider(
                            supabase_url=supabase_url,
                            service_key=supabase_service_key,
                            table=supabase_config.get('data_product_table', 'data_products'),
                            schema=supabase_config.get('schema', 'public'),
                            source_path=data_product_source,
                        )
                        await data_product_provider.load()
                        cls._factory.register_provider('data_product', data_product_provider)
                        cls._factory._provider_initialization_status['data_product'] = True
                        dp_count = len(data_product_provider.get_all() or {})
                        logger.info(f'Supabase data product provider initialized successfully with {dp_count} data products')
                    except Exception as supabase_err:
                        logger.warning(
                            'Falling back to YAML data product provider due to Supabase error: %s',
                            supabase_err,
                        )
                        data_product_provider = None

                if data_product_provider is None:
                    logger.info("Initializing YAML data product provider")
                    if os.path.exists(data_product_source):
                        data_product_provider = DataProductProvider(
                            source_path=data_product_source,
                            storage_format="yaml"
                        )
                        cls._factory.register_provider('data_product', data_product_provider)
                        await data_product_provider.load()
                        cls._factory._provider_initialization_status['data_product'] = True
                        dp_count = len(data_product_provider.get_all() or {})
                        logger.info(f"Initialized data product provider with {dp_count} data products")
                    else:
                        logger.warning(f"Data product registry file not found at {data_product_source}")
            else:
                logger.info("Data product provider already registered, using existing instance")
            
            # Initialize and register business process provider
            existing_bp_provider = cls._factory.get_provider('business_process')
            if existing_bp_provider is None:
                backend_choice = (os.getenv('BUSINESS_PROCESS_BACKEND', 'yaml') or 'yaml').lower()
                supabase_config = (config or {}).get('supabase', {})
                supabase_url = supabase_config.get('url') or os.getenv('SUPABASE_URL')
                supabase_service_key = supabase_config.get('service_key') or os.getenv('SUPABASE_SERVICE_ROLE_KEY')

                bp_provider = None
                bp_path = os.path.join(registry_base_path, "business_process", "business_process_registry.yaml")

                if backend_choice == 'supabase' and supabase_url and supabase_service_key:
                    try:
                        logger.info('Initializing Supabase business process provider')
                        bp_provider = SupabaseBusinessProcessProvider(
                            supabase_url=supabase_url,
                            service_key=supabase_service_key,
                            table=supabase_config.get('business_process_table', 'business_processes'),
                            schema=supabase_config.get('schema', 'public'),
                            source_path=bp_path,
                        )
                        await bp_provider.load()
                        cls._factory.register_provider('business_process', bp_provider)
                        cls._factory._provider_initialization_status['business_process'] = True
                        bp_count = len(bp_provider.get_all() or [])
                        logger.info(f'Supabase business process provider initialized successfully with {bp_count} processes')
                    except Exception as supabase_err:
                        logger.warning(
                            'Falling back to YAML business process provider due to Supabase error: %s',
                            supabase_err,
                        )
                        bp_provider = None

                if bp_provider is None:
                    logger.info("Initializing YAML business process provider")
                    if os.path.exists(bp_path):
                        bp_provider = BusinessProcessProvider(
                            source_path=bp_path,
                            storage_format="yaml"
                        )
                        cls._factory.register_provider('business_process', bp_provider)
                        await bp_provider.load()
                        cls._factory._provider_initialization_status['business_process'] = True
                        bp_count = len(bp_provider.get_all() or [])
                        logger.info(f"Initialized business process provider with {bp_count} processes")
                    else:
                        logger.warning(f"Business process registry file not found at {bp_path}")
            else:
                logger.info("Business process provider already registered, using existing instance")
            
            # Initialize and register KPI provider
            existing_kpi_provider = cls._factory.get_provider('kpi')
            if existing_kpi_provider is None:
                backend_choice = (os.getenv('KPI_REGISTRY_BACKEND', 'yaml') or 'yaml').lower()
                supabase_config = (config or {}).get('supabase', {})
                supabase_url = supabase_config.get('url') or os.getenv('SUPABASE_URL')
                supabase_service_key = supabase_config.get('service_key') or os.getenv('SUPABASE_SERVICE_ROLE_KEY')

                kpi_provider = None
                kpi_path = os.path.join(registry_base_path, "kpi", "kpi_registry.yaml")

                if backend_choice == 'supabase' and supabase_url and supabase_service_key:
                    try:
                        logger.info('Initializing Supabase KPI provider')
                        kpi_provider = SupabaseKPIProvider(
                            supabase_url=supabase_url,
                            service_key=supabase_service_key,
                            table=supabase_config.get('kpi_table', 'kpis'),
                            schema=supabase_config.get('schema', 'public'),
                            source_path=kpi_path,  # Fallback YAML path
                        )
                        await kpi_provider.load()
                        cls._factory.register_provider('kpi', kpi_provider)
                        cls._factory._provider_initialization_status['kpi'] = True
                        kpi_count = len(kpi_provider.get_all() or [])
                        logger.info(f'Supabase KPI provider initialized successfully with {kpi_count} KPIs')
                    except Exception as supabase_err:
                        logger.warning(
                            'Falling back to YAML KPI provider due to Supabase error: %s',
                            supabase_err,
                        )
                        kpi_provider = None

                if kpi_provider is None:
                    logger.info("Initializing YAML KPI provider")
                    if os.path.exists(kpi_path):
                        logger.info(f"Creating KPI provider with file at {kpi_path}")
                        kpi_provider = KPIProvider(
                            source_path=kpi_path,
                            storage_format="yaml"
                        )
                    else:
                        logger.warning(f"KPI registry file not found at {kpi_path}, creating default provider")
                        kpi_provider = KPIProvider()  # Will use default KPIs
                    
                    cls._factory.register_provider('kpi', kpi_provider)
                    await kpi_provider.load()
                    cls._factory._provider_initialization_status['kpi'] = True
                    kpi_count = len(kpi_provider.get_all() or [])
                    logger.info(f"KPI provider successfully registered and initialized with {kpi_count} KPIs")
            else:
                logger.info("KPI provider already registered, using existing instance")
            
            # Initialize agent factories using AgentBootstrap
            logger.info("Initializing agent bootstrap")
            agent_bootstrap_success = await AgentBootstrap.initialize({
                'base_path': base_path,
                'registry_factory': cls._factory
            })
            
            if agent_bootstrap_success:
                logger.info("Agent bootstrap initialization successful")
            else:
                logger.warning("Agent bootstrap initialization had issues, continuing with available agents")
            
            cls._initialized = True
            logger.info("Registry providers and agent factories initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize registry providers: {str(e)}")
            return False
    
    @classmethod
    def is_initialized(cls) -> bool:
        """Check if the registry bootstrap has been initialized."""
        return cls._initialized
