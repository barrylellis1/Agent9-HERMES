"""
A9 Situation Awareness Agent

This agent provides automated situation awareness for Finance KPIs,
detecting anomalies, trends, and insights based on principal context.

MVP implementation focuses on the Finance KPIs from the FI Star Schema.
"""

import os
import asyncio
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Union, Tuple

import yaml
from pydantic import ValidationError

from src.agents.models.situation_awareness_models import (
    PrincipalContext,
    BusinessProcess,
    TimeFrame,
    ComparisonType,
    SituationSeverity,
    Situation,
    SituationDetectionRequest,
    SituationDetectionResponse,
    NLQueryRequest,
    NLQueryResponse,
    HITLRequest,
    HITLResponse,
    PrincipalRole,
    KPIValue,
    KPIDefinition,
)

# Import the external registries
from src.registry_references.principal_registry.principal_profiles import default_principal_profiles
from src.registry_references.principal_registry.principal_roles import PrincipalRole as RegistryPrincipalRole
from src.registry_references.kpi_registry.kpi_registry import KPI_REGISTRY
from src.models.kpi_models import KPI, KPIThreshold, KPIComparisonMethod

# Import the actual agent for data product interaction
from src.agents.a9_data_product_mcp_service_agent import A9_Data_Product_MCP_Service_Agent

logger = logging.getLogger(__name__)

