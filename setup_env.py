#!/usr/bin/env python3
import os
import sys
import subprocess
import platform
import shutil
from pathlib import Path
# Import duckdb later after installation

def print_step(message):
    """Print a step message with formatting."""
    print(f"\n{'=' * 40}")
    print(f" {message}")
    print(f"{'=' * 40}\n")

def run_command(command, error_message=None):
    """Run a command and return True if successful, False otherwise."""
    try:
        subprocess.run(command, check=True)
        return True
    except subprocess.CalledProcessError:
        if error_message:
            print(f"Error: {error_message}")
        return False

def create_venv():
    """Create a virtual environment if it doesn't exist."""
    print_step("Setting up virtual environment...")
    
    venv_dir = "venv"
    if os.path.exists(venv_dir):
        print(f"Virtual environment already exists at {venv_dir}")
        return True
    
    # Create virtual environment
    success = run_command(
        [sys.executable, "-m", "venv", venv_dir],
        "Failed to create virtual environment"
    )
    
    if success:
        print(f"Created virtual environment at {venv_dir}")
        
        # Print activation instructions
        if platform.system() == "Windows":
            print("\nTo activate the virtual environment, run:")
            print(f"  {venv_dir}\\Scripts\\activate")
        else:
            print("\nTo activate the virtual environment, run:")
            print(f"  source {venv_dir}/bin/activate")
    
    return success

def install_dependencies():
    """Install dependencies from requirements.txt."""
    print_step("Installing dependencies...")
    
    if not os.path.exists("requirements.txt"):
        print("Error: requirements.txt not found")
        return False
    
    # Get path to pip
    if platform.system() == "Windows":
        pip_path = os.path.join("venv", "Scripts", "pip")
    else:
        pip_path = os.path.join("venv", "bin", "pip")
    
    # Skip pip upgrade as it's causing issues
    # Just log a message instead
    print("Skipping pip upgrade step...")
    success = True
    
    # Install dependencies
    success = run_command(
        [pip_path, "install", "-r", "requirements.txt"],
        "Failed to install dependencies"
    )
    
    if success:
        print("Successfully installed dependencies")
    
    return success

def setup_duckdb():
    """Set up DuckDB and load CSV files."""
    print_step("Setting up DuckDB...")
    
    try:
        # Try to import duckdb (should be installed by now)
        import duckdb
        
        # Create data directory if it doesn't exist
        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)
        
        # Initialize DuckDB database
        conn = duckdb.connect('data/agent9.duckdb')

        # Use the external SAP DataSphere data location
        csv_dir = Path(r'C:\Users\barry\Documents\Agent 9\SAP DataSphere Data\datasphere-content-1.7\datasphere-content-1.7\SAP_Sample_Content\CSV')
        if csv_dir.exists():
            print(f"Loading CSV files from {csv_dir}...")
            
            # Get list of CSV files (including in subdirectories)
            csv_files = []
            for path in csv_dir.glob('**/*.csv'):
                csv_files.append(path)
            
            for csv_file in csv_files:
                # Create a sanitized table name from the relative path
                relative_path = csv_file.relative_to(csv_dir)
                # Create a safe table name without backslashes or special characters
                table_name = str(relative_path).replace('\\', '_').replace('/', '_').replace('.csv', '').replace('-', '_')
                print(f"Loading {csv_file} into table {table_name}")
                
                # Convert path to string and escape backslashes for SQL
                csv_path_str = str(csv_file).replace('\\', '\\\\')
                
                # Create table from CSV
                conn.execute(f"CREATE TABLE IF NOT EXISTS {table_name} AS SELECT * FROM read_csv_auto('{csv_path_str}');")
                
            
            print(f"Loaded {len(csv_files)} CSV files into DuckDB")
        else:
            print(f"CSV directory not found at {csv_dir}")

        # List tables
        result = conn.execute("SHOW TABLES").fetchall()
        print("\nAvailable tables:")
        for table in result:
            print(f"- {table[0]}")

        conn.close()
        print("\nDuckDB setup complete!")
        return True
    except ImportError:
        print("DuckDB module not found. Please make sure it's installed.")
        return False
    except Exception as e:
        print(f"Error setting up DuckDB: {e}")
        return False

def create_env_file():
    """Create a .env file from .env.example if it doesn't exist."""
    print_step("Setting up environment variables...")
    
    if os.path.exists(".env"):
        print("A .env file already exists.")
        return True
    
    if os.path.exists(".env.example"):
        try:
            shutil.copy(".env.example", ".env")
            print("Created .env file from .env.example")
            print("Please update the .env file with your own values.")
            return True
        except Exception as e:
            print(f"Error creating .env file: {e}")
            return False
    else:
        print("Warning: .env.example not found")
        return False

def main():
    """Main function to set up the environment."""
    print_step("Agent9 Hackathon Environment Setup")
    
    # Create virtual environment
    if not create_venv():
        print("Failed to create virtual environment. Exiting.")
        return
    
    # Install dependencies
    if not install_dependencies():
        print("Failed to install dependencies. Exiting.")
        return
    
    # Set up DuckDB
    if not setup_duckdb():
        print("Failed to set up DuckDB. Exiting.")
        return
    
    # Create .env file
    create_env_file()
    
    print_step("Setup Complete!")
    print("The Agent9 Hackathon environment has been set up successfully.")
    print("\nNext steps:")
    print("1. Activate the virtual environment")
    print("2. Update the .env file with your own values if needed")
    print("3. Start developing!")

if __name__ == "__main__":
    main()
