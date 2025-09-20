#!/usr/bin/env python3
"""
Test script to verify the certificate verification system setup
Run this after completing the setup to ensure everything is working
"""
import asyncio
import sys
import os
import requests
import json
from datetime import datetime

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

async def test_backend_health():
    """Test if backend is running"""
    try:
        response = requests.get("http://localhost:8000/", timeout=5)
        if response.status_code == 200:
            print("✅ Backend is running and healthy")
            return True
        else:
            print(f"❌ Backend returned status code: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Backend is not accessible: {e}")
        return False

def test_frontend_health():
    """Test if frontend is running"""
    try:
        response = requests.get("http://localhost:3000/", timeout=5)
        if response.status_code == 200:
            print("✅ Frontend is running and accessible")
            return True
        else:
            print(f"❌ Frontend returned status code: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Frontend is not accessible: {e}")
        return False

async def test_certificate_issuance():
    """Test certificate issuance endpoint"""
    try:
        test_certificate = {
            "certificate_data": {
                "certificate_id": "TEST-001",
                "student_name": "Test Student",
                "course_name": "Test Course",
                "institution": "Test University",
                "issue_date": datetime.now().strftime("%Y-%m-%d"),
                "year": "2023",
                "grade": "First Class"
            },
            "institution_id": "default"
        }
        
        response = requests.post(
            "http://localhost:8000/api/issue/certificate",
            json=test_certificate,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Certificate issuance test passed")
            print(f"   Issuance ID: {result.get('issuance_id', 'N/A')}")
            print(f"   Verification URL: {result.get('verification_url', 'N/A')}")
            return result
        else:
            print(f"❌ Certificate issuance failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"❌ Certificate issuance request failed: {e}")
        return None

async def test_verification(verification_url):
    """Test public verification endpoint"""
    try:
        if not verification_url:
            print("❌ No verification URL provided")
            return False
        
        # Extract attestation ID from URL
        attestation_id = verification_url.split("/verify/")[-1]
        
        response = requests.get(f"http://localhost:8000/api/verify/{attestation_id}", timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("valid"):
                print("✅ Certificate verification test passed")
                print(f"   Certificate Valid: {result.get('valid')}")
                print(f"   Student: {result.get('certificate_details', {}).get('student_name', 'N/A')}")
                return True
            else:
                print(f"❌ Certificate verification failed: {result.get('error', 'Unknown error')}")
                return False
        else:
            print(f"❌ Verification request failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Verification request failed: {e}")
        return False

async def test_database_connection():
    """Test database connection by checking institutions"""
    try:
        # This tests the institution endpoint which requires database access
        response = requests.get("http://localhost:8000/api/analytics/verification-stats", timeout=10)
        
        if response.status_code == 200:
            print("✅ Database connection test passed")
            return True
        else:
            print(f"❌ Database connection test failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Database connection test failed: {e}")
        return False

def check_environment_variables():
    """Check if required environment variables are set"""
    required_vars = [
        "SUPABASE_URL",
        "SUPABASE_ANON_KEY", 
        "SUPABASE_SERVICE_ROLE_KEY"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        print("   Please check your .env file")
        return False
    else:
        print("✅ All required environment variables are set")
        return True

async def main():
    """Run all tests"""
    print("🧪 Running Certificate Verification System Tests")
    print("=" * 50)
    
    # Test 1: Environment variables
    print("\n1. Testing Environment Variables...")
    env_ok = check_environment_variables()
    
    # Test 2: Backend health
    print("\n2. Testing Backend Health...")
    backend_ok = await test_backend_health()
    
    # Test 3: Frontend health
    print("\n3. Testing Frontend Health...")
    frontend_ok = test_frontend_health()
    
    # Test 4: Database connection
    print("\n4. Testing Database Connection...")
    db_ok = await test_database_connection()
    
    # Test 5: Certificate issuance (if backend is working)
    print("\n5. Testing Certificate Issuance...")
    issuance_result = None
    if backend_ok and db_ok:
        issuance_result = await test_certificate_issuance()
    else:
        print("❌ Skipping issuance test (backend or database not working)")
    
    # Test 6: Certificate verification (if issuance worked)
    print("\n6. Testing Certificate Verification...")
    if issuance_result:
        verification_url = issuance_result.get("verification_url")
        await test_verification(verification_url)
    else:
        print("❌ Skipping verification test (issuance failed)")
    
    # Summary
    print("\n" + "=" * 50)
    print("🎯 Test Summary:")
    print(f"   Environment Variables: {'✅' if env_ok else '❌'}")
    print(f"   Backend Health: {'✅' if backend_ok else '❌'}")
    print(f"   Frontend Health: {'✅' if frontend_ok else '❌'}")
    print(f"   Database Connection: {'✅' if db_ok else '❌'}")
    print(f"   Certificate Issuance: {'✅' if issuance_result else '❌'}")
    
    if all([env_ok, backend_ok, db_ok, issuance_result]):
        print("\n🎉 All tests passed! Your system is ready to use.")
        print("\nNext steps:")
        print("1. Open http://localhost:3000 in your browser")
        print("2. Go to the 'Issue' tab to create certificates")
        print("3. Test QR code verification")
    else:
        print("\n⚠️  Some tests failed. Please check the setup guide and fix the issues.")
        print("   Refer to SETUP_GUIDE.md for troubleshooting steps.")

if __name__ == "__main__":
    asyncio.run(main())
