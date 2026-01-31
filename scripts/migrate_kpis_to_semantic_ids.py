import os
import yaml
import re
from pathlib import Path

STAGING_DIR = Path("src/registry_references/data_product_registry/staging")

def to_snake_case(name: str) -> str:
    """Convert a string to snake_case."""
    # Remove special characters
    name = re.sub(r'[^a-zA-Z0-9\s]', '', name)
    # Replace spaces with underscores and lower case
    return "_".join(name.lower().split())

def migrate_file(filepath: Path):
    print(f"Processing {filepath}...")
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        if not data or 'kpis' not in data or not isinstance(data['kpis'], list):
            print(f"  No KPIs found in {filepath.name}, skipping.")
            return

        updated_count = 0
        for kpi in data['kpis']:
            if not isinstance(kpi, dict):
                continue
            
            old_id = kpi.get('id')
            name = kpi.get('name')
            
            if name:
                new_id = to_snake_case(name)
                # Only update if it looks like a generic ID or just to enforce the standard
                if old_id != new_id:
                    print(f"  Renaming KPI: {old_id} -> {new_id} ({name})")
                    kpi['id'] = new_id
                    updated_count += 1
        
        if updated_count > 0:
            with open(filepath, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, sort_keys=False, allow_unicode=True)
            print(f"  Updated {updated_count} KPIs in {filepath.name}")
        else:
            print(f"  No changes needed for {filepath.name}")

    except Exception as e:
        print(f"Error processing {filepath}: {e}")

def main():
    if not STAGING_DIR.exists():
        print(f"Staging directory not found: {STAGING_DIR}")
        return

    for yaml_file in STAGING_DIR.glob("*.yaml"):
        migrate_file(yaml_file)

if __name__ == "__main__":
    main()
