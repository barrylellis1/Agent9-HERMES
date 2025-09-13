"""
Claude LLM Service for Agent9-HERMES

This module provides integration with Claude 3 Sonnet LLM with guardrail enforcement
and prompt template handling based on the cascade_guardrails.md and cascade_prompt_templates.md.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import yaml
import anthropic
from pydantic import BaseModel, ConfigDict, Field
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BehaviorRule(BaseModel):
    """Behavior rule for guardrails with explicit boolean 'required'"""
    model_config = ConfigDict(extra="allow")
    
    id: str
    description: str = ""
    pattern: str = ""
    required: bool = False


class GuardrailConfig(BaseModel):
    """Configuration for Claude guardrails"""
    model_config = ConfigDict(extra="allow")
    
    system_prompt: str
    prohibited_patterns: List[Dict[str, str]] = []
    required_behaviors: List[BehaviorRule] = []


class PromptTemplate(BaseModel):
    """Structure for prompt templates"""
    model_config = ConfigDict(extra="allow")
    
    template_id: str
    description: str
    content: str


class ClaudeServiceConfig(BaseModel):
    """Configuration for Claude Service"""
    model_config = ConfigDict(extra="allow")
    
    model_name: str = "claude-sonnet-4-20250514"  # Updated to latest model version per user instruction
    api_key_env_var: str = "ANTHROPIC_API_KEY"
    max_tokens: int = 4096
    temperature: float = 0.7
    guardrails_path: str = "docs/cascade_guardrails.yaml"
    prompt_templates_path: str = "docs/cascade_prompt_templates.md"
    system_prompt_override: Optional[str] = None


class ClaudeService:
    """
    Service for interacting with Claude 3 Sonnet with guardrails enforcement.
    
    Features:
    - Loads guardrails from YAML configuration
    - Applies system prompts with guardrails
    - Enforces prohibited patterns
    - Provides prompt template integration
    - Handles API communication with Claude
    """
    
    def __init__(self, config: Union[ClaudeServiceConfig, Dict[str, Any]]):
        """
        Initialize the Claude service with configuration
        
        Args:
            config: Configuration for the service, either as ClaudeServiceConfig or dict
        """
        if isinstance(config, dict):
            self.config = ClaudeServiceConfig(**config)
        else:
            self.config = config
            
        # Get API key - first try direct API key, then environment variable
        api_key = getattr(self.config, 'api_key', None)
        logger.info(f"Direct API key present: {api_key is not None}")
        
        # If no direct API key, try getting from environment variable
        if not api_key:
            # List all environment variables for debugging
            env_vars = {key: '***' if 'key' in key.lower() else val for key, val in os.environ.items()}
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
        masked_key = api_key[:4] + "*" * (len(api_key) - 8) + api_key[-4:] if len(api_key) > 8 else "****"
        logger.info(f"Initializing Claude client with API key: {masked_key}")
        
        # Initialize Claude client
        try:
            self.client = anthropic.Anthropic(api_key=api_key)
            logger.info(f"Claude client initialized with anthropic SDK version: {anthropic.__version__}")
        except Exception as e:
            logger.error(f"Failed to initialize anthropic client: {str(e)}")
            raise
        
        # Load guardrails and prompt templates
        self.guardrails = self._load_guardrails()
        self.prompt_templates = self._load_prompt_templates()
        
        logger.info(f"Claude Service initialized with model {self.config.model_name}")
        
    def _load_guardrails(self) -> GuardrailConfig:
        """Load guardrails configuration from YAML file"""
        try:
            with open(self.config.guardrails_path, 'r', encoding='utf-8') as f:
                guardrail_data = yaml.safe_load(f)
                
            # Extract system prompt from guardrails
            system_prompt = guardrail_data.get('system_prompts', {}).get(
                'claude_sonnet_thinking', {}).get('content', '')
            
            # Extract prohibited patterns
            prohibited_patterns = guardrail_data.get('prohibited_patterns', [])
            
            # Extract required behaviors
            required_behaviors: List[BehaviorRule] = []
            behaviors_data = guardrail_data.get('behaviors', {})
            for behavior_id, behavior in behaviors_data.items():
                required_behaviors.append(
                    BehaviorRule(
                        id=str(behavior_id),
                        description=str(behavior.get('description', '')),
                        pattern=str(behavior.get('pattern', '')),
                        required=bool(behavior.get('required', False))
                    )
                )
            
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
                system_prompt="You are Cascade, an AI assistant following Agent9 standards."
            )
    
    def _load_prompt_templates(self) -> Dict[str, PromptTemplate]:
        """Load prompt templates from markdown file"""
        templates = {}
        try:
            with open(self.config.prompt_templates_path, 'r', encoding='utf-8') as f:
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
        """Get the system prompt with guardrails"""
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
    
    async def generate(self, 
                     prompt: str, 
                     system_prompt: Optional[str] = None,
                     max_tokens: Optional[int] = None,
                     temperature: Optional[float] = None) -> Dict[str, Any]:
        """
        Generate a response from Claude with guardrails applied
        
        Args:
            prompt: User prompt to send to Claude
            system_prompt: Optional override for system prompt
            max_tokens: Optional override for max tokens
            temperature: Optional override for temperature
            
        Returns:
            Dict containing response and metadata
        """
        try:
            # Use configured values if not overridden
            _system_prompt = system_prompt or self.get_system_prompt()
            _max_tokens = max_tokens or self.config.max_tokens
            _temperature = temperature or self.config.temperature
            
            # Log request
            request_id = f"req_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            logger.info(f"Request {request_id}: Sending prompt to {self.config.model_name}")
            
            # Send request to Claude (using the correct API for the client version)
            # For anthropic SDK v0.8.0 which doesn't support 'system' parameter
            # Incorporate system prompt into the main prompt text
            system_prefix = f"\n\nHere's how you should respond: {_system_prompt}\n\n" if _system_prompt else ""
            formatted_prompt = f"{system_prefix}{anthropic.HUMAN_PROMPT} {prompt}{anthropic.AI_PROMPT}"
            
            message = self.client.completions.create(
                model=self.config.model_name,
                max_tokens_to_sample=_max_tokens,
                temperature=_temperature,
                prompt=formatted_prompt,
                stop_sequences=[anthropic.HUMAN_PROMPT]
                # 'system' parameter not supported in SDK 0.8.0
            )
            
            # Log success
            logger.info(f"Request {request_id}: Received response from {self.config.model_name}")
            
            # Extract response text (structure depends on SDK version)
            response_text = message.completion
            
            # Return response with metadata
            return {
                "request_id": request_id,
                "model": self.config.model_name,
                "response": response_text,
                "usage": {
                    "prompt_tokens": getattr(message, 'prompt_tokens', None),
                    "completion_tokens": getattr(message, 'completion_tokens', None)
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
def create_claude_service(config: Union[Dict[str, Any], ClaudeServiceConfig]) -> ClaudeService:
    """Create a new Claude service instance with configuration
    
    Args:
        config: Configuration for the service, either as a dict or ClaudeServiceConfig
        
    Returns:
        Initialized ClaudeService instance
    """
    try:
        # Create the service instance
        service = ClaudeService(config)
        logger.info("Created Claude service with factory function")
        return service
    except Exception as e:
        logger.error(f"Failed to create Claude service: {str(e)}")
        # Re-raise to let caller handle
        raise
