"""
A9_LLM_Service_Agent - Centralized LLM operations for Agent9-HERMES.

This agent provides a standardized interface for all LLM operations,
enforces guardrails, applies prompt templates, and manages provider connections.
All LLM operations should be routed through this agent for proper logging,
protocol compliance, and policy enforcement.
"""

import os
import logging
import yaml
import json
from datetime import datetime
from typing import Dict, List, Any, Optional, Union

# Import service layer
from src.llm_services.claude_service import ClaudeService, create_claude_service
from src.llm_services.openai_service import OpenAIService, create_openai_service

from pydantic import BaseModel, Field, ConfigDict
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import shared models
from src.agents.shared.a9_agent_base_model import (
    A9AgentBaseModel, A9AgentBaseRequest, A9AgentBaseResponse
)

# Import config models
from src.agents.agent_config_models import A9_LLM_Service_Agent_Config

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Request/Response Models for LLM Agent Protocol
class A9_LLM_Request(A9AgentBaseRequest):
    """Base request model for LLM operations"""
    prompt: str = Field(..., description="The prompt to send to the LLM")
    model: Optional[str] = Field(None, description="Override the default model")
    temperature: Optional[float] = Field(None, description="Override the default temperature")
    max_tokens: Optional[int] = Field(None, description="Override the default max tokens")
    system_prompt: Optional[str] = Field(None, description="Override the default system prompt")
    operation: str = Field("generate", description="The operation to perform")


class A9_LLM_TemplateRequest(A9AgentBaseRequest):
    """Request model for template-based LLM operations"""
    template_id: str = Field(..., description="ID of the template to use")
    template_variables: Dict[str, Any] = Field(..., description="Variables to format the template")
    model: Optional[str] = Field(None, description="Override the default model")
    temperature: Optional[float] = Field(None, description="Override the default temperature")
    max_tokens: Optional[int] = Field(None, description="Override the default max tokens")
    system_prompt: Optional[str] = Field(None, description="Override the default system prompt")
    operation: str = Field("generate_template", description="The operation to perform")


class A9_LLM_AnalysisRequest(A9AgentBaseRequest):
    """Request model for LLM analysis operations"""
    content: str = Field(..., description="Content to analyze")
    analysis_type: str = Field(..., description="Type of analysis to perform")
    context: Optional[str] = Field(None, description="Additional context for analysis")
    model: Optional[str] = Field(None, description="Override the default model")
    operation: str = Field("analyze", description="The operation to perform")


class A9_LLM_SummaryRequest(A9AgentBaseRequest):
    """Request model for LLM summarization operations"""
    content: str = Field(..., description="Content to summarize")
    max_length: Optional[int] = Field(None, description="Maximum length of summary")
    focus_areas: Optional[List[str]] = Field(None, description="Areas to focus on in summary")
    model: Optional[str] = Field(None, description="Override the default model")
    operation: str = Field("summarize", description="The operation to perform")


class A9_LLM_EvaluationRequest(A9AgentBaseRequest):
    """Request model for LLM evaluation operations"""
    options: List[str] = Field(..., description="Options to evaluate")
    criteria: List[str] = Field(..., description="Criteria for evaluation")
    context: Optional[str] = Field(None, description="Context for evaluation")
    model: Optional[str] = Field(None, description="Override the default model")
    operation: str = Field("evaluate", description="The operation to perform")


class A9_LLM_Response(A9AgentBaseResponse):
    """Base response model for LLM operations"""
    content: str = Field(..., description="The LLM-generated content")
    model_used: str = Field(..., description="The model used for generation")
    usage: Dict[str, Any] = Field(..., description="Token usage information")
    operation: str = Field(..., description="The operation that was performed")
    warnings: Optional[List[str]] = Field(None, description="Any warnings generated")


class A9_LLM_AnalysisResponse(A9AgentBaseResponse):
    """Response model for LLM analysis operations"""
    analysis: Dict[str, Any] = Field(..., description="Analysis results")
    model_used: str = Field(..., description="The model used for analysis")
    usage: Dict[str, Any] = Field(..., description="Token usage information")
    confidence: float = Field(..., description="Confidence score for analysis")


