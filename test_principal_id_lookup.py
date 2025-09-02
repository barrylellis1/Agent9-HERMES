"""
Test script for ID-based principal profile lookups in the Principal Context Agent.
This script tests both ID-based and role-based lookups to verify backward compatibility.
"""

import asyncio
import logging
import sys
import json
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('principal_id_lookup_test.log')
    ]
)

logger = logging.getLogger("principal_id_lookup_test")

# Import agent and models
from src.agents.a9_principal_context_agent import A9_Principal_Context_Agent
from src.agents.models.principal_context_models import (
    PrincipalProfileRequest, PrincipalProfileResponse
)

async def test_id_based_lookup():
    """Test ID-based principal profile lookups."""
    logger.info("Starting ID-based principal lookup test")
    
    # Initialize the agent
    agent = await A9_Principal_Context_Agent.create()
    
    # Test cases with different principal IDs and roles
    test_cases = [
        # Test with direct ID strings
        {"input": "cfo_001", "description": "CFO by ID string"},
        {"input": "ceo_001", "description": "CEO by ID string"},
        {"input": "coo_001", "description": "COO by ID string"},
        
        # Test with direct role strings
        {"input": "CFO", "description": "CFO by role string"},
        {"input": "CEO", "description": "CEO by role string"},
        {"input": "cfo", "description": "CFO by lowercase role string"},
        
        # Test with dictionary inputs
        {"input": {"principal_id": "cfo_001", "request_id": "dict-id-1"}, "description": "CFO by ID dict"},
        {"input": {"principal_role": "CFO", "request_id": "dict-role-1"}, "description": "CFO by role dict"},
        {"input": {"principal_role": "cfo", "request_id": "dict-role-2"}, "description": "CFO by lowercase role dict"},
        
        # Test error cases
        {"input": "nonexistent_id", "description": "Nonexistent ID string"},
        {"input": "Nonexistent Role", "description": "Nonexistent role string"},
    ]
    
    results = []
    
    # Run each test case
    for i, test_case in enumerate(test_cases):
        logger.info(f"Running test case {i+1}: {test_case['description']}")
        
        # Get the input value for this test case
        input_value = test_case['input']
        
        # Call the agent with the appropriate input type
        logger.info(f"Calling get_principal_context with input: {input_value}")
        response = await agent.get_principal_context(input_value)
        
        # Log the results
        result = {
            "test_case": test_case['description'],
            "input": input_value,
            "status": response.status,
            "message": response.message,
            "role": response.context.role if response.context else None,
            "principal_id": response.context.principal_id if response.context else None,
        }
        
        logger.info(f"Test case {i+1} result: {result['status']} - {result['message']}")
        logger.info(f"  Role: {result['role']}, Principal ID: {result['principal_id']}")
        
        results.append(result)
    
    # Print summary
    logger.info("\n===== TEST RESULTS SUMMARY =====")
    for i, result in enumerate(results):
        logger.info(f"{i+1}. {result['test_case']}: {result['status']} - Role: {result['role']}, ID: {result['principal_id']}")
    
    return results

async def main():
    """Main function to run all tests."""
    try:
        logger.info("Starting principal ID lookup tests")
        results = await test_id_based_lookup()
        
        # Save results to file
        with open('principal_id_lookup_results.json', 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info("Tests completed successfully. Results saved to principal_id_lookup_results.json")
        
    except Exception as e:
        logger.error(f"Error running tests: {str(e)}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(main())
