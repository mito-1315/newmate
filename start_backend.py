#!/usr/bin/env python3
"""
Script to start the backend server
"""
import subprocess
import sys
import os
import time
import requests

def start_backend():
    """Start the backend server"""
    try:
        print("Starting backend server...")
        
        # Change to backend directory
        backend_dir = os.path.join(os.path.dirname(__file__), 'backend')
        os.chdir(backend_dir)
        
        # Start the server
        process = subprocess.Popen([
            sys.executable, '-m', 'app.main'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        print(f"Backend process started with PID: {process.pid}")
        
        # Wait a bit for the server to start
        time.sleep(3)
        
        # Test if the server is running
        try:
            response = requests.get('http://localhost:8000/', timeout=5)
            if response.status_code == 200:
                print("✅ Backend server is running successfully!")
                print(f"Response: {response.json()}")
            else:
                print(f"❌ Backend server responded with status {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"❌ Could not connect to backend server: {e}")
        
        # Keep the process running
        print("Backend server is running. Press Ctrl+C to stop.")
        process.wait()
        
    except KeyboardInterrupt:
        print("\nStopping backend server...")
        process.terminate()
        process.wait()
        print("Backend server stopped.")
    except Exception as e:
        print(f"Error starting backend: {e}")

if __name__ == "__main__":
    start_backend()
