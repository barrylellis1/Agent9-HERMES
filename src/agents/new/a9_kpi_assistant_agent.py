"""
A9_KPI_Assistant_Agent - LLM-powered KPI definition assistant for data product onboarding.

This agent provides an interactive chat interface to help users define comprehensive KPIs
with all required registry attributes, strategic metadata tags, and governance mappings
during the data product onboarding workflow.
"""

import logging
import json
import re
import os
import yaml
from datetime import datetime
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field

from src.agents.shared.a9_agent_base_model import (
    A9AgentBaseModel, A9AgentBaseRequest, A9AgentBaseResponse
)
from src.agents.agent_config_models import A9_KPI_Assistant_Agent_Config, A9_LLM_Service_Agent_Config
from src.registry.models.kpi import KPI, KPIDimension, KPIThreshold, ComparisonType
from src.agents.new.a9_llm_service_agent import (
    A9_LLM_Service_Agent,
    A9_LLM_Request,
    A9_LLM_Response
)

logger = logging.getLogger(__name__)


# Request/Response Models
class SchemaMetadata(BaseModel):
    """Metadata about the inspected schema"""
    data_product_id: str
    domain: str
    source_system: str
    tables: List[str] = Field(default_factory=list, description="Table/view names in the data product")
    database: Optional[str] = Field(None, description="Database/project name")
    schema: Optional[str] = Field(None, description="Schema/dataset name")
    measures: List[Dict[str, Any]] = Field(default_factory=list, description="Columns tagged as measures")
    dimensions: List[Dict[str, Any]] = Field(default_factory=list, description="Columns tagged as dimensions")
    time_columns: List[Dict[str, Any]] = Field(default_factory=list, description="Columns tagged as time")
    identifiers: List[Dict[str, Any]] = Field(default_factory=list, description="Columns tagged as identifiers")


