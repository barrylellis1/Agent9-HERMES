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
from src.registry.providers.principal_provider import PrincipalProfileProvider
from src.agents.agent_bootstrap import AgentBootstrap
from src.registry.providers.data_product_provider import DataProductProvider
from src.registry.providers.kpi_provider import KPIProvider
from src.registry.providers.business_glossary_provider import (
    BusinessGlossaryProvider,
    BusinessTerm,
)
from src.registry.providers.business_process_provider import BusinessProcessProvider

# New generic database imports
from src.database.manager_factory import DatabaseManagerFactory
from src.registry.providers.database_provider import DatabaseRegistryProvider
from src.registry.models.kpi import KPI
from src.registry.models.principal import PrincipalProfile
from src.registry.models.data_product import DataProduct
from src.registry.models.business_process import BusinessProcess

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
    _db_manager = None
    
    @classmethod
    async def _get_shared_db_manager(cls, config: Dict[str, Any] = None):
        """
        Get or create a shared database manager instance.
        Checks for DATABASE_URL or explicit config.
        """
        if cls._db_manager:
            return cls._db_manager

        # Check for database configuration
        db_url = os.getenv("DATABASE_URL")
        supabase_db_url = os.getenv("SUPABASE_DB_URL")
        
        # Prioritize explicit config, then env vars
        config = config or {}
        db_config = config.get("database", {})
        
        dsn = db_config.get("dsn") or db_url or supabase_db_url
        
        if dsn:
            try:
                logger.info("Initializing generic DatabaseManager for registry persistence")
                # Assume Postgres if DSN is present (most common for Supabase/Enterprise)
                # We could parse the scheme from DSN to be smarter
                db_type = "postgres" 
                if dsn.startswith("duckdb"):
                    db_type = "duckdb"
                
                manager = DatabaseManagerFactory.create_manager(
                    db_type, 
                    {"dsn": dsn, **db_config}, 
                    logger
                )
                if await manager.connect({}):
                    cls._db_manager = manager
                    return manager
            except Exception as e:
                logger.error(f"Failed to initialize database manager: {e}")
                
        return None

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
            
            # Try to initialize shared database connection
            db_manager = await cls._get_shared_db_manager(config)
            
            # Helper to check if we should use DB provider
            def should_use_db(backend_var: str) -> bool:
                choice = (os.getenv(backend_var, 'yaml') or 'yaml').lower()
                return choice in ('database', 'postgres', 'supabase') and db_manager is not None

            # --- Principal Profile ---
            existing_principal_provider = cls._factory.get_provider('principal_profile')
            if existing_principal_provider is None:
                principal_provider = None
                principal_path = os.path.join(registry_base_path, "principal", "principal_registry.yaml")
                
                # 1. Try Generic Database Provider
                if should_use_db('PRINCIPAL_PROFILE_BACKEND'):
                    try:
                        logger.info('Initializing DatabaseRegistryProvider for Principal Profiles')
                        principal_provider = DatabaseRegistryProvider(
                            db_manager=db_manager,
                            table_name="principal_profiles",
                            model_class=PrincipalProfile,
                            key_fields=["id"]
                        )
                        await principal_provider.load()
                        cls._factory.register_provider('principal_profile', principal_provider)
                        cls._factory._provider_initialization_status['principal_profile'] = True
                        logger.info(f"Database principal provider initialized with {len(principal_provider.get_all())} profiles")
                    except Exception as e:
                        logger.warning(f"Database principal provider init failed: {e}")
                        principal_provider = None

                # 2. Fallback to YAML
                if principal_provider is None:
                    logger.info("Initializing YAML principal profile provider")
                    if os.path.exists(principal_path):
                        principal_provider = PrincipalProfileProvider(source_path=principal_path, storage_format="yaml")
                        cls._factory.register_provider('principal_profile', principal_provider)
                        await principal_provider.load()
                        cls._factory._provider_initialization_status['principal_profile'] = True
                    else:
                        logger.warning(f"Principal registry file not found at {principal_path}")
                        principal_provider = PrincipalProfileProvider()
                        principal_provider._load_default_profiles()
                        cls._factory.register_provider('principal_profile', principal_provider)
                        cls._factory._provider_initialization_status['principal_profile'] = True
            
            # --- Business Glossary ---
            existing_glossary_provider = cls._factory.get_provider('business_glossary')
            if existing_glossary_provider is None:
                glossary_provider = None
                glossary_path = os.path.join(registry_base_path, "data", "business_glossary.yaml")

                # 1. Try Generic Database Provider
                if should_use_db('BUSINESS_GLOSSARY_BACKEND'):
                    try:
                        logger.info('Initializing DatabaseRegistryProvider for Business Glossary')
                        glossary_provider = DatabaseRegistryProvider(
                            db_manager=db_manager,
                            table_name="business_glossary_terms",
                            model_class=BusinessTerm,
                            key_fields=["id"] 
                        )
                        await glossary_provider.load()
                        cls._factory.register_provider('business_glossary', glossary_provider)
                        cls._factory._provider_initialization_status['business_glossary'] = True
                    except Exception as e:
                        logger.warning(f"Database glossary provider init failed: {e}")
                        glossary_provider = None

                # 2. Fallback to YAML
                if glossary_provider is None:
                    logger.info("Initializing YAML business glossary provider")
                    glossary_provider = BusinessGlossaryProvider(glossary_path=glossary_path)
                    cls._factory.register_provider('business_glossary', glossary_provider)
                    cls._factory._provider_initialization_status['business_glossary'] = True
            
            # --- Data Product ---
            existing_data_product_provider = cls._factory.get_provider('data_product')
            if existing_data_product_provider is None:
                data_product_provider = None
                data_product_path = os.path.join(registry_base_path, "data_product", "data_product_registry.yaml")
                data_product_reference_dir = None
                if not os.getenv("REGISTRY_BASE_PATH"):
                    candidate_reference_dir = os.path.join(registry_references_path, "data_product_registry", "data_products")
                    if os.path.isdir(candidate_reference_dir):
                        data_product_reference_dir = candidate_reference_dir
                data_product_source = data_product_reference_dir or data_product_path

                # 1. Try Generic Database Provider
                if should_use_db('DATA_PRODUCT_BACKEND'):
                    try:
                        logger.info('Initializing DatabaseRegistryProvider for Data Products')
                        data_product_provider = DatabaseRegistryProvider(
                            db_manager=db_manager,
                            table_name="data_products",
                            model_class=DataProduct,
                            key_fields=["id"]
                        )
                        await data_product_provider.load()
                        cls._factory.register_provider('data_product', data_product_provider)
                        cls._factory._provider_initialization_status['data_product'] = True
                    except Exception as e:
                        logger.warning(f"Database data product provider init failed: {e}")
                        data_product_provider = None

                # 2. Fallback to YAML
                if data_product_provider is None:
                    logger.info("Initializing YAML data product provider")
                    if os.path.exists(data_product_source):
                        data_product_provider = DataProductProvider(source_path=data_product_source, storage_format="yaml")
                        cls._factory.register_provider('data_product', data_product_provider)
                        await data_product_provider.load()
                        cls._factory._provider_initialization_status['data_product'] = True
                    else:
                        logger.warning(f"Data product registry file not found at {data_product_source}")
            
            # --- Business Process ---
            existing_bp_provider = cls._factory.get_provider('business_process')
            if existing_bp_provider is None:
                bp_provider = None
                bp_path = os.path.join(registry_base_path, "business_process", "business_process_registry.yaml")

                # 1. Try Generic Database Provider
                if should_use_db('BUSINESS_PROCESS_BACKEND'):
                    try:
                        logger.info('Initializing DatabaseRegistryProvider for Business Processes')
                        bp_provider = DatabaseRegistryProvider(
                            db_manager=db_manager,
                            table_name="business_processes",
                            model_class=BusinessProcess,
                            key_fields=["id"]
                        )
                        await bp_provider.load()
                        cls._factory.register_provider('business_process', bp_provider)
                        cls._factory._provider_initialization_status['business_process'] = True
                    except Exception as e:
                        logger.warning(f"Database business process provider init failed: {e}")
                        bp_provider = None

                # 2. Fallback to YAML
                if bp_provider is None:
                    logger.info("Initializing YAML business process provider")
                    if os.path.exists(bp_path):
                        bp_provider = BusinessProcessProvider(source_path=bp_path, storage_format="yaml")
                        cls._factory.register_provider('business_process', bp_provider)
                        await bp_provider.load()
                        cls._factory._provider_initialization_status['business_process'] = True
                    else:
                        logger.warning(f"Business process registry file not found at {bp_path}")
            
            # --- KPI ---
            existing_kpi_provider = cls._factory.get_provider('kpi')
            if existing_kpi_provider is None:
                kpi_provider = None
                kpi_path = os.path.join(registry_base_path, "kpi", "kpi_registry.yaml")

                # 1. Try Generic Database Provider
                if should_use_db('KPI_REGISTRY_BACKEND'):
                    try:
                        logger.info('Initializing DatabaseRegistryProvider for KPIs')
                        kpi_provider = DatabaseRegistryProvider(
                            db_manager=db_manager,
                            table_name="kpis",
                            model_class=KPI,
                            key_fields=["id"]
                        )
                        await kpi_provider.load()
                        cls._factory.register_provider('kpi', kpi_provider)
                        cls._factory._provider_initialization_status['kpi'] = True
                    except Exception as e:
                        logger.warning(f"Database KPI provider init failed: {e}")
                        kpi_provider = None

                # 2. Fallback to YAML
                if kpi_provider is None:
                    logger.info("Initializing YAML KPI provider")
                    if os.path.exists(kpi_path):
                        kpi_provider = KPIProvider(source_path=kpi_path, storage_format="yaml")
                    else:
                        logger.warning(f"KPI registry file not found at {kpi_path}, creating default provider")
                        kpi_provider = KPIProvider()
                    
                    cls._factory.register_provider('kpi', kpi_provider)
                    await kpi_provider.load()
                    cls._factory._provider_initialization_status['kpi'] = True
            
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
