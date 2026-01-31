"""
A9 Situation Awareness Agent

This agent provides automated situation awareness for Finance KPIs,
detecting anomalies, trends, and insights based on principal context.

MVP implementation focuses on the Finance KPIs from the FI Star Schema.
"""

import os
import re
import json
import uuid
import yaml
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple, Protocol, runtime_checkable

# Import data models and enums
from src.agents.models.situation_awareness_models import (
    BusinessProcess, PrincipalRole, TimeFrame, ComparisonType, 
    SituationSeverity, KPIDefinition, Situation, KPIValue,
    PrincipalContext, SituationDetectionRequest, SituationDetectionResponse,
    NLQueryRequest, NLQueryResponse, HITLRequest, HITLResponse, HITLDecision
)
from src.agents.models.principal_context_models import PrincipalProfileResponse

# Import agent protocol and base classes
from src.agents.protocols.situation_awareness_protocol import SituationAwarenessProtocol
from src.agents.new.a9_orchestrator_agent import A9_Orchestrator_Agent
from src.agents.shared.a9_agent_base_model import A9AgentBaseModel

# Import registry and database components
from src.registry.factory import RegistryFactory
from src.registry.models.kpi import KPI

# Import other agents
from src.agents.new.a9_orchestrator_agent import A9_Orchestrator_Agent, agent_registry
from src.registry.providers.business_process_provider import BusinessProcessProvider
from src.registry.providers.kpi_provider import KPIProvider as KpiProvider
from src.models.kpi_models import KPI, KPIThreshold, KPIComparisonMethod

# LLM Service models for SQL generation
from src.agents.a9_llm_service_agent import A9_LLM_SQLGenerationRequest

# Data quality filtering utility
from src.agents.utils.data_quality_filter import DataQualityFilter

logger = logging.getLogger(__name__)

