# 🚨 WINDSURF CASCADE DEVELOPMENT GUARDRAILS FOR AGENT9 🚨

**READ THIS BEFORE ANY CODE GENERATION**

## 🛑 CRITICAL STOPS (NEVER DO THESE)

### ❌ PROHIBITED CODE PATTERNS
```python
# NEVER - Manual agent registration
registry.register_agent("agent_name", agent_instance)
agent_registry.add_agent(agent)

# NEVER - Direct agent instantiation in tests/production
agent = A9_Principal_Context_Agent(config)

# NEVER - Pydantic v1 patterns
class Config:  # This is v1 - FORBIDDEN
    extra = "allow"

# NEVER - Old serialization methods
agent.dict()  # Use .model_dump() instead
agent.json()  # Use .model_dump_json() instead

# NEVER - Hardcoded secrets
api_key = "sk-1234567890"  # Use os.getenv() instead
```

### ❌ ARCHITECTURE VIOLATIONS
- Creating duplicate orchestrator logic
- Building agent-to-agent direct communication
- Implementing manual discovery/registration systems
- Creating non-protocol-compliant inputs/outputs

## ✅ MANDATORY PATTERNS

### 🔥 AGENT CLASS TEMPLATE
```python
from typing import Dict, Any, Optional
from pydantic import ConfigDict
from ..shared.a9_agent_base_model import A9AgentBaseModel
from ..registries.agent_registry import AgentRegistry

class A9_{AGENT_NAME}_Agent_Request(A9AgentBaseModel):
    """Request model for {AGENT_NAME} Agent"""
    model_config = ConfigDict(extra="allow")
    
    # Required protocol fields
    request_id: str
    timestamp: str
    principal_id: str
    
    # Context fields (flexible)
    principal_context: Optional[Any] = None
    situation_context: Optional[Any] = None
    business_context: Optional[Any] = None
    extra: Optional[Dict[str, Any]] = None
    
    # Agent-specific fields here

class A9_{AGENT_NAME}_Agent_Response(A9AgentBaseModel):
    """Response model for {AGENT_NAME} Agent"""
    model_config = ConfigDict(extra="allow")
    
    # Required response fields
    status: str
    request_id: str
    timestamp: str
    
    # Agent-specific response fields here

class A9_{AGENT_NAME}_Agent:
    """
    {AGENT_NAME} Agent following Agent9 design standards
    See: docs/prd/agents/a9_{agent_name}_agent_prd.md
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.agent_id = f"a9_{agent_name}_agent"
    
    @classmethod
    def create_from_registry(cls, registry: AgentRegistry, config: Dict[str, Any]):
        """Factory method for orchestrator instantiation"""
        return cls(config)
    
    async def check_access(self, request: A9_{AGENT_NAME}_Agent_Request) -> bool:
        """Protocol entrypoint: access control"""
        # Implementation here
        return True
    
    async def process_request(self, request: A9_{AGENT_NAME}_Agent_Request) -> A9_{AGENT_NAME}_Agent_Response:
        """Protocol entrypoint: main processing"""
        # Implementation here
        return A9_{AGENT_NAME}_Agent_Response(
            status="success",
            request_id=request.request_id,
            timestamp=request.timestamp
        )
```

### 🔥 PYDANTIC V2 PATTERNS ONLY
```python
# ✅ CORRECT - Pydantic v2
from pydantic import ConfigDict

class MyModel(A9AgentBaseModel):
    model_config = ConfigDict(extra="allow")
    
    def serialize(self):
        return self.model_dump()  # ✅ CORRECT

# ❌ WRONG - Pydantic v1 (FORBIDDEN)
class MyModel(BaseModel):
    class Config:  # This is v1 - DO NOT USE
        extra = "allow"
```

## 📋 DEVELOPMENT WORKFLOW

### Step 1: READ PRD FIRST
```
BEFORE ANY CODE: Read docs/prd/agents/a9_{agent_name}_agent_prd.md
Summarize the requirements and get approval before coding.
```

### Step 2: FOLLOW NAMING CONVENTIONS
```
Files: src/agents/new/A9_{Agent_Name}_Agent.py
Classes: A9_{Agent_Name}_Agent
Models: A9_{Agent_Name}_Agent_Request/Response
Cards: src/agents/new/cards/A9_{Agent_Name}_Agent_card.py
```

