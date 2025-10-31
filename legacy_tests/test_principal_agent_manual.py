"""
Manual test script for the Principal Context Agent.
This script tests the basic functionality of the agent without using pytest.
"""

# NOTE: This script uses custom response models to match the actual implementation
# of the Principal Context Agent, which differs from the models in principal_context_models.py
import asyncio
import uuid
import sys
import logging
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the project root to the path
sys.path.append('.')

from src.agents.a9_principal_context_agent import A9_Principal_Context_Agent
from src.agents.models.principal_context_models import (
    ExtractFiltersRequest,
    SetPrincipalContextRequest
)
from src.agents.models.situation_awareness_models import PrincipalContext, TimeFrame, BusinessProcess, PrincipalRole
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

# Custom models to match the actual implementation
class PrincipalProfileRequest(BaseModel):
    """Request for principal profile."""
    principal_role: str = Field(description="Role of the principal")
    request_id: str = Field(description="Unique ID for the request")

class PrincipalProfileResponse(BaseModel):
    """Response with principal profile."""
    request_id: str = Field(description="ID of the corresponding request")
    status: str = Field(description="Status of the response (success/error/warning)")
    message: Optional[str] = Field(None, description="Additional message")
    context: PrincipalContext = Field(description="Principal context")

async def test_get_principal_context():
    """Test getting principal context for different roles."""
    agent = A9_Principal_Context_Agent()
    
    # Test with string input
    logger.info("Testing get_principal_context with string input (CFO)...")
    response = await agent.get_principal_context(PrincipalRole.CFO)
    logger.info(f"Response status: {response.status}")
    if response.status == "success":
        logger.info(f"Principal role: {response.context.role}")
        logger.info(f"Business processes: {[bp.name for bp in response.context.business_processes]}")
        logger.info(f"Default filters: {response.context.default_filters}")
    else:
        logger.error(f"Error: {response.message}")
    
    # Test with model input
    logger.info("\nTesting get_principal_context with model input (CFO)...")
    request = PrincipalProfileRequest(principal_role=PrincipalRole.CFO, request_id=str(uuid.uuid4()))
    response = await agent.get_principal_context(request)
    logger.info(f"Response status: {response.status}")
    if response.status == "success":
        logger.info(f"Principal role: {response.context.role}")
        logger.info(f"Business processes: {[bp.name for bp in response.context.business_processes]}")
        logger.info(f"Default filters: {response.context.default_filters}")
    else:
        logger.error(f"Error: {response.message}")
    
    # Test with unknown role - using dict input
    logger.info("\nTesting get_principal_context with unknown role...")
    response = await agent.get_principal_context({"principal_role": "UNKNOWN_ROLE", "request_id": str(uuid.uuid4())})
    logger.info(f"Response status: {response.status}")
    logger.info(f"Message: {response.message}")

async def test_extract_filters():
    """Test extracting filters from job descriptions."""
    agent = A9_Principal_Context_Agent()
    
    # Test with valid job description
    job_description = """
    Analyze the Q2 financial performance for the North America region, 
    focusing on the Retail division's revenue growth compared to last year.
    """
    
    logger.info("Testing extract_filters with valid job description...")
    request = ExtractFiltersRequest(
        job_description=job_description,
        request_id=str(uuid.uuid4())
    )
    
    response = await agent.extract_filters(request)
    logger.info(f"Response status: {response.status}")
    if response.status == "success":
        logger.info(f"Extracted filters: {json.dumps([f.dict() for f in response.filters], indent=2)}")
    else:
        logger.error(f"Error: {response.message}")
    
    # Test with empty job description
    logger.info("\nTesting extract_filters with empty job description...")
    request = ExtractFiltersRequest(
        job_description="",
        request_id=str(uuid.uuid4())
    )
    
    response = await agent.extract_filters(request)
    logger.info(f"Response status: {response.status}")
    logger.info(f"Message: {response.message}")

async def test_set_principal_context():
    """Test setting principal context."""
    agent = A9_Principal_Context_Agent()
    
    context = PrincipalContext(
        role=PrincipalRole.CFO,
        business_processes=[BusinessProcess.PROFITABILITY_ANALYSIS, BusinessProcess.REVENUE_GROWTH],
        default_filters={"region": "North America", "division": "Retail"},
        decision_style="Analytical",
        communication_style="Concise",
        preferred_timeframes=[TimeFrame.CURRENT_QUARTER, TimeFrame.YEAR_TO_DATE]
    )
    
    logger.info("Testing set_principal_context...")
    request = SetPrincipalContextRequest(
        principal_id="test_principal",
        context_data=context.model_dump(),
        request_id=str(uuid.uuid4())
    )
    
    response = await agent.set_principal_context(request)
    logger.info(f"Response status: {response.status}")
    if response.status == "success":
        logger.info(f"Principal role: {response.context.role}")
        logger.info(f"Business processes: {[bp.name for bp in response.context.business_processes]}")
        logger.info(f"Default filters: {response.context.default_filters}")
    else:
        logger.error(f"Error: {response.message}")

async def main():
    """Run all tests."""
    logger.info("=== Testing Principal Context Agent ===")
    
    logger.info("\n=== Testing get_principal_context ===")
    await test_get_principal_context()
    
    logger.info("\n=== Testing extract_filters ===")
    await test_extract_filters()
    
    logger.info("\n=== Testing set_principal_context ===")
    await test_set_principal_context()
    
    logger.info("\n=== All tests completed ===")

if __name__ == "__main__":
    asyncio.run(main())
