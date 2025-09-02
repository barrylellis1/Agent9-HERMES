import asyncio
from src.agents.a9_principal_context_agent import A9_Principal_Context_Agent
from src.agents.models.situation_awareness_models import PrincipalRole

async def main():
    agent = A9_Principal_Context_Agent()
    await agent.connect()
    
    print("\nAvailable profiles:")
    for key in agent.principal_profiles:
        print(f"  - {key}")
    
    print("\nTesting Finance Manager lookup:")
    result = await agent.get_principal_context(PrincipalRole.FINANCE_MANAGER)
    print(f"Success: {result.profile is not None}")
    
    if result.profile:
        print(f"Name: {result.profile.get('name')}")
        print(f"Role: {result.profile.get('role')}")

if __name__ == "__main__":
    asyncio.run(main())
