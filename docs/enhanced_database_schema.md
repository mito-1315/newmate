# Enhanced Database Schema for Certificate Verification System

## Overview
This document outlines the complete database schema for the certificate verification system, including authentication, roles, legacy verification, and enhanced tracking.

## Tables

### 1. User Profiles
```sql
CREATE TABLE user_profiles (
    user_id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    full_name TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('university_admin', 'student', 'employer', 'super_admin')),
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'pending_verification', 'suspended')),
    
    -- Institution-specific fields
    institution_id TEXT REFERENCES institutions(id),
    institution_name TEXT,
    student_id TEXT, -- For students
    department TEXT,
    
    -- Contact information
    phone TEXT,
    address TEXT,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE
);

-- RLS Policies
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own profile" ON user_profiles
    FOR SELECT USING (auth.uid()::text = user_id);

CREATE POLICY "Users can update own profile" ON user_profiles
    FOR UPDATE USING (auth.uid()::text = user_id);

CREATE POLICY "Admins can view all profiles" ON user_profiles
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM user_profiles 
            WHERE user_id = auth.uid()::text 
            AND role IN ('university_admin', 'super_admin')
        )
    );
```

### 2. Institutions
```sql
CREATE TABLE institutions (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    domain TEXT UNIQUE NOT NULL,
    contact_email TEXT NOT NULL,
    contact_phone TEXT,
    address TEXT,
    
    -- Verification settings
    public_key TEXT NOT NULL,
    verification_endpoint TEXT,
    auto_approve_legacy BOOLEAN DEFAULT FALSE,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- RLS Policies
ALTER TABLE institutions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Institutions are publicly readable" ON institutions
    FOR SELECT USING (is_active = TRUE);

CREATE POLICY "Admins can manage institutions" ON institutions
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM user_profiles 
            WHERE user_id = auth.uid()::text 
            AND role IN ('university_admin', 'super_admin')
        )
    );
```

### 3. Enhanced Issued Certificates
```sql
CREATE TABLE issued_certificates (
    id TEXT PRIMARY KEY,
    certificate_id TEXT NOT NULL,
    student_name TEXT NOT NULL,
    roll_no TEXT,
    course_name TEXT NOT NULL,
    institution TEXT NOT NULL,
    institution_id TEXT REFERENCES institutions(id),
    issue_date DATE NOT NULL,
    year TEXT,
    grade TEXT,
    additional_data JSONB,
    
    -- Enhanced issuance workflow fields
    status TEXT DEFAULT 'issued' CHECK (status IN ('issuing', 'issued', 'revoked', 'cancelled')),
    image_url TEXT,
    image_hashes JSONB, -- SHA256, pHash, etc.
    attestation_id TEXT UNIQUE,
    
    -- Source tracking
    source TEXT DEFAULT 'digital' CHECK (source IN ('digital', 'legacy_verified')),
    legacy_request_id TEXT, -- If from legacy verification
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(certificate_id, institution)
);

-- RLS Policies
ALTER TABLE issued_certificates ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Certificates are publicly readable" ON issued_certificates
    FOR SELECT USING (status = 'issued');

CREATE POLICY "Institution admins can manage their certificates" ON issued_certificates
    FOR ALL USING (
        institution_id IN (
            SELECT institution_id FROM user_profiles 
            WHERE user_id = auth.uid()::text 
            AND role = 'university_admin'
        )
    );
```

### 4. Legacy Verification Requests
```sql
CREATE TABLE legacy_verification_requests (
    request_id TEXT PRIMARY KEY,
    student_name TEXT NOT NULL,
    student_email TEXT NOT NULL,
    roll_no TEXT NOT NULL,
    course_name TEXT NOT NULL,
    year TEXT NOT NULL,
    institution TEXT NOT NULL,
    
    -- Uploaded certificate
    certificate_image_url TEXT NOT NULL,
    certificate_filename TEXT NOT NULL,
    file_size INTEGER NOT NULL,
    
    -- Status and tracking
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'under_review', 'approved', 'rejected', 'expired')),
    submitted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    reviewed_at TIMESTAMP WITH TIME ZONE,
    reviewer_id TEXT REFERENCES user_profiles(user_id),
    
    -- Review details
    review_notes TEXT,
    rejection_reason TEXT,
    
    -- Additional metadata
    additional_info JSONB DEFAULT '{}',
    
    -- Generated certificate (if approved)
    attestation_id TEXT,
    qr_code_url TEXT,
    verified_certificate_url TEXT
);

-- RLS Policies
ALTER TABLE legacy_verification_requests ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Students can view own requests" ON legacy_verification_requests
    FOR SELECT USING (student_email = auth.jwt() ->> 'email');

CREATE POLICY "Institution admins can view their requests" ON legacy_verification_requests
    FOR SELECT USING (
        institution IN (
            SELECT institution_name FROM user_profiles 
            WHERE user_id = auth.uid()::text 
            AND role = 'university_admin'
        )
    );

CREATE POLICY "Institution admins can update their requests" ON legacy_verification_requests
    FOR UPDATE USING (
        institution IN (
            SELECT institution_name FROM user_profiles 
            WHERE user_id = auth.uid()::text 
            AND role = 'university_admin'
        )
    );
```

