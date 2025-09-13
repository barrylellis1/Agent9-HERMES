"""
Simple test script to verify that the Data Product Agent implements the DataProductProtocol.
"""

import os
import sys
import inspect

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the agent and protocol
from src.agents.new.a9_data_product_agent import A9_Data_Product_Agent
from src.agents.protocols.data_product_protocol import DataProductProtocol


def main():
    """Main function to verify protocol implementation."""
    print("Testing Data Product Agent Protocol Implementation")
    print("=" * 50)
    
    # Check if the agent class implements the protocol
    if issubclass(A9_Data_Product_Agent, DataProductProtocol):
        print("✓ A9_Data_Product_Agent implements DataProductProtocol")
    else:
        print("✗ A9_Data_Product_Agent does NOT implement DataProductProtocol")
    
    # Get required methods from the protocol
    protocol_methods = {
        name: method for name, method in inspect.getmembers(DataProductProtocol, inspect.isfunction)
        if not name.startswith('_')
    }
    
    print(f"\nVerifying {len(protocol_methods)} required methods:")
    
    # Check each required method
    for method_name, protocol_method in protocol_methods.items():
        # Check if method exists in agent class
        if hasattr(A9_Data_Product_Agent, method_name):
            agent_method = getattr(A9_Data_Product_Agent, method_name)
            
            # Check if method is callable
            if callable(agent_method):
                # Check if method signature matches
                agent_sig = inspect.signature(agent_method)
                protocol_sig = inspect.signature(protocol_method)
                
                # Compare parameters (excluding 'self')
                agent_params = list(agent_sig.parameters.items())[1:]  # Skip 'self'
                protocol_params = list(protocol_sig.parameters.items())
                
                if agent_params == protocol_params:
                    print(f"✓ Method '{method_name}' has correct signature")
                else:
                    print(f"✗ Method '{method_name}' has incorrect signature")
                    print(f"  Expected: {protocol_sig}")
                    print(f"  Found: {agent_sig}")
            else:
                print(f"✗ Method '{method_name}' exists but is not callable")
        else:
            print(f"✗ Method '{method_name}' is missing")
    
    print("\nProtocol verification complete.")


if __name__ == "__main__":
    main()
