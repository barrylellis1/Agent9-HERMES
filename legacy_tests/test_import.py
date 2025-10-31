"""
Simple test script to verify the Situation Awareness Agent can be imported.
"""

print("Starting import test...")

try:
    from src.agents.a9_situation_awareness_agent import A9_Situation_Awareness_Agent
    print("Successfully imported A9_Situation_Awareness_Agent")
    print("No syntax errors detected in the agent file")
except SyntaxError as e:
    print(f"Syntax error in the agent file: {e}")
except ImportError as e:
    print(f"Import error: {e}")
except Exception as e:
    print(f"Other error: {e}")

print("Import test complete")
