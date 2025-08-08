"""
Quick script to fix the undefined tables variable in a9_data_product_mcp_service_agent.py
"""

# Simpler approach - read entire file content and do a simple string replacement
with open('src/agents/a9_data_product_mcp_service_agent.py', 'r', encoding='utf-8') as file:
    content = file.read()

# Replace the problematic line
original = '            # Original table listing\n            self.logger.info(f"Table names: {[t[0] for t in tables]}")'
replacement = '            # Table names already logged above using all_tables'

if original in content:
    print(f"Found problematic code, replacing...")
    new_content = content.replace(original, replacement)
    
    # Write back to the file
    with open('src/agents/a9_data_product_mcp_service_agent.py', 'w', encoding='utf-8') as file:
        file.write(new_content)
    print("Successfully updated the file.")
else:
    print("Could not find the problematic code pattern.")
    print("Manual fix required: Replace line 740 that refers to 'tables' with a comment.")
