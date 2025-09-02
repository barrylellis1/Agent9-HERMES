"""
Configuration module for Agent9.

This module provides access to configuration settings for Agent9 components.
"""

import os
import yaml
from typing import Dict, Any, Optional

# Default configuration paths
DEFAULT_CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config")
DEFAULT_REGISTRY_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "registry")

def get_config(config_name: str, config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Get configuration for a specific component.
    
    Args:
        config_name: Name of the configuration to load
        config_path: Optional path to configuration directory
        
    Returns:
        Configuration dictionary
    """
    if config_path is None:
        config_path = os.environ.get("AGENT9_CONFIG_PATH", DEFAULT_CONFIG_PATH)
    
    config_file = os.path.join(config_path, f"{config_name}.yaml")
    
    # Check if config file exists
    if not os.path.exists(config_file):
        # Return default configuration
        if config_name == "registry":
            return {
                "base_path": os.path.dirname(os.path.dirname(__file__)),
                "registry_path": DEFAULT_REGISTRY_PATH
            }
        return {}
    
    # Load configuration from file
    try:
        with open(config_file, "r") as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        print(f"Error loading configuration {config_name}: {str(e)}")
        return {}
