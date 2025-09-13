"""
Protocol definition for the Situation Awareness Agent.
Defines the interface that must be implemented by any agent providing situation awareness capabilities.
"""

from typing import Protocol, List, Dict, Any, Optional, runtime_checkable
from datetime import datetime

from src.agents.models.situation_awareness_models import (
    PrincipalContext,
    BusinessProcess,
    TimeFrame,
    ComparisonType,
    Situation,
    SituationDetectionRequest,
    SituationDetectionResponse,
    NLQueryRequest,
    NLQueryResponse,
    HITLRequest,
    HITLResponse,
)

@runtime_checkable
class SituationAwarenessProtocol(Protocol):
    """
    Protocol for Situation Awareness Agent.
    
    This protocol defines the methods that must be implemented by any agent
    providing situation awareness capabilities for KPI monitoring and analysis.
    """
    
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
        ...
    
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
        ...
    
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
        ...
    
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
        ...
    
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
        ...