class A9_Situation_Awareness_Agent:
    """
    Agent9 Situation Awareness Agent
    
    Detects situations based on KPI thresholds, trends, and principal context.
    Provides automated, personalized situation awareness for Finance KPIs.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Situation Awareness Agent.
        
        Args:
            config: Configuration dictionary for the agent
        """
        self.config = config
        self.name = "A9_Situation_Awareness_Agent"
        self.version = "0.1.0"
        self.kpi_registry = {}
        self.principal_profiles = {}
        
        # Initialize internal services
        self.data_product_agent = None  # Will be initialized in connect method
        self.contract_path = config.get("contract_path", "C:/Users/barry/CascadeProjects/Agent9-HERMES/src/contracts/fi_star_schema.yaml")
        
        # Load the contract and KPI definitions
        self._load_contract()
        
        # Initialize principal profiles
        self._initialize_principal_profiles()
    
    async def connect(self):
        """Initialize connections to dependent services."""
        # Initialize the Data Product MCP Service Agent using factory method pattern
        self.data_product_agent = await A9_Data_Product_MCP_Service_Agent.create(config={
            "name": "A9_Data_Product_MCP_Service_Agent",
            "data_directory": os.path.dirname(self.contract_path)
        })
        
        logger.info(f"{self.name} connected to dependent services")
        
    async def disconnect(self):
        """Disconnect from dependent services."""
        if self.data_product_agent:
            # Data Product MCP Service Agent uses close() method instead of disconnect()
            self.data_product_agent.close()
        
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
            self._load_kpi_registry()
            
            logger.info(f"Loaded {len(self.kpi_registry)} KPIs from registry and contract")
        except Exception as e:
            logger.error(f"Error loading contract or registry: {str(e)}")
            raise
    
    def _initialize_principal_profiles(self):
        """
        Initialize principal profiles for personalization by loading from the external registry.
        This ensures we use standardized principal profiles across the system.
        """
        # Load from the external registry
        for role, profile in default_principal_profiles.items():
            # Convert from registry roles to our internal model roles
            internal_role = None
            if role == RegistryPrincipalRole.CFO:
                internal_role = PrincipalRole.CFO
            elif role == RegistryPrincipalRole.MANAGER:
                internal_role = PrincipalRole.FINANCE_MANAGER
            
            # Only load profiles for roles we support in this agent
            if internal_role in [PrincipalRole.CFO, PrincipalRole.FINANCE_MANAGER]:
                # Map business processes from string format to our enum
                business_processes = []
                for bp_str in profile.business_processes:
                    if bp_str.startswith("Finance: "):
                        bp_name = bp_str.replace("Finance: ", "").upper().replace(" ", "_")
                        try:
                            bp = getattr(BusinessProcess, bp_name)
                            business_processes.append(bp)
                        except (AttributeError, ValueError):
                            logger.warning(f"Business process {bp_str} not found in BusinessProcess enum")
                
                # Map timeframes to our enum
                timeframes = []
                for tf_str in profile.typical_timeframes:
                    if tf_str == "Monthly":
                        timeframes.append(TimeFrame.CURRENT_MONTH)
                    elif tf_str == "Quarterly":
                        timeframes.append(TimeFrame.CURRENT_QUARTER)
                
                # Create our internal principal context
                self.principal_profiles[internal_role] = PrincipalContext(
                    role=internal_role,
                    business_processes=business_processes,
                    default_filters=profile.default_filters if profile.default_filters else {},
                    decision_style=profile.persona_profile.get("decision_style", "analytical"),
                    communication_style=profile.persona_profile.get("communication_style", "detailed"),
                    preferred_timeframes=timeframes if timeframes else [TimeFrame.CURRENT_MONTH]
                )
        
        logger.info(f"Initialized {len(self.principal_profiles)} principal profiles from registry")
    
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
            logger.info(f"Detecting situations for {request.principal_context.role}")
            
            # Get KPIs relevant to the principal's business processes
            relevant_kpis = self._get_relevant_kpis(
                request.principal_context,
                request.business_processes
            )
            
            # Fetch KPI values and detect situations
            situations = []
            for kpi_name, kpi_definition in relevant_kpis.items():
                kpi_value = await self._get_kpi_value(
                    kpi_name,
                    request.timeframe,
                    request.comparison_type,
                    request.filters
                )
                
                if kpi_value:
                    # Detect situations based on thresholds, trends, etc.
                    detected_situations = self._detect_kpi_situations(
                        kpi_definition,
                        kpi_value,
                        request.principal_context
                    )
                    
                    situations.extend(detected_situations)
            
            # Sort situations by severity (critical first)
            situations.sort(key=lambda s: list(SituationSeverity).index(s.severity))
            
            return SituationDetectionResponse(
                request_id=request.request_id,
                status="success",
                message=f"Detected {len(situations)} situations",
                situations=situations
            )
        
        except Exception as e:
            logger.error(f"Error detecting situations: {str(e)}")
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
            NLQueryResponse with the answer and related KPI values
        """
        try:
            logger.info(f"Processing NL query: {request.query}")
            
            # For MVP, we'll use a simple keyword-based approach
            # In production, this would use the NLP Interface Agent
            
            # Extract KPI names and business processes from the query
            query_lower = request.query.lower()
            kpi_values = []
            
            for kpi_name in self.kpi_registry.keys():
                if kpi_name.lower() in query_lower:
                    kpi_value = await self._get_kpi_value(
                        kpi_name,
                        TimeFrame.CURRENT_QUARTER,  # Default timeframe
                        ComparisonType.QUARTER_OVER_QUARTER,  # Default comparison
                        {}
                    )
                    if kpi_value:
                        kpi_values.append(kpi_value)
            
            # Generate SQL for the query (simplified for MVP)
            sql_query = self._generate_sql_for_query(request.query, kpi_values)
            
            # Generate answer based on KPI values and query
            answer = self._generate_answer_for_query(request.query, kpi_values)
            
            return NLQueryResponse(
                request_id=request.request_id,
                status="success",
                answer=answer,
                kpi_values=kpi_values,
                sql_query=sql_query
            )
        
        except Exception as e:
            logger.error(f"Error processing NL query: {str(e)}")
            return NLQueryResponse(
                request_id=request.request_id,
                status="error",
                message=f"Error processing query: {str(e)}",
                answer="I'm sorry, I couldn't process your query."
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
        relevant_kpis = self._get_relevant_kpis(principal_context, [business_process] if business_process else None)
        
        # Collect diagnostic questions from KPI definitions
        questions = []
        for kpi_name, kpi_def in relevant_kpis.items():
            if kpi_def.diagnostic_questions:
                questions.extend(kpi_def.diagnostic_questions)
        
        return questions[:5]  # Limit to top 5 questions
    
    async def get_kpi_definitions(
        self,
        principal_context: PrincipalContext,
        business_process: Optional[BusinessProcess] = None
    ) -> Dict[str, Any]:
        """
        Get KPI definitions relevant to the principal and business process.
        
        Args:
            principal_context: Context of the principal
            business_process: Optional specific business process
            
        Returns:
            Dictionary of KPI definitions
        """
        return self._get_relevant_kpis(principal_context, [business_process] if business_process else None)
    
    def _load_kpi_registry(self):
        """
        Load KPIs from the external KPI registry.
        Converts from KPI model to our internal KPIDefinition model.
        """
        self.kpi_registry = {}
        target_domains = self.config.get("target_domains", None)
        
        for kpi in KPI_REGISTRY:
            # If target domains specified, filter by domain
            if target_domains and not self._kpi_matches_domains(kpi, target_domains):
                continue
                
            # Convert and add to registry
            self.kpi_registry[kpi.name] = self._convert_to_kpi_definition(kpi)
    
    def _kpi_matches_domains(self, kpi: KPI, target_domains: List[str]) -> bool:
        """
        Check if a KPI is relevant to any of the specified target domains.
        
        This method is domain-agnostic and works with any business process prefix.
        """
        if not kpi.business_processes:
            return False
            
        for process in kpi.business_processes:
            for domain in target_domains:
                if process.startswith(f"{domain}:"):
                    return True
        return False
        
    def _convert_to_kpi_definition(self, kpi: KPI) -> KPIDefinition:
        """
        Convert from registry KPI model to our internal KPIDefinition model.
        """
        # Map comparison methods
        comparison_methods = []
        if hasattr(kpi, "comparison_methods") and kpi.comparison_methods:
            for method in kpi.comparison_methods:
                comparison_methods.append({
                    "type": method.type,
                    "description": method.description,
                    "timeframe_logic": method.timeframe_logic
                })
        
        # Create KPI definition from registry KPI
        return KPIDefinition(
            name=kpi.name,
            description=kpi.description,
            type=kpi.type,
            calculation=kpi.calculation,
            aggregation=kpi.aggregation,
            base_column=kpi.base_column,
            join_tables=kpi.join_tables,
            filters=kpi.filters,
            dimensions=kpi.dimensions if hasattr(kpi, "dimensions") else [],
            thresholds={
                "warning": kpi.thresholds.warning if hasattr(kpi.thresholds, "warning") else None,
                "critical": kpi.thresholds.critical if hasattr(kpi.thresholds, "critical") else None
            },
            positive_trend_is_good=kpi.positive_trend_is_good if hasattr(kpi, "positive_trend_is_good") else True,
            business_processes=kpi.business_processes if hasattr(kpi, "business_processes") else [],
            comparison_methods=comparison_methods,
            # Add required data_product_id field
            data_product_id=kpi.data_product_id if hasattr(kpi, "data_product_id") else "FI_Star_Schema"
        )
    
    def _get_relevant_kpis(
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
            # Skip if KPI has no business processes defined
            if not kpi_def.business_processes:
                continue
                
            # Check if KPI matches any of the relevant business processes
            if any(bp in kpi_def.business_processes for bp in process_strings):
                relevant_kpis[kpi_name] = kpi_def
        
        logger.debug(f"Found {len(relevant_kpis)} KPIs relevant to {len(processes)} business processes")
        return relevant_kpis
    
    async def _get_kpi_value(
        self,
        kpi_name: str,
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
            # For MVP, we'll use a simplified approach to get KPI values
            # In production, this would use the Data Product MCP Service Agent's API
            
            # Get KPI definition
            kpi_def = self.kpi_registry.get(kpi_name)
            if not kpi_def:
                logger.warning(f"KPI {kpi_name} not found in registry")
                return None
            
            # Generate SQL for the KPI based on definition, timeframe, and filters
            sql_query = self._generate_sql_for_kpi(kpi_def, timeframe, filters)
            
            # Execute the query via the Data Product MCP Service Agent
            result = await self.data_product_agent.execute_query(sql_query)
            
            if not result or not result.get("data") or len(result["data"]) == 0:
                logger.warning(f"No data returned for KPI {kpi_name}")
                return None
            
            # Extract the KPI value from the result
            current_value = float(result["data"][0][0])
            
            # If comparison is requested, get the comparison value
            comparison_value = None
            if comparison_type:
                comparison_sql = self._generate_sql_for_kpi_comparison(
                    kpi_def, 
                    timeframe, 
                    comparison_type, 
                    filters
                )
                comparison_result = await self.data_product_agent.execute_query(comparison_sql)
                if comparison_result and comparison_result.get("data") and len(comparison_result["data"]) > 0:
                    comparison_value = float(comparison_result["data"][0][0])
            
            return KPIValue(
                kpi_name=kpi_name,
                value=current_value,
                comparison_value=comparison_value,
                comparison_type=comparison_type,
                timeframe=timeframe,
                dimensions=filters
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
        base_query = kpi_definition.calculation.get("query_template", "")
        
        # Add timeframe filter
        timeframe_condition = self._get_timeframe_condition(timeframe)
        
        # Add any additional filters
        filter_conditions = []
        if filters:
            for column, value in filters.items():
                filter_conditions.append(f'"{column}" = \'{value}\'')
        
        # Add KPI-specific filters
        if kpi_definition.calculation.get("filters"):
            for filter_condition in kpi_definition.calculation.get("filters"):
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
        sql = f"SELECT {base_query} FROM {view_name} {where_clause}"
        
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
