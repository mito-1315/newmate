#!/usr/bin/env python3
"""
Test script to verify database connection and table structure
"""
import os
import sys
import asyncio
from supabase import create_client, Client

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.config import settings

async def test_database_connection():
    """Test database connection and table structure"""
    try:
        print("🔍 Testing database connection...")
        
        # Create Supabase client
        client: Client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_ROLE_KEY
        )
        
        print(f"✅ Connected to Supabase: {settings.SUPABASE_URL}")
        
        # Test basic connection
        print("\n🔍 Testing basic query...")
        result = client.table("issued_certificates").select("id").limit(1).execute()
        print(f"✅ Basic query successful: {len(result.data)} records found")
        
        # Check table structure
        print("\n🔍 Checking table structure...")
        result = client.rpc('get_table_columns', {'table_name': 'issued_certificates'}).execute()
        
        if result.data:
            columns = result.data
            print(f"✅ Table has {len(columns)} columns:")
            for col in columns:
                print(f"  - {col['column_name']}: {col['data_type']}")
        else:
            # Fallback: try to describe the table
            print("⚠️  Could not get column info via RPC, trying alternative method...")
            
            # Try to insert a test record to see what columns are missing
            test_record = {
                "id": "test_123",
                "certificate_id": "test_123",
                "student_name": "Test Student",
                "course_name": "Test Course",
                "institution": "Test University",
                "additional_data": {"test": "value"}
            }
            
            try:
                result = client.table("issued_certificates").insert(test_record).execute()
                print("✅ Test record inserted successfully")
                
                # Clean up test record
                client.table("issued_certificates").delete().eq("id", "test_123").execute()
                print("✅ Test record cleaned up")
                
            except Exception as e:
                print(f"❌ Error inserting test record: {str(e)}")
                if "additional_data" in str(e):
                    print("🔧 The 'additional_data' column is missing from the table")
                    print("📝 Please run the migration script: backend/migrations/add_missing_columns.sql")
        
        print("\n✅ Database connection test completed successfully!")
        
    except Exception as e:
        print(f"❌ Database connection failed: {str(e)}")
        print("\n🔧 Troubleshooting steps:")
        print("1. Check your SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in .env")
        print("2. Make sure the 'issued_certificates' table exists")
        print("3. Run the migration script: backend/migrations/add_missing_columns.sql")
        return False
    
    return True

if __name__ == "__main__":
    asyncio.run(test_database_connection())
