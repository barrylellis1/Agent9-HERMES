import asyncio
import json
from src.agents.a9_principal_context_agent import A9_Principal_Context_Agent
from src.agents.models.situation_awareness_models import PrincipalRole

async def test_principal_profile_lookup():
    """Test principal profile lookup for different roles."""
    print("Initializing Principal Context Agent")
    agent = A9_Principal_Context_Agent()
    await agent.connect()
    
    # Print available profiles
    print("\nAvailable profiles in agent:")
    for key in agent.principal_profiles.keys():
        print(f"  - {key}")
    
    # Test CFO profile lookup
    print("\nTesting CFO profile lookup")
    cfo_context = await agent.get_principal_context(PrincipalRole.CFO)
    if cfo_context.profile:
        print("CFO profile found:")
        print(json.dumps(cfo_context.profile, indent=2))
    else:
        print("CFO profile not found!")
    
    # Test Finance Manager profile lookup
    print("\nTesting Finance Manager profile lookup")
    finance_manager_context = await agent.get_principal_context(PrincipalRole.FINANCE_MANAGER)
    if finance_manager_context.profile:
        print("Finance Manager profile found:")
        print(json.dumps(finance_manager_context.profile, indent=2))
    else:
        print("Finance Manager profile not found!")
    
    # Test CEO profile lookup
    print("\nTesting CEO profile lookup")
    ceo_context = await agent.get_principal_context("CEO")
    if ceo_context.profile:
        print("CEO profile found:")
        print(json.dumps(ceo_context.profile, indent=2))
    else:
        print("CEO profile not found!")
    
    print("\nAll tests completed")

if __name__ == "__main__":
    asyncio.run(test_principal_profile_lookup())
