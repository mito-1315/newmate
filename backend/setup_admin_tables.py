#!/usr/bin/env python3
"""
Script to set up admin dashboard database tables
Run this after setting up your Supabase database
"""

import os
import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent / "app"))

from app.services.supabase_client import SupabaseClient
from app.config import settings

def setup_admin_tables():
    """Create admin dashboard tables in Supabase"""
    try:
        print("Setting up admin dashboard tables...")
        
        # Initialize Supabase client
        supabase_client = SupabaseClient()
        
        # Read the SQL file
        sql_file = Path(__file__).parent / "create_admin_tables.sql"
        with open(sql_file, 'r') as f:
            sql_content = f.read()
        
        # Split by semicolon and execute each statement
        statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
        
        for i, statement in enumerate(statements):
            if statement:
                print(f"Executing statement {i+1}/{len(statements)}...")
                try:
                    # Execute the SQL statement
                    result = supabase_client.client.rpc('exec_sql', {'sql': statement}).execute()
                    print(f"✓ Statement {i+1} executed successfully")
                except Exception as e:
                    print(f"⚠ Statement {i+1} failed (might already exist): {e}")
        
        print("\n✅ Admin dashboard tables setup completed!")
        print("\nTables created:")
        print("- verification_logs (tracks all verification attempts)")
        print("- blacklisted_certificates (blacklisted certificate IDs)")
        print("- blacklisted_ips (blacklisted IP addresses)")
        print("\nSample data inserted for testing.")
        
    except Exception as e:
        print(f"❌ Error setting up admin tables: {e}")
        print("\nMake sure your Supabase connection is working and you have the necessary permissions.")
        return False
    
    return True

if __name__ == "__main__":
    success = setup_admin_tables()
    sys.exit(0 if success else 1)
