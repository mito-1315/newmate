#!/usr/bin/env python3
"""
Database setup script for Certificate Verification System
"""
import os
import sys
import asyncio
from supabase import create_client, Client

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.config import settings

def create_issued_certificates_table():
    """Create the issued_certificates table with all required columns"""
    
    sql_commands = [
        """
        -- Create issued_certificates table if it doesn't exist
        CREATE TABLE IF NOT EXISTS issued_certificates (
            id TEXT PRIMARY KEY,
            certificate_id TEXT NOT NULL,
            student_name TEXT NOT NULL,
            roll_no TEXT,
            course_name TEXT NOT NULL,
            institution TEXT NOT NULL,
            institution_name TEXT,
            department TEXT,
            issue_date DATE NOT NULL,
            year TEXT,
            grade TEXT,
            cgpa TEXT,
            additional_data JSONB DEFAULT '{}',
            status TEXT DEFAULT 'issued' CHECK (status IN ('issuing', 'issued', 'revoked', 'cancelled')),
            source TEXT DEFAULT 'digital' CHECK (source IN ('digital', 'legacy_verified')),
            image_url TEXT,
            image_hashes JSONB,
            attestation_id TEXT UNIQUE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            UNIQUE(certificate_id, institution)
        );
        """,
        
        """
        -- Add missing columns if they don't exist
        ALTER TABLE issued_certificates 
        ADD COLUMN IF NOT EXISTS additional_data JSONB DEFAULT '{}',
        ADD COLUMN IF NOT EXISTS department TEXT,
        ADD COLUMN IF NOT EXISTS cgpa TEXT,
        ADD COLUMN IF NOT EXISTS institution_name TEXT,
        ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'issued',
        ADD COLUMN IF NOT EXISTS source TEXT DEFAULT 'digital';
        """,
        
        """
        -- Create indexes for better performance
        CREATE INDEX IF NOT EXISTS idx_issued_certificates_status ON issued_certificates(status);
        CREATE INDEX IF NOT EXISTS idx_issued_certificates_source ON issued_certificates(source);
        CREATE INDEX IF NOT EXISTS idx_issued_certificates_institution ON issued_certificates(institution);
        CREATE INDEX IF NOT EXISTS idx_issued_certificates_student ON issued_certificates(student_name);
        """,
        
        """
        -- Enable RLS (Row Level Security)
        ALTER TABLE issued_certificates ENABLE ROW LEVEL SECURITY;
        """,
        
        """
        -- Create RLS policies
        CREATE POLICY IF NOT EXISTS "Certificates are publicly readable" ON issued_certificates
            FOR SELECT USING (status = 'issued');
        """,
        
        """
        -- Create verifications table if it doesn't exist
        CREATE TABLE IF NOT EXISTS verifications (
            id TEXT PRIMARY KEY,
            verification_id TEXT UNIQUE NOT NULL,
            attestation_id TEXT REFERENCES issued_certificates(attestation_id),
            layer_results JSONB NOT NULL DEFAULT '{}',
            risk_score JSONB NOT NULL DEFAULT '{}',
            database_check JSONB,
            integrity_checks JSONB,
            decision_rationale TEXT,
            auto_decision_confidence FLOAT,
            escalation_reasons TEXT[],
            requires_manual_review BOOLEAN DEFAULT FALSE,
            review_notes TEXT,
            reviewer_id TEXT,
            processing_time_total_ms INTEGER,
            canonical_image_hash TEXT,
            original_filename TEXT,
            user_id TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """,
        
        """
        -- Enable RLS for verifications
        ALTER TABLE verifications ENABLE ROW LEVEL SECURITY;
        """,
        
        """
        -- Create RLS policies for verifications
        CREATE POLICY IF NOT EXISTS "Verifications are publicly readable" ON verifications
            FOR SELECT USING (TRUE);
        """,
        
        """
        -- Create attestations table if it doesn't exist
        CREATE TABLE IF NOT EXISTS attestations (
            id TEXT PRIMARY KEY,
            attestation_id TEXT UNIQUE NOT NULL,
            certificate_id TEXT REFERENCES issued_certificates(id),
            signature TEXT NOT NULL,
            public_key TEXT NOT NULL,
            qr_code_url TEXT,
            pdf_url TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """,
        
        """
        -- Enable RLS for attestations
        ALTER TABLE attestations ENABLE ROW LEVEL SECURITY;
        """,
        
        """
        -- Create RLS policies for attestations
        CREATE POLICY IF NOT EXISTS "Attestations are publicly readable" ON attestations
            FOR SELECT USING (TRUE);
        """
    ]
    
    return sql_commands

async def setup_database():
    """Setup the database with all required tables and columns"""
    try:
        print("🚀 Setting up Certificate Verification Database...")
        
        # Create Supabase client
        client: Client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_ROLE_KEY
        )
        
        print(f"✅ Connected to Supabase: {settings.SUPABASE_URL}")
        
        # Get SQL commands
        sql_commands = create_issued_certificates_table()
        
        # Execute each SQL command
        for i, sql in enumerate(sql_commands, 1):
            try:
                print(f"📝 Executing SQL command {i}/{len(sql_commands)}...")
                result = client.rpc('exec_sql', {'sql_query': sql}).execute()
                print(f"✅ Command {i} executed successfully")
            except Exception as e:
                if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                    print(f"⚠️  Command {i} skipped (already exists): {str(e)[:100]}...")
                else:
                    print(f"❌ Command {i} failed: {str(e)}")
                    # Try alternative approach for some commands
                    if "CREATE TABLE" in sql or "ALTER TABLE" in sql:
                        print(f"🔄 Trying alternative approach for command {i}...")
                        try:
                            # Use direct SQL execution
                            result = client.postgrest.rpc('exec', {'sql': sql}).execute()
                            print(f"✅ Command {i} executed successfully (alternative method)")
                        except Exception as e2:
                            print(f"❌ Alternative method also failed: {str(e2)}")
        
        print("\n🎉 Database setup completed!")
        print("\n📋 Next steps:")
        print("1. Test the certificate issuance endpoint")
        print("2. Check that all tables and columns are created correctly")
        print("3. Run the frontend and try issuing a certificate")
        
        return True
        
    except Exception as e:
        print(f"❌ Database setup failed: {str(e)}")
        print("\n🔧 Manual setup required:")
        print("1. Go to your Supabase dashboard")
        print("2. Open the SQL Editor")
        print("3. Run the SQL commands from backend/migrations/add_missing_columns.sql")
        return False

if __name__ == "__main__":
    asyncio.run(setup_database())