class A9_LLM_SummaryResponse(A9AgentBaseResponse):
    """Response model for LLM summary operations"""
    summary: str = Field(..., description="Generated summary")
    model_used: str = Field(..., description="The model used for summarization")
    usage: Dict[str, Any] = Field(..., description="Token usage information")
    compression_ratio: float = Field(..., description="Ratio of original to summary length")


class A9_LLM_EvaluationResponse(A9AgentBaseResponse):
    """Response model for LLM evaluation operations"""
    rankings: List[Dict[str, Any]] = Field(..., description="Ranked options with scores")
    model_used: str = Field(..., description="The model used for evaluation")
    usage: Dict[str, Any] = Field(..., description="Token usage information")
    rationale: str = Field(..., description="Rationale for rankings")


class A9_LLM_SQLGenerationRequest(A9AgentBaseRequest):
    """Request model for SQL generation operations"""
    natural_language_query: str = Field(..., description="The natural language query to convert to SQL")
    data_product_id: str = Field(..., description="ID of the data product view to query")
    yaml_contract: Optional[str] = Field(None, description="Data product contract YAML (if available)")
    schema_details: Optional[Dict[str, Any]] = Field(None, description="Additional schema information")
    filters: Optional[Dict[str, Any]] = Field(None, description="Additional filters to apply")
    include_explain: bool = Field(False, description="Whether to include query explanation")
    model: Optional[str] = Field(None, description="Override the default model")
    operation: str = Field("generate_sql", description="The operation to perform")


class A9_LLM_SQLGenerationResponse(A9AgentBaseResponse):
    """Response model for SQL generation operations"""
    sql_query: str = Field(..., description="The generated SQL query")
    model_used: str = Field(..., description="The model used for generation")
    usage: Dict[str, Any] = Field(..., description="Token usage information")
    confidence: float = Field(..., description="Confidence score for the generated SQL")
    explanation: Optional[str] = Field(None, description="Explanation of the generated SQL")
    warnings: Optional[List[str]] = Field(None, description="Any warnings about the generated SQL")


class GuardrailConfig(BaseModel):
    """Configuration for LLM guardrails"""
    model_config = ConfigDict(extra="allow")
    
    system_prompt: str
    prohibited_patterns: List[Dict[str, str]] = []
    required_behaviors: List[Dict[str, str]] = []


class PromptTemplate(BaseModel):
    """Structure for prompt templates"""
    model_config = ConfigDict(extra="allow")
    
    template_id: str
    description: str
    content: str


