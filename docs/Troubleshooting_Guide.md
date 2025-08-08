# Agent9 Troubleshooting Guide

## Introduction

This guide addresses common issues that you might encounter while implementing the Agent9 platform during the hackathon. It provides solutions, workarounds, and best practices to help you resolve problems quickly.

## Common Issues and Solutions

### Registry-Related Issues

#### Issue: Agent Not Found in Registry

```
KeyError: 'Agent A9_My_Agent not found in registry'
```

**Solution:**
1. Ensure your agent is properly registered with the Agent Registry
2. Check that you're using the correct agent name (case-sensitive)
3. Verify that the `create_from_registry` method is implemented correctly
4. Check for any initialization errors in the agent's constructor

#### Issue: Registry Integration Failure

```
AttributeError: 'NoneType' object has no attribute 'register_agent'
```

**Solution:**
1. Ensure the registry is properly initialized before passing it to the agent
2. Check that you're awaiting the registry initialization if it's async
3. Verify that the registry has the expected methods and attributes

### Protocol Compliance Issues

#### Issue: Invalid Model Type

```
ValueError: Input must be a SituationInput model
```

**Solution:**
1. Ensure you're passing the correct model type to agent methods
2. Check that your models inherit from the correct base classes
3. Verify that model fields are properly defined and validated

#### Issue: Missing Required Fields

```
ValidationError: 1 validation error for SituationOutput
status
  field required (type=value_error.missing)
```

**Solution:**
1. Ensure all required fields are included in your model instances
2. Check the model definition for any required fields
3. Verify that you're setting all required fields in your code

### LLM Integration Issues

#### Issue: LLM API Key Not Found

```
ValueError: OpenAI API key not found
```

**Solution:**
1. Ensure your `.env` file contains the required API keys
2. Check that you're loading environment variables correctly
3. Verify that the API key is properly passed to the LLM client

#### Issue: LLM Rate Limit Exceeded

```
RateLimitError: Rate limit exceeded
```

**Solution:**
1. Implement exponential backoff and retry logic
2. Reduce the number of concurrent requests
3. Consider using a different LLM provider or API key

### Orchestration Issues

#### Issue: Workflow Step Validation Failed

```
ValueError: Invalid workflow step: method 'analyze_situation' not found in agent 'A9_My_Agent'
```

**Solution:**
1. Ensure the method exists in the agent class
2. Check that the method name is spelled correctly
3. Verify that the method has the correct signature

#### Issue: Concurrency Issues

```
RuntimeError: This event loop is already running
```

**Solution:**
1. Ensure you're using `asyncio` correctly
2. Check for any blocking operations in async code
3. Verify that you're not creating multiple event loops

### Testing Issues

#### Issue: Test Harness Failure

```
AssertionError: Expected status 'success', got 'error'
```

**Solution:**
1. Check the agent's error handling logic
2. Verify that the test input data is valid
3. Look for any missing dependencies or configuration

#### Issue: Mock Registry Issues

```
AttributeError: 'MockRegistry' object has no attribute 'get_agent'
```

**Solution:**
1. Ensure your mock registry implements all required methods
2. Check that the mock registry is properly initialized
3. Verify that the mock registry is compatible with your agent

## Best Practices for Debugging

### 1. Use Structured Logging

```python
# Good practice
self.logger.error(f"Data processing failed: {str(e)}", extra={
    "agent": self.__class__.__name__,
    "method": "process_data",
    "input_id": input_data.id,
    "error_type": type(e).__name__
})
```

### 2. Implement Comprehensive Error Handling

```python
async def process_data(self, input_data):
    try:
        # Process data
        return SuccessOutput(data=result)
    except DataNotFoundError as e:
        self.logger.error(f"Data not found: {str(e)}")
        return ErrorOutput(error=f"Data not found: {str(e)}")
    except ValidationError as e:
        self.logger.error(f"Validation error: {str(e)}")
        return ErrorOutput(error=f"Validation error: {str(e)}")
    except Exception as e:
        self.logger.error(f"Unexpected error: {str(e)}")
        return ErrorOutput(error=f"Internal error: {str(e)}")
```

### 3. Use Debugging Tools

- Use `print` statements strategically
- Leverage Python's built-in `logging` module
- Use a debugger (e.g., pdb, VS Code debugger)

### 4. Isolate Components

When debugging complex issues:
1. Test each agent in isolation
2. Use mock objects for dependencies
3. Gradually integrate components

## Advanced Troubleshooting

### Registry Debugging

To debug registry-related issues, you can use the following approach:

```python
# Debug registry state
async def debug_registry(registry):
    agents = await registry.list_agents()
    print(f"Registered agents: {agents}")
    
    for agent_name in agents:
        agent = await registry.get_agent(agent_name)
        print(f"Agent {agent_name}: {type(agent)}")
        
        # Check agent methods
        methods = [m for m in dir(agent) if not m.startswith('_') and callable(getattr(agent, m))]
        print(f"Available methods: {methods}")
```

### Protocol Validation

To validate protocol compliance:

```python
# Validate model against protocol
def validate_protocol(model, expected_type):
    if not isinstance(model, expected_type):
        print(f"Model type mismatch: expected {expected_type.__name__}, got {type(model).__name__}")
        return False
    
    # Check required fields
    missing_fields = []
    for field_name, field in expected_type.__annotations__.items():
        if not hasattr(model, field_name):
            missing_fields.append(field_name)
    
    if missing_fields:
        print(f"Missing required fields: {missing_fields}")
        return False
    
    return True
```

## Getting Additional Help

If you're still experiencing issues:

1. Check the [Agent9 Agent Design Standards](Agent9_Agent_Design_Standards.md)
2. Review the relevant [PRDs](prd/index.md)
3. Examine the reference implementations in `src/registry-references/`
4. Use the test harnesses to validate your implementation
