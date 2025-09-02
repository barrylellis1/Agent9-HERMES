"""
Simple script to examine the registry structure directly from YAML files.
"""
import sys
import logging
import yaml
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_yaml(file_path):
    """Load YAML file."""
    try:
        with open(file_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Error loading YAML file {file_path}: {e}")
        return None

def main():
    """Examine registry structure."""
    logger.info("=== Examining Registry Structure ===")
    
    # Define registry paths
    registry_paths = {
        "principal": "src/registry/principal/principal_registry.yaml",
        "business_process": "src/registry/business_process/business_process_registry.yaml",
        "kpi": "src/registry/kpi/kpi_registry.yaml",
        "data_product": "src/registry/data_product/data_product_registry.yaml",
        "business_glossary": "src/registry/data/business_glossary.yaml"
    }
    
    # Check each registry
    for name, path in registry_paths.items():
        full_path = Path(path)
        logger.info(f"Checking {name} registry at {full_path}")
        
        if full_path.exists():
            logger.info(f"  File exists: {full_path}")
            data = load_yaml(full_path)
            if data:
                logger.info(f"  Successfully loaded {name} registry")
                if name == "principal":
                    # Examine principal registry structure
                    if "principals" in data:
                        principals = data["principals"]
                        logger.info(f"  Found {len(principals)} principals:")
                        for principal in principals:
                            logger.info(f"    ID: {principal.get('id')}")
                            logger.info(f"    Name: {principal.get('name')}")
                            logger.info(f"    Role: {principal.get('role')}")
                            logger.info(f"    Business Processes: {principal.get('business_processes', [])}")
                            logger.info(f"    Default Filters: {principal.get('default_filters', {})}")
                            logger.info("    ---")
                    else:
                        logger.warning("  No principals found in registry")
                        
                    if "roles" in data:
                        roles = data["roles"]
                        logger.info(f"  Found {len(roles)} roles:")
                        for role in roles:
                            logger.info(f"    ID: {role.get('id')}")
                            logger.info(f"    Name: {role.get('name')}")
                            logger.info(f"    Description: {role.get('description')}")
                            logger.info(f"    Permissions: {role.get('permissions', [])}")
                            logger.info("    ---")
                    else:
                        logger.warning("  No roles found in registry")
            else:
                logger.error(f"  Failed to load {name} registry")
        else:
            logger.error(f"  File does not exist: {full_path}")

if __name__ == "__main__":
    main()