class A9_LLM_Service_Agent:
    """
    Agent for centralized LLM operations with guardrails enforcement.
    
    This agent handles all LLM interactions for Agent9, providing:
    - Centralized LLM service with provider abstraction
    - Guardrails enforcement and prompt template application
    - Protocol-compliant request/response handling
    - Logging and auditability
    """
    
    def __init__(self, config: Union[A9_LLM_Service_Agent_Config, Dict[str, Any]]):
        """
        Initialize the LLM service agent with configuration.
        
        Args:
            config: Configuration for the agent, either as config model or dict
        """
        if isinstance(config, dict):
            self.config = A9_LLM_Service_Agent_Config(**config)
        else:
            self.config = config
        
        # Initialize appropriate LLM service based on provider
        self._initialize_llm_service()
        
        logger.info(f"A9_LLM_Service_Agent initialized with {self.config.provider} provider")
    
    @classmethod
    def create_from_registry(cls, config_dict: Dict[str, Any]) -> 'A9_LLM_Service_Agent':
        """
        Create an instance from registry configuration.
        This is the factory method used by the orchestrator.
        
        Args:
            config_dict: Configuration dictionary from registry
            
        Returns:
            Instance of A9_LLM_Service_Agent
        """
        return cls(config_dict)
    
    def _initialize_llm_service(self):
        """Initialize the appropriate LLM service based on provider config"""
        try:
            # Get API key from config or environment
            api_key = getattr(self.config, 'api_key', None) 
            if not api_key:
                api_key = os.environ.get(self.config.api_key_env_var)
            
            # Log API key presence (masked)
            if api_key:
                masked_key = api_key[:4] + "*" * (len(api_key) - 8) + api_key[-4:] if len(api_key) > 8 else "****"
                logger.info(f"Using {self.config.provider} API key: {masked_key}")
            else:
                logger.warning(f"No API key found in config or environment var {self.config.api_key_env_var}")
                raise ValueError(f"Missing API key for {self.config.provider} provider")
            
            # Convert agent config to service config
            service_config = {
                "model_name": self.config.model_name,
                "api_key": api_key,  # Pass the API key directly
                "api_key_env_var": self.config.api_key_env_var,
                "max_tokens": self.config.max_tokens,
                "temperature": self.config.temperature,
                "guardrails_path": self.config.guardrails_path,
                "prompt_templates_path": self.config.prompt_templates_path,
                "system_prompt_override": getattr(self.config, 'system_prompt', None),
            }
            
            # Initialize the appropriate service based on provider
            provider = self.config.provider.lower()
            logger.info(f"Initializing LLM service for provider: {provider}")
            
            # Debug service config
            logger.info(f"Service config: {service_config}")
            
            if provider == "anthropic":
                logger.info("Initializing Claude service with config...")
                self.llm_service = create_claude_service(service_config)
                logger.info(f"Claude service initialized successfully: {self.llm_service is not None}")
            elif provider == "openai":
                logger.info("Initializing OpenAI service with config...")
                try:
                    self.llm_service = create_openai_service(service_config)
                    logger.info(f"OpenAI service initialized successfully: {self.llm_service is not None}")
                except Exception as e:
                    logger.error(f"Failed to initialize OpenAI service: {str(e)}")
                    raise
            else:
                error_msg = f"Unsupported LLM provider: {provider}. Supported providers: anthropic, openai"
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            # Load guardrails and templates from the service
            self.guardrails = getattr(self.llm_service, 'guardrails', None)
            self.prompt_templates = getattr(self.llm_service, 'prompt_templates', None)
            
        except Exception as e:
            logger.error(f"Failed to initialize LLM service for {self.config.provider}: {str(e)}")
            self.llm_service = None
            self.guardrails = None
            self.prompt_templates = None
            raise
    
    def _load_guardrails(self) -> GuardrailConfig:
        """Load guardrails configuration from YAML file"""
        try:
            with open(self.config.guardrails_path, 'r') as f:
                guardrail_data = yaml.safe_load(f)
                
            # Extract system prompt from guardrails
            system_prompt = guardrail_data.get('system_prompts', {}).get(
                'claude_sonnet_thinking', {}).get('content', '')
            
            # Extract prohibited patterns
            prohibited_patterns = guardrail_data.get('prohibited_patterns', [])
            
            # Extract required behaviors
            required_behaviors = []
            behaviors_data = guardrail_data.get('behaviors', {})
            for behavior_id, behavior in behaviors_data.items():
                required_behaviors.append({
                    'id': behavior_id,
                    'description': behavior.get('description', ''),
                    'pattern': behavior.get('pattern', ''),
                    'required': behavior.get('required', False)
                })
            
            logger.info(f"Loaded guardrails from {self.config.guardrails_path}")
            return GuardrailConfig(
                system_prompt=system_prompt,
                prohibited_patterns=prohibited_patterns,
                required_behaviors=required_behaviors
            )
        except Exception as e:
            logger.error(f"Failed to load guardrails: {str(e)}")
            # Return default guardrails
            return GuardrailConfig(
                system_prompt="You are an AI assistant following Agent9 standards."
            )
    
    def _load_prompt_templates(self) -> Dict[str, PromptTemplate]:
        """Load prompt templates from markdown file"""
        templates = {}
        try:
            with open(self.config.prompt_templates_path, 'r') as f:
                content = f.read()
            
            # Simple parsing of markdown code blocks with titles
            import re
            pattern = r'### ([^\n]+)\n```\n(.*?)\n```'
            matches = re.findall(pattern, content, re.DOTALL)
            
            for title, template_content in matches:
                template_id = title.strip().lower().replace(' ', '_')
                templates[template_id] = PromptTemplate(
                    template_id=template_id,
                    description=title.strip(),
                    content=template_content.strip()
                )
            
            logger.info(f"Loaded {len(templates)} prompt templates from {self.config.prompt_templates_path}")
            return templates
        except Exception as e:
            logger.error(f"Failed to load prompt templates: {str(e)}")
            return {}
    
    def get_system_prompt(self) -> str:
        """Get the system prompt with guardrails applied"""
        if self.config.system_prompt_override:
            return self.config.system_prompt_override
        return self.guardrails.system_prompt
    
    def get_prompt_template(self, template_id: str) -> Optional[str]:
        """Get a prompt template by ID"""
        template = self.prompt_templates.get(template_id.lower().replace(' ', '_'))
        if template:
            return template.content
        return None
    
    def format_prompt_template(self, template_id: str, **kwargs) -> Optional[str]:
        """Format a prompt template with variables"""
        template_content = self.get_prompt_template(template_id)
        if not template_content:
            return None
        
        # Format the template with provided variables
        try:
            return template_content.format(**kwargs)
        except KeyError as e:
            logger.error(f"Missing variable in template formatting: {str(e)}")
            return None
    
    async def generate(self, request: A9_LLM_Request) -> A9_LLM_Response:
        """
        Generate text from LLM based on prompt
        
        Args:
            request: A9_LLM_Request with prompt and parameters
            
        Returns:
            A9_LLM_Response with generated content
        """
        try:
            # Use configured values if not overridden in request
            system_prompt = request.system_prompt or self.get_system_prompt()
            max_tokens = request.max_tokens or self.config.max_tokens
            temperature = request.temperature or self.config.temperature
            model = request.model or self.config.model_name
            
            # Log request (if enabled)
            if self.config.log_all_requests:
                logger.info(f"LLM request: {request.operation} using {model}")
            
            # Check if LLM service is available
            if not self.llm_service:
                raise ValueError(f"No LLM service available for provider {self.config.provider}")
            
            # Send request to provider via service layer
            provider = self.config.provider.lower()
            if provider == "anthropic":
                try:
                    # Use the service layer to generate the response - await the coroutine
                    result = await self.llm_service.generate(
                        prompt=request.prompt,
                        system_prompt=system_prompt,
                        max_tokens=max_tokens,
                        temperature=temperature
                    )
                    
                    # Extract response text and usage from service result
                    response_text = result.get("response", "")
                    usage = result.get("usage", {
                        "prompt_tokens": None,
                        "completion_tokens": None,
                        "total_tokens": None
                    })
                    
                    # Check if there was an error
                    if result.get("error"):
                        raise ValueError(f"Service layer error: {result.get('error')}")
                        
                    logger.info(f"Successfully generated response via Claude service with model {model}")
                except Exception as e:
                    logger.error(f"Error using Claude service: {str(e)}")
                    raise e
            elif provider == "openai":
                try:
                    # Use the service layer to generate the response - OpenAI service is NOT async
                    result = self.llm_service.generate(
                        prompt=request.prompt,
                        system_prompt=system_prompt,
                        max_tokens=max_tokens,
                        temperature=temperature
                    )
                    
                    # Extract response text and usage from service result
                    response_text = result.get("response", "")
                    usage = result.get("usage", {
                        "prompt_tokens": None,
                        "completion_tokens": None,
                        "total_tokens": None
                    })
                    
                    # Check if there was an error
                    if result.get("error"):
                        raise ValueError(f"Service layer error: {result.get('error')}")
                        
                    logger.info(f"Successfully generated response via OpenAI service with model {model}")
                except Exception as e:
                    logger.error(f"Error using OpenAI service: {str(e)}")
                    raise e
            else:
                # Mock response for unsupported providers
                logger.warning(f"Using mock response for unsupported provider: {provider}")
                response_text = f"Mock response for {request.prompt[:50]}..."
                usage = {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30}
            
            # Create and return response
            return A9_LLM_Response(
                status="success",
                request_id=request.request_id,
                content=response_text,
                model_used=model,
                usage=usage,
                operation=request.operation
            )
        except Exception as e:
            logger.error(f"Error in LLM generation: {str(e)}")
            return A9_LLM_Response(
                status="error",
                request_id=request.request_id,
                error_message=str(e),
                content="",
                model_used=request.model or self.config.model_name,
                usage={},
                operation=request.operation
            )
    
    async def generate_with_template(self, request: A9_LLM_TemplateRequest) -> A9_LLM_Response:
        """
        Generate text using a prompt template
        
        Args:
            request: A9_LLM_TemplateRequest with template ID and variables
            
        Returns:
            A9_LLM_Response with generated content
        """
        try:
            # Check if we can use the service layer's template capabilities directly
            if hasattr(self.llm_service, 'generate_with_template') and self.llm_service is not None:
                try:
                    # Use the service layer to generate with template
                    result = await self.llm_service.generate_with_template(
                        template_id=request.template_id,
                        template_vars=request.template_variables,
                        system_prompt=request.system_prompt,
                        max_tokens=request.max_tokens or self.config.max_tokens,
                        temperature=request.temperature or self.config.temperature
                    )
                    
                    # Check if there was an error
                    if result.get("error"):
                        raise ValueError(f"Service layer template error: {result.get('error')}")
                    
                    # Extract response and usage
                    response_text = result.get("response", "")
                    usage = result.get("usage", {"prompt_tokens": None, "completion_tokens": None, "total_tokens": None})
                    
                    return A9_LLM_Response(
                        status="success",
                        request_id=request.request_id,
                        content=response_text,
                        model_used=self.config.model_name,
                        usage=usage,
                        operation=request.operation
                    )
                except Exception as e:
                    logger.error(f"Error using service layer template generation: {str(e)}. Falling back to standard method.")
                    # Fall back to the standard method below
            
            # Format the template with provided variables (fallback)
            formatted_prompt = self.format_prompt_template(
                request.template_id, 
                **request.template_variables
            )
            
            if not formatted_prompt:
                return A9_LLM_Response(
                    status="error",
                    request_id=request.request_id,
                    error_message=f"Template {request.template_id} not found or formatting error",
                    content="",
                    model_used=request.model or self.config.model_name,
                    usage={},
                    operation=request.operation
                )
            
            # Create a standard request with the formatted prompt
            standard_request = A9_LLM_Request(
                request_id=request.request_id,
                timestamp=request.timestamp,
                principal_id=request.principal_id,
                principal_context=request.principal_context,
                situation_context=request.situation_context,
                business_context=request.business_context,
                prompt=formatted_prompt,
                model=request.model,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                system_prompt=request.system_prompt,
                operation=request.operation
            )
            
            # Process using the standard generate method
            return await self.generate(standard_request)
        except Exception as e:
            logger.error(f"Error in template generation: {str(e)}")
            return A9_LLM_Response(
                status="error",
                request_id=request.request_id,
                error_message=str(e),
                content="",
                model_used=request.model or self.config.model_name,
                usage={},
                operation=request.operation
            )
    
    async def analyze(self, request: A9_LLM_AnalysisRequest) -> A9_LLM_AnalysisResponse:
        """
        Analyze text or data using LLM
        
        Args:
            request: A9_LLM_AnalysisRequest with content to analyze
            
        Returns:
            A9_LLM_AnalysisResponse with analysis results
        """
        try:
            # Construct prompt for analysis based on type
            analysis_prompts = {
                "sentiment": "Analyze the sentiment of the following text. Return a JSON object with sentiment (positive/neutral/negative) and confidence score:\n\n{content}",
                "topics": "Extract the main topics from the following text. Return a JSON array of topics:\n\n{content}",
                "entities": "Extract named entities from the following text. Return a JSON object grouping entities by type:\n\n{content}",
                "summary": "Provide a concise summary of the following text. Return a JSON object with summary and key points:\n\n{content}",
                "custom": "{context}\n\n{content}"
            }
            
            # Get appropriate prompt or use custom
            prompt_template = analysis_prompts.get(
                request.analysis_type.lower(), 
                analysis_prompts["custom"]
            )
            
            # Format the prompt
            context = request.context or "Analyze the following content:"
            prompt = prompt_template.format(content=request.content, context=context)
            
            # Create a standard request
            standard_request = A9_LLM_Request(
                request_id=request.request_id,
                timestamp=request.timestamp,
                principal_id=request.principal_id,
                principal_context=request.principal_context,
                situation_context=request.situation_context,
                business_context=request.business_context,
                prompt=prompt,
                model=request.model,
                system_prompt="You are an analytical assistant. Respond only with valid JSON.",
                operation=request.operation
            )
            
            # Process using the standard generate method
            response = await self.generate(standard_request)
            
            if response.status == "error":
                return A9_LLM_AnalysisResponse(
                    status="error",
                    request_id=request.request_id,
                    error_message=response.error_message,
                    analysis={},
                    model_used=response.model_used,
                    usage=response.usage,
                    confidence=0.0
                )
            
            # Parse JSON response
            try:
                analysis_data = json.loads(response.content)
                confidence = analysis_data.get("confidence", 0.85)  # Default if not provided
            except json.JSONDecodeError:
                # Fallback if response is not valid JSON
                analysis_data = {"raw_response": response.content}
                confidence = 0.5
            
            # Create and return analysis response
            return A9_LLM_AnalysisResponse(
                status="success",
                request_id=request.request_id,
                analysis=analysis_data,
                model_used=response.model_used,
                usage=response.usage,
                confidence=confidence
            )
        except Exception as e:
            logger.error(f"Error in analysis: {str(e)}")
            return A9_LLM_AnalysisResponse(
                status="error",
                request_id=request.request_id,
                error_message=str(e),
                analysis={},
                model_used=request.model or self.config.model_name,
                usage={},
                confidence=0.0
            )
    
    async def summarize(self, request: A9_LLM_SummaryRequest) -> A9_LLM_SummaryResponse:
        """
        Create a summary of provided content
        
        Args:
            request: A9_LLM_SummaryRequest with content to summarize
            
        Returns:
            A9_LLM_SummaryResponse with summary
        """
        try:
            # Construct prompt for summarization
            max_length = f"Keep the summary under {request.max_length} words." if request.max_length else ""
            focus_areas = ""
            if request.focus_areas:
                focus_areas = "Focus particularly on these aspects: " + ", ".join(request.focus_areas)
            
            prompt = f"Summarize the following content concisely. {max_length} {focus_areas}\n\n{request.content}"
            
            # Create a standard request
            standard_request = A9_LLM_Request(
                request_id=request.request_id,
                timestamp=request.timestamp,
                principal_id=request.principal_id,
                principal_context=request.principal_context,
                situation_context=request.situation_context,
                business_context=request.business_context,
                prompt=prompt,
                model=request.model,
                operation=request.operation
            )
            
            # Process using the standard generate method
            response = await self.generate(standard_request)
            
            if response.status == "error":
                return A9_LLM_SummaryResponse(
                    status="error",
                    request_id=request.request_id,
                    error_message=response.error_message,
                    summary="",
                    model_used=response.model_used,
                    usage=response.usage,
                    compression_ratio=0.0
                )
            
            # Calculate compression ratio
            original_length = len(request.content.split())
            summary_length = len(response.content.split())
            compression_ratio = original_length / max(summary_length, 1)
            
            # Create and return summary response
            return A9_LLM_SummaryResponse(
                status="success",
                request_id=request.request_id,
                summary=response.content,
                model_used=response.model_used,
                usage=response.usage,
                compression_ratio=compression_ratio
            )
        except Exception as e:
            logger.error(f"Error in summarization: {str(e)}")
            return A9_LLM_SummaryResponse(
                status="error",
                request_id=request.request_id,
                error_message=str(e),
                summary="",
                model_used=request.model or self.config.model_name,
                usage={},
                compression_ratio=0.0
            )
    
    async def evaluate(self, request: A9_LLM_EvaluationRequest) -> A9_LLM_EvaluationResponse:
        """
        Evaluate or rank options using LLM
        
        Args:
            request: A9_LLM_EvaluationRequest with options to evaluate
            
        Returns:
            A9_LLM_EvaluationResponse with rankings
        """
        try:
            # Construct prompt for evaluation
            options_text = "\n".join([f"{i+1}. {option}" for i, option in enumerate(request.options)])
            criteria_text = "\n".join([f"- {criterion}" for criterion in request.criteria])
            context = request.context or "Evaluate the following options based on the criteria:"
            
            prompt = f"""${context}

OPTIONS:
{options_text}

CRITERIA:
{criteria_text}

Rank the options based on the criteria. Return a JSON array of objects, each with:
1. option: the option text
2. rank: numerical ranking (1 being best)
3. score: score out of 10
4. rationale: brief explanation for the ranking

Also include an overall "rationale" field explaining your reasoning process.
"""
            
            # Create a standard request
            standard_request = A9_LLM_Request(
                request_id=request.request_id,
                timestamp=request.timestamp,
                principal_id=request.principal_id,
                principal_context=request.principal_context,
                situation_context=request.situation_context,
                business_context=request.business_context,
                prompt=prompt,
                model=request.model,
                system_prompt="You are an evaluation assistant. Respond only with valid JSON.",
                operation=request.operation
            )
            
            # Process using the standard generate method
            response = await self.generate(standard_request)
            
            if response.status == "error":
                return A9_LLM_EvaluationResponse(
                    status="error",
                    request_id=request.request_id,
                    error_message=response.error_message,
                    rankings=[],
                    model_used=response.model_used,
                    usage=response.usage,
                    rationale=""
                )
            
            # Parse JSON response
            try:
                eval_data = json.loads(response.content)
                rankings = eval_data.get("rankings", [])
                rationale = eval_data.get("rationale", "")
            except json.JSONDecodeError:
                # Fallback if response is not valid JSON
                rankings = [{"option": opt, "rank": i+1, "score": 5.0, "rationale": "Error parsing response"} 
                           for i, opt in enumerate(request.options)]
                rationale = "Error parsing LLM response."
            
            # Create and return evaluation response
            return A9_LLM_EvaluationResponse(
                status="success",
                request_id=request.request_id,
                rankings=rankings,
                model_used=response.model_used,
                usage=response.usage,
                rationale=rationale
            )
        except Exception as e:
            logger.error(f"Error in evaluation: {str(e)}")
            return A9_LLM_EvaluationResponse(
                status="error",
                request_id=request.request_id,
                error_message=str(e),
                rankings=[],
                model_used=request.model or self.config.model_name,
                usage={},
                rationale=""
            )
            
    async def generate_sql(self, request: A9_LLM_SQLGenerationRequest) -> A9_LLM_SQLGenerationResponse:
        """
        Generate SQL from natural language query targeting a specific Data Product view
        
        Args:
            request: A9_LLM_SQLGenerationRequest with natural language query and data product details
            
        Returns:
            A9_LLM_SQLGenerationResponse with generated SQL query
        """
        try:
            # Prepare the context for SQL generation
            yaml_context = request.yaml_contract or ""
            schema_context = ""
            
            if request.schema_details:
                schema_fields = request.schema_details.get("fields", {})
                schema_context = "\nAvailable fields:\n" + "\n".join(
                    [f"- {field}: {details.get('description', '')} ({details.get('type', '')})" 
                     for field, details in schema_fields.items()]
                )
            
            # Construct the prompt for SQL generation
            prompt = f"""Generate a SQL query for the following natural language request. 
            The query should target the Data Product view '{request.data_product_id}'.
            
Natural language query: "{request.natural_language_query}"

Data Product ID: {request.data_product_id}

{schema_context}

"""
            
            # Add YAML contract if available
            if yaml_context:
                prompt += f"\nData Product Contract YAML:\n```yaml\n{yaml_context}\n```\n"
                
            # Add any filters that should be applied
            if request.filters and len(request.filters) > 0:
                filters_text = "\n".join([f"- {key}: {value}" for key, value in request.filters.items()])
                prompt += f"\nAdditional filters to apply:\n{filters_text}\n"
                
            # Add instructions for response format and explanation
            prompt += """
Generate a valid SQL query that addresses the natural language request.
Return your response in the following JSON format:
{
  "sql_query": "<the complete SQL query>",
  "confidence": <a number between 0 and 1 indicating your confidence>,
  "warnings": ["<any warnings about the query>"],
  "explanation": "<explanation of the query logic if requested>"
}

Important guidelines:
- Use only the fields available in the Data Product view
- Follow SQL best practices (use aliases, proper quoting, etc.)
- Only include explanation if specifically requested
- Avoid complex joins as they are already handled in the view definition
- Use standard SQL syntax compatible with DuckDB
- Start the query with SELECT
"""

            # Create a standard request
            standard_request = A9_LLM_Request(
                request_id=request.request_id,
                timestamp=request.timestamp,
                principal_id=request.principal_id,
                principal_context=request.principal_context,
                situation_context=request.situation_context,
                business_context=request.business_context,
                prompt=prompt,
                model=request.model,
                system_prompt="You are an expert SQL developer assistant specializing in DuckDB queries for business analytics. Always provide valid SQL that conforms to standard SQL syntax.",
                operation="generate_sql"
            )
            
            # Process using the standard generate method
            response = await self.generate(standard_request)
            
            if response.status == "error":
                return A9_LLM_SQLGenerationResponse(
                    status="error",
                    request_id=request.request_id,
                    error_message=response.error_message,
                    sql_query="",
                    model_used=response.model_used,
                    usage=response.usage,
                    confidence=0.0
                )
            
            # Parse JSON response
            try:
                sql_data = json.loads(response.content)
                sql_query = sql_data.get("sql_query", "")
                confidence = float(sql_data.get("confidence", 0.8)) # Default to 0.8 if not provided
                warnings = sql_data.get("warnings", [])
                explanation = sql_data.get("explanation", "") if request.include_explain else None
                
                # Basic validation of SQL query
                if not sql_query.strip().upper().startswith("SELECT"):
                    warnings.append("Generated query does not start with SELECT statement")
                    confidence = max(confidence * 0.7, 0.3)  # Reduce confidence
                    
                # Check for basic SQL injection patterns
                if any(pattern in sql_query.lower() for pattern in ["--", ";", "/*", "*/", "xp_"]):
                    warnings.append("Generated query contains potentially unsafe patterns")
                    confidence = max(confidence * 0.5, 0.2)  # Significantly reduce confidence
                
            except json.JSONDecodeError:
                # Fallback if response is not valid JSON - try to extract SQL using regex
                import re
                sql_match = re.search(r'SELECT[\s\S]+?(?=```|$)', response.content, re.IGNORECASE)
                sql_query = sql_match.group(0) if sql_match else ""
                confidence = 0.4  # Low confidence for regex extraction
                warnings = ["Failed to parse response as JSON, extracted SQL using pattern matching"]
                explanation = None
            
            # Create and return SQL generation response
            return A9_LLM_SQLGenerationResponse(
                status="success",
                request_id=request.request_id,
                sql_query=sql_query,
                model_used=response.model_used,
                usage=response.usage,
                confidence=confidence,
                explanation=explanation,
                warnings=warnings
            )
        except Exception as e:
            logger.error(f"Error in SQL generation: {str(e)}")
            return A9_LLM_SQLGenerationResponse(
                status="error",
                request_id=request.request_id,
                error_message=str(e),
                sql_query="",
                model_used=request.model or self.config.model_name,
                usage={},
                confidence=0.0
            )
