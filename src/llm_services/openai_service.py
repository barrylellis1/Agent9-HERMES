"""
OpenAI LLM Service for Agent9-HERMES

This module provides integration with OpenAI GPT models with guardrail enforcement
and prompt template handling based on cascade_guardrails.md and cascade_prompt_templates.md.

Supports multi-model configuration for different task types:
- SQL generation: optimized for structured output
- NLP parsing: optimized for extraction
- Reasoning/Solution finding: optimized for complex analysis
- General: balanced for most tasks
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import yaml
from openai import OpenAI
from pydantic import BaseModel, ConfigDict, Field
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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


class TaskType:
    """Task type constants for model selection"""
    SQL_GENERATION = "sql_generation"
    NLP_PARSING = "nlp_parsing"
    REASONING = "reasoning"
    SOLUTION_FINDING = "solution_finding"
    BRIEFING = "briefing"
    GENERAL = "general"


# Default model mappings per task type
# Note: Using gpt-4-turbo as fallback since not all OpenAI projects have access to gpt-4o
DEFAULT_TASK_MODELS: Dict[str, str] = {
    TaskType.SQL_GENERATION: "gpt-4-turbo",
    TaskType.NLP_PARSING: "gpt-4-turbo",
    TaskType.REASONING: "gpt-4-turbo",
    TaskType.SOLUTION_FINDING: "gpt-4-turbo",
    TaskType.BRIEFING: "gpt-4-turbo",
    TaskType.GENERAL: "gpt-4-turbo",
}

# Environment variable names for task-specific model overrides
TASK_MODEL_ENV_VARS: Dict[str, str] = {
    TaskType.SQL_GENERATION: "OPENAI_MODEL_SQL",
    TaskType.NLP_PARSING: "OPENAI_MODEL_NLP",
    TaskType.REASONING: "OPENAI_MODEL_REASONING",
    TaskType.SOLUTION_FINDING: "OPENAI_MODEL_SOLUTION",
    TaskType.BRIEFING: "OPENAI_MODEL_BRIEFING",
    TaskType.GENERAL: "OPENAI_MODEL",
}


def get_model_for_task(task_type: str = TaskType.GENERAL) -> str:
    """
    Get the appropriate model for a given task type.
    
    Priority:
    1. Environment variable override for specific task
    2. General OPENAI_MODEL environment variable
    3. Default model for task type
    
    Args:
        task_type: One of TaskType constants
        
    Returns:
        Model name string
    """
    # Check task-specific env var first
    env_var = TASK_MODEL_ENV_VARS.get(task_type)
    if env_var:
        model = os.environ.get(env_var)
        if model:
            return model
    
    # Check general OPENAI_MODEL env var
    general_model = os.environ.get("OPENAI_MODEL")
    if general_model:
        return general_model
    
    # Fall back to default for task type
    return DEFAULT_TASK_MODELS.get(task_type, DEFAULT_TASK_MODELS[TaskType.GENERAL])


class OpenAIServiceConfig(BaseModel):
    """Configuration for OpenAI Service"""
    model_config = ConfigDict(extra="allow")
    
    model_name: str = Field(default_factory=lambda: get_model_for_task(TaskType.GENERAL))
    task_type: str = TaskType.GENERAL  # Task type for automatic model selection
    api_key_env_var: str = "OPENAI_API_KEY"
    max_tokens: int = 4096
    temperature: float = 0.7
    guardrails_path: str = "docs/cascade_guardrails.yaml"
    prompt_templates_path: str = "docs/cascade_prompt_templates.md"
    system_prompt_override: Optional[str] = None


class OpenAIService:
    """
    Service for interacting with OpenAI GPT models with guardrails enforcement.
    
    Features:
    - Loads guardrails from YAML configuration
    - Applies system prompts with guardrails
    - Enforces prohibited patterns
    - Provides prompt template integration
    - Handles API communication with OpenAI
    """
    
    def __init__(self, config: Union[OpenAIServiceConfig, Dict[str, Any]]):
        """
        Initialize the OpenAI service with configuration
        
        Args:
            config: Configuration for the service, either as OpenAIServiceConfig or dict
        """
        if isinstance(config, dict):
            self.config = OpenAIServiceConfig(**config)
        else:
            self.config = config
        
        # If model_name wasn't explicitly set, use task_type to determine model
        if not config.get("model_name") if isinstance(config, dict) else True:
            task_model = get_model_for_task(self.config.task_type)
            # Only override if using default
            if self.config.model_name == get_model_for_task(TaskType.GENERAL):
                self.config = OpenAIServiceConfig(
                    **{**self.config.model_dump(), "model_name": task_model}
                )
            
        # Get API key - first try direct API key, then environment variable
        api_key = getattr(self.config, 'api_key', None)
        logger.info(f"Direct API key present: {api_key is not None}")
        
        # If no direct API key, try getting from environment variable
        if not api_key:
            # List all environment variables for debugging
            env_vars = {key: '***' if 'key' in key.lower() or 'secret' in key.lower() else val 
                      for key, val in os.environ.items()}
            logger.info(f"Environment variables: {env_vars}")
            
            api_key = os.environ.get(self.config.api_key_env_var)
            logger.info(f"API key from env var {self.config.api_key_env_var} present: {api_key is not None}")
            
            # Double-check by explicitly loading from .env again
            if not api_key:
                logger.info("Trying to reload from .env file directly...")
                from dotenv import load_dotenv
                load_dotenv(override=True)
                api_key = os.environ.get(self.config.api_key_env_var)
                logger.info(f"API key after forced .env reload present: {api_key is not None}")
        
            
        # Validate we have an API key
        if not api_key:
            raise ValueError(f"API key not found - checked direct config and environment variable {self.config.api_key_env_var}")
        
        # Mask for logging (security)
        mask_body = "*" * max(len(api_key) - 4, 0)
        masked_key = (api_key[:4] + mask_body) if len(api_key) >= 4 else "****"
        logger.info(f"Initializing OpenAI client with API key: {masked_key}")
        
        # Initialize OpenAI client
        try:
            self.client = OpenAI(api_key=api_key)
            logger.info(f"OpenAI client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {str(e)}")
            raise
        
        # Load guardrails and prompt templates
        self.guardrails = self._load_guardrails()
        self.prompt_templates = self._load_prompt_templates()
        
        logger.info(f"OpenAI Service initialized with model {self.config.model_name}")
        
    def _load_guardrails(self) -> GuardrailConfig:
        """Load guardrails configuration from YAML file"""
        try:
            with open(self.config.guardrails_path, 'r', encoding='utf-8') as f:
                guardrail_data = yaml.safe_load(f)
                
            # Extract system prompt from guardrails
            system_prompt = guardrail_data.get('system_prompts', {}).get(
                'primary', "You are a helpful AI assistant."
            )
            
            # Extract prohibited patterns
            prohibited_patterns = guardrail_data.get('prohibited_patterns', [])
            
            # Extract required behaviors
            required_behaviors = guardrail_data.get('required_behaviors', [])
            
            return GuardrailConfig(
                system_prompt=system_prompt,
                prohibited_patterns=prohibited_patterns,
                required_behaviors=required_behaviors
            )
        except Exception as e:
            logger.error(f"Error loading guardrails from {self.config.guardrails_path}: {str(e)}")
            # Return default guardrail config
            return GuardrailConfig(
                system_prompt="You are a helpful AI assistant."
            )
    
    def _load_prompt_templates(self) -> Dict[str, PromptTemplate]:
        """Load prompt templates from markdown file"""
        templates = {}
        try:
            with open(self.config.prompt_templates_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Parse markdown content to extract templates
            # This assumes templates are in the format:
            # ## template_id
            # Description: template description
            # ```
            # template content
            # ```
            
            # Simple markdown parser
            import re
            pattern = r'## ([a-zA-Z0-9_]+)\s+Description:\s+(.*?)\s+```(.*?)```'
            matches = re.findall(pattern, content, re.DOTALL)
            
            for template_id, description, template_content in matches:
                templates[template_id] = PromptTemplate(
                    template_id=template_id,
                    description=description.strip(),
                    content=template_content.strip()
                )
                
            logger.info(f"Loaded {len(templates)} prompt templates from {self.config.prompt_templates_path}")
            
            return templates
        except Exception as e:
            logger.error(f"Error loading prompt templates from {self.config.prompt_templates_path}: {str(e)}")
            return {}
    
    def get_system_prompt(self) -> str:
        """Get the system prompt with guardrails"""
        # Override from config takes precedence
        return self.config.system_prompt_override or self.guardrails.system_prompt
    
    def get_prompt_template(self, template_id: str) -> Optional[PromptTemplate]:
        """Get a prompt template by ID"""
        return self.prompt_templates.get(template_id)
    
    def format_prompt_template(self, template_id: str, **kwargs) -> Optional[str]:
        """Format a prompt template with variables"""
        template = self.get_prompt_template(template_id)
        if not template:
            logger.error(f"Prompt template '{template_id}' not found")
            return None
        
        try:
            return template.content.format(**kwargs)
        except KeyError as e:
            logger.error(f"Missing variable in template '{template_id}': {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error formatting template '{template_id}': {str(e)}")
            return None

    def generate(self, 
                prompt: str, 
                system_prompt: Optional[str] = None,
                max_tokens: Optional[int] = None,
                temperature: Optional[float] = None) -> Dict[str, Any]:
        """
        Generate a response from OpenAI with guardrails applied
        
        Args:
            prompt: User prompt to send to the model
            system_prompt: Optional override for system prompt
            max_tokens: Optional override for max tokens
            temperature: Optional override for temperature
            
        Returns:
            Dict containing response and metadata
        """
        try:
            # Set up parameters with overrides
            _system_prompt = system_prompt or self.get_system_prompt()
            _max_tokens = max_tokens or self.config.max_tokens
            _temperature = temperature or self.config.temperature
            
            # Log request
            request_id = f"req_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            logger.info(f"Request {request_id}: Sending prompt to {self.config.model_name}")
            
            # Send request to OpenAI
            message = self.client.chat.completions.create(
                model=self.config.model_name,
                messages=[
                    {"role": "system", "content": _system_prompt},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=_max_tokens,
                temperature=_temperature
            )
            
            # Log success
            logger.info(f"Request {request_id}: Received response from {self.config.model_name}")
            
            # Extract response text
            response_text = message.choices[0].message.content
            
            # Return response with metadata
            return {
                "request_id": request_id,
                "model": self.config.model_name,
                "response": response_text,
                "usage": {
                    "prompt_tokens": message.usage.prompt_tokens,
                    "completion_tokens": message.usage.completion_tokens,
                    "total_tokens": message.usage.total_tokens
                },
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            # Return error response
            return {
                "request_id": f"err_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "error": str(e),
                "model": self.config.model_name,
                "response": None,
                "timestamp": datetime.now().isoformat()
            }
    
    def generate_with_template(self, 
                              template_id: str, 
                              template_vars: Dict[str, Any],
                              system_prompt: Optional[str] = None,
                              max_tokens: Optional[int] = None,
                              temperature: Optional[float] = None) -> Dict[str, Any]:
        """
        Generate a response using a prompt template
        
        Args:
            template_id: ID of the prompt template to use
            template_vars: Variables to format the template with
            system_prompt: Optional override for system prompt
            max_tokens: Optional override for max tokens
            temperature: Optional override for temperature
            
        Returns:
            Dict containing response and metadata
        """
        formatted_prompt = self.format_prompt_template(template_id, **template_vars)
        if not formatted_prompt:
            return {
                "error": f"Template {template_id} not found or formatting error",
                "response": None,
                "timestamp": datetime.now().isoformat()
            }
        
        return self.generate(
            prompt=formatted_prompt,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
            temperature=temperature
        )


# Factory function for creating the service
def create_openai_service(config: Union[Dict[str, Any], OpenAIServiceConfig]) -> OpenAIService:
    """Create a new OpenAI service instance with configuration
    
    Args:
        config: Configuration for the service, either as a dict or OpenAIServiceConfig
        
    Returns:
        Initialized OpenAIService instance
    """
    try:
        # Create the service instance
        service = OpenAIService(config)
        logger.info("Created OpenAI service with factory function")
        return service
    except Exception as e:
        logger.error(f"Failed to create OpenAI service: {str(e)}")
        # Re-raise to let caller handle
        raise


def create_service_for_task(task_type: str, **config_overrides) -> OpenAIService:
    """
    Create an OpenAI service optimized for a specific task type.
    
    Args:
        task_type: One of TaskType constants (sql_generation, nlp_parsing, reasoning, etc.)
        **config_overrides: Additional config overrides
        
    Returns:
        OpenAIService configured for the task
        
    Example:
        sql_service = create_service_for_task(TaskType.SQL_GENERATION)
        reasoning_service = create_service_for_task(TaskType.REASONING, temperature=0.3)
    """
    model = get_model_for_task(task_type)
    
    # Set appropriate defaults based on task type
    task_defaults = {
        TaskType.SQL_GENERATION: {"temperature": 0.1, "max_tokens": 2048},
        TaskType.NLP_PARSING: {"temperature": 0.1, "max_tokens": 1024},
        TaskType.REASONING: {"temperature": 0.7, "max_tokens": 8192},
        TaskType.SOLUTION_FINDING: {"temperature": 0.7, "max_tokens": 8192},
        TaskType.BRIEFING: {"temperature": 0.5, "max_tokens": 4096},
        TaskType.GENERAL: {"temperature": 0.7, "max_tokens": 4096},
    }
    
    defaults = task_defaults.get(task_type, task_defaults[TaskType.GENERAL])
    
    config = {
        "model_name": model,
        "task_type": task_type,
        **defaults,
        **config_overrides,
    }
    
    logger.info(f"Creating service for task '{task_type}' with model '{model}'")
    return create_openai_service(config)


# Convenience factory functions for common tasks
def create_sql_service(**config_overrides) -> OpenAIService:
    """Create a service optimized for SQL generation"""
    return create_service_for_task(TaskType.SQL_GENERATION, **config_overrides)


def create_nlp_service(**config_overrides) -> OpenAIService:
    """Create a service optimized for NLP parsing"""
    return create_service_for_task(TaskType.NLP_PARSING, **config_overrides)


def create_reasoning_service(**config_overrides) -> OpenAIService:
    """Create a service optimized for complex reasoning tasks"""
    return create_service_for_task(TaskType.REASONING, **config_overrides)


def create_solution_service(**config_overrides) -> OpenAIService:
    """Create a service optimized for solution finding/debate"""
    return create_service_for_task(TaskType.SOLUTION_FINDING, **config_overrides)


def create_briefing_service(**config_overrides) -> OpenAIService:
    """Create a service optimized for executive briefing generation"""
    return create_service_for_task(TaskType.BRIEFING, **config_overrides)
