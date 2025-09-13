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
from typing import List, Dict, Any, Optional, Tuple

# Import data models and enums
from src.agents.models.situation_awareness_models import (
    BusinessProcess, PrincipalRole, TimeFrame, ComparisonType, 
    SituationSeverity, KPIDefinition, Situation, KPIValue,
    PrincipalContext, SituationDetectionRequest, SituationDetectionResponse,
    NLQueryRequest, NLQueryResponse, HITLRequest, HITLResponse, HITLDecision
)

# Import agent protocol and base classes
from src.agents.protocols.situation_awareness_protocol import SituationAwarenessProtocol
from src.agents.a9_orchestrator_agent import A9_Orchestrator_Agent
from src.agents.shared.a9_agent_base_model import A9AgentBaseModel

# Import registry and database components
from src.registry.factory import RegistryFactory
from src.registry.models.kpi import KPI

# Import other agents
from src.agents.a9_orchestrator_agent import A9_Orchestrator_Agent, agent_registry, initialize_agent_registry
from src.registry.providers.business_process_provider import BusinessProcessProvider
from src.registry.providers.kpi_provider import KPIProvider as KpiProvider
from src.models.kpi_models import KPI, KPIThreshold, KPIComparisonMethod

# Import the actual agent for data product interaction
from src.agents.a9_data_product_mcp_service_agent import A9_Data_Product_MCP_Service_Agent, SQLExecutionRequest

# Import Data Governance Agent for KPI to data product mapping
from src.agents.a9_data_governance_agent import A9_Data_Governance_Agent
from src.agents.models.data_governance_models import KPIDataProductMappingRequest, KPIDataProductMapping

logger = logging.getLogger(__name__)

