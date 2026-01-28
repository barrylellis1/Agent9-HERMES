import os
import sys
import subprocess
import logging
from typing import List

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def run_script(script_path: str):
    """Run a python script and stream output."""
    logger.info(f"Running {script_path}...")
    try:
        # Use the same python interpreter
        result = subprocess.run(
            [sys.executable, script_path],
            check=True,
            capture_output=True,
            text=True,
            env=os.environ.copy()
        )
        print(result.stdout)
        logger.info(f"✅ Successfully ran {script_path}")
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Failed to run {script_path}")
        print(e.stdout)
        print(e.stderr)
        raise

def main():
    logger.info("Starting unified sync from YAML to Supabase...")
    
    # Check environment variables
    if not os.getenv("SUPABASE_URL") or not os.getenv("SUPABASE_SERVICE_ROLE_KEY"):
        logger.error("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY. Please set them in .env")
        sys.exit(1)

    base_path = os.path.dirname(os.path.abspath(__file__))
    
    scripts_to_run = [
        "supabase_seed_data_products.py",
        "supabase_seed_kpis.py",
        "supabase_seed_business_processes.py",
        "supabase_seed_principal_profiles.py",
        "supabase_seed_business_glossary.py"
    ]
    
    success_count = 0
    
    for script_name in scripts_to_run:
        script_path = os.path.join(base_path, script_name)
        if not os.path.exists(script_path):
            logger.warning(f"Script not found: {script_path}")
            continue
            
        try:
            run_script(script_path)
            success_count += 1
        except Exception as e:
            logger.error(f"Stopping sync due to error in {script_name}")
            sys.exit(1)
            
    logger.info(f"🎉 Sync complete! {success_count}/{len(scripts_to_run)} registries synced.")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    main()
