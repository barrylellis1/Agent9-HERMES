    # Define an async factory that properly awaits the agent creation
    async def async_data_product_agent_factory(config):
        if config.get("mock", False):
            return MockDataProductMCPServiceAgent()
        else:
            # Await the async create method
            return await A9_Data_Product_MCP_Service_Agent.create({
                "contracts_path": "src/contracts",
                "data_directory": "C:/Users/barry/Documents/Agent 9/SAP DataSphere Data/datasphere-content-1.7/datasphere-content-1.7/SAP_Sample_Content/CSV/FI",
                "registry_path": "src/registry/data_product/data_product_registry.yaml"  # Use YAML-based registry
            })
    
    # Override the Data Product MCP Service Agent factory with our async factory
    AgentRegistry.register_agent_factory(
        "A9_Data_Product_MCP_Service_Agent",
        async_data_product_agent_factory
    )
