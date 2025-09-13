#!/usr/bin/env python3
"""
Launch script for Decision Studio UI

This script properly sets up the Python path before running the Streamlit app.
"""

import os
import sys
import subprocess

# Add the project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)

# Run the Streamlit app
streamlit_path = os.path.join(project_root, "decision_studio.py")

if __name__ == "__main__":
    print(f"Starting Decision Studio UI from {streamlit_path}")
    print(f"Project root: {project_root}")
    
    # Use subprocess to run the streamlit command
    subprocess.run([
        "streamlit", "run", streamlit_path, 
        "--server.port=8503", 
        "--server.headless=false",
        "--browser.serverAddress=localhost"
    ])
