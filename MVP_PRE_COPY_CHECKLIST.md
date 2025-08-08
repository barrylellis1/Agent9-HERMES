# Agent9 MVP Template - Pre-Copy Checklist

**Purpose**: Ensure the MVP template is clean, complete, and ready for duplication across 3 LLM instances. Each LLM will start with an identical, clean foundation for the Agent9 MVP competition.

## ✅ Pre-Copy Verification Steps

### 1. **Dependencies & Environment**
- [ ] All Python dependencies installed: `pip install -r requirements.txt`
- [ ] DuckDB specifically verified: `python -c "import duckdb; print('DuckDB OK')"`
- [ ] FastAPI imports working: `python -c "from fastapi import FastAPI; print('FastAPI OK')"`
- [ ] Environment template exists: `.env.template` is present
- [ ] Virtual environment activated (if using venv)

### 2. **Database & Data State**
- [ ] Clean DuckDB database: `data/agent9.duckdb` exists but contains no test data
- [ ] No leftover workflow executions in database
- [ ] KPI tables initialized but empty
- [ ] Registry tables created with default schemas

### 3. **Code Structure Verification**
- [ ] Core orchestrator exists: `src/orchestration/hybrid_workflow_orchestrator.py`
- [ ] API endpoints ready: `src/api/workflow_api.py` and `src/api/main_updated.py`
- [ ] Dashboard UI ready: `ui/workflow-dashboard.html`
- [ ] No test/debug code left in production files

### 4. **Configuration**
- [ ] `.env` file does NOT exist (each LLM will create their own)
- [ ] `.env.template` has all required variables
- [ ] No hardcoded API keys or secrets in code
- [ ] Port configurations are standard (8000 for API)

### 5. **File System Cleanliness**
- [ ] No `__pycache__` directories: `find . -name "__pycache__" -type d`
- [ ] No `.pyc` files: `find . -name "*.pyc" -type f`
- [ ] No temporary files or logs
- [ ] No IDE-specific files (.vscode, .idea, etc.)

### 6. **Functional Verification**
- [ ] Import test passes: `python -c "from src.orchestration.hybrid_workflow_orchestrator import HybridWorkflowOrchestrator; print('Imports OK')"`
- [ ] Database initialization works: `python -c "from src.orchestration.hybrid_workflow_orchestrator import MCPRegistryService; r = MCPRegistryService(); print('DB Init OK')"`
- [ ] API server starts without errors (test briefly, then stop)
- [ ] Dashboard HTML loads without console errors

## 🚀 Copy Instructions

### For Each LLM Copy:
1. **Create Directory**: `Agent9-Hackathon-[LLM-Name]` (e.g., `Agent9-Hackathon-Claude`, `Agent9-Hackathon-GPT4`)
2. **Copy Template**: Copy entire template directory to new location
3. **Unique Database**: Rename `data/agent9.duckdb` to `data/agent9-[llm-name].duckdb`
4. **Unique Ports**: Update API port in each copy (8000, 8001, 8002) to avoid conflicts
5. **Environment Setup**: Each LLM creates their own `.env` from `.env.template`

### Port Assignments:
- **Claude 3.7 Sonnet**: Port 8000
- **GPT-4.1**: Port 8001  
- **[Third LLM]**: Port 8002

## 📊 Success Criteria

Each copied template should:
- [ ] Start API server without errors
- [ ] Load dashboard UI successfully
- [ ] Execute test simulation workflow
- [ ] Display real-time KPIs
- [ ] Store handoff data in database

## 🔧 Quick Test Commands

```bash
# Test dependencies
python -c "import duckdb, fastapi, pydantic; print('All imports OK')"

# Test orchestrator
python -c "from src.orchestration.hybrid_workflow_orchestrator import HybridWorkflowOrchestrator; o = HybridWorkflowOrchestrator(); print('Orchestrator OK')"

# Test API (run briefly then Ctrl+C)
python src/api/main_updated.py

# Test dashboard (open in browser)
# file://[path]/ui/workflow-dashboard.html
```

## 🏁 Ready for Hackathon

Once all checkboxes are complete:
1. **Template is ready for duplication**
2. **Each LLM gets identical starting point**
3. **Fair competition environment established**
4. **Enterprise-grade foundation provided**

---

**Note**: This checklist ensures each LLM starts with the same high-quality foundation, making the competition fair and the results meaningful for investor demos.