### Step 3: USE EXISTING FOUNDATION
```python
# ✅ CORRECT - Use existing orchestrator
from src.orchestration.hybrid_workflow_orchestrator import HybridWorkflowOrchestrator

# ✅ CORRECT - Registry integration
@classmethod
def create_from_registry(cls, registry: AgentRegistry, config: Dict[str, Any]):
    return cls(config)
```

### Step 4: PROTOCOL COMPLIANCE
```python
# ✅ ALL agent methods must use protocol models
async def process_request(self, request: A9_Agent_Request) -> A9_Agent_Response:
    # Never use raw dicts/lists

# ✅ ALL responses must include required fields
response = A9_Agent_Response(
    status="success",  # Required
    request_id=request.request_id,  # Required
    timestamp=datetime.utcnow().isoformat()  # Required
)
```

## 🎯 IMPLEMENTATION CHECKLIST

### Before Starting Any Agent:
- [ ] Read the specific PRD document
- [ ] Understand the agent's role in the workflow
- [ ] Identify required input/output models
- [ ] Check existing orchestrator patterns
- [ ] Verify no duplicate logic exists

### During Implementation:
- [ ] Use the agent template above
- [ ] Follow Pydantic v2 patterns only
- [ ] Include all required protocol fields
- [ ] Use `create_from_registry` factory method
- [ ] Implement both `check_access` and `process_request`

### After Implementation:
- [ ] Create agent card in cards/ directory
- [ ] Add config model if needed
- [ ] Test via orchestrator only (no direct instantiation)
- [ ] Verify protocol compliance
- [ ] Update documentation

## 🚨 CASCADE-SPECIFIC INSTRUCTIONS

### When I Ask You To Implement An Agent:

1. **STOP** - Ask me which PRD document to reference
2. **READ** - Summarize the PRD requirements first
3. **PLAN** - Create implementation plan for approval
4. **CODE** - Use templates above, no architectural changes
5. **VERIFY** - Check against all guardrails before presenting

### Prohibited Responses:
- "I'll create the agent structure..." (READ PRD FIRST)
- "Let me implement the orchestration..." (USE EXISTING)
- "I'll add some helper methods..." (FOLLOW TEMPLATE)
- "Here's a complete system..." (ONE AGENT AT A TIME)

### Required Responses:
- "I've read the PRD for {agent_name}. Here's my understanding..."
- "Using the existing HybridWorkflowOrchestrator pattern..."
- "Following Agent9 design standards with Pydantic v2..."
- "This agent will integrate with the registry via create_from_registry..."

## 📁 FILE STRUCTURE COMPLIANCE

```
src/agents/new/
├── A9_{Agent_Name}_Agent.py          # Main agent implementation
├── cards/
│   └── A9_{Agent_Name}_Agent_card.py # Agent configuration card
└── agent_config_models.py            # Config models (if needed)

tests/
└── test_A9_{Agent_Name}_Agent.py     # Tests using orchestrator only

docs/prd/agents/
└── a9_{agent_name}_agent_prd.md      # Requirements document
```

## 🔧 ENVIRONMENT & DEPENDENCIES

### Required Environment Variables:
```bash
# Never hardcode these
OPENAI_API_KEY=your_key_here
AGENT9_LOG_LEVEL=INFO
AGENT9_DATABASE_URL=sqlite:///data/agent9.duckdb
```

### Standard Imports:
```python
from typing import Dict, Any, Optional, List
from pydantic import ConfigDict
from datetime import datetime
import os
import logging
from ..shared.a9_agent_base_model import A9AgentBaseModel
from ..registries.agent_registry import AgentRegistry
```

---

## 🎯 REMEMBER: You are building for a $120M+ enterprise product

- **Code quality matters** - This goes to investors and customers
- **Protocol compliance is mandatory** - No exceptions
- **Follow existing patterns** - Don't reinvent the wheel
- **One agent at a time** - Build incrementally
- **Test through orchestrator** - Never direct instantiation

**When in doubt, ASK before coding. It's better to clarify than refactor.**
