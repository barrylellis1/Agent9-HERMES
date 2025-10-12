# Windsurf Cascade Prompt Templates for Agent9

## Use These Exact Prompts to Control Cascade Behavior

### PRD Reading Prompt
```
STEP 1 - PRD ANALYSIS REQUIRED:

Read docs/prd/agents/a9_{agent_name}_agent_prd.md and provide:
1. Agent purpose and responsibilities
2. Required input/output models
3. Key functional requirements
4. Integration points with other agents
5. Any special compliance notes

DO NOT write any code until I approve your PRD analysis.
REFERENCE: Agent9_Agent_Design_Standards.md for compliance requirements.
```

### Implementation Planning Prompt  
```
STEP 2 - IMPLEMENTATION PLAN REQUIRED:

Based on the PRD analysis, create an implementation plan that includes:
1. Pydantic v2 request/response models
2. Agent class structure following A9 template
3. Required protocol entrypoints (check_access, process_request)
4. Integration with existing HybridWorkflowOrchestrator
5. Registry factory method (create_from_registry)

CONSTRAINTS:
- Use ONLY existing orchestrator patterns
- NO manual agent registration code
- NO duplicate orchestration logic
- Follow Agent9 naming conventions exactly

DO NOT write implementation code until plan is approved.
```

### Single Agent Implementation Prompt
```
STEP 3 - IMPLEMENT SINGLE AGENT:

Implement ONLY the {agent_name} agent following:
1. Use the approved implementation plan
2. Follow the Agent9 agent template exactly
3. Include all required Pydantic v2 models
4. Use ConfigDict(extra="allow") pattern
5. Implement create_from_registry factory method
6. Include proper error handling and logging

CRITICAL CONSTRAINTS:
- ONE agent file only (src/agents/new/A9_{Agent_Name}_Agent.py)
- NO orchestrator modifications
- NO test files (separate request)
- NO agent card files (separate request)
- Use .model_dump() for serialization
- Follow existing import patterns

REFERENCE: Windsurf Cascade Guardrails document for all patterns.
```

### Testing Prompt (Separate Request)
```
STEP 4 - TESTING VIA ORCHESTRATOR:

Create tests for {agent_name} that:
1. Use HybridWorkflowOrchestrator ONLY
2. NO direct agent instantiation
3. Test via orchestrator workflow execution
4. Assert on registry event logs
5. Use protocol-compliant input models
6. Follow Agent9_Test_Patterns.md

PROHIBITED:
- Direct agent instantiation: A9_Agent(config)
- Manual registration: registry.register_agent()
- Monkeypatching orchestrator methods
- Raw dict/list inputs

REQUIRED:
- All tests go through orchestrator
- Use Pydantic models for all inputs
- Assert on workflow outputs and events
```

### Debugging/Fix Prompt
```
DEBUG MODE - FIX SPECIFIC ISSUE:

Problem: {describe_specific_error}

Fix requirements:
1. Identify root cause in existing code
2. Apply minimal fix following Agent9 patterns
3. NO architectural changes
4. NO new patterns or approaches
5. Maintain Pydantic v2 compliance
6. Preserve orchestrator integration

Show ONLY the specific lines that need changing.
Reference Agent9_Agent_Design_Standards.md for compliance.
```

## ðŸŽ­ Cascade Behavior Control Phrases

### âœ… Use These Phrases:
- "Following the Agent9 template exactly..."
- "Using existing HybridWorkflowOrchestrator patterns..."
- "Referencing the PRD document for requirements..."
- "Maintaining Pydantic v2 compliance with ConfigDict..."
- "Integrating via create_from_registry factory method..."

### âŒ Stop These Phrases:
- "I'll create a new orchestration pattern..."
- "Let me build the complete system..."
- "I'll add some helper functions..."
- "Here's a more flexible approach..."
- "I'll improve the architecture..."

## ðŸ”„ Progressive Development Workflow

### Workflow 1: New Agent Development
```
Request 1: "Use PRD Reading Prompt for Principal Context Agent"
- Wait for PRD analysis
- Review and approve analysis
Request 2: "Use Implementation Planning Prompt"
- Wait for implementation plan  
- Review and approve plan
Request 3: "Use Single Agent Implementation Prompt"
- Wait for agent code
- Test integration
Request 4: "Use Testing Prompt"
- Wait for test implementation
- Verify all tests pass
```

### Workflow 2: Bug Fixing
```
Request 1: "Use Debugging/Fix Prompt with specific error"
- Wait for root cause analysis
- Review proposed fix
Request 2: "Apply the minimal fix only"
- Verify fix works
- Run full test suite
```

### Workflow 3: Integration Testing
```
Request 1: "Test {Agent_A} -> {Agent_B} handoff via orchestrator"
- Use existing workflow patterns only
- Assert on event logs and outputs
Request 2: "Test complete workflow: Situation -> Analysis -> Solution"
- End-to-end orchestrator testing
- Verify KPI metrics update
```

## ðŸš¨ Emergency Stop Commands

### When Cascade Goes Off-Track:
```
STOP - RESET TO AGENT9 STANDARDS

You are violating Agent9 design standards. 
Please:
1. Read the Windsurf Cascade Guardrails document
2. Reference the specific PRD for this agent
3. Use ONLY the provided agent template
4. NO architectural changes or new patterns

Start over with the PRD Reading Prompt.
```

### When Getting Duplicate Code:
```
STOP - CHECK EXISTING CODE

Before writing any code:
1. Check if this functionality already exists
2. Review HybridWorkflowOrchestrator for existing patterns
3. Look for similar agents in src/agents/new/
4. Use existing patterns, don't duplicate

Show me what existing code you found first.
```

### When Getting Protocol Violations:
```
STOP - PROTOCOL COMPLIANCE CHECK

Your code violates Agent9 protocols:
1. All models must use Pydantic v2 with ConfigDict
2. All agents must use create_from_registry factory
3. All tests must go through orchestrator
4. No manual registration allowed

Fix the protocol violations only, no other changes.
```

## ðŸ“ Response Format Requirements

### Required Response Structure:
```markdown
## PRD Analysis Summary
[Your analysis here]

## Implementation Approach  
[Your approach following Agent9 patterns]

## Code Implementation
[Only the requested code, following templates]

## Compliance Verification
- [ ] Follows Agent9 template
- [ ] Uses Pydantic v2 patterns
- [ ] Integrates with existing orchestrator
- [ ] No duplicate code created
- [ ] Protocol compliant
```

### Prohibited Response Patterns:
- Starting with code without PRD analysis
- Suggesting architectural improvements
- Creating multiple files in one response
- Adding "helpful" extensions not requested
- Mixing orchestrator changes with agent code

---

## ðŸŽ¯ Quick Reference Card

**Before Every Cascade Request:**
1. Specify which prompt template to use
2. Reference specific PRD document  
3. Remind about Agent9 compliance requirements
4. Ask for ONE specific deliverable only

**Common Cascade Commands:**
- "Use PRD Reading Prompt for {agent_name}"
- "Use Single Agent Implementation Prompt following approved plan"
- "Use Debugging/Fix Prompt for {specific_error}"
- "STOP - Reset to Agent9 standards"

**Success Indicators:**
- Cascade asks to read PRD first
- Follows agent template exactly
- Uses existing orchestrator patterns
- No duplicate code generation
- Pydantic v2 compliance maintained