class A9_Situation_Awareness_Agent:
    """
    Agent9 Situation Awareness Agent
    
    Implements SituationAwarenessProtocol to detect situations based on KPI thresholds, 
    trends, and principal context. Provides automated, personalized situation 
    awareness for Finance KPIs.
    """
    
    @classmethod
    async def create(cls, config: Dict[str, Any] = None) -> 'A9_Situation_Awareness_Agent':
        """
        Create a new instance of the Situation Awareness Agent.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            A9_Situation_Awareness_Agent instance
        """
        agent = cls(config)
        await agent.connect()
        return agent
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the Situation Awareness Agent.
        
        Args:
            config: Configuration dictionary
        """
        # Store configuration
        if config is None:
            config = {}
            
        # Store the config for later use
        self.config = config 
        # Set up agent properties
        self.name = "A9_Situation_Awareness_Agent"
        self.version = "0.1.0"
        self.data_product_agent = None  # Will be loaded via orchestrator during connect
        self.orchestrator_agent = None  # Will be initialized during connect
        self.principal_context_agent = None  # Will be loaded via orchestrator during connect
        self.llm_service_agent = None  # Will be loaded via orchestrator during connect
        
        # Set up internal data structures
        self.business_processes = {}
        self.kpi_registry = {}
        self.principal_profiles = {}  # Initialize principal_profiles to avoid AttributeError
        
        # Initialize logging
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Load contract and registries - use canonical registry_references path
        default_contract_path = "src/registry_references/data_product_registry/data_products/fi_star_schema.yaml"
        # Try absolute path if relative doesn't exist
        if not os.path.exists(default_contract_path):
            proj_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
            default_contract_path = os.path.join(proj_root, "src", "registry_references", "data_product_registry", "data_products", "fi_star_schema.yaml")
        self.contract_path = config.get("contract_path", default_contract_path)
        
        # Load the contract and KPI definitions
        self._load_contract()
        
        # Initialize KPI registry with empty registry to avoid errors
        self.kpi_registry = {}
        # Cache for last generated SQL per KPI to avoid regenerating for UI display
        self._last_sql_cache: Dict[str, Dict[str, str]] = {}
    
    async def connect(self, orchestrator=None):
        """Initialize connections to dependent services."""
        try:
            # Use provided orchestrator if available
            if orchestrator:
                self.orchestrator_agent = orchestrator

            # Initialize the orchestrator agent if not already set
            if not hasattr(self, 'orchestrator_agent') or self.orchestrator_agent is None:
                self.orchestrator_agent = await A9_Orchestrator_Agent.create({})
                if self.orchestrator_agent is None:
                    logger.error("Failed to create orchestrator agent")
                    return False
            
            # Get the Data Product Agent via the orchestrator
            if self.orchestrator_agent:
                try:
                    self.data_product_agent = await self.orchestrator_agent.get_agent("A9_Data_Product_Agent")
                except Exception as e:
                    logger.error(f"Error getting Data Product Agent from orchestrator: {e}")
                    self.data_product_agent = None
            if not self.data_product_agent:
                # Fallback to direct instantiation if not available via orchestrator
                logger.warning("Data Product Agent not available via orchestrator, using direct instantiation")
                from src.agents.new.a9_data_product_agent import A9_Data_Product_Agent
                self.data_product_agent = await A9_Data_Product_Agent.create({})
                await self.data_product_agent.connect()
                # Register the directly instantiated agent with the orchestrator
                await self.orchestrator_agent.register_agent("A9_Data_Product_Agent", self.data_product_agent)
            
            # Get the Data Governance Agent via the orchestrator
            if self.orchestrator_agent:
                try:
                    self.data_governance_agent = await self.orchestrator_agent.get_agent("A9_Data_Governance_Agent")
                except Exception as e:
                    logger.error(f"Error getting Data Governance Agent from orchestrator: {e}")
                    self.data_governance_agent = None
            if not self.data_governance_agent:
                # Fallback to direct instantiation if not available via orchestrator
                logger.warning("Data Governance Agent not available via orchestrator, using direct instantiation")
                try:
                    from src.agents.new.a9_data_governance_agent import A9_Data_Governance_Agent
                    self.data_governance_agent = await A9_Data_Governance_Agent.create({})
                    await self.data_governance_agent.connect()
                    # Register the directly instantiated agent with the orchestrator
                    await self.orchestrator_agent.register_agent("A9_Data_Governance_Agent", self.data_governance_agent)
                except Exception as e:
                    logger.error(f"Failed to instantiate Data Governance Agent directly: {e}")
                    logger.warning("Data Governance Agent functionality will be limited")
            
            # Get the Principal Context Agent via the orchestrator
            if self.orchestrator_agent:
                try:
                    self.principal_context_agent = await self.orchestrator_agent.get_agent("A9_Principal_Context_Agent")
                except Exception as e:
                    logger.error(f"Error getting Principal Context Agent from orchestrator: {e}")
                    self.principal_context_agent = None
            if not self.principal_context_agent:
                # Fallback to direct instantiation if not available via orchestrator
                logger.warning("Principal Context Agent not available via orchestrator, using direct instantiation")
                try:
                    from src.agents.new.a9_principal_context_agent import A9_Principal_Context_Agent
                    self.principal_context_agent = await A9_Principal_Context_Agent.create({})
                    await self.principal_context_agent.connect()
                    # Register the directly instantiated agent with the orchestrator
                    await self.orchestrator_agent.register_agent("A9_Principal_Context_Agent", self.principal_context_agent)
                except Exception as e:
                    logger.error(f"Failed to instantiate Principal Context Agent directly: {e}")
                    logger.warning("Principal Context Agent functionality will be limited")
            # Load principal profiles from Principal Context Agent (both orchestrator and fallback paths)
            try:
                if hasattr(self.principal_context_agent, 'principal_profiles'):
                    self.principal_profiles = self.principal_context_agent.principal_profiles
                    # Normalize to dict for downstream code/tests expecting a dict-like structure
                    if isinstance(self.principal_profiles, list):
                        normalized = {}
                        for idx, profile in enumerate(self.principal_profiles):
                            if isinstance(profile, dict):
                                key = profile.get('id') or profile.get('role') or profile.get('name') or f"profile_{idx+1}"
                                normalized[key] = profile
                            else:
                                # Convert model-like objects to dict
                                try:
                                    pdata = profile.model_dump() if hasattr(profile, 'model_dump') else (vars(profile) if hasattr(profile, '__dict__') else {})
                                except Exception:
                                    pdata = {}
                                key = pdata.get('id') or pdata.get('role') or pdata.get('name') or f"profile_{idx+1}"
                                normalized[key] = pdata
                        self.principal_profiles = normalized
                    logger.info(f"Loaded {len(self.principal_profiles)} principal profiles from Principal Context Agent")
                else:
                    # Fallback to empty dictionary
                    logger.warning("Principal Context Agent doesn't have principal_profiles attribute")
                    self.principal_profiles = {}
            except Exception as e:
                logger.error(f"Error loading principal profiles: {e}")
                self.principal_profiles = {}
            
            # Get the LLM Service Agent via the orchestrator
            if self.orchestrator_agent:
                try:
                    self.llm_service_agent = await self.orchestrator_agent.get_agent("A9_LLM_Service_Agent")
                except Exception as e:
                    logger.error(f"Error getting LLM Service Agent from orchestrator: {e}")
                    self.llm_service_agent = None
            if not self.llm_service_agent:
                # Fallback to direct instantiation if not available via orchestrator
                logger.warning("LLM Service Agent not available via orchestrator, using direct instantiation")
                try:
                    from src.agents.a9_llm_service_agent import A9_LLM_Service_Agent
                    self.llm_service_agent = await A9_LLM_Service_Agent.create({})
                    # Register the directly instantiated agent with the orchestrator
                    await self.orchestrator_agent.register_agent("A9_LLM_Service_Agent", self.llm_service_agent)
                except Exception as e:
                    logger.error(f"Failed to instantiate LLM Service Agent directly: {e}")
                    logger.warning("LLM-based SQL generation will be limited")
            
            # Load KPIs from registry
            await self._load_kpi_registry()
            
            
            logger.info("Connected to dependent services")
            return True
        except Exception as e:
            logger.error(f"Error connecting to services: {e}")
            return False
    
    async def _load_kpi_registry(self):
        """
        Load KPIs from the registry asynchronously.
        """
        try:
            try:
                from src.registry.registry_factory import RegistryFactory as _RF
            except Exception:
                from src.registry.factory import RegistryFactory as _RF
            registry_factory = _RF()
            try:
                if not registry_factory.is_initialized:
                    await registry_factory.initialize()
                    logger.info("Registry factory initialized successfully")
                else:
                    logger.info("Registry factory already initialized")
            except Exception as e:
                logger.warning(f"Error initializing registry factory: {str(e)}")
            kpi_provider = None
            try:
                kpi_provider = registry_factory.get_kpi_provider()
                if kpi_provider:
                    logger.info(f"Successfully got KPI provider via get_kpi_provider: {kpi_provider}")
            except Exception as e:
                logger.warning(f"Error getting KPI provider via get_kpi_provider: {str(e)}")
            if kpi_provider is None:
                try:
                    kpi_provider = registry_factory.get_provider("kpi")
                    if kpi_provider:
                        logger.info(f"Successfully got KPI provider via get_provider: {kpi_provider}")
                except Exception as e:
                    logger.warning(f"Error getting KPI provider: {str(e)}")
                    kpi_provider = None
            if not kpi_provider:
                logger.warning("Could not get KPI provider from registry factory")
                self._load_kpis_from_contract()
                return
            kpis = kpi_provider.get_all() or []
            if not kpis:
                try:
                    await kpi_provider.load()
                    kpis = kpi_provider.get_all() or []
                except Exception as e:
                    logger.warning(f"KPI provider load attempt failed: {e}")
            if not kpis:
                logger.warning("No KPIs found in registry, attempting to load from file")
                try:
                    registry_path = os.path.join("src", "registry", "kpi", "kpi_registry.yaml")
                    if os.path.exists(registry_path):
                        with open(registry_path, 'r') as file:
                            yaml_data = yaml.safe_load(file)
                            if yaml_data and "kpis" in yaml_data and isinstance(yaml_data["kpis"], list):
                                try:
                                    from src.registry.models.kpi import KPI as RegistryKPI
                                except Exception:
                                    RegistryKPI = None
                                for kpi_item in yaml_data["kpis"]:
                                    try:
                                        if RegistryKPI and isinstance(kpi_item, dict):
                                            kpi_obj = RegistryKPI(**kpi_item)
                                            kpi_provider.register(kpi_obj)
                                    except Exception:
                                        continue
                                kpis = kpi_provider.get_all() or []
                                if kpis:
                                    logger.info(f"Successfully loaded {len(kpis)} KPIs from file")
                except Exception as e:
                    logger.error(f"Error loading KPIs from file: {str(e)}")
            if not kpis:
                logger.warning("Still no KPIs found, using empty KPI registry")
                return
            target_domains = self.config.get("target_domains", ["Finance"])
            logger.info(f"Filtering KPIs for domains: {target_domains}")
            self.kpi_registry = {}
            for kpi in kpis:
                if self._kpi_matches_domains(kpi, target_domains):
                    kpi_def = self._convert_to_kpi_definition(kpi)
                    if kpi_def:
                        self.kpi_registry[kpi_def.name] = kpi_def
            logger.info(f"Added {len(self.kpi_registry)} KPIs to registry for domains: {target_domains}")
            if not self.kpi_registry:
                logger.warning("No matching KPIs found in registry, trying contract fallback")
            
            # Always try to load additional KPIs from contract to ensure full coverage
            # This is important for KPIs defined in data products but not yet in the central registry
            self._load_kpis_from_contract()
        except Exception as e:
            logger.error(f"Error loading KPI registry: {str(e)}")
            self.kpi_registry = {}
            self._load_kpis_from_contract()
    
    async def disconnect(self):
        """Disconnect from dependent services."""
        # Data Product Agent doesn't need explicit disconnection as it's managed by the orchestrator
        
        logger.info(f"{self.name} disconnected from dependent services")
    
    def _load_contract(self):
        """
        Load the data contract and KPI definitions.
        While the contract is still loaded for reference, KPI definitions come from the KPI registry.
        """
        try:
            # Load the contract for reference (tables, schema, etc.)
            with open(self.contract_path, "r") as f:
                self.contract = yaml.safe_load(f)
            
            # Extract business processes from the contract (if any)
            self.business_processes = self.contract.get("supported_business_processes", [])
            
            # Load KPIs from the external registry
            # Skip awaiting here as this is a synchronous method
            # KPIs will be loaded during connect() which properly awaits the async method
            
            logger.info(f"Loaded {len(self.kpi_registry)} KPIs from registry and contract")
        except Exception as e:
            logger.error(f"Error loading contract or registry: {str(e)}")
            raise
    
    # Principal profile management has been moved to the Principal Context Agent
    
    async def detect_situations(
        self, 
        request: SituationDetectionRequest = None, **kwargs
    ) -> SituationDetectionResponse:
        """Handle both direct request object and dictionary with request key"""
        # Store original request_id for response
        original_request_id = str(uuid.uuid4())
        
        # Handle case where request is passed as a keyword argument
        if request is None and 'request' in kwargs:
            request = kwargs['request']
            
        # Convert dict to SituationDetectionRequest if needed
        if isinstance(request, dict):
            # Save the request_id if present
            if 'request_id' in request:
                original_request_id = request.get('request_id')
                
            # Ensure request has all required fields
            if 'request_id' not in request:
                request['request_id'] = original_request_id
            if 'timestamp' not in request:
                request['timestamp'] = datetime.now()
            if 'principal_context' not in request:
                self.logger.error("Missing principal_context in request")
                return SituationDetectionResponse(
                    request_id=original_request_id,
                    status="error",
                    message="Missing principal_context in request",
                    situations=[]
                )
            if 'business_processes' not in request:
                request['business_processes'] = []
                
            try:
                request = SituationDetectionRequest(**request)
            except Exception as e:
                self.logger.error(f"Error converting request dict to SituationDetectionRequest: {str(e)}")
                return SituationDetectionResponse(
                    request_id=original_request_id,
                    status="error",
                    message=f"Invalid request format: {str(e)}",
                    situations=[]
                )
        """
        Detect situations across KPIs based on principal context and business processes.
        
        Args:
            request: SituationDetectionRequest containing principal context and filters
            
        Returns:
            SituationDetectionResponse with detected situations
        """
        try:
            # Ensure we have a valid request_id for the response
            request_id = getattr(request, 'request_id', original_request_id)
            
            self.logger.info(f"Detecting situations for {request.principal_context.role}")
            
            # Get relevant KPIs based on principal context and business processes
            relevant_kpis = self._get_relevant_kpis(
                request.principal_context,
                request.business_processes
            )
            if not relevant_kpis:
                self.logger.warning("No relevant KPIs found for principal context and business processes")
                return SituationDetectionResponse(
                    request_id=request_id,
                    status="success",
                    message="No relevant KPIs found for principal context and business processes",
                    situations=[]
                )
            
            self.logger.info(f"Found {len(relevant_kpis)} relevant KPIs for detection")
            
            # For bullet tracer MVP, we'll process a limited set of KPIs
            # In production, we would process all relevant KPIs
            situations = []
            kpi_values = []
            
            # Process each relevant KPI to fetch actual values from database (no cap)
            for kpi_name, kpi_definition in relevant_kpis.items():
                try:
                    # Get actual KPI value from database using Data Product Agent
                    kpi_value = await self._get_kpi_value(
                        kpi_definition,
                        request.timeframe,
                        request.comparison_type,
                        request.filters,
                        request.principal_context
                    )
                    
                    if kpi_value:
                        kpi_values.append(kpi_value)
                        self.logger.info(f"Retrieved KPI value: {kpi_name} = {kpi_value.value}")
                        
                        # Detect situations based on thresholds, trends, etc.
                        detected_situations = self._detect_kpi_situations(
                            kpi_definition,
                            kpi_value,
                            request.principal_context
                        )
                        
                        self.logger.info(f"Detected {len(detected_situations)} situations for {kpi_name}")
                        situations.extend(detected_situations)
                except Exception as kpi_error:
                    self.logger.warning(f"Error processing KPI {kpi_name}: {str(kpi_error)}")
                    # Continue with other KPIs
            
            # Sort situations by severity (critical first)
            situations.sort(key=lambda s: list(SituationSeverity).index(s.severity) if s.severity in SituationSeverity else 99)
            
            # Generate summary SQL for debugging/transparency
            sample_sql = ""
            if kpi_values and self.data_product_agent:
                first_kpi_def = relevant_kpis.get(kpi_values[0].kpi_name)
                if first_kpi_def:
                    try:
                        # Use Data Product Agent to generate SQL for the KPI
                        merged_filters = {}
                        try:
                            pc_df = getattr(request.principal_context, 'default_filters', None)
                            if isinstance(pc_df, dict):
                                merged_filters.update(pc_df)
                        except Exception:
                            pass
                        try:
                            if isinstance(request.filters, dict):
                                merged_filters.update(request.filters)
                        except Exception:
                            pass
                        # Debug: log merged filters so we can verify principal defaults are present
                        try:
                            self.logger.info(f"[SA SQL-DEBUG] merged_filters for sample SQL: {merged_filters}")
                        except Exception:
                            pass
                        sql_response = await self.data_product_agent.generate_sql_for_kpi(
                            kpi_definition=first_kpi_def,
                            timeframe=request.timeframe,
                            filters=merged_filters
                        )
                        if sql_response.get('success', False) and sql_response.get('sql'):
                            sample_sql = sql_response['sql']
                    except Exception as e:
                        logger.warning(f"Error generating sample SQL: {e}")
                        sample_sql = ""
            
            return SituationDetectionResponse(
                request_id=request.request_id,
                status="success",
                message=f"Detected {len(situations)} situations across {len(kpi_values)} KPIs",
                situations=situations,
                sql_query=sample_sql,
                kpi_evaluated_count=len(kpi_values),
                kpis_evaluated=[kv.kpi_name for kv in kpi_values]
            )
        
        except Exception as e:
            self.logger.error(f"Error detecting situations: {str(e)}")
            # Use the stored request_id in case request object is invalid
            req_id = getattr(request, 'request_id', original_request_id) if hasattr(request, 'request_id') else original_request_id
            return SituationDetectionResponse(
                request_id=req_id,
                status="error",
                message=f"Error detecting situations: {str(e)}",
                situations=[]
            )
    
    async def process_nl_query(
        self,
        request: NLQueryRequest = None, **kwargs
    ) -> NLQueryResponse:
        """Handle both direct request object and dictionary with request key"""
        # Store original request_id for response
        original_request_id = str(uuid.uuid4())
        
        # Handle case where request is passed as a keyword argument
        if request is None and 'request' in kwargs:
            request = kwargs['request']
            
        # Convert dict to NLQueryRequest if needed
        if isinstance(request, dict):
            # Save the request_id if present
            if 'request_id' in request:
                original_request_id = request.get('request_id')
                
            # Ensure request has all required fields
            if 'request_id' not in request:
                request['request_id'] = original_request_id
            if 'timestamp' not in request:
                request['timestamp'] = datetime.now()
            if 'query' not in request:
                self.logger.error("Missing query in request")
                return NLQueryResponse(
                    request_id=original_request_id,
                    status="error",
                    answer="Missing query in request",
                    kpi_values=[],
                    sql_query=""
                )
            if 'principal_context' not in request:
                self.logger.warning("Missing principal_context in request, using default")
                
            try:
                request = NLQueryRequest(**request)
            except Exception as e:
                self.logger.error(f"Error converting request dict to NLQueryRequest: {str(e)}")
                return NLQueryResponse(
                    request_id=original_request_id,
                    status="error",
                    answer=f"Invalid request format: {str(e)}",
                    kpi_values=[],
                    sql_query=""
                )
        """
        Process a natural language query about KPIs or situations.
        
        Args:
            request: NLQueryRequest containing the query and principal context
            
        Returns:
            NLQueryResponse containing the answer, KPI values, and SQL query
        """
        try:
            logger.info(f"Processing NL query: {request.query}")
            
            # Extract business terms from the query using Data Governance Agent
            # This is a simple extraction for MVP - in production would use NLP Agent
            query_terms = [term.strip() for term in request.query.split() if len(term.strip()) > 3]
            
            if self.data_governance_agent:
                try:
                    # Import the request/response models
                    from src.agents.models.data_governance_models import BusinessTermTranslationRequest
                    
                    # Translate business terms to technical attribute names
                    translation_result = await self.data_governance_agent.translate_business_terms(
                        BusinessTermTranslationRequest(
                            business_terms=query_terms,
                            system="duckdb",
                            context={
                                "principal_context": request.principal_context.model_dump() if request.principal_context else {},
                                "business_processes": getattr(request, 'business_processes', None) or (
                                    request.principal_context.business_processes if request.principal_context else []
                                )
                            }
                        )
                    )
                    # Persist for later checks in this method
                    self.translation_result = translation_result
                    
                    # Check for unmapped terms that require human input
                    if translation_result.human_action_required:
                        logger.warning(f"Unmapped business terms: {translation_result.unmapped_terms}")
                        
                        # For MVP, we continue with what we have rather than failing
                        # In production, this would return a HITL response
                        if not translation_result.resolved_terms:
                            logger.warning("No business terms could be mapped, falling back to direct KPI matching")
                except Exception as e:
                    logger.warning(f"Error translating business terms: {str(e)}")
            
            # Extract KPI mentions from the query
            query_lower = request.query.lower()
            kpi_values = []
            
            # Try to map KPIs using Data Governance Agent first
            mapped_kpis = []
            if self.data_governance_agent:
                try:
                    # Import the request model
                    from src.agents.models.data_governance_models import KPIDataProductMappingRequest
                    
                    # Get potential KPI names from business terms and direct query text
                    potential_kpi_names = []
                    
                    # Add translated business terms if available
                    if hasattr(self, 'translation_result') and getattr(self.translation_result, 'resolved_terms', None):
                        potential_kpi_names.extend(list(self.translation_result.resolved_terms.values()))
                    
                    # Add direct matches from query
                    for kpi_name in self.kpi_registry.keys():
                        if kpi_name.lower() in query_lower:
                            potential_kpi_names.append(kpi_name)
                    
                    # Deduplicate
                    potential_kpi_names = list(set(potential_kpi_names))
                    
                    if potential_kpi_names:
                        # Use Data Governance Agent to map KPIs to data products with business process context
                        mapping_response = await self.data_governance_agent.map_kpis_to_data_products(
                            KPIDataProductMappingRequest(
                                kpi_names=potential_kpi_names,
                                context={
                                    "principal_id": request.principal_context.principal_id if request.principal_context else "",
                                    "business_processes": getattr(request, 'business_processes', None) or (
                                        request.principal_context.business_processes if request.principal_context else []
                                    )
                                }
                            )
                        )
                        
                        # Process mapped KPIs
                        for mapping in mapping_response.mappings:
                            mapped_kpis.append(mapping.kpi_name)
                            
                        logger.info(f"Data Governance Agent mapped {len(mapping_response.mappings)} KPIs")
                except Exception as e:
                    logger.warning(f"Error using Data Governance Agent for KPI mapping: {e}")
            
            # Process KPIs - first from Data Governance Agent mappings, then fall back to direct matching
            processed_kpis = set()
            
            # First process mapped KPIs from Data Governance Agent
            for kpi_name in mapped_kpis:
                if kpi_name not in processed_kpis:
                    try:
                        # Check if we have this KPI in our registry
                        if kpi_name in self.kpi_registry:
                            kpi_def = self.kpi_registry[kpi_name]
                        else:
                            # Try to get KPI definition from Data Governance Agent
                            try:
                                # Get the mapping for this KPI
                                for mapping in mapping_response.mappings:
                                    if mapping.kpi_name == kpi_name:
                                        # Create a temporary KPI definition from the mapping
                                        kpi_def = KPIDefinition(
                                            name=mapping.kpi_name,
                                            description=mapping.metadata.get("description", "") if mapping.metadata else "",
                                            data_product_id=mapping.data_product_id,
                                            calculation="",  # Will be generated by Data Product Agent
                                            view_name=mapping.technical_name,
                                            thresholds=mapping.metadata.get("thresholds", {}) if mapping.metadata else {},
                                            dimensions=mapping.metadata.get("dimensions", []) if mapping.metadata else [],
                                            business_processes=mapping.metadata.get("business_processes", []) if mapping.metadata else [],
                                            positive_trend_is_good=mapping.metadata.get("positive_trend_is_good", True) if mapping.metadata else True
                                        )
                                        break
                            except Exception as e:
                                logger.warning(f"Error creating KPI definition from mapping: {e}")
                                kpi_def = None
                                
                        # Get KPI value if we have a definition
                        if kpi_def:
                            kpi_value = await self._get_kpi_value(
                                kpi_def,
                                request.timeframe if request.timeframe else TimeFrame.CURRENT_QUARTER,  # Default timeframe
                                request.comparison_type if request.comparison_type else ComparisonType.QUARTER_OVER_QUARTER,  # Default comparison
                                request.filters if request.filters else {},
                                request.principal_context
                            )
                            if kpi_value:
                                kpi_values.append(kpi_value)
                                processed_kpis.add(kpi_name)
                    except Exception as kpi_error:
                        logger.warning(f"Error retrieving KPI {kpi_name}: {str(kpi_error)}")
                        # Continue with other KPIs
                        
            # Then fall back to direct KPI name matching in the query for any KPIs not already processed
            for kpi_name in self.kpi_registry.keys():
                if kpi_name.lower() in query_lower and kpi_name not in processed_kpis:
                    try:
                        kpi_def = self.kpi_registry[kpi_name]
                        kpi_value = await self._get_kpi_value(
                            kpi_def,
                            request.timeframe if request.timeframe else TimeFrame.CURRENT_QUARTER,  # Default timeframe
                            request.comparison_type if request.comparison_type else ComparisonType.QUARTER_OVER_QUARTER,  # Default comparison
                            request.filters if request.filters else {},
                            request.principal_context
                        )
                        if kpi_value:
                            kpi_values.append(kpi_value)
                            processed_kpis.add(kpi_name)
                    except Exception as kpi_error:
                        logger.warning(f"Error retrieving KPI {kpi_name}: {str(kpi_error)}")
                        # Continue with other KPIs
            
            # For bullet tracer MVP, if no KPIs are found in query, get principal's top KPI
            if not kpi_values and request.principal_context:
                try:
                    # Get KPIs relevant to principal
                    relevant_kpis = self._get_relevant_kpis(
                        request.principal_context,
                        None  # No business process filter for NL queries
                    )
                    
                    # Get first KPI
                    if relevant_kpis:
                        first_kpi_name = next(iter(relevant_kpis.keys()))
                        # Use KPI definition (not name) when fetching KPI value
                        first_kpi_def = relevant_kpis[first_kpi_name]
                        kpi_value = await self._get_kpi_value(
                            first_kpi_def,
                            request.timeframe if request.timeframe else TimeFrame.CURRENT_QUARTER,
                            request.comparison_type if request.comparison_type else ComparisonType.QUARTER_OVER_QUARTER,
                            request.filters if request.filters else {}
                        )
                        if kpi_value:
                            kpi_values.append(kpi_value)
                except Exception as e:
                    logger.warning(f"Error getting default KPI: {str(e)}")
            
            # Generate SQL for the query using Data Product Agent
            sql_query = await self._generate_sql_for_query(request.query, kpi_values)
            # Fallback: if NL->SQL did not return SQL but we have a KPI, generate deterministic SQL
            if (not sql_query) and kpi_values and self.data_product_agent:
                try:
                    first_kpi_name = getattr(kpi_values[0], 'kpi_name', None)
                    kpi_def = None
                    # Try to resolve KPI definition from registry
                    if first_kpi_name and isinstance(self.kpi_registry, dict):
                        kpi_def = self.kpi_registry.get(first_kpi_name)
                    # Merge principal default filters with explicit request filters
                    merged_filters = {}
                    try:
                        if getattr(request.principal_context, 'default_filters', None):
                            df = request.principal_context.default_filters
                            if isinstance(df, dict):
                                merged_filters.update(df)
                    except Exception:
                        pass
                    try:
                        if isinstance(request.filters, dict):
                            merged_filters.update(request.filters)
                    except Exception:
                        pass

                    # Minimal NL intent extraction for Top/Bottom N breakdowns (e.g., "top 5 profit centers")
                    # Prefer simple, robust patterns for MVP
                    def _parse_topn_and_dims(q: str):
                        try:
                            import re as _re
                            ql = (q or "").strip().lower()
                            limit_type = None
                            limit_n = None
                            # Numeric N (e.g., "top 5", "bottom 10")
                            m_top = _re.search(r"\btop\s+(\d+)\b", ql)
                            m_bot = _re.search(r"\bbottom\s+(\d+)\b", ql)
                            if m_top:
                                limit_type = 'top'
                                limit_n = int(m_top.group(1))
                            elif m_bot:
                                limit_type = 'bottom'
                                limit_n = int(m_bot.group(1))
                            else:
                                # Spelled-out small numbers (e.g., "top five") and default when just 'top'/'bottom'
                                words_map = {
                                    'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
                                    'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10, 'twelve': 12
                                }
                                m_word = _re.search(r"\b(top|bottom)\s+(one|two|three|four|five|six|seven|eight|nine|ten|twelve)\b", ql)
                                if m_word:
                                    limit_type = m_word.group(1)
                                    limit_n = words_map.get(m_word.group(2))
                                else:
                                    if _re.search(r"\btop\b", ql):
                                        limit_type, limit_n = 'top', 10
                                    elif _re.search(r"\bbottom\b", ql):
                                        limit_type, limit_n = 'bottom', 10
                            # Dimension detection (extendable): map common phrases to canonical business terms
                            # Prefer more specific patterns before generic ones (e.g., Product Type before Product)
                            dim_map = [
                                (r"\bproduct\s*type(s)?\b|\bproduct\s*category(ies)?\b|\bcategory(ies)?\b", "Product Type"),
                                (r"\bproduct(s)?\b", "Product"),
                                (r"\bprofit\s*center(s)?\b", "Profit Center"),
                                (r"\bcustomer\s*type(s)?\b", "Customer Type"),
                                (r"\bregion(s)?\b", "Region"),
                                (r"\bcountr(y|ies)\b", "Country"),
                                (r"\bchannel(s)?\b", "Channel"),
                            ]
                            dims = []
                            for pat, canon in dim_map:
                                if _re.search(pat, ql):
                                    dims.append(canon)
                            return limit_type, limit_n, dims
                        except Exception:
                            return None, None, []

                    # If the question asks for a Top/Bottom breakdown on a known dimension, request grouped SQL
                    breakdown = False
                    override_group_by = None
                    topn_spec = None
                    lt, ln, dims = _parse_topn_and_dims(request.query)
                    # Keep SA neutral: do not reorder detected dimensions post hoc; dim_map order already prefers specificity
                    # Detect growth intent (fastest growing vs previous period)
                    try:
                        import re as _re
                        ql = (request.query or "").strip().lower()
                        growth_metric = bool(_re.search(r"\b(fastest\s+growing|growth|increase|vs\s+previous|versus\s+previous|delta|variance)\b", ql))
                    except Exception:
                        growth_metric = False

                    if dims:
                        breakdown = True
                        override_group_by = dims[:1]  # Single-dimension breakdown for MVP
                        # Build TopN spec; if growth intent but no N specified, default to 5
                        if not (lt and isinstance(ln, int) and ln > 0) and growth_metric:
                            lt, ln = 'top', 5
                        if lt and isinstance(ln, int) and ln > 0:
                            topn_spec = {"limit_type": lt, "limit_n": ln}
                            if growth_metric:
                                topn_spec["metric"] = "delta_prev"

                    if kpi_def:
                        dp_resp_fallback = await self.data_product_agent.generate_sql_for_kpi(
                            kpi_definition=kpi_def,
                            timeframe=request.timeframe if request.timeframe else TimeFrame.CURRENT_QUARTER,
                            filters=merged_filters,
                            breakdown=breakdown,
                            override_group_by=override_group_by,
                            topn=topn_spec,
                        )
                        if isinstance(dp_resp_fallback, dict) and dp_resp_fallback.get('success') and dp_resp_fallback.get('sql'):
                            sql_query = dp_resp_fallback['sql']
                            try:
                                logger.info("[SA] Using KPI SQL fallback for NL response display (breakdown=%s, group_by=%s, topn=%s)", breakdown, override_group_by, topn_spec)
                            except Exception:
                                pass
                except Exception as _fallback_err:
                    try:
                        logger.warning(f"KPI SQL fallback failed: {_fallback_err}")
                    except Exception:
                        pass
            
            # Check if we need HITL escalation due to unmapped terms
            human_action_required = False
            human_action_type = None
            human_action_context = None
            
            # If we have unmapped terms from the Data Governance Agent, provide HITL context
            if self.data_governance_agent and hasattr(self, 'translation_result') and \
               self.translation_result.human_action_required and not kpi_values:
                human_action_required = True
                human_action_type = "clarification"
                human_action_context = {
                    "unmapped_terms": self.translation_result.unmapped_terms,
                    "message": "I need clarification on these business terms to answer your query."
                }
                answer = "I need additional clarification on some terms in your query."
            else:
                # Generate answer based on KPI values and query
                answer = self._generate_answer_for_query(request.query, kpi_values)
            
            return NLQueryResponse(
                request_id=request.request_id,
                status="success",
                answer=answer,
                kpi_values=kpi_values,
                sql_query=sql_query,
                human_action_required=human_action_required,
                human_action_type=human_action_type,
                human_action_context=human_action_context
            )
            
        except Exception as e:
            logger.error(f"Error processing NL query: {str(e)}")
            # Use the stored request_id in case request object is invalid
            req_id = getattr(request, 'request_id', original_request_id) if hasattr(request, 'request_id') else original_request_id
            return NLQueryResponse(
                request_id=req_id,
                status="error",
                message=f"Error processing query: {str(e)}",
                answer="I'm sorry, I couldn't process your query due to an error.",
                kpi_values=[]
            )
    
    async def process_hitl_feedback(
        self,
        request: HITLRequest
    ) -> HITLResponse:
        """
        Process human-in-the-loop feedback for a situation.
        
        Args:
            request: HITLRequest containing the decision and any modifications
            
        Returns:
            HITLResponse with the updated situation if applicable
        """
        # For MVP, we'll just acknowledge the feedback
        # In production, this would update the situation and potentially trigger actions
        
        return HITLResponse(
            request_id=request.request_id,
            status="success",
            message=f"Processed {request.decision} feedback"
        )
    
    def _load_kpis_from_contract(self):
        """
        Load KPIs directly from the contract file as a fallback when registry is unavailable.
        Creates internal KPIDefinition objects from the contract's KPI specifications.
        """
        try:
            logger.info(f"Loading KPIs from contract file: {self.contract_path}")
            
            # Log the absolute path to contract file
            abs_contract_path = os.path.abspath(self.contract_path)
            logger.info(f"Loading KPIs from contract file (absolute path): {abs_contract_path}")
            
            # Check if contract file exists
            if not os.path.exists(abs_contract_path):
                logger.error(f"Contract file not found: {abs_contract_path}")
                return
                
            logger.info(f"Contract file exists, attempting to parse YAML")
            try:
                with open(abs_contract_path, 'r') as f:
                    contract_data = yaml.safe_load(f)
                    logger.info(f"Contract file parsed successfully: {list(contract_data.keys()) if contract_data else 'empty'}") 
            except Exception as yaml_err:
                logger.error(f"Error parsing contract file: {str(yaml_err)}")
                return
                
            # Extract KPIs from contract
            kpis = contract_data.get('kpis', [])
            logger.info(f"Found {len(kpis)} KPIs in contract file")
            
            # Log the first KPI to see its structure
            if kpis:
                logger.info(f"First KPI structure: {kpis[0].keys() if isinstance(kpis[0], dict) else 'not a dict'}")
            else:
                logger.warning("Contract file does not contain any KPIs under 'kpis' key")
            
            # Convert contract KPIs to internal KPI definitions
            for kpi_data in kpis:
                try:
                    # Create a basic KPI definition from contract data
                    kpi_name = kpi_data.get('name')
                    if not kpi_name:
                        continue
                        
                    # Map contract KPI fields to internal KPI definition
                    thresholds = kpi_data.get('thresholds')
                    thresholds_dict = thresholds if isinstance(thresholds, dict) else None

                    # Prefer explicit calculation; if missing, synthesize from aggregation/base_column/filter_type
                    calc_value = kpi_data.get('calculation')
                    
                    # Initialize filters dictionary
                    filters_dict = {}
                    
                    # 1. Try top-level 'filters'
                    if kpi_data.get('filters') and isinstance(kpi_data.get('filters'), dict):
                        filters_dict.update(kpi_data.get('filters'))
                        
                    # 2. Try nested in 'calculation' if it's a dict
                    if isinstance(calc_value, dict) and 'filters' in calc_value:
                        if isinstance(calc_value['filters'], dict):
                            filters_dict.update(calc_value['filters'])
                            
                    # 3. Try filter_type/filter_value pair (Legacy/Simple format)
                    # This overrides previous keys if there's a conflict, which is desired for simple definitions
                    filter_type = kpi_data.get('filter_type')
                    filter_value = kpi_data.get('filter_value')
                    if filter_type and filter_value:
                        key = filter_type
                        # Normalize common column names
                        if str(filter_type).lower() == 'account_hierarchy_desc':
                            key = "Account Hierarchy Desc"
                        filters_dict[key] = filter_value

                    if not calc_value:
                        agg = kpi_data.get('aggregation')
                        base_col = kpi_data.get('base_column')
                        if agg and base_col:
                            # Normalize base column quoting to match view aliases
                            expr_col = base_col
                            if isinstance(expr_col, str) and not expr_col.startswith('[') and ' ' in expr_col:
                                expr_col = f"[{expr_col}]"
                            calc_expr = f"{agg}({expr_col})"
                            # Inline filter support for common pattern account_hierarchy_desc
                            # (We still patch the string calculation for completeness, though filters_dict is what matters for SQL gen)
                            if filter_type and filter_value:
                                if str(filter_type).lower() == 'account_hierarchy_desc':
                                    calc_value = f"{calc_expr} WHERE \"Account Hierarchy Desc\" = '{filter_value}'"
                                else:
                                    # Generic inline filter using provided type as column name
                                    calc_value = f"{calc_expr} WHERE {filter_type} = '{filter_value}'"
                            else:
                                calc_value = calc_expr
                        # else leave as None
                    
                    # Extract view name from join_tables if available
                    view_name = None
                    join_tables = kpi_data.get('join_tables')
                    if join_tables and isinstance(join_tables, list) and len(join_tables) > 0:
                        view_name = join_tables[0]

                    kpi_def = KPIDefinition(
                        name=kpi_name,
                        description=kpi_data.get('description', ''),
                        data_product_id=kpi_data.get('data_product_id') or contract_data.get('data_product', ''),
                        calculation=calc_value,
                        diagnostic_questions=kpi_data.get('diagnostic_questions'),
                        business_processes=kpi_data.get('business_terms', []),
                        thresholds=thresholds_dict,
                        view_name=view_name,
                        filters=filters_dict  # Pass the extracted filters
                    )
                    
                    # Add to registry only if not already present (Registry takes precedence)
                    if kpi_name not in self.kpi_registry:
                        self.kpi_registry[kpi_name] = kpi_def
                        logger.info(f"Added KPI from contract: {kpi_name}")
                    else:
                        logger.debug(f"Skipping KPI from contract (already in registry): {kpi_name}")
                    
                except Exception as kpi_err:
                    logger.warning(f"Error creating KPI definition for {kpi_data.get('name', 'unknown')}: {str(kpi_err)}")
                    
            logger.info(f"Loaded {len(self.kpi_registry)} KPIs from contract file")
            
        except Exception as e:
            logger.error(f"Error loading KPIs from contract: {str(e)}")
            # Last resort - create empty registry
            self.kpi_registry = {}
    
    def _kpi_matches_domains(self, kpi: KPI, target_domains: List[str]) -> bool:
        """
        Check if a KPI is relevant to any of the specified target domains.
        
        This method works with the canonical KPI model structure and handles
        different ways domains might be specified.
        
        Args:
            kpi: The canonical KPI model instance
            target_domains: List of domain names to match against
            
        Returns:
            True if the KPI matches any of the target domains, False otherwise
        """
        # Dict-based KPIs (used in tests/mocks)
        if isinstance(kpi, dict):
            domain = kpi.get('domain')
            if isinstance(domain, str):
                for d in target_domains:
                    if d.lower() == domain.lower():
                        return True
            # business_process_ids (canonical)
            for bp_id in (kpi.get('business_process_ids') or []):
                for d in target_domains:
                    if isinstance(bp_id, str) and bp_id.lower().startswith(d.lower() + '_'):
                        return True
            # business_processes (display strings)
            for process in (kpi.get('business_processes') or []):
                for d in target_domains:
                    if isinstance(process, str) and process.lower().startswith(f"{d.lower()}:"):
                        return True
            # tags
            for tag in (kpi.get('tags') or []):
                for d in target_domains:
                    if isinstance(tag, str) and d.lower() in tag.lower():
                        return True
            # name heuristic for Finance
            if 'Finance' in target_domains:
                name = kpi.get('name')
                if isinstance(name, str) and 'finance' in name.lower():
                    return True
            return False

        # First check the canonical 'domain' attribute
        if hasattr(kpi, 'domain') and isinstance(kpi.domain, str):
            # Direct domain match
            for domain in target_domains:
                if domain.lower() == kpi.domain.lower():
                    return True
                    
        # Check business_process_ids (canonical model)
        if hasattr(kpi, 'business_process_ids') and kpi.business_process_ids:
            for bp_id in kpi.business_process_ids:
                # Check if business process ID starts with any target domain
                for domain in target_domains:
                    if bp_id.lower().startswith(domain.lower() + '_'):
                        return True
        
        # Check business_processes (backward compatibility)
        if hasattr(kpi, 'business_processes') and kpi.business_processes:
            for process in kpi.business_processes:
                for domain in target_domains:
                    # Check for "Domain: Process" format
                    if isinstance(process, str) and process.lower().startswith(f"{domain.lower()}:"):
                        return True
        
        # Check tags for domain references
        if hasattr(kpi, 'tags') and kpi.tags:
            for tag in kpi.tags:
                for domain in target_domains:
                    if domain.lower() in tag.lower():
                        return True
        
        # For MVP, include Finance KPIs based on name if Finance is a target domain
        if 'Finance' in target_domains and hasattr(kpi, 'name'):
            if 'finance' in kpi.name.lower():
                return True
                
        return False
            
    def _convert_to_kpi_definition(self, kpi: KPI) -> Optional[KPIDefinition]:
        """
        Convert from canonical KPI model to our internal KPIDefinition model.
        
        Args:
            kpi: The canonical KPI model instance from the registry
            
        Returns:
            KPIDefinition instance or None if conversion fails
        """
        # Handle dict-shaped KPIs used by tests/mocks
        if isinstance(kpi, dict):
            name = kpi.get('name')
            if not name:
                return None
            description = kpi.get('description', '')
            unit = kpi.get('unit')
            dp_id = kpi.get('data_product_id') or "FI_Star_Schema"
            business_processes = kpi.get('business_processes') or []
            dimensions = kpi.get('dimensions') or []
            calc = kpi.get('calculation')
            # Optional thresholds mapping
            thresholds = None
            try:
                th = kpi.get('thresholds') or {}
                if isinstance(th, dict):
                    thresholds = {}
                    if 'warning' in th and isinstance(th['warning'], dict):
                        thresholds[SituationSeverity.HIGH] = th['warning'].get('value')
                    if 'critical' in th and isinstance(th['critical'], dict):
                        thresholds[SituationSeverity.CRITICAL] = th['critical'].get('value')
            except Exception:
                thresholds = None
            return KPIDefinition(
                name=name,
                description=description,
                unit=unit,
                calculation=calc,
                thresholds=thresholds,
                dimensions=dimensions,
                business_processes=business_processes,
                data_product_id=dp_id,
                positive_trend_is_good=True
            )

        try:
            # Initialize variables with safe defaults
            dimensions = []
            business_processes = []
            thresholds = {}
            positive_trend = True
            diagnostic_questions = []
            kpi_dp_id = "FI_Star_Schema"  # Default
            sql_query = ""
            unit = getattr(kpi, 'unit', None)  # Extract unit
            
            # Extract dimensions with safe access
            try:
                if hasattr(kpi, 'dimensions') and kpi.dimensions:
                    # Convert KPIDimension objects to dimension names
                    for dimension in kpi.dimensions:
                        if hasattr(dimension, 'name'):
                            dimensions.append(dimension.name)
                        elif isinstance(dimension, str):
                            dimensions.append(dimension)
            except Exception as e:
                logger.warning(f"Error accessing dimensions for KPI {kpi.name if hasattr(kpi, 'name') else 'unknown'}: {str(e)}")
                
            # Extract business processes with safe access
            try:
                if hasattr(kpi, 'business_processes') and kpi.business_processes:
                    business_processes = kpi.business_processes
                    
                # Also check business_process_ids (canonical model)
                if hasattr(kpi, 'business_process_ids') and kpi.business_process_ids:
                    for bp_id in kpi.business_process_ids:
                        # Format: domain_process_name
                        parts = bp_id.split('_', 1)
                        if len(parts) > 1:
                            domain, process = parts
                            # Format for display: "Domain: Process Name"
                            formatted_bp = f"{domain.capitalize()}: {process.replace('_', ' ').title()}"
                            business_processes.append(formatted_bp)
            except Exception as e:
                logger.warning(f"Error accessing business_processes for KPI {kpi.name if hasattr(kpi, 'name') else 'unknown'}: {str(e)}")
                
            # Extract thresholds with safe access
            try:
                if hasattr(kpi, 'thresholds') and kpi.thresholds:
                    for threshold in kpi.thresholds:
                        if hasattr(threshold, 'severity') and hasattr(threshold, 'value'):
                            # Map severity string to enum
                            severity_str = threshold.severity.lower()
                            if severity_str == 'warning':
                                thresholds[SituationSeverity.HIGH] = threshold.value
                            elif severity_str == 'critical':
                                thresholds[SituationSeverity.CRITICAL] = threshold.value
                                
                            # Store inverse logic flag if available
                            if hasattr(threshold, 'inverse_logic') and threshold.inverse_logic:
                                # Store in a special key for reference
                                thresholds['_inverse_logic'] = threshold.inverse_logic
            except Exception as e:
                logger.warning(f"Error accessing thresholds for KPI {kpi.name if hasattr(kpi, 'name') else 'unknown'}: {str(e)}")
            
            # Extract filters with safe access
            filters = {}
            try:
                if hasattr(kpi, 'filters') and kpi.filters:
                    filters = kpi.filters
            except Exception as e:
                logger.warning(f"Error accessing filters for KPI {kpi.name if hasattr(kpi, 'name') else 'unknown'}: {str(e)}")
                            
            # Determine if positive trend is good with safe access
            try:
                if hasattr(kpi, 'positive_trend_is_good'):
                    positive_trend = kpi.positive_trend_is_good
                elif hasattr(kpi, 'metadata') and isinstance(kpi.metadata, dict):
                    if 'positive_trend_is_good' in kpi.metadata:
                        # Parse boolean value from metadata
                        value = kpi.metadata['positive_trend_is_good']
                        if isinstance(value, bool):
                            positive_trend = value
                        elif isinstance(value, str):
                            positive_trend = value.lower() == 'true'
                elif hasattr(kpi, 'name'):
                    # Infer from name for common financial metrics
                    kpi_name_lower = kpi.name.lower()
                    if ('cost' in kpi_name_lower or 'expense' in kpi_name_lower or 
                        'debt' in kpi_name_lower or 'deficit' in kpi_name_lower):
                        positive_trend = False
            except Exception as e:
                logger.warning(f"Error determining positive_trend for KPI {kpi.name if hasattr(kpi, 'name') else 'unknown'}: {str(e)}")
                    
            # Get SQL query with safe access
            try:
                if hasattr(kpi, 'sql_query') and kpi.sql_query:
                    sql_query = kpi.sql_query
            except Exception as e:
                logger.warning(f"Error accessing sql_query for KPI {kpi.name if hasattr(kpi, 'name') else 'unknown'}: {str(e)}")
                
            # Get diagnostic questions with safe access
            try:
                if hasattr(kpi, 'diagnostic_questions') and kpi.diagnostic_questions:
                    diagnostic_questions = kpi.diagnostic_questions
                elif hasattr(kpi, 'metadata') and isinstance(kpi.metadata, dict):
                    if 'diagnostic_questions' in kpi.metadata:
                        questions = kpi.metadata['diagnostic_questions']
                        if isinstance(questions, list):
                            diagnostic_questions = questions
                        elif isinstance(questions, str):
                            # Split by newlines or semicolons if it's a string
                            diagnostic_questions = [q.strip() for q in re.split(r'[\n;]', questions) if q.strip()]
            except Exception as e:
                logger.warning(f"Error accessing diagnostic_questions for KPI {kpi.name if hasattr(kpi, 'name') else 'unknown'}: {str(e)}")
                
            # Get data product ID with safe access
            try:
                if hasattr(kpi, 'data_product_id') and kpi.data_product_id:
                    kpi_dp_id = kpi.data_product_id
            except Exception as e:
                logger.warning(f"Error accessing data_product_id for KPI {kpi.name if hasattr(kpi, 'name') else 'unknown'}: {str(e)}")
            
            # Get filters with safe access
            kpi_filters = {}
            try:
                if hasattr(kpi, 'filters') and kpi.filters:
                    kpi_filters = kpi.filters
            except Exception as e:
                logger.warning(f"Error accessing filters for KPI {kpi.name if hasattr(kpi, 'name') else 'unknown'}: {str(e)}")

            # Create KPI definition with all mapped fields
            # First safely get all required attributes
            kpi_name = kpi.name if hasattr(kpi, 'name') else "unknown"
            kpi_desc = kpi.description if hasattr(kpi, 'description') and kpi.description else ""
            kpi_unit = kpi.unit if hasattr(kpi, 'unit') and kpi.unit else ""

            # Propagate registry metadata (including line/altitude) when present
            kpi_metadata = {}
            try:
                if hasattr(kpi, 'metadata') and isinstance(kpi.metadata, dict):
                    kpi_metadata = dict(kpi.metadata)
            except Exception:
                kpi_metadata = {}

            kpi_def = KPIDefinition(
                name=kpi_name,
                description=kpi_desc,
                unit=kpi_unit,
                calculation=sql_query,
                filters=kpi_filters,
                thresholds=thresholds,
                dimensions=dimensions,
                business_processes=business_processes,
                data_product_id=kpi_dp_id,
                positive_trend_is_good=positive_trend,
                diagnostic_questions=diagnostic_questions,
                metadata=kpi_metadata or None,
            )
            # Map registry KPIThreshold (comparison-based) into variance thresholds metadata for downstream evaluation
            try:
                if hasattr(kpi, 'thresholds') and kpi.thresholds:
                    variance_thresholds = {}
                    for t in kpi.thresholds:
                        try:
                            comp = getattr(t, 'comparison_type', None)
                            comp_val = comp.value if hasattr(comp, 'value') else (str(comp) if comp is not None else None)
                            if not comp_val:
                                continue
                            ct = str(comp_val).strip().lower()
                            # Normalize keys commonly used in registry
                            if ct in ("qoq", "quarter_over_quarter", "quarter-over-quarter"):
                                key = "qoq"
                            elif ct in ("yoy", "year_over_year", "year-over-year"):
                                key = "yoy"
                            elif ct in ("mom", "month_over_month", "month-over-month"):
                                key = "mom"
                            elif "budget" in ct:
                                key = "budget"
                            elif "target" in ct:
                                key = "target"
                            else:
                                key = ct
                            entry = {}
                            gv = getattr(t, 'green_threshold', None)
                            yv = getattr(t, 'yellow_threshold', None)
                            rv = getattr(t, 'red_threshold', None)
                            inv = getattr(t, 'inverse_logic', False)
                            if gv is not None:
                                entry['green'] = float(gv)
                            if yv is not None:
                                entry['yellow'] = float(yv)
                            if rv is not None:
                                entry['red'] = float(rv)
                            entry['inverse_logic'] = bool(inv)
                            variance_thresholds[key] = entry
                        except Exception:
                            continue
                    if variance_thresholds:
                        if not getattr(kpi_def, 'metadata', None):
                            kpi_def.metadata = {}
                        kpi_def.metadata['variance_thresholds'] = variance_thresholds
            except Exception as _vt_err:
                logger.warning(f"Error mapping variance thresholds for KPI {kpi_name}: {_vt_err}")
            # Inject contract-level filters and metadata (GL accounts, timeframe hints, base column, etc.)
            contract = getattr(self, 'contract', None)
            if isinstance(contract, dict):
                kpis_data = contract.get('kpis', []) or []
                contract_views = contract.get('views') or []
                for kpi_entry in kpis_data:
                    if not isinstance(kpi_entry, dict):
                        continue
                    entry_name = kpi_entry.get('name')
                    if not isinstance(entry_name, str):
                        continue
                    if entry_name.strip().lower() != kpi_name.strip().lower():
                        continue
                    # Found matching KPI in contract
                    calc = kpi_entry.get('calculation')
                    if isinstance(calc, dict):
                        # Merge static filters (e.g., GL account restrictions)
                        if isinstance(calc.get('filters'), dict):
                            kpi_def.filters = {
                                **(kpi_def.filters or {}),
                                **(calc.get('filters') or {})
                            }
                        # Try to derive base_column from query_template if not explicitly set later
                        qt = calc.get('query_template') or calc.get('template')
                        if (not getattr(kpi_def, 'base_column', None)) and isinstance(qt, str):
                            # Extract first quoted or bracketed column
                            m = re.search(r'"([^\"]+)"', qt)
                            if m and m.group(1):
                                kpi_def.base_column = m.group(1)
                            else:
                                m2 = re.search(r'\[([^\]]+)\]', qt)
                                if m2 and m2.group(1):
                                    kpi_def.base_column = m2.group(1)
                    # Explicit base_column at top level takes precedence
                    if isinstance(kpi_entry.get('base_column'), str) and kpi_entry.get('base_column').strip():
                        kpi_def.base_column = kpi_entry.get('base_column')

                    # Simple mapping for grouping/ordering/limit when present
                    if isinstance(kpi_entry.get('partition_by'), list):
                        kpi_def.group_by = kpi_entry.get('partition_by')
                    if isinstance(kpi_entry.get('order_by'), list):
                        kpi_def.order_by = kpi_entry.get('order_by')
                    if kpi_entry.get('top_n') is not None:
                        try:
                            kpi_def.limit = int(kpi_entry.get('top_n'))
                        except Exception:
                            pass

                    # View resolution hint from contract (will still be resolved by DPA/Governance)
                    join_tables = kpi_entry.get('join_tables')
                    if isinstance(join_tables, list) and join_tables:
                        jt0 = join_tables[0]
                        if isinstance(jt0, str) and jt0.strip():
                            kpi_def.view_name = jt0.strip()
                    elif isinstance(contract_views, list) and contract_views:
                        v0 = contract_views[0]
                        if isinstance(v0, dict) and isinstance(v0.get('name'), str):
                            kpi_def.view_name = v0.get('name')

                    # Timeframe hints (date column)
                    # In FI Star View, the canonical alias is "Transaction Date"
                    if not getattr(kpi_def, 'date_column', None):
                        # Allow override via contract if present
                        if isinstance(kpi_entry.get('date_column'), str) and kpi_entry.get('date_column').strip():
                            kpi_def.date_column = kpi_entry.get('date_column').strip()
                        else:
                            kpi_def.date_column = "Transaction Date"

                    # Optional explicit time_filter injection if contract provides one later
                    if isinstance(kpi_entry.get('time_filter'), dict):
                        kpi_def.time_filter = kpi_entry.get('time_filter')

                    break  # done with matching entry

            return kpi_def
        except Exception as e:
            logger.error(f"Error converting KPI to KPIDefinition: {str(e)}")
            return None
    
    def _get_relevant_kpis(
        self,
        principal_context: PrincipalContext,
        business_processes: Optional[List[str]] = None
    ) -> Dict[str, KPIDefinition]:
        """Get KPIs relevant to the principal's business processes.
        
        This method now also applies *principal-specific KPI preferences* based on
        line (top_line/bottom_line) and altitude (strategic/operational), using
        metadata on both the principal profile and the KPIDefinition metadata.
        
        Args:
            principal_context: Principal context with business processes
            business_processes: Optional list of business processes to filter by
            
        Returns:
            Dictionary of relevant KPI definitions, ordered by principal
            preferences when metadata is available.
        """

        # Collect KPIs that match the requested business processes
        relevant_kpis: Dict[str, KPIDefinition] = {}

        # Use explicit business processes if provided, otherwise from principal context
        processes = business_processes if business_processes else (
            principal_context.business_processes if hasattr(principal_context, 'business_processes') else []
        )

        # Normalize selected processes: handle both display names (e.g., "Finance: Expense Management")
        # and canonical IDs (e.g., "finance_expense_management") for robust matching.
        def _to_bp_id(bp_str: str) -> str:
            try:
                s = (bp_str or "").strip().lower()
                # If already looks like an id (no colon and contains underscores), use as-is
                if ':' not in s and '_' in s:
                    return s
                # Drop domain prefix like "finance:" if present
                if ':' in s:
                    s = s.split(':', 1)[1]
                # Replace non-alphanum with spaces, then collapse to underscores
                import re as _re
                s = _re.sub(r"[^a-z0-9]+", " ", s).strip()
                s = "_".join([tok for tok in s.split() if tok])
                # Prepend domain when known from original input
                domain_prefix = None
                if isinstance(bp_str, str) and ':' in bp_str:
                    domain_prefix = bp_str.split(':', 1)[0].strip().lower()
                if domain_prefix:
                    return f"{domain_prefix}_{s}"
                # Fallback to finance domain for MVP if no domain present
                return f"finance_{s}" if not s.startswith("finance_") else s
            except Exception:
                return (bp_str or "").strip().lower()

        selected_bp_names = set(str(bp).strip() for bp in processes if isinstance(bp, str))
        selected_bp_ids = set(_to_bp_id(str(bp)) for bp in selected_bp_names)

        # For domain-level business processes, we just use the processes directly
        # since they're already at the domain level (e.g., "Finance")
        process_strings = []
        
        # Handle both domain-level strings and more specific business processes
        for bp in processes:
            # If it's already a domain name (e.g., "Finance"), use it directly
            if isinstance(bp, str) and ":" not in bp:
                process_strings.append(bp)
            # If it has a domain prefix (e.g., "Finance: Profitability Analysis"), use it as is
            elif isinstance(bp, str) and ":" in bp:
                process_strings.append(bp)
            # Handle enum values or objects
            elif hasattr(bp, 'value'):
                process_name = bp.value.replace('_', ' ').title()
                process_strings.append(process_name)
            else:
                # For any other string business processes
                process_strings.append(str(bp))
        
        # Filter KPIs by business process
        for kpi_name, kpi_def in self.kpi_registry.items():
            # For testing/development: Include KPIs without business processes defined
            # This allows tests to progress even when KPIs lack complete metadata
            if not kpi_def.business_processes:
                # During development/testing, include all KPIs without business processes
                # In production, we'd skip them with 'continue'
                relevant_kpis[kpi_name] = kpi_def
                continue
                
            # Check if KPI matches any of the relevant business processes
            for bp in process_strings:
                # Domain-level matching (e.g., "Finance" matches any "Finance: *" or "finance_*")
                if isinstance(bp, str) and ":" not in bp:
                    # Check if any KPI business process starts with this domain
                    for kpi_bp in kpi_def.business_processes:
                        if isinstance(kpi_bp, str) and (kpi_bp.startswith(f"{bp}:") or 
                                                      kpi_bp.lower().startswith(f"{bp.lower()}_")):
                            relevant_kpis[kpi_name] = kpi_def
                            break
                    # Also check business_process_ids if available
                    if hasattr(kpi_def, 'business_process_ids'):
                        for kpi_bp_id in kpi_def.business_process_ids:
                            if isinstance(kpi_bp_id, str) and kpi_bp_id.lower().startswith(f"{bp.lower()}_"):
                                relevant_kpis[kpi_name] = kpi_def
                                break
                # Exact matching for fully qualified business processes
                elif bp in kpi_def.business_processes:
                    relevant_kpis[kpi_name] = kpi_def
                    break
                # Also check business_process_ids for exact matches
                elif hasattr(kpi_def, 'business_process_ids') and bp in kpi_def.business_process_ids:
                    relevant_kpis[kpi_name] = kpi_def
                    break
                # Check for normalized business process IDs
                elif hasattr(kpi_def, 'business_process_ids') and _to_bp_id(bp) in kpi_def.business_process_ids:
                    relevant_kpis[kpi_name] = kpi_def
                    break

        # Apply principal KPI preferences (line/altitude) to ordering when possible
        ordered_kpis = self._apply_principal_kpi_preferences(principal_context, relevant_kpis)

        logger.debug(
            f"Found {len(ordered_kpis)} KPIs relevant to {len(processes)} business processes "
            f"for principal_id={getattr(principal_context, 'principal_id', None)}"
        )
        return ordered_kpis

    def _apply_principal_kpi_preferences(
        self,
        principal_context: PrincipalContext,
        kpis: Dict[str, KPIDefinition],
    ) -> Dict[str, KPIDefinition]:
        """Reorder KPIs based on principal KPI preferences and KPI metadata.

        Preferences are sourced from the principal profile registry via
        ``self.principal_profiles`` (loaded during ``connect``) using the
        principal's ``principal_id`` or ``role``. KPI semantics come from
        ``KPIDefinition.metadata`` (line/altitude) which were populated from
        the KPI registry.
        """

        if not kpis:
            return kpis

        # Default preferences if none are configured
        line_pref = "balanced"          # top_line_first | bottom_line_first | balanced
        altitude_pref = "balanced"      # strategic_first | operational_first | balanced

        # Look up the full principal profile (dict) by principal_id or role
        try:
            principal_id = getattr(principal_context, "principal_id", None)
            principal_role = getattr(principal_context, "role", None)
            profile = None

            if isinstance(self.principal_profiles, dict):
                # Direct key lookup first
                if principal_id and principal_id in self.principal_profiles:
                    profile = self.principal_profiles[principal_id]
                elif principal_role and principal_role in self.principal_profiles:
                    profile = self.principal_profiles[principal_role]
                # Fallback: search values by id/role fields
                if profile is None:
                    for value in self.principal_profiles.values():
                        try:
                            pdata = (
                                value.model_dump() if hasattr(value, "model_dump")
                                else (dict(value) if isinstance(value, dict) else getattr(value, "__dict__", {}))
                            )
                        except Exception:
                            pdata = {}
                        if not isinstance(pdata, dict):
                            continue
                        if principal_id and pdata.get("id") == principal_id:
                            profile = pdata
                            break
                        if principal_role and (
                            pdata.get("role") == principal_role
                            or pdata.get("name") == principal_role
                        ):
                            profile = pdata
                            break

            # Normalize profile to a dict and extract preferences from profile.metadata if present
            if profile:
                if not isinstance(profile, dict):
                    try:
                        if hasattr(profile, "model_dump"):
                            profile = profile.model_dump()
                        elif hasattr(profile, "__dict__"):
                            profile = dict(profile.__dict__)
                    except Exception:
                        profile = None

            if profile and isinstance(profile, dict):
                meta = profile.get("metadata") or {}
                if isinstance(meta, dict):
                    line_pref = meta.get("kpi_line_preference", line_pref) or line_pref
                    altitude_pref = meta.get("kpi_altitude_preference", altitude_pref) or altitude_pref
        except Exception:
            # If anything goes wrong, fall back to original ordering
            return kpis

        # If no preferences are set, keep original ordering
        if line_pref == "balanced" and altitude_pref == "balanced":
            return kpis

        def _score_kpi(defn: KPIDefinition) -> int:
            """Compute a simple preference score for a KPI based on metadata."""
            score = 0
            try:
                md = getattr(defn, "metadata", None) or {}
                if not isinstance(md, dict):
                    return score
                line = (md.get("line") or "").lower()
                altitude = (md.get("altitude") or "").lower()

                # Line preference: strong signal
                if line_pref == "top_line_first" and line == "top_line":
                    score += 20
                elif line_pref == "bottom_line_first" and line == "bottom_line":
                    score += 20

                # Altitude preference: secondary signal
                if altitude_pref == "strategic_first" and altitude == "strategic":
                    score += 10
                elif altitude_pref == "operational_first" and altitude == "operational":
                    score += 10
            except Exception:
                return score
            return score

        # Sort items by descending score, preserving original order for ties
        scored_items: List[Tuple[str, KPIDefinition]] = list(kpis.items())
        scored_items.sort(key=lambda item: _score_kpi(item[1]), reverse=True)

        # Rebuild ordered dict so downstream iteration respects preferences
        ordered: Dict[str, KPIDefinition] = {}
        for name, defn in scored_items:
            ordered[name] = defn
        try:
            top_names = [name for name, _ in scored_items[:10]]
            self.logger.info(
                "[SA KPI-PREF] principal_id=%s role=%s line_pref=%s altitude_pref=%s ordered_kpis=%s",
                getattr(principal_context, "principal_id", None),
                getattr(principal_context, "role", None),
                line_pref,
                altitude_pref,
                top_names,
            )
        except Exception:
            pass
        return ordered
    
    async def _get_kpi_value(
        self,
        kpi_definition: KPIDefinition,
        timeframe: TimeFrame,
        comparison_type: Optional[ComparisonType],
        filters: Optional[Dict[str, Any]],
        principal_context: Optional[PrincipalContext] = None
    ) -> Optional[KPIValue]:
        """
        Get KPI value from the Data Product MCP Service Agent.
        Uses Data Governance Agent for view name resolution when available.
        
        Args:
            kpi_name: Name of the KPI
            timeframe: Time frame for analysis
            comparison_type: Type of comparison
            filters: Additional filters
            
        Returns:
            KPI value with comparison if applicable
        """
        try:
            # View resolution is owned by the Data Product Agent. Do not resolve here.
            
            # Get KPI name from definition for logging
            kpi_name = kpi_definition.name
                
            if not kpi_definition:
                self.logger.warning(f"KPI definition is None")
                return None
                
            # Verify data product agent is available
            if not self.data_product_agent:
                logger.error(f"Data Product MCP Service Agent not initialized for KPI {kpi_name}")
                return None
            
            # Merge principal default filters with provided filters
            merged_filters: Dict[str, Any] = {}
            try:
                if principal_context and hasattr(principal_context, 'default_filters') and isinstance(principal_context.default_filters, dict):
                    merged_filters.update(principal_context.default_filters)
            except Exception:
                pass
            try:
                if isinstance(filters, dict):
                    merged_filters.update(filters)
            except Exception:
                pass

            # Single-source SQL generation (for both execution and later UI display)
            # 1) Generate Base SQL via DPA
            base_sql = ""
            try:
                gen_resp = await self.data_product_agent.generate_sql_for_kpi(
                    kpi_definition=kpi_definition,
                    timeframe=timeframe,
                    filters=merged_filters
                )
                if isinstance(gen_resp, dict) and gen_resp.get('success') and isinstance(gen_resp.get('sql', ''), str):
                    base_sql = gen_resp['sql']
                else:
                    self.logger.error(f"Failed to generate base SQL for KPI {kpi_name}: {gen_resp}")
                    return None
            except Exception as ge:
                self.logger.error(f"Error generating base SQL for KPI {kpi_name}: {ge}")
                return None

            # Cache base SQL for UI
            try:
                if kpi_name not in self._last_sql_cache:
                    self._last_sql_cache[kpi_name] = {}
                self._last_sql_cache[kpi_name]['base_sql'] = base_sql
                self.logger.info(f"[SA SQL-DEBUG] cached base_sql for '{kpi_name}', length={len(base_sql)}")
            except Exception:
                pass

            # 2) Execute Base SQL via DPA to obtain current KPI value
            current_value = None
            try:
                exec_resp = await self.data_product_agent.execute_sql(base_sql, parameters=None, principal_context=principal_context)
                rows = exec_resp.get('rows') or exec_resp.get('data') or []
                if rows:
                    first = rows[0]
                    if isinstance(first, (list, tuple)) and len(first) > 0:
                        current_value = float(first[0])
                    elif isinstance(first, dict):
                        # Prefer common alias if present
                        if 'total_value' in first:
                            current_value = float(first['total_value'])
                        elif len(first.values()) > 0:
                            current_value = float(list(first.values())[0])
                if current_value is None:
                    current_value = 0.0
                self.logger.info(f"Extracted KPI value for {kpi_name}: {current_value}")
            except Exception as e:
                self.logger.error(f"Error executing base SQL for {kpi_name}: {e}")
                return None
            # For testing/MVP when comparison not available, return basic KPI value
            if not comparison_type:
                return KPIValue(
                    kpi_name=kpi_name,
                    value=current_value,
                    comparison_value=None,
                    comparison_type=None,
                    timeframe=timeframe,
                    dimensions=merged_filters,
                    percent_change=None
                )
            
            # If comparison is requested, generate comparison SQL once and execute it
            comparison_value = None
            try:
                comp_sql = ""
                comp_sql_resp = await self.data_product_agent.generate_sql_for_kpi_comparison(
                    kpi_definition=kpi_definition,
                    timeframe=timeframe,
                    comparison_type=comparison_type,
                    filters=merged_filters
                )
                if isinstance(comp_sql_resp, dict) and comp_sql_resp.get('success') and isinstance(comp_sql_resp.get('sql', ''), str):
                    comp_sql = comp_sql_resp['sql']
                    # Cache comparison SQL for UI
                    try:
                        if kpi_name not in self._last_sql_cache:
                            self._last_sql_cache[kpi_name] = {}
                        self._last_sql_cache[kpi_name]['comparison_sql'] = comp_sql
                        self.logger.info(f"[SA SQL-DEBUG] cached comparison_sql for '{kpi_name}', length={len(comp_sql)}")
                    except Exception:
                        pass
                    # Execute comparison SQL
                    exec_comp = await self.data_product_agent.execute_sql(comp_sql, parameters=None, principal_context=principal_context)
                    crows = exec_comp.get('rows') or exec_comp.get('data') or []
                    if crows:
                        cfirst = crows[0]
                        if isinstance(cfirst, (list, tuple)) and len(cfirst) > 0:
                            comparison_value = float(cfirst[0])
                        elif isinstance(cfirst, dict):
                            if 'total_value' in cfirst:
                                comparison_value = float(cfirst['total_value'])
                            elif len(cfirst.values()) > 0:
                                comparison_value = float(list(cfirst.values())[0])
                else:
                    self.logger.warning(f"No comparison SQL generated for KPI {kpi_name}: {comp_sql_resp}")
            except Exception as comp_error:
                self.logger.warning(f"Error generating/executing comparison SQL for {kpi_name}: {str(comp_error)}")
                # Continue without comparison value
            
            # Calculate percent change if we have both values
            percent_change = None
            if comparison_value is not None and comparison_value != 0:
                percent_change = ((current_value - comparison_value) / abs(comparison_value)) * 100

            return KPIValue(
                kpi_name=kpi_name,
                value=current_value,
                comparison_value=comparison_value,
                comparison_type=comparison_type,
                timeframe=timeframe,
                dimensions=merged_filters,
                percent_change=percent_change
            )
        except Exception as e:
            logger.error(f"Error getting KPI value for {kpi_name}: {str(e)}")
            return None

    async def _get_sql_for_kpi(
        self,
        kpi: Any,
        filters: Optional[Dict[str, Any]] = None,
        principal_context: Optional[PrincipalContext] = None,
        timeframe: Optional[TimeFrame] = None
    ) -> str:
        """
        Delegator that returns SQL for a KPI by calling the Data Product Agent.

        Args:
            kpi: KPI name/id (str), dict payload, or a `KPIDefinition` instance
            filters: Optional filter dict
            timeframe: Optional `TimeFrame`

        Returns:
            SQL string if generated, else empty string
        """
        try:
            # Resolve KPI definition
            kpi_def: Optional[KPIDefinition] = None
            if hasattr(kpi, '__dict__'):
                kpi_def = kpi
            elif isinstance(kpi, dict):
                try:
                    kpi_def = KPIDefinition(**kpi)
                except Exception:
                    kpi_def = None
            elif isinstance(kpi, str):
                if kpi in self.kpi_registry:
                    kpi_def = self.kpi_registry[kpi]
                else:
                    k_lower = kpi.strip().lower()
                    for name, kd in self.kpi_registry.items():
                        if str(name).strip().lower() == k_lower:
                            kpi_def = kd
                            break

            if not kpi_def:
                self.logger.warning("_get_sql_for_kpi: KPI definition not found")
                return ""

            if not self.data_product_agent:
                self.logger.error("_get_sql_for_kpi: Data Product Agent not available")
                return ""

            # If available, serve the cached SQL used during detection (avoids re-generation)
            try:
                kpi_name = getattr(kpi_def, 'name', None)
                if isinstance(kpi_name, str) and kpi_name in getattr(self, '_last_sql_cache', {}):
                    cached = self._last_sql_cache[kpi_name].get('base_sql')
                    if isinstance(cached, str) and cached.strip():
                        return cached
            except Exception:
                pass

            # Merge principal default filters with provided filters for SQL generation
            merged_filters: Dict[str, Any] = {}
            try:
                if principal_context is not None:
                    if isinstance(principal_context, dict):
                        pc_df = principal_context.get('default_filters', {})
                    else:
                        pc_df = getattr(principal_context, 'default_filters', {})
                    if isinstance(pc_df, dict):
                        merged_filters.update(pc_df)
            except Exception:
                pass
            try:
                if isinstance(filters, dict):
                    merged_filters.update(filters)
            except Exception:
                pass

            # Debug: log merged filters for per-KPI base SQL
            try:
                self.logger.info(f"[SA SQL-DEBUG] merged_filters for per-KPI base SQL: {merged_filters}")
            except Exception:
                pass

            resp = await self.data_product_agent.generate_sql_for_kpi(
                kpi_definition=kpi_def,
                timeframe=timeframe,
                filters=merged_filters
            )
            if isinstance(resp, dict) and resp.get('success') and isinstance(resp.get('sql', ''), str):
                return resp['sql']
            if hasattr(self.data_product_agent, 'generate_sql_for_query') and isinstance(resp, dict):
                alt = await self.data_product_agent.generate_sql_for_query(resp.get('sql', ''))
                if isinstance(alt, dict) and alt.get('success') and isinstance(alt.get('sql', ''), str):
                    return alt['sql']
            return ""
        except Exception as e:
            self.logger.warning(f"_get_sql_for_kpi error: {e}")
            return ""

    async def _get_comparison_sql_for_kpi(
        self,
        kpi: Any,
        comparison_type: Optional[ComparisonType] = None,
        filters: Optional[Dict[str, Any]] = None,
        principal_context: Optional[PrincipalContext] = None,
        timeframe: Optional[TimeFrame] = None
    ) -> str:
        """
        Delegator that returns Comparison SQL for a KPI by calling the Data Product Agent.

        Args:
            kpi: KPI name/id (str), dict payload, or a `KPIDefinition` instance
            comparison_type: Comparison type (e.g., Budget Vs Actual, QoQ, YoY)
            filters: Optional filter dict
            timeframe: Optional `TimeFrame`

        Returns:
            SQL string if generated, else empty string
        """
        try:
            # Resolve KPI definition
            kpi_def: Optional[KPIDefinition] = None
            if hasattr(kpi, '__dict__'):
                kpi_def = kpi
            elif isinstance(kpi, dict):
                try:
                    kpi_def = KPIDefinition(**kpi)
                except Exception:
                    kpi_def = None
            elif isinstance(kpi, str):
                if kpi in self.kpi_registry:
                    kpi_def = self.kpi_registry[kpi]
                else:
                    k_lower = kpi.strip().lower()
                    for name, kd in self.kpi_registry.items():
                        if str(name).strip().lower() == k_lower:
                            kpi_def = kd
                            break

            if not kpi_def:
                self.logger.warning("_get_comparison_sql_for_kpi: KPI definition not found")
                return ""

            if not self.data_product_agent:
                self.logger.error("_get_comparison_sql_for_kpi: Data Product Agent not available")
                return ""

            # If available, serve the cached comparison SQL used during detection
            try:
                kpi_name = getattr(kpi_def, 'name', None)
                if isinstance(kpi_name, str) and kpi_name in getattr(self, '_last_sql_cache', {}):
                    cached = self._last_sql_cache[kpi_name].get('comparison_sql')
                    if isinstance(cached, str) and cached.strip():
                        return cached
            except Exception:
                pass

            # Merge principal default filters with provided filters for SQL generation
            merged_filters: Dict[str, Any] = {}
            try:
                if principal_context is not None:
                    if isinstance(principal_context, dict):
                        pc_df = principal_context.get('default_filters', {})
                    else:
                        pc_df = getattr(principal_context, 'default_filters', {})
                    if isinstance(pc_df, dict):
                        merged_filters.update(pc_df)
            except Exception:
                pass
            try:
                if isinstance(filters, dict):
                    merged_filters.update(filters)
            except Exception:
                pass

            # Debug: log merged filters for per-KPI comparison SQL
            try:
                self.logger.info(f"[SA SQL-DEBUG] merged_filters for per-KPI comparison SQL: {merged_filters}")
            except Exception:
                pass

            resp = await self.data_product_agent.generate_sql_for_kpi_comparison(
                kpi_definition=kpi_def,
                timeframe=timeframe,
                comparison_type=comparison_type,
                filters=merged_filters
            )
            if isinstance(resp, dict) and isinstance(resp.get('sql', ''), str) and resp.get('sql'):
                return resp['sql']
            return ""
        except Exception as e:
            self.logger.warning(f"_get_comparison_sql_for_kpi error: {e}")
            return ""

    def _detect_kpi_situations(
        self,
        kpi_definition: KPIDefinition,
        kpi_value: KPIValue,
        principal_context: PrincipalContext
    ) -> List[Situation]:
        """
        Detect situations for a KPI based on its value and thresholds.
        
        This method uses the canonical KPI model thresholds structure and
        evaluates KPI values against defined thresholds to detect situations.
        
        Args:
            kpi_definition: KPI definition with thresholds
            kpi_value: Current KPI value
            principal_context: Principal context for personalization
            
        Returns:
            List of detected situations
        """
        situations = []
        
        # Check if we have thresholds defined
        if kpi_definition.thresholds:
            # Get the current value for comparison
            current_value = kpi_value.value
            
            # Check if we have inverse logic flag (lower values are better)
            inverse_logic = False
            if '_inverse_logic' in kpi_definition.thresholds:
                inverse_logic = kpi_definition.thresholds['_inverse_logic']
            elif not kpi_definition.positive_trend_is_good:
                # If positive trend is not good, then lower values are better
                inverse_logic = True
                
            # Process thresholds based on severity
            for threshold_key, threshold_value in kpi_definition.thresholds.items():
                # Skip special keys
                if threshold_key == '_inverse_logic':
                    continue
                    
                # Handle different threshold types based on severity
                if threshold_key == SituationSeverity.CRITICAL or threshold_key == "critical":
                    if (inverse_logic and current_value > threshold_value) or \
                       (not inverse_logic and current_value < threshold_value):
                        situations.append(self._create_threshold_situation(
                            kpi_definition,
                            kpi_value,
                            SituationSeverity.CRITICAL,
                            f"{kpi_definition.name} is at a critical level",
                            principal_context
                        ))
                        
                elif threshold_key == SituationSeverity.HIGH or threshold_key == "warning" or threshold_key == "high":
                    if (inverse_logic and current_value > threshold_value) or \
                       (not inverse_logic and current_value < threshold_value):
                        situations.append(self._create_threshold_situation(
                            kpi_definition,
                            kpi_value,
                            SituationSeverity.HIGH,
                            f"{kpi_definition.name} requires attention",
                            principal_context
                        ))
                        
                elif threshold_key == SituationSeverity.INFORMATION or threshold_key == "information" or threshold_key == "low":
                    if (inverse_logic and current_value > threshold_value) or \
                       (not inverse_logic and current_value < threshold_value):
                        situations.append(self._create_threshold_situation(
                            kpi_definition,
                            kpi_value,
                            SituationSeverity.INFORMATION,
                            f"{kpi_definition.name} is outside normal range",
                            principal_context
                        ))
        
        # Check for significant changes if comparison value exists
        if kpi_value.comparison_value is not None and kpi_value.comparison_value != 0:
            # Calculate percent change
            percent_change = (kpi_value.value - kpi_value.comparison_value) / abs(kpi_value.comparison_value) * 100

            # Prefer registry-defined variance thresholds when available
            vt_cfg = None
            try:
                meta = getattr(kpi_definition, 'metadata', None) or {}
                vt_all = meta.get('variance_thresholds') or {}
                comp_key = None
                ct = getattr(kpi_value, 'comparison_type', None)
                if ct is not None:
                    ct_val = ct.value if hasattr(ct, 'value') else str(ct)
                    ct_l = str(ct_val).lower()
                    if 'year' in ct_l or ct_l == 'yoy':
                        comp_key = 'yoy'
                    elif 'quarter' in ct_l or ct_l == 'qoq':
                        comp_key = 'qoq'
                    elif 'month' in ct_l or ct_l == 'mom':
                        comp_key = 'mom'
                    elif 'budget' in ct_l:
                        comp_key = 'budget'
                    elif 'target' in ct_l:
                        comp_key = 'target'
                vt_cfg = vt_all.get(comp_key) if comp_key else None
            except Exception:
                vt_cfg = None

            if vt_cfg:
                inv = bool(vt_cfg.get('inverse_logic', False))
                g = vt_cfg.get('green')
                y = vt_cfg.get('yellow')
                r = vt_cfg.get('red')

                # Emulate registry KPI.evaluate() semantics
                evaluation = 'red'
                if not inv:
                    if g is not None and percent_change >= g:
                        evaluation = 'green'
                    elif y is not None and percent_change >= y:
                        evaluation = 'yellow'
                    elif r is not None and percent_change >= r:
                        evaluation = 'red'
                    else:
                        evaluation = 'red'
                else:
                    if g is not None and percent_change <= g:
                        evaluation = 'green'
                    elif y is not None and percent_change <= y:
                        evaluation = 'yellow'
                    elif r is not None and percent_change <= r:
                        evaluation = 'red'
                    else:
                        evaluation = 'red'

                if evaluation in ('yellow', 'red'):
                    severity = SituationSeverity.HIGH if evaluation == 'yellow' else SituationSeverity.CRITICAL
                    change_direction = "increased" if percent_change > 0 else "decreased"
                    situations.append(self._create_threshold_situation(
                        kpi_definition,
                        kpi_value,
                        severity,
                        f"{kpi_definition.name} {change_direction} by {abs(percent_change):.1f}% vs baseline (threshold={evaluation})",
                        principal_context
                    ))
                else:
                    # Optionally record informational improvement within green band
                    change_direction = "increased" if percent_change > 0 else "decreased"
                    situations.append(self._create_threshold_situation(
                        kpi_definition,
                        kpi_value,
                        SituationSeverity.INFORMATION,
                        f"{kpi_definition.name} {change_direction} by {abs(percent_change):.1f}% (within green threshold)",
                        principal_context
                    ))
            else:
                # Fallback: heuristic severity based on magnitude and trend direction
                is_positive_change = percent_change > 0
                is_good_change = (is_positive_change and kpi_definition.positive_trend_is_good) or \
                                 (not is_positive_change and not kpi_definition.positive_trend_is_good)
                if abs(percent_change) >= 20:
                    severity = SituationSeverity.CRITICAL if not is_good_change else SituationSeverity.INFORMATION
                elif abs(percent_change) >= 10:
                    severity = SituationSeverity.HIGH if not is_good_change else SituationSeverity.INFORMATION
                elif abs(percent_change) >= 5:
                    severity = SituationSeverity.MEDIUM if not is_good_change else SituationSeverity.INFORMATION
                else:
                    severity = SituationSeverity.INFORMATION

                if abs(percent_change) >= 5:
                    change_direction = "increased" if percent_change > 0 else "decreased"
                    change_quality = "worsened" if not is_good_change else "improved"
                    # Business-specific phrasing rule:
                    # For COGS-like KPIs, when the situation is assessed as worsened
                    # but the numeric change is negative ("decreased"), prefer the
                    # display term "increased" per stakeholder phrasing request.
                    try:
                        kpi_name_lower = (getattr(kpi_definition, 'name', '') or '').lower()
                    except Exception:
                        kpi_name_lower = ''
                    if kpi_name_lower in ("cost of goods sold", "cogs", "cost of sales"):
                        if change_quality == "worsened" and change_direction == "decreased":
                            change_direction = "increased"
                    situations.append(self._create_threshold_situation(
                        kpi_definition,
                        kpi_value,
                        severity,
                        f"{kpi_definition.name} {change_direction} by {abs(percent_change):.1f}% ({change_quality})",
                        principal_context
                    ))
        
        return situations
    
    def _create_threshold_situation(
        self,
        kpi_definition: KPIDefinition,
        kpi_value: KPIValue,
        severity: SituationSeverity,
        description: str,
        principal_context: PrincipalContext
    ) -> Situation:
        """
        Create a situation object for a threshold breach.
        
        Args:
            kpi_definition: KPI definition
            kpi_value: Current KPI value
            severity: Situation severity
            description: Situation description
            principal_context: Principal context for personalization
            
        Returns:
            Situation object
        """
        # Generate business impact based on severity and principal's role
        if severity == SituationSeverity.CRITICAL:
            if principal_context.role == PrincipalRole.CFO:
                business_impact = f"Immediate attention required: {kpi_definition.name} is significantly outside expected range, potentially impacting financial targets and shareholder expectations."
            else:
                business_impact = f"Immediate attention required: {kpi_definition.name} is significantly outside expected range, potentially impacting financial targets."
        elif severity == SituationSeverity.HIGH:
            business_impact = f"Attention needed: {kpi_definition.name} is outside normal parameters, potentially indicating an emerging financial issue."
        elif severity == SituationSeverity.MEDIUM:
            business_impact = f"Monitor closely: {kpi_definition.name} shows notable variation from expected values."
        else:
            business_impact = f"For information: {kpi_definition.name} has changed but remains within expected parameters."
        
        # Get diagnostic questions if available
        diagnostic_questions = kpi_definition.diagnostic_questions
        
        # Generate suggested actions based on severity
        suggested_actions = [
            f"Review {kpi_definition.name} in detail",
            f"Compare {kpi_definition.name} across business dimensions"
        ]
        
        if severity in [SituationSeverity.CRITICAL, SituationSeverity.HIGH]:
            suggested_actions.append("Escalate to appropriate stakeholders")
            suggested_actions.append("Initiate deep analysis")
        
        return Situation(
            situation_id=str(uuid.uuid4()),
            kpi_name=kpi_definition.name,
            kpi_value=kpi_value,
            severity=severity,
            description=description,
            business_impact=business_impact,
            suggested_actions=suggested_actions,
            diagnostic_questions=diagnostic_questions,
            timestamp=datetime.now()
        )
    
    # SQL generation methods have been moved to the Data Product Agent
        
    async def _detect_situations_from_kpi_values(
        self,
        kpi_values: List[KPIValue],
        principal_context: PrincipalContext
    ) -> List[Situation]:
        """
        Detect situations from a list of KPI values.
        
        This method analyzes real data values from the backend and identifies
        situations based on thresholds, trends, and comparison values.
        
        Args:
            kpi_values: List of KPI values retrieved from the database
            principal_context: Principal context for personalization
            
        Returns:
            List of detected situations
        """
        self.logger.info(f"Detecting situations from {len(kpi_values)} KPI values")
        
        # Store all detected situations
        all_situations = []
        
        # Process each KPI value
        for kpi_value in kpi_values:
            # Get the KPI definition from registry
            kpi_definition = self.kpi_registry.get(kpi_value.kpi_name)
            if not kpi_definition:
                self.logger.warning(f"KPI definition not found for {kpi_value.kpi_name}, skipping situation detection")
                continue
            
            # Detect situations for this KPI
            self.logger.info(f"Analyzing KPI {kpi_value.kpi_name} = {kpi_value.value}")
            kpi_situations = self._detect_kpi_situations(
                kpi_definition,
                kpi_value,
                principal_context
            )
            
            self.logger.info(f"Detected {len(kpi_situations)} situations for KPI {kpi_value.kpi_name}")
            
            # Add to all situations
            all_situations.extend(kpi_situations)
        
        # Sort situations by severity (critical first)
        all_situations.sort(key=lambda s: list(SituationSeverity).index(s.severity) if s.severity in SituationSeverity else 99)
        
        self.logger.info(f"Total situations detected: {len(all_situations)}")
        return all_situations
    
    async def _generate_sql_for_query(
        self,
        query: str,
        kpi_values: List[KPIValue]
    ) -> Optional[str]:
        """
        Generate SQL for a natural language query by delegating to the Data Product Agent.
        Centralizes all SQL generation paths (LLM and deterministic) in the Data Product Agent.
        """
        try:
            if not self.data_product_agent:
                self.logger.warning("Data Product Agent not available for SQL generation")
                return None
            # Build a minimal context for DPA (let DPA decide how to use LLM/deterministic paths)
            dp_id = os.path.splitext(os.path.basename(self.contract_path))[0] if hasattr(self, 'contract_path') else "fi_star_schema"
            context = {
                'data_product_id': dp_id,
                'contract_path': getattr(self, 'contract_path', None),
                'kpi_values': [kv.model_dump() if hasattr(kv, 'model_dump') else kv.__dict__ for kv in (kpi_values or [])]
            }
            dp_resp = await self.data_product_agent.generate_sql(query, context)
            if isinstance(dp_resp, dict) and dp_resp.get('success') and dp_resp.get('sql'):
                return dp_resp['sql']
            self.logger.warning(f"Data Product Agent returned no SQL: {dp_resp}")
            return None
        except Exception as e:
            self.logger.error(f"Error delegating SQL generation to Data Product Agent: {e}")
            return None


    def _generate_answer_for_query(self, query: str, kpi_values: List[KPIValue]) -> str:
        """
        Deterministic, lightweight answer generator for NL queries.
        Produces a concise summary from available KPI values without LLMs.
        """
        try:
            if not kpi_values:
                return (
                    "I couldn't map your question to a specific KPI. "
                    "Please refine the question or select a KPI from the card."
                )

            def _fmt_timeframe(tf: Any) -> str:
                try:
                    if hasattr(tf, 'name'):
                        return str(tf.name).replace('_', ' ').title()
                    if hasattr(tf, 'value'):
                        return str(tf.value)
                    return str(tf) if tf else "current period"
                except Exception:
                    return "current period"

            lines: List[str] = []
            for kv in kpi_values[:3]:
                name = getattr(kv, 'kpi_name', 'KPI')
                val = getattr(kv, 'value', None)
                tf = _fmt_timeframe(getattr(kv, 'timeframe', None))

                # Optional unit lookup from registry
                unit = ""
                try:
                    if hasattr(self, 'kpi_registry') and isinstance(self.kpi_registry, dict) and name in self.kpi_registry:
                        unit_str = getattr(self.kpi_registry[name], 'unit', None)
                        if unit_str:
                            unit = f" {unit_str}"
                except Exception:
                    unit = ""

                if isinstance(val, (int, float)):
                    val_str = f"{val:,.2f}"
                else:
                    val_str = str(val)
                lines.append(f"{name} for {tf}: {val_str}{unit}")

            if len(kpi_values) > 3:
                lines.append(f"...and {len(kpi_values) - 3} more.")
            return " | ".join(lines)
        except Exception as e:
            # Fail-safe fallback
            try:
                self.logger.warning(f"_generate_answer_for_query fallback due to: {e}")
            except Exception:
                pass
            if kpi_values:
                try:
                    return "; ".join(
                        [f"{getattr(kv, 'kpi_name', 'KPI')}: {getattr(kv, 'value', 'N/A')}" for kv in kpi_values[:3]]
                    )
                except Exception:
                    return "Answer available, but formatting failed."
            return "No KPI values available to answer."


    async def get_recommended_questions(self, principal_context: PrincipalContext, business_process: Optional[BusinessProcess] = None) -> List[str]:
        try:
            kpis = list(self.kpi_registry.keys()) if isinstance(self.kpi_registry, dict) else []
            tf_list = getattr(principal_context, 'preferred_timeframes', None) or []
            def _tf_label(tf):
                try:
                    return getattr(tf, 'value', None) or getattr(tf, 'name', None) or str(tf)
                except Exception:
                    return "current_period"
            tf_label = _tf_label(tf_list[0]) if tf_list else "current_period"
            qs: List[str] = []
            if kpis:
                top = kpis[:3]
                for name in top:
                    qs.append(f"What is {name} for {tf_label}?")
                if len(kpis) > 1:
                    qs.append(f"How does {kpis[0]} compare to budget for {tf_label}?")
            else:
                qs = [
                    f"What are the top KPIs for {tf_label}?",
                    f"Which KPIs deviated most from budget for {tf_label}?",
                ]
            return qs
        except Exception:
            return ["Show me key finance KPIs this period."]


def create_situation_awareness_agent(config: Dict[str, Any]) -> "A9_Situation_Awareness_Agent":
    """
    Factory function to create a Situation Awareness Agent.
    
    Args:
        config: Configuration dictionary with these options:
            - contract_path: Path to the data contract YAML file (required)
            - target_domains: List of domain prefixes to filter KPIs (optional, defaults to ['Finance'])
            - kpi_thresholds: Custom KPI thresholds (optional)
            - principal_profile_path: Custom principal profile path (optional)
        
    Returns:
        A9_Situation_Awareness_Agent instance
    """
    # Set defaults for optional config
    if "target_domains" not in config:
        config["target_domains"] = ["Finance"]  # Default for MVP
        
    return A9_Situation_Awareness_Agent(config)
