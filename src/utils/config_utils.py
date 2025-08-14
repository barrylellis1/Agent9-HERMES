"""
Utility functions for loading and handling configuration files.
"""

import os
import yaml
from typing import Dict, Any, Optional


def load_yaml(file_path: str) -> Dict[str, Any]:
    """
    Load a YAML file and return its contents as a dictionary.
    
    Args:
        file_path: Path to the YAML file
        
    Returns:
        Dictionary containing YAML file contents
        
    Raises:
        FileNotFoundError: If file does not exist
        yaml.YAMLError: If file contains invalid YAML
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"YAML file not found: {file_path}")
    
    with open(file_path, 'r') as f:
        try:
            return yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"Error parsing YAML file {file_path}: {str(e)}")