class KPISuggestionRequest(BaseModel):
    """Request to generate KPI suggestions based on schema analysis"""
    schema_metadata: SchemaMetadata
    user_context: Optional[Dict[str, Any]] = Field(None, description="Additional user context")
    num_suggestions: int = Field(5, description="Number of KPI suggestions to generate")
    request_id: str = Field(default_factory=lambda: f"kpi_suggest_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    principal_id: str = Field(default="system", description="ID of the principal making the request")


class KPISuggestionResponse(A9AgentBaseResponse):
    """Response containing suggested KPIs"""
    suggested_kpis: List[Dict[str, Any]] = Field(default_factory=list, description="List of suggested KPIs with all attributes")
    conversation_id: str = Field(default="", description="ID for continuing the conversation")
    rationale: str = Field(default="", description="Explanation of suggestions")


class KPIChatRequest(BaseModel):
    """Request for conversational KPI refinement"""
    conversation_id: str
    message: str
    current_kpis: List[Dict[str, Any]] = Field(default_factory=list)
    request_id: str = Field(default_factory=lambda: f"kpi_chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    principal_id: str = Field(default="system")


class KPIChatResponse(A9AgentBaseResponse):
    """Response from KPI chat interaction"""
    response: str = Field(..., description="Assistant's response")
    updated_kpis: Optional[List[Dict[str, Any]]] = Field(None, description="Updated KPI definitions if applicable")
    actions: Optional[List[Dict[str, str]]] = Field(None, description="Suggested actions for the user")


class KPIValidationRequest(BaseModel):
    """Request to validate a KPI definition"""
    kpi_definition: Dict[str, Any]
    schema_metadata: SchemaMetadata
    request_id: str = Field(default_factory=lambda: f"kpi_validate_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    principal_id: str = Field(default="system")


class KPIValidationResponse(A9AgentBaseResponse):
    """Response from KPI validation"""
    valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)


class KPIFinalizeRequest(BaseModel):
    """Request to finalize KPIs and update contract"""
    data_product_id: str
    kpis: List[Dict[str, Any]]
    extend_mode: bool = Field(default=False, description="If True, merge new KPIs with existing ones; if False, replace all KPIs")
    request_id: str = Field(default_factory=lambda: f"kpi_finalize_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    principal_id: str = Field(default="system")


class KPIFinalizeResponse(A9AgentBaseResponse):
    """Response from KPI finalization"""
    updated_contract_yaml: str
    registry_updates: Dict[str, Any]


class A9_KPI_Assistant_Agent:
    """
    KPI Assistant Agent for interactive KPI definition during data product onboarding.
    
    Provides LLM-powered suggestions, conversational refinement, validation,
    and contract updates for comprehensive KPI definitions.
    """
    
    def __init__(self, config: Optional[A9_KPI_Assistant_Agent_Config] = None):
        """Initialize the KPI Assistant Agent"""
        self.config = config or A9_KPI_Assistant_Agent_Config()
        self.logger = logging.getLogger(__name__)
        self.conversation_history: Dict[str, List[Dict[str, str]]] = {}
        self.llm_agent: Optional[A9_LLM_Service_Agent] = None
        self.data_governance_agent: Optional[Any] = None
        
    async def connect(self) -> bool:
        """Connect to required services"""
        try:
            self.logger.info("KPI Assistant Agent connecting...")
            
            # Initialize LLM Service Agent
            llm_config = A9_LLM_Service_Agent_Config(
                provider=self.config.llm_provider,
                model_name=self.config.llm_model,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                task_type="general"
            )
            self.llm_agent = await A9_LLM_Service_Agent.create(llm_config.__dict__)
            self.logger.info("LLM Service Agent initialized successfully")
            
            # Initialize Data Governance Agent connection for validation
            try:
                from src.agents.new.a9_data_governance_agent import A9_Data_Governance_Agent
                self.data_governance_agent = await A9_Data_Governance_Agent.create({})
                self.logger.info("Data Governance Agent initialized successfully")
            except Exception as dg_err:
                self.data_governance_agent = None
                self.logger.warning(f"Data Governance Agent unavailable, KPI validation will use local rules only: {dg_err}")

            return True
        except Exception as e:
            self.logger.error(f"Failed to connect KPI Assistant Agent: {e}")
            return False
    
    async def disconnect(self) -> bool:
        """Disconnect from services"""
        try:
            self.logger.info("KPI Assistant Agent disconnecting...")
            return True
        except Exception as e:
            self.logger.error(f"Failed to disconnect KPI Assistant Agent: {e}")
            return False
    
    async def suggest_kpis(self, request: KPISuggestionRequest) -> KPISuggestionResponse:
        """
        Generate KPI suggestions based on schema analysis.
        
        Analyzes the inspected schema (measures, dimensions, time columns) and suggests
        3-7 business KPIs with complete attribute sets including strategic metadata.
        """
        try:
            self.logger.info(f"Generating KPI suggestions for {request.schema_metadata.data_product_id}")
            
            # Build LLM prompt for KPI suggestion
            system_prompt = self._build_suggestion_system_prompt(request.schema_metadata)
            user_prompt = self._build_suggestion_user_prompt(request.schema_metadata, request.num_suggestions)
            
            # Call LLM Service Agent via A9_LLM_Service_Agent
            llm_response = await self._call_llm_for_suggestions(system_prompt, user_prompt)
            
            # Parse LLM response into structured KPI definitions
            suggested_kpis = self._parse_kpi_suggestions(llm_response, request.schema_metadata)
            
            # Generate conversation ID
            conversation_id = f"kpi_conv_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.conversation_history[conversation_id] = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
                {"role": "assistant", "content": llm_response}
            ]
            
            return KPISuggestionResponse(
                status="success",
                request_id=request.request_id,
                suggested_kpis=suggested_kpis,
                conversation_id=conversation_id,
                rationale=self._extract_rationale(llm_response)
            )
            
        except Exception as e:
            self.logger.error(f"Error generating KPI suggestions: {e}")
            return KPISuggestionResponse(
                status="error",
                request_id=request.request_id,
                error_message=str(e),
                suggested_kpis=[],
                conversation_id="",
                rationale=""
            )
    
    async def chat(self, request: KPIChatRequest) -> KPIChatResponse:
        """
        Handle conversational KPI refinement.
        
        Accepts natural language requests to customize KPIs, clarify thresholds,
        adjust dimensions, or modify governance mappings.
        """
        try:
            self.logger.info(f"Processing chat message for conversation {request.conversation_id}")
            
            # Retrieve conversation history
            history = self.conversation_history.get(request.conversation_id, [])
            
            # Add user message to history
            history.append({"role": "user", "content": request.message})
            
            # Build context with current KPIs
            context = self._build_chat_context(request.current_kpis)
            
            # Call LLM Service Agent with conversation history via A9_LLM_Service_Agent
            llm_response = await self._call_llm_for_chat(history, context)
            
            # Parse response for KPI updates
            updated_kpis = self._extract_kpi_updates(llm_response, request.current_kpis)
            actions = self._extract_actions(llm_response)
            
            # Update conversation history
            history.append({"role": "assistant", "content": llm_response})
            self.conversation_history[request.conversation_id] = history
            
            return KPIChatResponse(
                status="success",
                request_id=request.request_id,
                response=llm_response,
                updated_kpis=updated_kpis,
                actions=actions
            )
            
        except Exception as e:
            self.logger.error(f"Error in chat: {e}")
            return KPIChatResponse(
                status="error",
                request_id=request.request_id,
                error=str(e),
                response="",
                updated_kpis=None,
                actions=None
            )
    
    async def validate_kpi(self, request: KPIValidationRequest) -> KPIValidationResponse:
        """
        Validate a KPI definition against schema and governance rules.
        
        Checks:
        - All required attributes present
        - SQL query valid against schema
        - Strategic metadata tags consistent
        - Dimensions exist in schema
        """
        try:
            self.logger.info("Validating KPI definition")
            
            errors = []
            warnings = []
            suggestions = []
            
            # Validate required fields
            required_fields = ['id', 'name', 'domain', 'description', 'unit', 'data_product_id']
            for field in required_fields:
                if field not in request.kpi_definition or not request.kpi_definition[field]:
                    errors.append(f"Missing required field: {field}")
            
            # Validate strategic metadata
            metadata = request.kpi_definition.get('metadata', {})
            if 'line' not in metadata:
                errors.append("Missing strategic metadata: line")
            elif metadata['line'] not in ['top_line', 'middle_line', 'bottom_line']:
                errors.append(f"Invalid line value: {metadata['line']}")
            
            if 'altitude' not in metadata:
                errors.append("Missing strategic metadata: altitude")
            elif metadata['altitude'] not in ['strategic', 'tactical', 'operational']:
                errors.append(f"Invalid altitude value: {metadata['altitude']}")
            
            if 'profit_driver_type' not in metadata:
                errors.append("Missing strategic metadata: profit_driver_type")
            elif metadata['profit_driver_type'] not in ['revenue', 'expense', 'efficiency', 'risk']:
                errors.append(f"Invalid profit_driver_type value: {metadata['profit_driver_type']}")
            
            if 'lens_affinity' not in metadata:
                errors.append("Missing strategic metadata: lens_affinity")
            
            # Validate logical consistency
            if metadata.get('line') == 'top_line' and metadata.get('profit_driver_type') == 'expense':
                warnings.append("Inconsistent: top_line with expense driver (usually revenue)")
            
            if metadata.get('line') == 'bottom_line' and metadata.get('profit_driver_type') == 'revenue':
                warnings.append("Inconsistent: bottom_line with revenue driver (usually expense)")
            
            # Validate SQL query against schema
            sql_query = request.kpi_definition.get('sql_query')
            if sql_query:
                sql_errors = self._validate_sql_against_schema(sql_query, request.schema_metadata)
                errors.extend(sql_errors)
            else:
                errors.append("Missing sql_query")
            
            # Validate dimensions exist in schema
            dimensions = request.kpi_definition.get('dimensions', [])
            for dim in dimensions:
                if not self._dimension_exists_in_schema(dim.get('field'), request.schema_metadata):
                    warnings.append(f"Dimension field not found in schema: {dim.get('field')}")
            
            # Generate suggestions
            if not request.kpi_definition.get('thresholds'):
                suggestions.append("Consider adding thresholds for situation detection")
            
            if not request.kpi_definition.get('owner_role'):
                suggestions.append("Consider specifying an owner_role for governance")
            
            valid = len(errors) == 0
            
            return KPIValidationResponse(
                status="success",
                request_id=request.request_id,
                valid=valid,
                errors=errors,
                warnings=warnings,
                suggestions=suggestions
            )
            
        except Exception as e:
            self.logger.error(f"Error validating KPI: {e}")
            return KPIValidationResponse(
                status="error",
                request_id=request.request_id,
                error=str(e),
                valid=False,
                errors=[str(e)],
                warnings=[],
                suggestions=[]
            )
    
    async def finalize_kpis(self, request: KPIFinalizeRequest) -> KPIFinalizeResponse:
        """
        Finalize KPIs and update data product contract YAML.
        
        Adds validated KPIs to the data product contract and triggers registry updates.
        Supports both replace mode (new products) and extend mode (adding to existing products).
        """
        try:
            mode_str = "extend" if request.extend_mode else "replace"
            self.logger.info(f"Finalizing {len(request.kpis)} KPIs for {request.data_product_id} (mode: {mode_str})")
            
            # Load existing contract
            contract_yaml = await self._load_contract_yaml(request.data_product_id)
            
            # Update KPIs section (merge or replace based on extend_mode)
            updated_yaml = self._update_contract_with_kpis(contract_yaml, request.kpis, extend_mode=request.extend_mode)
            
            # Save updated contract
            await self._save_contract_yaml(request.data_product_id, updated_yaml)
            
            # Trigger registry updates
            registry_updates = await self._trigger_registry_updates(request.data_product_id, request.kpis)
            
            return KPIFinalizeResponse(
                status="success",
                request_id=request.request_id,
                updated_contract_yaml=updated_yaml,
                registry_updates=registry_updates
            )
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            self.logger.error(f"Error finalizing KPIs: {e}\n{error_details}")
            return KPIFinalizeResponse(
                status="error",
                request_id=request.request_id,
                error_message=str(e),
                updated_contract_yaml="",
                registry_updates={}
            )
    
    # Helper methods
    
    def _build_suggestion_system_prompt(self, schema: SchemaMetadata) -> str:
        """Build system prompt for KPI suggestion"""
        return f"""You are a KPI definition assistant for Agent9's data product onboarding.

CONTEXT:
- Data Product ID: {schema.data_product_id}
- Domain: {schema.domain}
- Source System: {schema.source_system}
- Available Measures: {len(schema.measures)} columns
- Available Dimensions: {len(schema.dimensions)} columns
- Time Columns: {len(schema.time_columns)} columns

YOUR ROLE:
Help users define comprehensive KPIs with ALL required attributes for the Agent9 registry.

KPI STRUCTURE (ALL fields required):
1. Core Identity:
   - id: Semantic snake_case ID (e.g., "gross_revenue", "customer_churn_rate"). MUST be globally unique and derived from the name. Do NOT use generic IDs like "kpi_001".
   - name, domain, description, unit, data_product_id
2. Calculation: sql_query, filters (optional)
3. Dimensions: name, field, description, values
4. Thresholds: comparison_type (qoq/yoy/mom/target/budget), green/yellow/red thresholds, inverse_logic
5. Governance: business_process_ids, tags, owner_role, stakeholder_roles
6. Strategic Metadata:
   - line (top_line/middle_line/bottom_line)
   - altitude (strategic/tactical/operational)
   - profit_driver_type (revenue/expense/efficiency/risk)
   - lens_affinity (bcg/bain/mckinsey combinations)
   - refresh_frequency, data_latency, calculation_complexity

STRATEGIC METADATA GUIDANCE:
- Revenue KPIs → line:top_line, altitude:strategic, driver:revenue, lens:bcg,mckinsey
- Efficiency KPIs → line:middle_line, altitude:tactical, driver:efficiency, lens:bain
- Cost KPIs → line:bottom_line, altitude:operational, driver:expense, lens:bain

INTERACTION STYLE:
- Suggest 3-5 KPIs with complete attributes and sensible defaults
- Explain WHY you chose each metadata value
- Validate SQL against available schema
- Format suggestions as structured JSON with all attributes
"""
    
    def _build_suggestion_user_prompt(self, schema: SchemaMetadata, num_suggestions: int) -> str:
        """Build user prompt for KPI suggestion"""
        measures_str = "\n".join([f"  - {m.get('name')} ({m.get('data_type')})" for m in schema.measures[:10]])
        dimensions_str = "\n".join([f"  - {d.get('name')} ({d.get('data_type')})" for d in schema.dimensions[:10]])
        tables_str = "\n".join([f"  - {table}" for table in schema.tables]) if schema.tables else "  - (no tables specified)"
        
        # Build fully qualified table name for SQL examples
        if schema.tables:
            primary_table = schema.tables[0]
            if schema.source_system == "bigquery" and schema.database and schema.schema:
                example_table = f"`{schema.database}.{schema.schema}.{primary_table}`"
            elif schema.source_system == "duckdb":
                example_table = primary_table
            else:
                example_table = primary_table
        else:
            example_table = "table_name"
        
        return f"""Analyze this data product schema and suggest {num_suggestions} business KPIs:

DATA SOURCE:
  - Source System: {schema.source_system}
  - Database/Project: {schema.database or 'N/A'}
  - Schema/Dataset: {schema.schema or 'N/A'}

TABLES/VIEWS:
{tables_str}

MEASURES:
{measures_str}

DIMENSIONS:
{dimensions_str}

Please suggest {num_suggestions} KPIs with:
- Semantic IDs (e.g., "total_sales_volume", NOT "kpi_001")
- Complete attribute sets (all required fields)
- Strategic metadata tags with explanations
- SQL queries using the available measures and dimensions
- Appropriate thresholds for situation detection
- Governance mappings (owner, stakeholders, business processes)

CRITICAL SQL REQUIREMENTS:
- Use fully qualified table names in all SQL queries
- For BigQuery: Use backticks and format as `project.dataset.table`
- Example: SELECT SUM(measure) FROM {example_table}
- Use the actual table names from the TABLES/VIEWS list above

IMPORTANT: Return a JSON array of KPI objects in this EXACT flat structure:
```json
[
  {{
    "id": "total_gross_sales",
    "name": "Total Gross Sales",
    "domain": "{schema.domain}",
    "description": "Clear description",
    "unit": "USD or count or percent",
    "data_product_id": "{schema.data_product_id}",
    "sql_query": "SELECT SUM(measure_column) FROM {example_table}",
    "dimensions": [{{ "name": "Dimension Name", "field": "column_name", "description": "...", "values": ["all"] }}],
    "thresholds": [{{ "comparison_type": "target", "green_threshold": 100, "yellow_threshold": 50, "red_threshold": 10, "inverse_logic": false }}],
    "metadata": {{
      "line": "top_line",
      "altitude": "strategic",
      "profit_driver_type": "revenue",
      "lens_affinity": "bcg,bain",
      "refresh_frequency": "daily",
      "data_latency": "1 hour",
      "calculation_complexity": "simple"
    }},
    "business_process_ids": ["sales", "revenue_management"],
    "tags": ["revenue", "sales"],
    "owner_role": "CFO",
    "stakeholder_roles": ["Sales VP", "Finance Director"]
  }}
]
```

Do NOT use nested sections like "Core Identity" or "Calculation". Use a flat structure with all fields at the top level.
"""
    
    async def _call_llm_for_suggestions(self, system_prompt: str, user_prompt: str) -> str:
        """Call LLM Service Agent for KPI suggestions"""
        try:
            if not self.llm_agent:
                raise ValueError("LLM Service Agent not initialized")
            
            # Create LLM request
            llm_request = A9_LLM_Request(
                request_id=f"kpi_suggest_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                principal_id="system",
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                operation="generate_kpi_suggestions"
            )
            
            # Call LLM Service Agent
            response = await self.llm_agent.generate(llm_request)
            
            if response.status != "success":
                raise ValueError(f"LLM generation failed: {response.error_message}")
            
            self.logger.info(f"LLM generated KPI suggestions (tokens: {response.usage.get('total_tokens', 0)})")
            return response.content
            
        except Exception as e:
            self.logger.error(f"Error calling LLM for suggestions: {e}")
            raise
    
    async def _call_llm_for_chat(self, history: List[Dict[str, str]], context: str) -> str:
        """Call LLM Service Agent for chat response"""
        try:
            if not self.llm_agent:
                raise ValueError("LLM Service Agent not initialized")
            
            # Build conversation prompt from history
            conversation = "\n\n".join([
                f"{msg['role'].upper()}: {msg['content']}"
                for msg in history[:-1]  # Exclude the last user message
            ])
            
            # Get the latest user message
            user_message = history[-1]['content'] if history else ""
            
            # Build full prompt with context
            full_prompt = f"""CONVERSATION HISTORY:
{conversation}

CURRENT CONTEXT:
{context}

USER MESSAGE:
{user_message}

Please respond to the user's message, providing helpful guidance on KPI definition.
If the user is requesting changes to KPIs, format your response with clear JSON blocks for updated KPI definitions.
"""
            
            # Get system prompt from history if available
            system_prompt = next(
                (msg['content'] for msg in history if msg['role'] == 'system'),
                self._build_suggestion_system_prompt(SchemaMetadata(
                    data_product_id="unknown",
                    domain="unknown",
                    source_system="unknown"
                ))
            )
            
            # Create LLM request
            llm_request = A9_LLM_Request(
                request_id=f"kpi_chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                principal_id="system",
                prompt=full_prompt,
                system_prompt=system_prompt,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                operation="kpi_chat_refinement"
            )
            
            # Call LLM Service Agent
            response = await self.llm_agent.generate(llm_request)
            
            if response.status != "success":
                raise ValueError(f"LLM generation failed: {response.error_message}")
            
            self.logger.info(f"LLM generated chat response (tokens: {response.usage.get('total_tokens', 0)})")
            return response.content
            
        except Exception as e:
            self.logger.error(f"Error calling LLM for chat: {e}")
            raise
    
    def _parse_kpi_suggestions(self, llm_response: str, schema: SchemaMetadata) -> List[Dict[str, Any]]:
        """Parse LLM response into structured KPI definitions"""
        try:
            self.logger.debug(f"Parsing LLM response (length: {len(llm_response)} chars)")
            self.logger.debug(f"First 500 chars: {llm_response[:500]}")
            kpis = []
            
            # Try to extract JSON blocks from the response
            # Look for JSON arrays or individual JSON objects
            json_pattern = r'```json\s*([\s\S]*?)\s*```|```\s*([\s\S]*?)\s*```'
            matches = re.findall(json_pattern, llm_response)
            
            self.logger.debug(f"Found {len(matches)} JSON code blocks")
            if matches:
                # Process each JSON block found
                for match in matches:
                    json_str = match[0] or match[1]
                    if json_str.strip():
                        try:
                            parsed = json.loads(json_str)
                            # Handle both array and single object
                            if isinstance(parsed, list):
                                kpis.extend(parsed)
                            elif isinstance(parsed, dict):
                                kpis.append(parsed)
                        except json.JSONDecodeError as e:
                            self.logger.warning(f"Failed to parse JSON block: {e}")
                            continue
            else:
                # Try to parse the entire response as JSON
                try:
                    parsed = json.loads(llm_response)
                    if isinstance(parsed, list):
                        kpis = parsed
                    elif isinstance(parsed, dict):
                        kpis = [parsed]
                except json.JSONDecodeError:
                    self.logger.warning("No valid JSON found in LLM response")
            
            # Validate and enrich each KPI
            validated_kpis = []
            for kpi in kpis:
                if self._validate_kpi_structure(kpi):
                    # Ensure data_product_id is set
                    if 'data_product_id' not in kpi:
                        kpi['data_product_id'] = schema.data_product_id
                    validated_kpis.append(kpi)
                else:
                    self.logger.warning(f"KPI failed validation: {kpi.get('id', 'unknown')}")
            
            self.logger.info(f"Parsed {len(validated_kpis)} valid KPIs from LLM response")
            return validated_kpis
            
        except Exception as e:
            self.logger.error(f"Error parsing KPI suggestions: {e}")
            return []
    
    def _validate_kpi_structure(self, kpi: Dict[str, Any]) -> bool:
        """Validate that a KPI has minimum required structure"""
        required_fields = ['id', 'name', 'domain', 'description']
        return all(field in kpi for field in required_fields)
    
    def _extract_rationale(self, llm_response: str) -> str:
        """Extract rationale from LLM response"""
        try:
            # Look for rationale section in the response
            rationale_patterns = [
                r'(?:Rationale|RATIONALE|Why these KPIs)[:\s]*([\s\S]*?)(?:\n\n|```|$)',
                r'(?:Explanation|EXPLANATION)[:\s]*([\s\S]*?)(?:\n\n|```|$)',
            ]
            
            for pattern in rationale_patterns:
                match = re.search(pattern, llm_response, re.IGNORECASE)
                if match:
                    rationale = match.group(1).strip()
                    if rationale:
                        return rationale[:500]  # Limit length
            
            # If no specific rationale section, extract first paragraph before JSON
            json_start = llm_response.find('```')
            if json_start > 0:
                intro = llm_response[:json_start].strip()
                if intro:
                    return intro[:500]
            
            # Default rationale
            return "KPIs suggested based on schema analysis and business best practices."
            
        except Exception as e:
            self.logger.error(f"Error extracting rationale: {e}")
            return "KPI suggestions generated."
    
    def _build_chat_context(self, current_kpis: List[Dict[str, Any]]) -> str:
        """Build context string with current KPIs"""
        return f"Current KPIs: {len(current_kpis)}"
    
    def _extract_kpi_updates(self, llm_response: str, current_kpis: List[Dict[str, Any]]) -> Optional[List[Dict[str, Any]]]:
        """Extract KPI updates from LLM response"""
        try:
            # Look for JSON blocks in the response
            json_pattern = r'```json\s*([\s\S]*?)\s*```|```\s*([\s\S]*?)\s*```'
            matches = re.findall(json_pattern, llm_response)
            
            if not matches:
                # No JSON updates in response
                return None
            
            updated_kpis = []
            for match in matches:
                json_str = match[0] or match[1]
                if json_str.strip():
                    try:
                        parsed = json.loads(json_str)
                        if isinstance(parsed, list):
                            updated_kpis.extend(parsed)
                        elif isinstance(parsed, dict):
                            updated_kpis.append(parsed)
                    except json.JSONDecodeError:
                        continue
            
            if updated_kpis:
                self.logger.info(f"Extracted {len(updated_kpis)} updated KPIs from chat response")
                return updated_kpis
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error extracting KPI updates: {e}")
            return None
    
    def _extract_actions(self, llm_response: str) -> Optional[List[Dict[str, str]]]:
        """Extract suggested actions from LLM response"""
        try:
            actions = []
            
            # Look for action buttons or suggestions
            action_patterns = [
                r'\[([^\]]+)\]',  # [Accept], [Customize], etc.
                r'(?:Action|TODO|Next)[:\s]*([^\n]+)',
            ]
            
            for pattern in action_patterns:
                matches = re.findall(pattern, llm_response)
                for match in matches:
                    action_text = match.strip()
                    if action_text and len(action_text) < 100:
                        # Determine action type
                        action_type = 'info'
                        if any(word in action_text.lower() for word in ['accept', 'approve', 'confirm']):
                            action_type = 'accept'
                        elif any(word in action_text.lower() for word in ['edit', 'customize', 'modify']):
                            action_type = 'edit'
                        elif any(word in action_text.lower() for word in ['reject', 'decline', 'cancel']):
                            action_type = 'reject'
                        
                        actions.append({
                            'label': action_text,
                            'action': action_type
                        })
            
            # Remove duplicates
            seen = set()
            unique_actions = []
            for action in actions:
                key = action['label'].lower()
                if key not in seen:
                    seen.add(key)
                    unique_actions.append(action)
            
            return unique_actions if unique_actions else None
            
        except Exception as e:
            self.logger.error(f"Error extracting actions: {e}")
            return None
    
    def _validate_sql_against_schema(self, sql: str, schema: SchemaMetadata) -> List[str]:
        """Validate SQL query against schema using rule-based checks against available columns."""
        errors = []
        if not sql or not sql.strip():
            errors.append("SQL query is empty")
            return errors

        sql_upper = sql.upper()

        if not sql_upper.strip().startswith("SELECT"):
            errors.append("SQL query must start with SELECT")

        # Build set of all known column names (case-insensitive)
        all_columns = set()
        for col in schema.measures + schema.dimensions + schema.time_columns + schema.identifiers:
            col_name = col.get("name")
            if col_name:
                all_columns.add(col_name.lower())

        # Check that at least one known table name appears in the SQL
        if schema.tables:
            table_found = any(table.lower() in sql.lower() for table in schema.tables)
            if not table_found:
                errors.append(
                    f"SQL query does not reference any known table. "
                    f"Expected one of: {', '.join(schema.tables)}"
                )

        return errors
    
    def _dimension_exists_in_schema(self, field: str, schema: SchemaMetadata) -> bool:
        """Check if dimension field exists in schema"""
        all_columns = schema.measures + schema.dimensions + schema.time_columns + schema.identifiers
        return any(col.get('name') == field for col in all_columns)
    
    async def _load_contract_yaml(self, data_product_id: str) -> str:
        """Load existing contract YAML from staging or registered location"""
        
        # Look in staging directory first (for new products)
        staging_path = f"src/registry_references/data_product_registry/staging/{data_product_id}.yaml"
        
        if os.path.exists(staging_path):
            with open(staging_path, 'r', encoding='utf-8') as f:
                return f.read()
        
        # Check if this is a registered product by looking up in registry
        try:
            from src.registry.factory import RegistryFactory
            factory = RegistryFactory()
            if not factory.is_initialized:
                await factory.initialize()
            
            provider = factory.get_data_product_provider()
            if provider:
                data_product = provider.get(data_product_id)
                if data_product and hasattr(data_product, 'metadata'):
                    yaml_contract_path = data_product.metadata.get('yaml_contract_path')
                    if yaml_contract_path and os.path.exists(yaml_contract_path):
                        with open(yaml_contract_path, 'r', encoding='utf-8') as f:
                            return f.read()
        except Exception as e:
            self.logger.warning(f"Could not load from registry: {e}")
        
        # Fallback to old location
        old_path = f"src/registry/data_product/{data_product_id}.yaml"
        if os.path.exists(old_path):
            with open(old_path, 'r', encoding='utf-8') as f:
                return f.read()
        
        raise FileNotFoundError(f"Contract not found for {data_product_id}")
    
    def _update_contract_with_kpis(self, contract_yaml: str, kpis: List[Dict[str, Any]], extend_mode: bool = False) -> str:
        """
        Update contract YAML with KPIs.
        
        Args:
            contract_yaml: Existing contract YAML content
            kpis: New KPIs to add
            extend_mode: If True, merge with existing KPIs; if False, replace all KPIs
        """
        
        # Parse existing contract
        contract = yaml.safe_load(contract_yaml)
        
        if extend_mode and 'kpis' in contract and contract['kpis']:
            # Merge mode: Add new KPIs to existing ones
            existing_kpis = contract['kpis']
            existing_kpi_ids = {kpi.get('id') for kpi in existing_kpis if isinstance(kpi, dict)}
            
            # Add only new KPIs (avoid duplicates by ID)
            merged_kpis = list(existing_kpis)
            for new_kpi in kpis:
                if isinstance(new_kpi, dict):
                    kpi_id = new_kpi.get('id')
                    if kpi_id not in existing_kpi_ids:
                        merged_kpis.append(new_kpi)
                        self.logger.info(f"Adding new KPI: {kpi_id}")
                    else:
                        # Update existing KPI with same ID
                        for i, existing_kpi in enumerate(merged_kpis):
                            if isinstance(existing_kpi, dict) and existing_kpi.get('id') == kpi_id:
                                merged_kpis[i] = new_kpi
                                self.logger.info(f"Updating existing KPI: {kpi_id}")
                                break
            
            contract['kpis'] = merged_kpis
            self.logger.info(f"Merged {len(kpis)} new KPIs with {len(existing_kpis)} existing KPIs, total: {len(merged_kpis)}")
        else:
            # Replace mode: Set KPIs section to new KPIs
            contract['kpis'] = kpis
            self.logger.info(f"Replaced KPIs section with {len(kpis)} new KPIs")
        
        # Convert back to YAML
        return yaml.dump(contract, sort_keys=False, allow_unicode=True)
    
    async def _save_contract_yaml(self, data_product_id: str, yaml_content: str) -> None:
        """Save updated contract YAML to staging location"""
        
        # Save to staging directory
        staging_path = f"src/registry_references/data_product_registry/staging/{data_product_id}.yaml"
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(staging_path), exist_ok=True)
        
        # Write updated contract
        with open(staging_path, 'w', encoding='utf-8') as f:
            f.write(yaml_content)
        
        self.logger.info(f"Updated contract saved to {staging_path}")
    
    async def _trigger_registry_updates(self, data_product_id: str, kpis: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Trigger registry updates for new KPIs"""
        results = {
            "success": [],
            "failed": []
        }
        
        try:
            from src.registry.factory import RegistryFactory
            from src.registry.models.kpi import KPI
            
            # Get KPI provider
            factory = RegistryFactory()
            if not factory.is_initialized:
                await factory.initialize()
                
            provider = factory.get_kpi_provider()
            if not provider:
                raise ValueError("KPI provider not available")
            
            self.logger.info(f"Registering {len(kpis)} KPIs to {provider.__class__.__name__}")
            
            import inspect
            
            for kpi_data in kpis:
                try:
                    # Convert dict to KPI model
                    # Ensure data_product_id is set
                    if "data_product_id" not in kpi_data:
                        kpi_data["data_product_id"] = data_product_id
                        
                    kpi = KPI(**kpi_data)
                    
                    # Register with provider (handles Database insertion if configured)
                    # Handle both sync and async providers
                    if hasattr(provider, 'register'):
                        result = provider.register(kpi)
                        if inspect.isawaitable(result):
                            success = await result
                        else:
                            success = result
                    else:
                        success = False
                        self.logger.warning(f"Provider {provider.__class__.__name__} has no register method")
                    
                    if success:
                        results["success"].append(kpi.id)
                        self.logger.info(f"Successfully registered KPI: {kpi.id}")
                    else:
                        results["failed"].append({"id": kpi.id, "error": "Registration returned False"})
                        self.logger.warning(f"Failed to register KPI: {kpi.id}")
                        
                except Exception as e:
                    results["failed"].append({"id": kpi_data.get("id", "unknown"), "error": str(e)})
                    self.logger.error(f"Error registering KPI {kpi_data.get('id')}: {e}")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error in registry updates: {e}")
            return {
                "success": [],
                "failed": [{"id": "all", "error": str(e)}]
            }


# Factory function for orchestrator-driven creation
def create_kpi_assistant_agent(config: Optional[A9_KPI_Assistant_Agent_Config] = None) -> A9_KPI_Assistant_Agent:
    """Factory function to create KPI Assistant Agent instance"""
    return A9_KPI_Assistant_Agent(config)