### 5. Enhanced Verifications
```sql
CREATE TABLE verifications (
    id TEXT PRIMARY KEY,
    verification_id TEXT UNIQUE NOT NULL,
    attestation_id TEXT REFERENCES issued_certificates(attestation_id),
    
    -- Enhanced layer results
    layer_results JSONB NOT NULL, -- Complete layer analysis results
    risk_score JSONB NOT NULL, -- Detailed risk scoring
    database_check JSONB, -- Database matching results
    integrity_checks JSONB, -- QR and hash integrity checks
    decision_rationale TEXT, -- Human-readable decision explanation
    
    -- Processing metadata
    auto_decision_confidence FLOAT,
    escalation_reasons TEXT[],
    requires_manual_review BOOLEAN DEFAULT FALSE,
    review_notes TEXT,
    reviewer_id TEXT REFERENCES user_profiles(user_id),
    
    -- Performance tracking
    processing_time_total_ms INTEGER,
    canonical_image_hash TEXT,
    original_filename TEXT,
    
    -- User tracking
    user_id TEXT REFERENCES user_profiles(user_id),
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- RLS Policies
ALTER TABLE verifications ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Verifications are publicly readable" ON verifications
    FOR SELECT USING (TRUE);

CREATE POLICY "Users can create verifications" ON verifications
    FOR INSERT WITH CHECK (auth.uid()::text = user_id);

CREATE POLICY "Admins can manage verifications" ON verifications
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM user_profiles 
            WHERE user_id = auth.uid()::text 
            AND role IN ('university_admin', 'super_admin')
        )
    );
```

### 6. Attestations
```sql
CREATE TABLE attestations (
    id TEXT PRIMARY KEY,
    attestation_id TEXT UNIQUE NOT NULL,
    certificate_id TEXT REFERENCES issued_certificates(id),
    signature TEXT NOT NULL,
    public_key TEXT NOT NULL,
    qr_code_url TEXT,
    pdf_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- RLS Policies
ALTER TABLE attestations ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Attestations are publicly readable" ON attestations
    FOR SELECT USING (TRUE);
```

### 7. Audit Logs
```sql
CREATE TABLE audit_logs (
    id TEXT PRIMARY KEY,
    action TEXT NOT NULL,
    user_id TEXT REFERENCES user_profiles(user_id),
    verification_id TEXT,
    request_id TEXT, -- For legacy requests
    details JSONB DEFAULT '{}',
    ip_address TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- RLS Policies
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Admins can view audit logs" ON audit_logs
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM user_profiles 
            WHERE user_id = auth.uid()::text 
            AND role IN ('university_admin', 'super_admin')
        )
    );
```

## Indexes

```sql
-- Performance indexes
CREATE INDEX idx_user_profiles_email ON user_profiles(email);
CREATE INDEX idx_user_profiles_role ON user_profiles(role);
CREATE INDEX idx_user_profiles_institution ON user_profiles(institution_id);

CREATE INDEX idx_issued_certificates_attestation ON issued_certificates(attestation_id);
CREATE INDEX idx_issued_certificates_institution ON issued_certificates(institution_id);
CREATE INDEX idx_issued_certificates_student ON issued_certificates(student_name);

CREATE INDEX idx_legacy_requests_status ON legacy_verification_requests(status);
CREATE INDEX idx_legacy_requests_institution ON legacy_verification_requests(institution);
CREATE INDEX idx_legacy_requests_student ON legacy_verification_requests(student_email);

CREATE INDEX idx_verifications_attestation ON verifications(attestation_id);
CREATE INDEX idx_verifications_user ON verifications(user_id);
CREATE INDEX idx_verifications_created ON verifications(created_at);

CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_created ON audit_logs(created_at);
```

## Functions and Triggers

```sql
-- Update timestamp trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply to all tables with updated_at
CREATE TRIGGER update_user_profiles_updated_at BEFORE UPDATE ON user_profiles FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_institutions_updated_at BEFORE UPDATE ON institutions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_issued_certificates_updated_at BEFORE UPDATE ON issued_certificates FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_verifications_updated_at BEFORE UPDATE ON verifications FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Auto-generate IDs
CREATE OR REPLACE FUNCTION generate_uuid() RETURNS TEXT AS $$
BEGIN
    RETURN gen_random_uuid()::text;
END;
$$ LANGUAGE plpgsql;
```

## Storage Buckets

```sql
-- Certificate images bucket
INSERT INTO storage.buckets (id, name, public) VALUES ('certificates', 'certificates', true);

-- QR codes bucket  
INSERT INTO storage.buckets (id, name, public) VALUES ('qr-codes', 'qr-codes', true);

-- Attestation PDFs bucket
INSERT INTO storage.buckets (id, name, public) VALUES ('attestations', 'attestations', true);
```

## Storage Policies

```sql
-- Certificate images are publicly readable
CREATE POLICY "Certificate images are publicly readable" ON storage.objects
    FOR SELECT USING (bucket_id = 'certificates');

-- QR codes are publicly readable
CREATE POLICY "QR codes are publicly readable" ON storage.objects
    FOR SELECT USING (bucket_id = 'qr-codes');

-- Attestation PDFs are publicly readable
CREATE POLICY "Attestation PDFs are publicly readable" ON storage.objects
    FOR SELECT USING (bucket_id = 'attestations');

-- Institution admins can upload certificates
CREATE POLICY "Institution admins can upload certificates" ON storage.objects
    FOR INSERT WITH CHECK (
        bucket_id = 'certificates' AND
        EXISTS (
            SELECT 1 FROM user_profiles 
            WHERE user_id = auth.uid()::text 
            AND role = 'university_admin'
        )
    );
```
