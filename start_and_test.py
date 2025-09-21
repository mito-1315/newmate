#!/usr/bin/env python3
"""
Script to start the backend server and test certificate issuance
"""
import subprocess
import sys
import os
import time
import requests
import json
import threading

def start_backend():
    """Start the backend server in a separate thread"""
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
        return process
        
    except Exception as e:
        print(f"Error starting backend: {e}")
        return None

def test_certificate_issuance():
    """Test the certificate issuance endpoint"""
    try:
        # Wait for server to start
        time.sleep(5)
        
        # Test if server is running
        try:
            response = requests.get('http://localhost:8000/', timeout=5)
            if response.status_code == 200:
                print("✅ Backend server is running!")
            else:
                print(f"❌ Backend server responded with status {response.status_code}")
                return
        except requests.exceptions.RequestException as e:
            print(f"❌ Could not connect to backend server: {e}")
            return
        
        # Test certificate issuance
        print("\nTesting certificate issuance...")
        
        # Create a simple test image
        png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\nIDATx\x9cc\xf8\x00\x00\x00\x01\x00\x01\x00\x00\x00\x00IEND\xaeB`\x82'
        
        # Test data
        test_certificate_data = {
            "student_name": "John Doe",
            "roll_no": "CS2023001", 
            "course_name": "Computer Science",
            "institution_name": "University of Technology",
            "year_of_passing": "2023",
            "grade": "A+",
            "department": "Computer Science"
        }
        
        # Prepare the request
        url = "http://localhost:8000/issue/certificate"
        
        files = {
            'file': ('test_certificate.png', png_data, 'image/png')
        }
        
        data = {
            'certificate_data': json.dumps(test_certificate_data)
        }
        
        print(f"Making request to: {url}")
        print(f"Certificate data: {test_certificate_data}")
        
        # Make the request
        response = requests.post(url, files=files, data=data, timeout=30)
        
        print(f"Response status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Certificate issuance test PASSED!")
            result = response.json()
            print(f"Certificate ID: {result.get('certificate_id')}")
            print(f"Success: {result.get('success')}")
            print(f"Message: {result.get('message')}")
        else:
            print("❌ Certificate issuance test FAILED!")
            
    except Exception as e:
        print(f"❌ Error during test: {str(e)}")

def main():
    """Main function"""
    print("Certificate Issuance Test Script")
    print("=" * 40)
    
    # Start backend server
    process = start_backend()
    if not process:
        print("Failed to start backend server")
        return
    
    try:
        # Test certificate issuance
        test_certificate_issuance()
        
        print("\nBackend server is running. Press Ctrl+C to stop.")
        process.wait()
        
    except KeyboardInterrupt:
        print("\nStopping backend server...")
        process.terminate()
        process.wait()
        print("Backend server stopped.")

if __name__ == "__main__":
    main()