class A9_Situation_Awareness_Agent:
    """
    Agent9 Situation Awareness Agent
    
    Detects situations based on KPI thresholds, trends, and principal context.
    Provides automated, personalized situation awareness for Finance KPIs.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the Situation Awareness Agent with the provided configuration.
        
        Args:
            config: Configuration dictionary with required settings.
        """
        # Store the configuration
        self.config = config or {}
        
        # Set up agent properties
        self.name = "A9_Situation_Awareness_Agent"
        self.version = "0.1.0"
        
        # Initialize registry providers
        self.registry_factory = None
        self.kpi_provider = None
        self.business_process_provider = None
        
        # Initialize agent dependencies
        self.data_product_agent = None
        self.data_governance_agent = None
        
        # Setup logging
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Load contract and registries
        self.contract_path = config.get("contract_path", "C:/Users/barry/CascadeProjects/Agent9-HERMES/src/contracts/fi_star_schema.yaml")
        
        # Initialize empty contract and KPI registry (will be loaded in connect)
        self.contract = None
        self.kpi_registry = {}
        
    async def _load_kpi_registry(self):
        """
        Load KPI definitions from registry and contract.
        """
        try:
            # Initialize the KPI registry
            self.kpi_registry = {}
            
            # Try to get KPI provider from registry factory
            try:
                if not self.registry_factory:
                    self.registry_factory = RegistryFactory()
                
                if not self.kpi_provider:
                    self.kpi_provider = self.registry_factory.get_provider('kpi')
                
                if self.kpi_provider:
                    # Use get_all() which returns a list of KPI objects
                    kpis = self.kpi_provider.get_all()
                    for kpi in kpis:
                        # Convert registry KPI to internal KPI definition
                        kpi_def = await self._convert_to_kpi_definition(kpi)
                        if kpi_def:
                            self.kpi_registry[kpi_def.name] = kpi_def
            except Exception as e:
                self.logger.warning(f"Could not get KPI provider from registry factory")
                
            # Load KPIs from contract as backup or additional source
            if hasattr(self, 'contract') and self.contract and hasattr(self.contract, 'kpis'):
                for kpi in self.contract.kpis:
                    self.kpi_registry[kpi.name] = kpi
                    
            self.logger.info(f"Loaded {len(self.kpi_registry)} KPIs from registry and contract")
        except Exception as e:
            self.logger.error(f"Error initializing KPI registry: {str(e)}")
            # Initialize with empty registry to avoid errors
            self.kpi_registry = {}

    @classmethod
    async def create(cls, config: Dict[str, Any] = None) -> "A9_Situation_Awareness_Agent":
        """
        Standards-compliant async factory that ensures the agent is connected.
        """
        agent = cls(config or {})
        await agent.connect()
        return agent
    
    async def connect(self):
        """Initialize connections to dependent services."""
        try:
            # Initialize the orchestrator agent
            self.orchestrator_agent = await A9_Orchestrator_Agent.create({})
            
            # Ensure agent factories are registered before requesting agents
            await initialize_agent_registry()
            
            # Load the contract
            await self._load_contract()
            
            # Get the Data Product MCP Service Agent through the orchestrator
            import os
            contracts_dir = os.path.dirname(self.contract_path) if self.contract_path else "src/registry_references/data_product_registry/data_products"
            self.data_product_agent = await self.orchestrator_agent.get_agent(
                "A9_Data_Product_MCP_Service_Agent", 
                {"contracts_path": contracts_dir}
            )
            if self.data_product_agent:
                logger.info("Data Product MCP Service Agent retrieved and set on SA agent")
                
            # Get the Data Governance Agent for term translation and access validation
            self.data_governance_agent = await self.orchestrator_agent.get_agent(
                "A9_Data_Governance_Agent"
            )
            
            # Load principal profiles through the orchestrator
            await self._load_principal_profiles()
            
            # Load KPI registry (critical for situation detection and SQL generation)
            await self._load_kpi_registry()
            
            # Validate initialization state
            if not self.kpi_registry:
                logger.warning("KPI registry is empty after loading! This will prevent situation detection.")
            else:
                logger.info(f"Successfully loaded {len(self.kpi_registry)} KPIs into registry")
                
            logger.info("Connected to dependent services")
            return True
        except Exception as e:
            logger.error(f"Error connecting to services: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from dependent services."""
        if self.data_product_agent:
            # Data Product MCP Service Agent uses close() method instead of disconnect()
            self.data_product_agent.close()
        
        logger.info(f"{self.name} disconnected from dependent services")
    
    async def _load_contract(self):
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
            
            logger.info(f"Loaded contract from {self.contract_path}")
        except Exception as e:
            logger.error(f"Error loading contract: {str(e)}")
            raise
    
    async def _load_principal_profiles(self):
        """
        Load principal profiles for personalization by requesting them from the Principal Context Agent
        """
        try:
            # Get PrincipalContextAgent from orchestrator
            principal_context_agent = await self.orchestrator_agent.get_agent("A9_Principal_Context_Agent")
            
            if not principal_context_agent:
                logger.warning("Principal Context Agent not found in orchestrator")
                return
            
            # Define key roles we want to load
            key_roles = {
                "CFO": PrincipalRole.CFO,           # cfo
                "FINANCE_MANAGER": PrincipalRole.FINANCE_MANAGER  # finance_manager
            }
            
            # Get principal profiles for key roles
            for display_role_name, role_enum in key_roles.items():
                # Get exact registry ID from enum value
                registry_id = role_enum.value
                
                # Try multiple approaches to find the profile
                # 1. Try exact match with registry ID from enum
                profile = await principal_context_agent.fetch_principal_profile(registry_id)
                
                # 2. If that fails, try with display name (legacy approach)
                if not profile:
                    profile = await principal_context_agent.fetch_principal_profile(display_role_name)
                
                # 3. If that fails, try with lowercase variant
                if not profile:
                    profile = await principal_context_agent.fetch_principal_profile(display_role_name.lower())
                
                if profile:
                    # Add to internal profiles using the enum as key
                    self.principal_profiles[role_enum] = profile
                    logger.info(f"Loaded profile for {display_role_name} (ID: {registry_id})")
                else:
                    logger.warning(f"Principal profile not found: {display_role_name} (tried ID: {registry_id})")
            
            # Ensure we have at least CFO and Finance Manager roles with necessary business processes
            for role in [PrincipalRole.CFO, PrincipalRole.FINANCE_MANAGER]:
                if role not in self.principal_profiles:
                    # Create default profile if missing
                    role_name = role.name.replace('_', ' ').title()
                    self.principal_profiles[role] = {
                        "id": role.value,
                        "name": role_name,
                        "business_processes": [],
                        "default_filters": {},
                        "communication_style": "direct",
                        "decision_timeframe": "monthly"
                    }
                
                # Ensure we have all 5 Finance business processes for MVP
                finance_bps = [
                    "Finance: Profitability Analysis",
                    "Finance: Revenue Growth Analysis",
                    "Finance: Expense Management",
                    "Finance: Cash Flow Management",
                    "Finance: Budget vs. Actuals"
                ]
                
                existing_bps = self.principal_profiles[role].get("business_processes", [])
                missing_bps = [bp for bp in finance_bps if bp not in existing_bps]
                
                if missing_bps:
                    self.principal_profiles[role]["business_processes"] = [
                        *existing_bps,
                        *missing_bps
                    ]
            
            logger.info(f"Loaded {len(self.principal_profiles)} principal profiles from Principal Context Agent")
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            logger.error(f"Error loading principal profiles: {type(e).__name__}: {str(e)}\n{error_details}")
            # Create minimal profiles for fallback
            self.principal_profiles = {}
    
    async def detect_situations(
        self, 
        request: SituationDetectionRequest
    ) -> SituationDetectionResponse:
        """
        Detect situations across KPIs based on principal context and business processes.
        
        Args:
            request: SituationDetectionRequest containing principal context and filters
            
        Returns:
            SituationDetectionResponse with detected situations
        """
        try:
            self.logger.info(f"Detecting situations for {request.principal_context.role}")
            
            # Get relevant KPIs based on principal context and business processes
            relevant_kpis = await self._get_relevant_kpis(
                request.principal_context,
                request.business_processes
            )
            
            self.logger.info(f"Found {len(relevant_kpis)} relevant KPIs for detection")
            
            # For bullet tracer MVP, we'll process a limited set of KPIs
            # In production, we would process all relevant KPIs
            situations = []
            kpi_values = []
            
            # Process each relevant KPI to fetch actual values from database
            for kpi_name, kpi_definition in list(relevant_kpis.items())[:5]:  # Limit to 5 KPIs for MVP
                try:
                    # Get actual KPI value from database using Data Product Agent
                    kpi_value = await self._get_kpi_value(
                        kpi_definition,
                        request.timeframe,
                        request.comparison_type,
                        request.filters
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
            if kpi_values:
                first_kpi_def = relevant_kpis.get(kpi_values[0].kpi_name)
                if first_kpi_def:
                    sample_sql = self._generate_sql_for_kpi(
                        first_kpi_def,
                        request.timeframe,
                        request.filters
                    )
            
            return SituationDetectionResponse(
                request_id=request.request_id,
                status="success",
                message=f"Detected {len(situations)} situations across {len(kpi_values)} KPIs",
                situations=situations,
                sql_query=sample_sql
            )
        
        except Exception as e:
            self.logger.error(f"Error detecting situations: {str(e)}")
            return SituationDetectionResponse(
                request_id=request.request_id,
                status="error",
                message=f"Error detecting situations: {str(e)}",
                situations=[]
            )
    
    async def process_nl_query(
        self,
        request: NLQueryRequest
    ) -> NLQueryResponse:
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
                            context={"principal_context": (request.principal_context.model_dump() if request.principal_context else {})}
                        )
                    )
                    
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
            
            # First try to identify KPIs via translated business terms
            mapped_kpis = []
            if self.data_governance_agent and hasattr(self, 'translation_result') and self.translation_result.resolved_terms:
                for business_term, technical_name in self.translation_result.resolved_terms.items():
                    # Check if the technical name matches a KPI name
                    if technical_name in self.kpi_registry.keys():
                        mapped_kpis.append(technical_name)
            
            # Then fall back to direct KPI name matching in the query
            for kpi_name in self.kpi_registry.keys():
                if kpi_name.lower() in query_lower or kpi_name in mapped_kpis:
                    try:
                        kpi_def = self.kpi_registry.get(kpi_name)
                        if not kpi_def:
                            continue
                        kpi_value = await self._get_kpi_value(
                            kpi_def,
                            request.timeframe if request.timeframe else TimeFrame.CURRENT_QUARTER,  # Default timeframe
                            request.comparison_type if request.comparison_type else ComparisonType.QUARTER_OVER_QUARTER,  # Default comparison
                            request.filters if request.filters else {}
                        )
                        if kpi_value:
                            kpi_values.append(kpi_value)
                    except Exception as kpi_error:
                        logger.warning(f"Error retrieving KPI {kpi_name}: {str(kpi_error)}")
                        # Continue with other KPIs
            
            # For bullet tracer MVP, if no KPIs are found in query, get principal's top KPI
            if not kpi_values and request.principal_context:
                try:
                    # Get KPIs relevant to principal
                    relevant_kpis = await self._get_relevant_kpis(
                        request.principal_context,
                        None  # No business process filter for NL queries
                    )
                    
                    # Get first KPI
                    if relevant_kpis:
                        first_kpi_name = next(iter(relevant_kpis.keys()))
                        kpi_def = relevant_kpis.get(first_kpi_name)
                        if kpi_def:
                            kpi_value = await self._get_kpi_value(
                                kpi_def,
                                request.timeframe if request.timeframe else TimeFrame.CURRENT_QUARTER,
                                request.comparison_type if request.comparison_type else ComparisonType.QUARTER_OVER_QUARTER,
                                request.filters if request.filters else {}
                            )
                            if kpi_value:
                                kpi_values.append(kpi_value)
                except Exception as e:
                    logger.warning(f"Error getting default KPI: {str(e)}")
            
            # Generate SQL for the query (simplified for MVP)
            sql_query = self._generate_sql_for_query(request.query, kpi_values)
            
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
            return NLQueryResponse(
                request_id=request.request_id,
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
    
    async def get_principal_context(self, principal_role: PrincipalRole) -> PrincipalContext:
        """
        Get principal context for a given role.
        
        Args:
            principal_role: Role of the principal
            
        Returns:
            Principal context containing preferences and relevant business processes
        """
        # Log the request
        self.logger.info(f"Getting principal context for role: {principal_role}")
        
        # First try to load from registry if not already loaded
        if not self.principal_profiles:
            await self._load_principal_profiles()
            
        # Try to find matching profile for the role
        profile_key = principal_role.value.lower()
        for key, profile in self.principal_profiles.items():
            if key.lower() == profile_key or profile.get('role', '').lower() == profile_key:
                # Create and return PrincipalContext
                business_processes = []
                for bp in profile.get('business_processes', []):
                    # Try to map to BusinessProcess enum
                    try:
                        business_processes.append(BusinessProcess(bp))
                    except ValueError:
                        self.logger.warning(f"Unknown business process: {bp} for principal {principal_role}")
                
                # Create context with defaults if values are missing
                return PrincipalContext(
                    role=principal_role,
                    principal_id=profile.get('id', f"default-{principal_role.value.lower().replace(' ', '-')}"),
                    business_processes=business_processes or list(BusinessProcess),
                    default_filters=profile.get('default_filters', {}),
                    decision_style=profile.get('decision_style', "Analytical"),
                    communication_style=profile.get('communication_style', "Concise"),
                    preferred_timeframes=[TimeFrame.CURRENT_QUARTER, TimeFrame.YEAR_TO_DATE]
                )
        
        # If no matching profile is found, return a default context
        self.logger.warning(f"No principal profile found for role {principal_role}, using default")
        return PrincipalContext(
            role=principal_role,
            principal_id=f"default-{principal_role.value.lower().replace(' ', '-')}",
            business_processes=list(BusinessProcess),
            default_filters={},
            decision_style="Analytical",
            communication_style="Concise",
            preferred_timeframes=[TimeFrame.CURRENT_QUARTER, TimeFrame.YEAR_TO_DATE]
        )
        
    async def get_diagnostic_questions(self, principal_context: PrincipalContext, business_process: Optional[BusinessProcess] = None) -> List[str]:
        """
        Get recommended questions for the principal based on context.
        
        Args:
            principal_context: Context of the principal
            
        Returns:
            List of recommended questions
        """
        # Get relevant KPIs based on principal context and business process
        relevant_kpis = await self._get_relevant_kpis(principal_context, [business_process] if business_process else None)
        
        # Collect diagnostic questions from KPI definitions
        questions = []
        for kpi_name, kpi_def in relevant_kpis.items():
            if kpi_def.diagnostic_questions:
                questions.extend(kpi_def.diagnostic_questions)
        
        return questions[:5]  # Limit to top 5 questions
    
    async def get_recommended_questions(
        self,
        principal_context: PrincipalContext,
        business_process: Optional[BusinessProcess] = None
    ) -> List[str]:
        """
        Get recommended questions for the principal based on context.
        
        Args:
            principal_context: Context of the principal
            business_process: Optional specific business process
            
        Returns:
            List of recommended questions
        """
        # Get relevant KPIs based on principal context and business process
        relevant_kpis = await self._get_relevant_kpis(principal_context, [business_process] if business_process else None)
        
        # Collect diagnostic questions from KPI definitions
        questions = []
        for kpi_name, kpi_def in relevant_kpis.items():
            if kpi_def.diagnostic_questions:
                questions.extend(kpi_def.diagnostic_questions)
        
        return questions[:5]  # Limit to top 5 questions
    
    async def _get_relevant_kpis(self, principal_context: PrincipalContext, business_processes: Optional[List[BusinessProcess]] = None) -> Dict[str, KPIDefinition]:
        """
        Get KPIs relevant to the principal context and business processes.
        
        Args:
            principal_context: Context of the principal
            business_processes: Optional list of business processes to filter by
            
        Returns:
            Dictionary of KPI name to KPIDefinition
        """
        try:
            logger.info(f"Getting relevant KPIs for {principal_context.role}")
            
            # Filter KPIs based on principal context and business processes
            relevant_kpis = {}
            
            # If no KPIs in registry, return empty dict
            if not self.kpi_registry:
                logger.warning("KPI registry is empty, cannot get relevant KPIs")
                return {}
                
            # Get business processes to filter by
            filter_bps = business_processes or principal_context.business_processes
            
            # If no business processes specified, return all KPIs
            if not filter_bps:
                logger.info("No business processes specified, returning all KPIs")
                return self.kpi_registry.copy()
                
            # Filter KPIs by business process
            for kpi_name, kpi_def in self.kpi_registry.items():
                # Check if KPI is relevant to any of the specified business processes
                if not hasattr(kpi_def, 'business_processes') or not kpi_def.business_processes:
                    # If KPI has no business process, include it for all principals
                    relevant_kpis[kpi_name] = kpi_def
                    continue
                    
                # Check if any of the KPI's business processes match the filter
                for bp in filter_bps:
                    if bp.value in kpi_def.business_processes or bp.name in kpi_def.business_processes:
                        relevant_kpis[kpi_name] = kpi_def
                        break
                        
            logger.info(f"Found {len(relevant_kpis)} KPIs relevant to {principal_context.role} and specified business processes")
            return relevant_kpis
        except Exception as e:
            logger.error(f"Error getting relevant KPIs: {str(e)}")
            return {}
            
    async def _convert_to_kpi_definition(self, kpi) -> Optional[KPIDefinition]:
        """
        Convert a KPI from the registry to a KPIDefinition.
        Uses Data Governance Agent to get authoritative data product mapping.
        
        Args:
            kpi: KPI object from registry
            
        Returns:
            KPIDefinition or None if conversion fails
        """
        try:
            # Extract basic KPI properties
            kpi_name = kpi.name if hasattr(kpi, 'name') else str(kpi)
            logger.info(f"Converting KPI {kpi_name} to KPIDefinition")
            
            # Get data product mapping from Data Governance Agent if available
            data_product_id = None
            if self.data_governance_agent:
                try:
                    # Create mapping request
                    mapping_request = KPIDataProductMappingRequest(
                        kpi_name=kpi_name,
                        kpi_id=kpi.id if hasattr(kpi, 'id') else None
                    )
                    
                    # Get mapping from Data Governance Agent
                    mapping_result = await self.data_governance_agent.get_kpi_data_product_mapping(mapping_request)
                    
                    if mapping_result and mapping_result.data_product_id:
                        data_product_id = mapping_result.data_product_id
                        logger.info(f"Data Governance Agent mapped KPI {kpi_name} to data product {data_product_id}")
                    else:
                        logger.warning(f"Data Governance Agent could not map KPI {kpi_name} to a data product")
                except Exception as e:
                    logger.warning(f"Error getting KPI data product mapping from Data Governance Agent: {str(e)}")
            
            # Fall back to KPI attributes if Data Governance Agent mapping failed
            if not data_product_id:
                data_product_id = kpi.data_product_id if hasattr(kpi, 'data_product_id') and kpi.data_product_id else "FI_Star_Schema"
                logger.info(f"Using fallback data product ID for KPI {kpi_name}: {data_product_id}")
            
            # Create KPI definition with mapped data product
            return KPIDefinition(
                name=kpi_name,
                description=kpi.description if hasattr(kpi, 'description') else "",
                business_processes=kpi.business_processes if hasattr(kpi, 'business_processes') else [],
                calculation=kpi.calculation if hasattr(kpi, 'calculation') else "",
                data_product_id=data_product_id,
                thresholds=kpi.thresholds if hasattr(kpi, 'thresholds') else {},
                diagnostic_questions=kpi.diagnostic_questions if hasattr(kpi, 'diagnostic_questions') else []
            )
        except Exception as e:
            logger.error(f"Error converting KPI to KPIDefinition: {str(e)}")
            return None
            
    async def _get_kpi_value(self, kpi_definition: KPIDefinition, timeframe: TimeFrame, comparison_type: ComparisonType, filters: Dict[str, Any]) -> Optional[KPIValue]:
        """
        Get the actual value of a KPI from the data product.
        
        Args:
            kpi_definition: KPI definition to get value for
            timeframe: Time frame to get value for
            comparison_type: Type of comparison to make
            filters: Additional filters to apply
            
        Returns:
            KPIValue object with actual and comparison values
        """
        try:
            # Generate SQL for the KPI
            sql = self._generate_sql_for_kpi(kpi_definition, timeframe, filters)
            
            # Execute SQL using Data Product Agent
            if not self.data_product_agent:
                logger.error("Data Product Agent not available")
                return None
                
            # Create SQL execution request
            request = SQLExecutionRequest(
                sql=sql,
                data_product_id=kpi_definition.data_product_id
            )
            
            # Execute SQL
            result = await self.data_product_agent.execute_sql(request)
            
            if not result or not result.rows:
                logger.warning(f"No data returned for KPI {kpi_definition.name}")
                return None
                
            # Extract value from result
            value = result.rows[0][0] if result.rows and len(result.rows[0]) > 0 else None
            
            # Get comparison value if needed
            comparison_value = None
            if comparison_type != ComparisonType.NONE:
                comparison_sql = self._generate_sql_for_kpi(
                    kpi_definition, 
                    self._get_comparison_timeframe(timeframe, comparison_type),
                    filters
                )
                
                comparison_request = SQLExecutionRequest(
                    sql=comparison_sql,
                    data_product_id=kpi_definition.data_product_id
                )
                
                comparison_result = await self.data_product_agent.execute_sql(comparison_request)
                comparison_value = comparison_result.rows[0][0] if comparison_result.rows and len(comparison_result.rows[0]) > 0 else None
            
            # Create KPI value object
            return KPIValue(
                kpi_name=kpi_definition.name,
                value=value,
                comparison_value=comparison_value,
                comparison_type=comparison_type,
                timeframe=timeframe,
                timestamp=datetime.now().isoformat()
            )
        except Exception as e:
            logger.error(f"Error getting KPI value: {str(e)}")
            return None
            
    def _kpi_matches_domains(self, kpi: KPI, target_domains: List[str]) -> bool:
        """
        Check if a KPI is relevant to any of the specified target domains.
        
        This method is domain-agnostic and works with any business process prefix.
        Handles KPIs without business_processes attribute or with domain in other attributes.
        """
        # Handle case where business_processes attribute doesn't exist
        if not hasattr(kpi, 'business_processes') or not kpi.business_processes:
            # For MVP, include all Finance KPIs if target domain is Finance
            if 'Finance' in target_domains:
                # Try to determine if it's a Finance KPI from other attributes
                if hasattr(kpi, 'domain') and isinstance(kpi.domain, str):
                    return kpi.domain == 'Finance' or 'finance' in kpi.domain.lower()
                if hasattr(kpi, 'name') and isinstance(kpi.name, str):
                    return 'finance' in kpi.name.lower()
                # Default to including the KPI if we can't determine its domain
                return True
            return False
            
        # Normal case with business_processes attribute
        for process in kpi.business_processes:
            for domain in target_domains:
                if isinstance(process, str) and process.startswith(f"{domain}:"):
                    return True
        return False
            
    async def _convert_to_kpi_definition(self, kpi: KPI) -> Optional[KPIDefinition]:
        """
        Convert from registry KPI model to our internal KPIDefinition model.
        """
        try:
            if not hasattr(kpi, 'name') or not kpi.name:
                logger.warning("KPI missing name, skipping conversion")
                return None
            
            # Map thresholds to our format - YAML structure uses specific fields
            thresholds = {}
            if hasattr(kpi, 'thresholds') and kpi.thresholds:
                for threshold in kpi.thresholds:
                    # Check if threshold is a dict (from YAML) or an object
                    if isinstance(threshold, dict):
                        # Handle dict-based threshold
                        if 'comparison_type' in threshold:
                            # Using the green threshold as a representative value
                            if 'green_threshold' in threshold:
                                severity = SituationSeverity.INFORMATION
                                thresholds[severity] = threshold['green_threshold']
                            if 'yellow_threshold' in threshold:
                                severity = SituationSeverity.WARNING
                                thresholds[severity] = threshold['yellow_threshold']
                            if 'red_threshold' in threshold:
                                severity = SituationSeverity.CRITICAL
                                thresholds[severity] = threshold['red_threshold']
                    else:
                        # Handle object-based threshold
                        # Check if using new structure with comparison_type, green/yellow/red_threshold
                        if hasattr(threshold, 'comparison_type'):
                            # Using the green threshold as a representative value
                            if hasattr(threshold, 'green_threshold'):
                                severity = SituationSeverity.INFORMATION
                                thresholds[severity] = threshold.green_threshold
                            # Also add warning threshold if available
                            if hasattr(threshold, 'yellow_threshold'):
                                severity = SituationSeverity.MEDIUM
                                thresholds[severity] = threshold.yellow_threshold
                            # Also add critical threshold if available
                            if hasattr(threshold, 'red_threshold'):
                                severity = SituationSeverity.CRITICAL
                                thresholds[severity] = threshold.red_threshold
                        else:
                            # Fallback to old structure (level/type/severity)
                            severity = None
                            threshold_type = None
                            if threshold_type:
                                if isinstance(threshold_type, str) and threshold_type.lower() in ["warning", "warn", "yellow"]:
                                    severity = SituationSeverity.MEDIUM
                                elif isinstance(threshold_type, str) and threshold_type.lower() in ["critical", "error", "red", "alert"]:
                                    severity = SituationSeverity.CRITICAL
                                else:
                                    severity = SituationSeverity.MEDIUM
                            else:
                                severity = SituationSeverity.MEDIUM
                            # Get threshold value
                            threshold_value = None
                            if hasattr(threshold, 'value'):
                                threshold_value = threshold.value
                            
                            if severity and threshold_value is not None:
                                thresholds[severity] = threshold_value
            
            # If no thresholds were found, add default ones
            if not thresholds:
                thresholds = {
                    SituationSeverity.WARNING: 0.0,
                    SituationSeverity.CRITICAL: -10.0
                }
            
            # Extract dimensions
            dimensions = []
            if hasattr(kpi, 'dimensions') and kpi.dimensions:
                dimensions = kpi.dimensions
            
            # Map business processes - handle business_process_ids attribute in YAML
            business_processes = []
            
            # Check for business_process_ids first (new structure in YAML)
            if hasattr(kpi, 'business_process_ids') and kpi.business_process_ids:
                for bp_id in kpi.business_process_ids:
                    # Convert snake_case to format needed by BusinessProcess enum
                    try:
                        bp_name = bp_id.replace("finance_", "").upper()
                        bp = getattr(BusinessProcess, bp_name)
                        business_processes.append(bp)
                    except (AttributeError, ValueError):
                        # Add as string for compatibility
                        finance_bp = f"Finance: {bp_id.replace('finance_', '').replace('_', ' ').title()}"
                        business_processes.append(finance_bp)
            
            # Also check business_processes for backward compatibility
            elif hasattr(kpi, 'business_processes') and kpi.business_processes:
                for bp_str in kpi.business_processes:
                    if isinstance(bp_str, str) and bp_str.startswith("Finance: "):
                        try:
                            bp_name = bp_str.replace("Finance: ", "").upper().replace(" ", "_")
                            bp = getattr(BusinessProcess, bp_name)
                            business_processes.append(bp)
                        except (AttributeError, ValueError):
                            # Keep as string for compatibility
                            business_processes.append(bp_str)
            
            # For testing purposes, use a default business process if none found
            if not business_processes:
                try:
                    # Add default Finance business processes
                    business_processes = [BusinessProcess.PROFITABILITY_ANALYSIS]
                except:
                    # Keep as string if enum not available
                    business_processes = ["Finance: Profitability Analysis"]
            
            # Get SQL query for KPI calculation
            sql_query = ""
            if hasattr(kpi, 'sql_query') and kpi.sql_query:
                sql_query = kpi.sql_query
            
            # Determine positive_trend value based on KPI name or override
            positive_trend = True  # Default to positive trend is good
            if hasattr(kpi, 'positive_trend_is_good'):
                # Use the provided value from registry/YAML if available
                positive_trend = kpi.positive_trend_is_good
            else:
                # Otherwise infer from KPI name: cost and expense KPIs should have False
                kpi_name_lower = kpi.name.lower()
                if kpi_name_lower.startswith('cost') or 'expense' in kpi_name_lower or 'debt' in kpi_name_lower:
                    positive_trend = False
            
            # Create KPI definition with all required fields
            kpi_def = KPIDefinition(
                name=kpi.name,
                description=kpi.description if hasattr(kpi, 'description') and kpi.description else "",
                unit=kpi.unit if hasattr(kpi, 'unit') and kpi.unit else "",
                # Use sql_query as calculation for now
                calculation=sql_query, 
                thresholds=thresholds,
                dimensions=dimensions,
                business_processes=business_processes,
                # Use Data Governance Agent to get data_product_id if available
                data_product_id=await self._get_data_product_for_kpi(kpi),
                # Include the positive_trend_is_good flag
                positive_trend_is_good=positive_trend
            )
            
            return kpi_def
        except Exception as e:
            logger.error(f"Error converting KPI {kpi.name if hasattr(kpi, 'name') else 'unknown'}: {type(e).__name__}: {str(e)}")
            # Even with errors, try to return a basic KPI definition rather than None
            try:
                # Determine if this KPI name suggests a positive trend is good
                is_positive_good = True
                if hasattr(kpi, 'name'):
                    kpi_name_lower = kpi.name.lower()
                    if kpi_name_lower.startswith('cost') or 'expense' in kpi_name_lower or 'debt' in kpi_name_lower:
                        is_positive_good = False
                
                # Create default thresholds using proper enum values
                default_thresholds = {
                    SituationSeverity.MEDIUM: 0.0,
                    SituationSeverity.CRITICAL: -10.0
                }
                
                # Try to get business processes from BusinessProcess enum
                try:
                    default_business_processes = [BusinessProcess.PROFITABILITY_ANALYSIS]
                except Exception:
                    default_business_processes = ["Finance: Profitability Analysis"]
                
                # Create fallback KPI definition with required fields
                return KPIDefinition(
                    name=kpi.name if hasattr(kpi, 'name') else "unknown",
                    description=kpi.description if hasattr(kpi, 'description') and kpi.description else "",
                    unit=kpi.unit if hasattr(kpi, 'unit') and kpi.unit else "",
                    calculation="",
                    thresholds=default_thresholds,
                    dimensions=[],
                    business_processes=default_business_processes,
                    data_product_id=await self._get_data_product_for_kpi(kpi),
                    positive_trend_is_good=is_positive_good
                )
            except Exception as inner_e:
                logger.error(f"Failed to create fallback KPI definition: {str(inner_e)}")
                return None
    
    async def _get_data_product_for_kpi(self, kpi) -> str:
        """
        Get the data product ID for a KPI using the Data Governance Agent.
        
        Args:
            kpi: The KPI object to get the data product for
            
        Returns:
            The data product ID for the KPI
        """
        try:
            # First check if the KPI already has a data_product_id attribute
            if hasattr(kpi, 'data_product_id') and kpi.data_product_id:
                return kpi.data_product_id
            
            # If we have a Data Governance Agent, use it to map the KPI to a data product
            if self.data_governance_agent:
                # Get the KPI name
                kpi_name = kpi.name if hasattr(kpi, 'name') else "unknown"
                
                # Create the request
                request = KPIDataProductMappingRequest(
                    kpi_names=[kpi_name],
                    context={
                        "business_domain": "Finance" if hasattr(kpi, 'business_domain') else None
                    }
                )
                
                # Call the Data Governance Agent
                try:
                    response = await self.data_governance_agent.map_kpis_to_data_products(request)
                    
                    # Check if we got a mapping for this KPI
                    if response and response.mappings and kpi_name in response.mappings:
                        mapping = response.mappings[kpi_name]
                        logger.info(f"Data Governance Agent mapped KPI {kpi_name} to data product {mapping.data_product_id}")
                        return mapping.data_product_id
                    else:
                        logger.warning(f"Data Governance Agent did not return a mapping for KPI {kpi_name}")
                except Exception as e:
                    logger.error(f"Error calling Data Governance Agent: {type(e).__name__}: {str(e)}")
            else:
                logger.warning("Data Governance Agent not available for KPI to data product mapping")
            
            # Fall back to default
            return "FI_Star_Schema"
        except Exception as e:
            logger.error(f"Error getting data product for KPI: {type(e).__name__}: {str(e)}")
            return "FI_Star_Schema"
    
    async def _get_relevant_kpis(
        self,
        principal_context: PrincipalContext,
        business_processes: Optional[List[BusinessProcess]] = None
    ) -> Dict[str, KPIDefinition]:
        """
        Get KPIs relevant to the principal's business processes.
        
        Args:
            principal_context: Principal context with business processes
            business_processes: Optional list of business processes to filter by
            
        Returns:
            Dictionary of relevant KPI definitions
        """
        relevant_kpis = {}
        
        # Use provided business processes or fall back to principal's
        processes = business_processes or principal_context.business_processes
        
        # Convert business processes to string format used in KPI definitions
        # Use target domains from config or default to all domains
        domains = self.config.get("target_domains", ["Finance"])
        process_strings = []
        
        for domain in domains:
            for bp in processes:
                process_strings.append(f"{domain}: {bp.value.replace('_', ' ').title()}")
        
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
            if any(bp in kpi_def.business_processes for bp in process_strings):
                relevant_kpis[kpi_name] = kpi_def
        
        logger.debug(f"Found {len(relevant_kpis)} KPIs relevant to {len(processes)} business processes")
        return relevant_kpis
    
    async def _get_kpi_value(
        self,
        kpi_definition: KPIDefinition,
        timeframe: TimeFrame,
        comparison_type: Optional[ComparisonType],
        filters: Optional[Dict[str, Any]]
    ) -> Optional[KPIValue]:
        """
        Get KPI value from the Data Product MCP Service Agent.
        
        Args:
            kpi_name: Name of the KPI
            timeframe: Time frame for analysis
            comparison_type: Type of comparison
            filters: Additional filters
            
        Returns:
            KPI value with comparison if applicable
        """
        try:
            # Get KPI name from definition for logging
            kpi_name = kpi_definition.name
                
            if not kpi_definition:
                self.logger.warning(f"KPI definition is None")
                return None
                
            # Ensure we have the data product agent (lazy-init if needed)
            if not self.data_product_agent:
                logger.warning("Data Product MCP Service Agent not set on SA agent; attempting lazy retrieval from orchestrator")
                if self.orchestrator_agent:
                    try:
                        import os
                        contracts_dir = os.path.dirname(self.contract_path) if self.contract_path else "src/registry_references/data_product_registry/data_products"
                        self.data_product_agent = await self.orchestrator_agent.get_agent(
                            "A9_Data_Product_MCP_Service_Agent",
                            {"contracts_path": contracts_dir}
                        )
                    except Exception as get_e:
                        logger.warning(f"Lazy retrieval of Data Product agent failed: {str(get_e)}")
                if not self.data_product_agent:
                    logger.error(f"Data Product MCP Service Agent not initialized for KPI {kpi_name}")
                    return None
                
            # Verify data product agent is available
            if not self.data_product_agent:
                logger.error(f"Data Product MCP Service Agent not initialized for KPI {kpi_name}")
                return None
            
            # Generate SQL for the KPI based on definition, timeframe, and filters
            sql_query = self._generate_sql_for_kpi(kpi_definition, timeframe, filters)
            if not sql_query:
                self.logger.error(f"Failed to generate SQL query for KPI {kpi_name}")
                return None
                
            # Build a request_id and log the FULL SQL before execution
            request_id = f"kpi_{kpi_name}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            self.logger.info(f"[SQL][{request_id}] Primary KPI SQL for {kpi_name}: {sql_query}")

            # Create SQL execution request using protocol-compliant fields
            sql_exec_request = SQLExecutionRequest(
                request_id=request_id,
                sql=sql_query,
                context={
                    "kpi_name": kpi_name,
                    "timeframe": getattr(timeframe, "name", str(timeframe)),
                    "filters": filters or {}
                },
                principal_context=None,
                principal_id="default"  # Add principal_id to fix validation error
            )

            # Execute the query via the Data Product MCP Service Agent
            try:
                self.logger.info(f"[SQL][{request_id}] Executing primary SQL for KPI {kpi_name}")
                sql_exec_response = await self.data_product_agent.execute_sql(sql_exec_request)

                # Check response status
                if getattr(sql_exec_response, "status", "error") != "success":
                    self.logger.error(f"[SQL][{request_id}] SQL execution failed for KPI {kpi_name}: {getattr(sql_exec_response, 'error_message', 'unknown error')}")
                    return None

                # Validate rows
                rows = getattr(sql_exec_response, "rows", [])
                if not rows:
                    self.logger.warning(f"[SQL][{request_id}] No data returned for KPI {kpi_name}")
                    return None

                # Extract the KPI value from the first row/first column
                try:
                    first_row = rows[0]
                    if first_row is None:
                        self.logger.warning(f"[SQL][{request_id}] First row is None for KPI {kpi_name}")
                        return None
                    if isinstance(first_row, list):
                        if not first_row or first_row[0] is None:
                            self.logger.warning(f"[SQL][{request_id}] Empty/None first column in list row for KPI {kpi_name}: {first_row}")
                            return None
                        current_value = float(first_row[0])
                    elif isinstance(first_row, dict):
                        if not first_row:
                            self.logger.warning(f"[SQL][{request_id}] Empty dict row for KPI {kpi_name}")
                            return None
                        first_val = next(iter(first_row.values()))
                        if first_val is None:
                            self.logger.warning(f"[SQL][{request_id}] None value in first column of dict row for KPI {kpi_name}: {first_row}")
                            return None
                        current_value = float(first_val)
                    else:
                        current_value = float(first_row)
                    self.logger.info(f"[SQL][{request_id}] Extracted KPI value for {kpi_name}: {current_value}")
                except (ValueError, TypeError, IndexError, StopIteration) as e:
                    self.logger.error(f"[SQL][{request_id}] Error parsing KPI value: {str(e)}, raw row: {rows[0] if rows else None}")
                    return None

            except Exception as query_error:
                self.logger.error(f"[SQL][{request_id}] Error executing primary SQL for KPI {kpi_name}: {str(query_error)}")
                return None
            
            # For testing/MVP when comparison not available, return basic KPI value
            if not comparison_type:
                return KPIValue(
                    kpi_name=kpi_name,
                    value=current_value,
                    comparison_value=None,
                    comparison_type=None,
                    timeframe=timeframe,
                    dimensions=filters,
                    percent_change=None
                )
            
            # If comparison is requested, get the comparison value
            comparison_value = None
            try:
                comparison_sql = self._generate_sql_for_kpi_comparison(
                    kpi_definition, 
                    timeframe, 
                    comparison_type, 
                    filters
                )
                if comparison_sql:
                    comp_request_id = f"kpi_comp_{kpi_name}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                    self.logger.info(f"[SQL][{comp_request_id}] Comparison SQL for {kpi_name}: {comparison_sql}")

                    # Create comparison SQL execution request using protocol-compliant fields
                    comparison_exec_request = SQLExecutionRequest(
                        request_id=comp_request_id,
                        sql=comparison_sql,
                        context={
                            "kpi_name": kpi_name,
                            "timeframe": getattr(timeframe, "name", str(timeframe)),
                            "comparison_type": getattr(comparison_type, "name", str(comparison_type)),
                            "filters": filters or {}
                        },
                        principal_context=None,
                        principal_id="default"  # Add principal_id to fix validation error
                    )

                    # Execute the comparison query
                    self.logger.info(f"[SQL][{comp_request_id}] Executing comparison SQL for KPI {kpi_name}")
                    comparison_exec_response = await self.data_product_agent.execute_sql(comparison_exec_request)

                    # Check response status and extract value
                    if getattr(comparison_exec_response, "status", "error") == "success":
                        comp_rows = getattr(comparison_exec_response, "rows", [])
                        if comp_rows:
                            try:
                                first_comp_row = comp_rows[0]
                                if isinstance(first_comp_row, list):
                                    comparison_value = float(first_comp_row[0])
                                elif isinstance(first_comp_row, dict):
                                    comparison_value = float(next(iter(first_comp_row.values())))
                                else:
                                    comparison_value = float(first_comp_row)
                                self.logger.info(f"[SQL][{comp_request_id}] Extracted comparison value for {kpi_name}: {comparison_value}")
                            except (ValueError, TypeError, IndexError) as e:
                                self.logger.error(f"[SQL][{comp_request_id}] Error parsing comparison value: {str(e)}")
                        else:
                            self.logger.warning(f"[SQL][{comp_request_id}] No comparison data returned for KPI {kpi_name}")
                    else:
                        self.logger.warning(f"[SQL][{comp_request_id}] Comparison SQL execution failed for KPI {kpi_name}: {getattr(comparison_exec_response, 'error_message', 'unknown error')}")
            except Exception as comp_error:
                self.logger.warning(f"Error getting comparison value for {kpi_name}: {str(comp_error)}")
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
                dimensions=filters,
                percent_change=percent_change
            )
        
        except Exception as e:
            logger.error(f"Error getting KPI value for {kpi_name}: {str(e)}")
            return None
    
    def _detect_kpi_situations(
        self,
        kpi_definition: KPIDefinition,
        kpi_value: KPIValue,
        principal_context: PrincipalContext
    ) -> List[Situation]:
        """
        Detect situations for a KPI based on its value and thresholds.
        
        Args:
            kpi_definition: KPI definition
            kpi_value: Current KPI value with comparison
            principal_context: Principal context for personalization
            
        Returns:
            List of detected situations
        """
        situations = []
        
        # Check for thresholds if defined
        if kpi_definition.thresholds:
            for threshold_type, threshold_value in kpi_definition.thresholds.items():
                if threshold_type == "critical_high" and kpi_value.value > threshold_value:
                    situations.append(self._create_threshold_situation(
                        kpi_definition,
                        kpi_value,
                        SituationSeverity.CRITICAL,
                        f"{kpi_definition.name} exceeds critical threshold",
                        principal_context
                    ))
                
                elif threshold_type == "high" and kpi_value.value > threshold_value:
                    situations.append(self._create_threshold_situation(
                        kpi_definition,
                        kpi_value,
                        SituationSeverity.HIGH,
                        f"{kpi_definition.name} exceeds high threshold",
                        principal_context
                    ))
                
                elif threshold_type == "critical_low" and kpi_value.value < threshold_value:
                    situations.append(self._create_threshold_situation(
                        kpi_definition,
                        kpi_value,
                        SituationSeverity.CRITICAL,
                        f"{kpi_definition.name} below critical threshold",
                        principal_context
                    ))
                
                elif threshold_type == "low" and kpi_value.value < threshold_value:
                    situations.append(self._create_threshold_situation(
                        kpi_definition,
                        kpi_value,
                        SituationSeverity.HIGH,
                        f"{kpi_definition.name} below threshold",
                        principal_context
                    ))
        
        # Check for significant changes if comparison value exists
        if kpi_value.comparison_value is not None:
            # Calculate percent change
            if kpi_value.comparison_value != 0:
                percent_change = (kpi_value.value - kpi_value.comparison_value) / abs(kpi_value.comparison_value) * 100
                
                # Determine severity based on percent change
                if abs(percent_change) >= 20:
                    severity = SituationSeverity.CRITICAL
                elif abs(percent_change) >= 10:
                    severity = SituationSeverity.HIGH
                elif abs(percent_change) >= 5:
                    severity = SituationSeverity.MEDIUM
                else:
                    severity = SituationSeverity.INFORMATION
                
                # Create situation for significant change
                if abs(percent_change) >= 5:  # Only create situations for changes >= 5%
                    change_direction = "increased" if percent_change > 0 else "decreased"
                    situations.append(self._create_threshold_situation(
                        kpi_definition,
                        kpi_value,
                        severity,
                        f"{kpi_definition.name} {change_direction} by {abs(percent_change):.1f}%",
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
    
    def _generate_sql_for_kpi(
        self,
        kpi_definition: KPIDefinition,
        timeframe: TimeFrame,
        filters: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate SQL for a KPI based on its definition, timeframe, and filters.
        
        Args:
            kpi_definition: KPI definition
            timeframe: Time frame for analysis
            filters: Additional filters
            
        Returns:
            SQL query string
        """
        # For MVP, we'll use a simplified approach
        # In production, this would be more sophisticated
        
        # Start with the base query template from the KPI definition
        base_query = ""
        calc = getattr(kpi_definition, "calculation", None)
        if isinstance(calc, dict):
            base_query = calc.get("query_template", "")
        elif isinstance(calc, str):
            # Allow plain string expressions/templates
            base_query = calc
        elif calc is None:
            self.logger.warning(f"KPI {kpi_definition.name} has no calculation; cannot generate SQL")
            return ""
        else:
            # Unsupported type
            self.logger.warning(f"KPI {kpi_definition.name} calculation has unsupported type {type(calc)}; cannot generate SQL")
            return ""
        
        # Add timeframe filter
        timeframe_condition = self._get_timeframe_condition(timeframe)
        
        # Add any additional filters
        filter_conditions = []
        if filters:
            for column, value in filters.items():
                filter_conditions.append(f'"{column}" = \'{value}\'')
        
        # Add KPI-specific filters defined in calculation if present
        if isinstance(calc, dict):
            calc_filters = calc.get("filters")
            if isinstance(calc_filters, list):
                for filter_condition in calc_filters:
                    filter_conditions.append(filter_condition)
        
        # Combine all conditions
        where_clause = ""
        all_conditions = []
        if timeframe_condition:
            all_conditions.append(timeframe_condition)
        if filter_conditions:
            all_conditions.extend(filter_conditions)
        
        if all_conditions:
            where_clause = f"WHERE {' AND '.join(all_conditions)}"
        
        # Construct the final query
        view_name = "FI_Star_View"  # From the contract
        # If base_query looks like a full SELECT, pass through; else build SELECT
        base_lower = base_query.strip().lower()
        if base_lower.startswith("select "):
            sql = base_query
        else:
            # Support inline WHERE in calculation strings like "SUM(col) WHERE ..."
            expr = base_query
            inline_where = None
            if " where " in base_lower:
                idx = base_lower.find(" where ")
                expr = base_query[:idx]
                inline_where = base_query[idx + len(" where "):]  # preserve original casing/content
            # Merge WHERE clauses
            merged_conditions = []
            if inline_where:
                merged_conditions.append(f"({inline_where.strip()})")
            if where_clause.strip().startswith("WHERE "):
                merged_conditions.append(where_clause.strip()[6:])
            final_where = f" WHERE {' AND '.join(merged_conditions)}" if merged_conditions else ""
            sql = f"SELECT {expr.strip()} FROM {view_name}{final_where}"

        return sql
    
    def _generate_sql_for_kpi_comparison(
        self,
        kpi_definition: KPIDefinition,
        timeframe: TimeFrame,
        comparison_type: ComparisonType,
        filters: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate SQL for a KPI comparison.
        
        Args:
            kpi_definition: KPI definition
            timeframe: Current time frame
            comparison_type: Type of comparison
            filters: Additional filters
            
        Returns:
            SQL query string for comparison
        """
        # For MVP, we'll use a simplified approach
        # In production, this would be more sophisticated
        
        # Determine the comparison timeframe based on the comparison type
        comparison_timeframe = timeframe
        if comparison_type == ComparisonType.YEAR_OVER_YEAR:
            # Use same timeframe but previous year
            comparison_timeframe = self._get_previous_year_timeframe(timeframe)
        elif comparison_type == ComparisonType.QUARTER_OVER_QUARTER:
            # Use previous quarter
            comparison_timeframe = self._get_previous_quarter_timeframe(timeframe)
        elif comparison_type == ComparisonType.MONTH_OVER_MONTH:
            # Use previous month
            comparison_timeframe = self._get_previous_month_timeframe(timeframe)
        
        # Generate SQL with the comparison timeframe
        return self._generate_sql_for_kpi(kpi_definition, comparison_timeframe, filters)
    
    def _get_timeframe_condition(self, timeframe: TimeFrame) -> str:
        """
        Get SQL condition for a timeframe.
        
        Args:
            timeframe: Time frame enum
            
        Returns:
            SQL condition string
        """
        # For MVP, we'll use a simplified approach with fiscal flags
        if timeframe == TimeFrame.CURRENT_MONTH:
            return '"Fiscal MTD Flag" = 1'
        elif timeframe == TimeFrame.CURRENT_QUARTER:
            return '"Fiscal QTD Flag" = 1'
        elif timeframe == TimeFrame.CURRENT_YEAR:
            return '"Fiscal YTD Flag" = 1'
        elif timeframe == TimeFrame.YEAR_TO_DATE:
            return '"Fiscal YTD Flag" = 1'
        elif timeframe == TimeFrame.QUARTER_TO_DATE:
            return '"Fiscal QTD Flag" = 1'
        elif timeframe == TimeFrame.MONTH_TO_DATE:
            return '"Fiscal MTD Flag" = 1'
        else:
            # Default to current quarter
            return '"Fiscal QTD Flag" = 1'
    
    def _get_previous_year_timeframe(self, current_timeframe: TimeFrame) -> TimeFrame:
        """Get equivalent timeframe for previous year."""
        # For MVP, simplistic implementation
        return current_timeframe
    
    def _get_previous_quarter_timeframe(self, current_timeframe: TimeFrame) -> TimeFrame:
        """Get equivalent timeframe for previous quarter."""
        # For MVP, simplistic implementation
        return current_timeframe
    
    def _get_previous_month_timeframe(self, current_timeframe: TimeFrame) -> TimeFrame:
        """Get equivalent timeframe for previous month."""
        # For MVP, simplistic implementation
        return current_timeframe
        
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
    
    def _generate_sql_for_query(
        self,
        query: str,
        kpi_values: List[KPIValue]
    ) -> Optional[str]:
        """
        Generate SQL for a natural language query.
        
        Args:
            query: Natural language query
            kpi_values: KPI values related to the query
            
        Returns:
            SQL query string or None
        """
        # For MVP, we'll return a simplified SQL
        # In production, this would use the NLP Interface Agent
        
        if not kpi_values:
            return None
        
        # Get the first KPI for simplicity
        kpi_value = kpi_values[0]
        kpi_def = self.kpi_registry.get(kpi_value.kpi_name)
        
        if not kpi_def:
            return None
        
        # Generate a simple SQL query for the KPI
        return self._generate_sql_for_kpi(
            kpi_def,
            kpi_value.timeframe,
            kpi_value.dimensions
        )
    
    def _generate_answer_for_query(
        self,
        query: str,
        kpi_values: List[KPIValue]
    ) -> str:
        """
        Generate an answer for a natural language query.
        
        Args:
            query: Natural language query
            kpi_values: KPI values related to the query
            
        Returns:
            Answer string
        """
        # For MVP, we'll generate a simple answer
        # In production, this would use the LLM Service Agent
        
        if not kpi_values:
            return "I don't have enough information to answer your question."
        
        # Format the KPI values in the answer
        kpi_descriptions = []
        for kpi_value in kpi_values:
            kpi_def = self.kpi_registry.get(kpi_value.kpi_name)
            if not kpi_def:
                continue
                
            description = f"{kpi_value.kpi_name} is {kpi_value.value}"
            
            if kpi_value.comparison_value is not None:
                percent_change = 0
                if kpi_value.comparison_value != 0:
                    percent_change = (kpi_value.value - kpi_value.comparison_value) / abs(kpi_value.comparison_value) * 100
                
                comparison_desc = f"compared to {kpi_value.comparison_value} "
                if kpi_value.comparison_type:
                    comparison_desc += f"({kpi_value.comparison_type.value}), "
                
                change_direction = "up" if percent_change > 0 else "down"
                comparison_desc += f"which is {change_direction} {abs(percent_change):.1f}%"
                
                description += f", {comparison_desc}"
            
            kpi_descriptions.append(description)
        
        if query.lower().startswith("what is"):
            return f"Based on the current data, {'. '.join(kpi_descriptions)}."
        elif query.lower().startswith("how"):
            return f"Based on my analysis, {'. '.join(kpi_descriptions)}."
        else:
            return f"Here's what I found: {'. '.join(kpi_descriptions)}."


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
