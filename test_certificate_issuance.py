#!/usr/bin/env python3
"""
Test script for certificate issuance endpoint
"""
import requests
import json
import os

# Test data
test_certificate_data = {
    "student_name": "John Doe",
    "roll_no": "CS2023001", 
    "course_name": "Computer Science",
    "year_of_passing": "2023",
    "grade": "A+",
    "institution_name": "University of Technology"
}

# Create a simple test image file
def create_test_image():
    # Create a simple 1x1 pixel PNG image
    png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\nIDATx\x9cc\xf8\x00\x00\x00\x01\x00\x01\x00\x00\x00\x00IEND\xaeB`\x82'
    
    with open('test_certificate.png', 'wb') as f:
        f.write(png_data)
    
    return 'test_certificate.png'

def test_certificate_issuance():
    """Test the certificate issuance endpoint"""
    try:
        # Create test image
        image_path = create_test_image()
        
        # Prepare the request
        url = "http://localhost:8000/issue/certificate"
        
        # Prepare files and data
        files = {
            'file': ('test_certificate.png', open(image_path, 'rb'), 'image/png')
        }
        
        data = {
            'certificate_data': json.dumps(test_certificate_data)
        }
        
        print("Testing certificate issuance endpoint...")
        print(f"URL: {url}")
        print(f"Certificate data: {test_certificate_data}")
        
        # Make the request
        response = requests.post(url, files=files, data=data)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Certificate issuance test PASSED!")
            result = response.json()
            print(f"Certificate ID: {result.get('certificate_id')}")
            print(f"Success: {result.get('success')}")
        else:
            print("❌ Certificate issuance test FAILED!")
            
    except Exception as e:
        print(f"❌ Error during test: {str(e)}")
    finally:
        # Clean up test file
        if os.path.exists('test_certificate.png'):
            os.remove('test_certificate.png')

if __name__ == "__main__":
    test_certificate_issuance()
