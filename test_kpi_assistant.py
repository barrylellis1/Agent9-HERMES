"""
Test script to debug KPI Assistant Agent errors
"""
import sys
import asyncio
import logging
sys.path.insert(0, 'src')

from agents.new.a9_kpi_assistant_agent import (
    A9_KPI_Assistant_Agent,
    create_kpi_assistant_agent,
    KPISuggestionRequest,
    SchemaMetadata
)
from agents.agent_config_models import A9_KPI_Assistant_Agent_Config

# Set up detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_kpi_suggestion():
    print("=" * 80)
    print("Testing KPI Assistant Agent")
    print("=" * 80)
    
    try:
        # Create agent
        print("\n1. Creating KPI Assistant Agent...")
        config = A9_KPI_Assistant_Agent_Config()
        print(f"   Config: provider={config.llm_provider}, model={config.llm_model}")
        
        agent = create_kpi_assistant_agent(config)
        
        # Connect
        print("\n2. Connecting agent...")
        connected = await agent.connect()
        print(f"   Connected: {connected}")
        
        # Create test request
        print("\n3. Creating test request...")
        schema_metadata = SchemaMetadata(
            data_product_id="test_dp_sales_schema",
            domain="Sales",
            source_system="bigquery",
            measures=[{"name": "total_amount", "type": "numeric"}],
            dimensions=[{"name": "customer_id", "type": "string"}],
            time_columns=[{"name": "order_date", "type": "date"}],
            identifiers=[{"name": "order_id", "type": "string"}]
        )
        
        request = KPISuggestionRequest(
            schema_metadata=schema_metadata,
            num_suggestions=3
        )
        
        # Call suggest_kpis
        print("\n4. Calling suggest_kpis...")
        
        # Monkey-patch to capture LLM response
        original_call = agent._call_llm_for_suggestions
        captured_response = []
        
        async def capture_llm_response(system_prompt, user_prompt):
            result = await original_call(system_prompt, user_prompt)
            captured_response.append(result)
            return result
        
        agent._call_llm_for_suggestions = capture_llm_response
        
        response = await agent.suggest_kpis(request)
        
        print(f"\n5. Response status: {response.status}")
        if response.status == "success":
            print(f"   Suggested KPIs: {len(response.suggested_kpis)}")
            print(f"   Conversation ID: {response.conversation_id}")
            print(f"   Rationale: {response.rationale[:200]}...")
            
            if captured_response:
                print(f"\n6. LLM Response (first 1000 chars):")
                print(captured_response[0][:1000])
        else:
            print(f"   Error: {response.error_message}")
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_kpi_suggestion())
