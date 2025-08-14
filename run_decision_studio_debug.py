"""
Run Script for Decision Studio Debug UI

This script launches the Debug-enhanced Decision Studio UI
"""

import os
import subprocess
import sys
import time

def run_streamlit_app():
    """Run the Streamlit app for Decision Studio Debug UI."""
    print("Starting Decision Studio Debug UI...")
    
    # Path to the UI script
    ui_path = os.path.join("src", "views", "decision_studio_debug_ui.py")
    
    # Check if the file exists
    if not os.path.exists(ui_path):
        print(f"Error: UI file not found at {ui_path}")
        return False
    
    try:
        # Kill any existing Streamlit processes
        print("Stopping any existing Streamlit processes...")
        subprocess.run(["taskkill", "/F", "/IM", "streamlit.exe"], 
                      stdout=subprocess.PIPE, 
                      stderr=subprocess.PIPE)
        time.sleep(1)  # Give it a moment to shut down
    except Exception as e:
        # It's okay if this fails (no existing processes)
        pass
    
    try:
        # Run the Streamlit app
        print(f"Launching Streamlit app: {ui_path}")
        subprocess.Popen(["streamlit", "run", ui_path], 
                        stdout=subprocess.PIPE, 
                        stderr=subprocess.PIPE)
        
        print("Decision Studio Debug UI is now running!")
        print("Access the UI at: http://localhost:8501")
        return True
    except Exception as e:
        print(f"Error starting Streamlit app: {str(e)}")
        return False

if __name__ == "__main__":
    run_streamlit_app()
