"""
Registry Bootstrap

This module is responsible for initializing and registering all registry providers
with the RegistryFactory, ensuring they are available to agents and services.

Provides standardized initialization of registry providers and agent factories.
"""

import os
import logging
from typing import Dict, Any
from dotenv import load_dotenv
load_dotenv()

from src.registry.factory import RegistryFactory
from src.agents.agent_bootstrap import AgentBootstrap
from src.registry.providers.business_glossary_provider import BusinessGlossaryProvider, BusinessTerm

# Database-backed registry providers (Supabase)
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

            # Initialize registry factory
            cls._factory = RegistryFactory()
            
            # Try to initialize shared database connection
            db_manager = await cls._get_shared_db_manager(config)

            # Active client scope — determines which tenant's records are loaded
            active_client_id = os.getenv("ACTIVE_CLIENT_ID", "lubricants")
            logger.info("Active client ID: %s", active_client_id)

            # Helper to check if we should use DB provider
            def should_use_db(backend_var: str) -> bool:
                choice = (os.getenv(backend_var, 'yaml') or 'yaml').lower()
                return choice in ('database', 'postgres', 'supabase') and db_manager is not None

            # --- Principal Profile ---
            existing_principal_provider = cls._factory.get_provider('principal_profile')
            if existing_principal_provider is None:
                principal_provider = None

                if should_use_db('PRINCIPAL_PROFILE_BACKEND'):
                    try:
                        logger.info('Initializing DatabaseRegistryProvider for Principal Profiles')
                        principal_provider = DatabaseRegistryProvider(
                            db_manager=db_manager,
                            table_name="principal_profiles",
                            model_class=PrincipalProfile,
                            client_id=active_client_id
                        )
                        await principal_provider.load()
                        cls._factory.register_provider('principal_profile', principal_provider)
                        cls._factory._provider_initialization_status['principal_profile'] = True
                        logger.info(f"Database principal provider initialized with {len(principal_provider.get_all())} profiles")
                    except Exception as e:
                        logger.warning(f"Database principal provider init failed: {e}")
                        principal_provider = None

                # YAML fallback removed (2026-02-19) — Supabase is the sole registry backend.
                if principal_provider is None:
                    logger.error("Principal profile provider failed to initialize from Supabase. Check SUPABASE_DB_URL and PRINCIPAL_PROFILE_BACKEND env vars.")
            
            # --- Business Glossary ---
            existing_glossary_provider = cls._factory.get_provider('business_glossary')
            if existing_glossary_provider is None:
                glossary_provider = None

                if should_use_db('BUSINESS_GLOSSARY_BACKEND'):
                    try:
                        logger.info('Initializing BusinessGlossaryProvider (hydrated from Supabase)')
                        # Load raw records from DB using the generic provider
                        db_glossary_loader = DatabaseRegistryProvider(
                            db_manager=db_manager,
                            table_name="business_glossary_terms",
                            model_class=BusinessTerm,
                            client_id=None  # shared across all clients
                        )
                        await db_glossary_loader.load()
                        # Hydrate a BusinessGlossaryProvider in-memory so the registry
                        # route isinstance check passes and term-specific methods work
                        glossary_provider = BusinessGlossaryProvider(auto_load=False)
                        for term in db_glossary_loader.get_all():
                            glossary_provider.terms[term.name.lower()] = term
                            for synonym in term.synonyms:
                                glossary_provider.synonym_map[synonym.lower()] = term.name.lower()
                        cls._factory.register_provider('business_glossary', glossary_provider)
                        cls._factory._provider_initialization_status['business_glossary'] = True
                        logger.info(f"Business glossary provider initialized with {len(glossary_provider.terms)} terms from Supabase")
                    except Exception as e:
                        logger.warning(f"Database glossary provider init failed: {e}")
                        glossary_provider = None

                # Fallback: use an empty in-memory BusinessGlossaryProvider so the
                # Registry Explorer works even if Supabase glossary table is empty/missing.
                if glossary_provider is None:
                    logger.warning("Business glossary Supabase init failed — using empty in-memory provider")
                    glossary_provider = BusinessGlossaryProvider(auto_load=False)
                    cls._factory.register_provider('business_glossary', glossary_provider)
                    cls._factory._provider_initialization_status['business_glossary'] = True
            
            # --- Data Product ---
            existing_data_product_provider = cls._factory.get_provider('data_product')
            if existing_data_product_provider is None:
                data_product_provider = None

                if should_use_db('DATA_PRODUCT_BACKEND'):
                    try:
                        logger.info('Initializing DatabaseRegistryProvider for Data Products')
                        data_product_provider = DatabaseRegistryProvider(
                            db_manager=db_manager,
                            table_name="data_products",
                            model_class=DataProduct,
                            client_id=None  # Load all clients' data products so SA agent can resolve any database
                        )
                        await data_product_provider.load()
                        cls._factory.register_provider('data_product', data_product_provider)
                        cls._factory._provider_initialization_status['data_product'] = True
                    except Exception as e:
                        logger.warning(f"Database data product provider init failed: {e}")
                        data_product_provider = None

                # YAML fallback removed (2026-02-19) — Supabase is the sole registry backend.
                if data_product_provider is None:
                    logger.error("Data product provider failed to initialize from Supabase. Check SUPABASE_DB_URL and DATA_PRODUCT_BACKEND env vars.")
            
            # --- Business Process ---
            existing_bp_provider = cls._factory.get_provider('business_process')
            if existing_bp_provider is None:
                bp_provider = None

                if should_use_db('BUSINESS_PROCESS_BACKEND'):
                    try:
                        logger.info('Initializing DatabaseRegistryProvider for Business Processes')
                        bp_provider = DatabaseRegistryProvider(
                            db_manager=db_manager,
                            table_name="business_processes",
                            model_class=BusinessProcess,
                            client_id=None  # shared across all clients
                        )
                        await bp_provider.load()
                        cls._factory.register_provider('business_process', bp_provider)
                        cls._factory._provider_initialization_status['business_process'] = True
                    except Exception as e:
                        logger.warning(f"Database business process provider init failed: {e}")
                        bp_provider = None

                # YAML fallback removed (2026-02-19) — Supabase is the sole registry backend.
                if bp_provider is None:
                    logger.error("Business process provider failed to initialize from Supabase. Check SUPABASE_DB_URL and BUSINESS_PROCESS_BACKEND env vars.")
            
            # --- KPI ---
            existing_kpi_provider = cls._factory.get_provider('kpi')
            if existing_kpi_provider is None:
                kpi_provider = None

                if should_use_db('KPI_REGISTRY_BACKEND'):
                    try:
                        logger.info('Initializing DatabaseRegistryProvider for KPIs')
                        kpi_provider = DatabaseRegistryProvider(
                            db_manager=db_manager,
                            table_name="kpis",
                            model_class=KPI,
                            client_id=None  # Load all clients' KPIs; SA agent filters by kpi.client_id at request time
                        )
                        await kpi_provider.load()
                        cls._factory.register_provider('kpi', kpi_provider)
                        cls._factory._provider_initialization_status['kpi'] = True
                    except Exception as e:
                        logger.warning(f"Database KPI provider init failed: {e}")
                        kpi_provider = None

                # YAML fallback removed (2026-02-19) — Supabase is the sole registry backend.
                if kpi_provider is None:
                    logger.error("KPI provider failed to initialize from Supabase. Check SUPABASE_DB_URL and KPI_REGISTRY_BACKEND env vars.")
            
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
