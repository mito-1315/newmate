# Database Schema

## Overview

The certificate verifier uses Supabase (PostgreSQL) as the primary database with the following tables:

## Tables

### verifications

Stores all certificate verification attempts and results (enhanced for 3-layer analysis).

```sql
CREATE TABLE verifications (
    id TEXT PRIMARY KEY,
    status TEXT NOT NULL CHECK (status IN ('pending', 'verified', 'failed', 'requires_review', 'tampered', 'signature_invalid')),
    
    -- Enhanced 3-layer results
    layer_results JSONB,  -- Contains layer1_extraction, layer2_forensics, layer3_signatures, qr_integrity
    risk_score JSONB,     -- Enhanced risk scoring with forensic analysis
    database_check JSONB,
    integrity_checks JSONB,
    
    -- Decision engine outputs
    decision_rationale TEXT,
    auto_decision_confidence FLOAT,
    escalation_reasons TEXT[],
    
    -- Review workflow
    requires_manual_review BOOLEAN DEFAULT FALSE,
    review_notes TEXT,
    reviewer_id TEXT,
    
    -- Processing metadata
    processed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processing_time_total_ms FLOAT,
    image_url TEXT,
    canonical_image_hash TEXT,
    original_filename TEXT,
    user_id TEXT,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_verifications_status ON verifications(status);
CREATE INDEX idx_verifications_processed_at ON verifications(processed_at);
CREATE INDEX idx_verifications_user_id ON verifications(user_id);
CREATE INDEX idx_verifications_canonical_hash ON verifications(canonical_image_hash);
CREATE INDEX idx_verifications_requires_review ON verifications(requires_manual_review);
```

### attestations

Stores cryptographic attestations for verified certificates.

```sql
CREATE TABLE attestations (
    id TEXT PRIMARY KEY,
    verification_id TEXT NOT NULL REFERENCES verifications(id),
    signature TEXT NOT NULL,
    public_key TEXT NOT NULL,
    payload JSONB NOT NULL,
    qr_code_url TEXT,
    pdf_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    revoked_at TIMESTAMP WITH TIME ZONE,
    revocation_reason TEXT
);

-- Indexes
CREATE INDEX idx_attestations_verification_id ON attestations(verification_id);
CREATE INDEX idx_attestations_created_at ON attestations(created_at);
CREATE UNIQUE INDEX idx_attestations_verification_unique ON attestations(verification_id);
```

### issued_certificates

Database of known valid certificates from institutions (enhanced for issuance workflow).

```sql
CREATE TABLE issued_certificates (
    id TEXT PRIMARY KEY,  -- Changed to TEXT for issuance_id
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
    
    -- Issuance workflow fields
    status TEXT DEFAULT 'issued' CHECK (status IN ('issuing', 'issued', 'revoked', 'cancelled')),
    image_url TEXT,
    image_hashes JSONB,
    attestation_id TEXT,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(certificate_id, institution)
);

-- Indexes
CREATE INDEX idx_issued_certificates_student_name ON issued_certificates(student_name);
CREATE INDEX idx_issued_certificates_institution ON issued_certificates(institution);
CREATE INDEX idx_issued_certificates_course_name ON issued_certificates(course_name);
CREATE INDEX idx_issued_certificates_issue_date ON issued_certificates(issue_date);
CREATE INDEX idx_issued_certificates_status ON issued_certificates(status);
CREATE INDEX idx_issued_certificates_roll_no ON issued_certificates(roll_no);
CREATE UNIQUE INDEX idx_issued_certificates_id_institution ON issued_certificates(certificate_id, institution);
```

### institutions

Registered institutions and their verification endpoints.

```sql
CREATE TABLE institutions (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    domain TEXT NOT NULL UNIQUE,
    public_key TEXT NOT NULL,
    contact_email TEXT NOT NULL,
    verification_endpoint TEXT,
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'suspended', 'inactive')),
    registered_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_institutions_domain ON institutions(domain);
CREATE INDEX idx_institutions_status ON institutions(status);
```

### audit_logs

Complete audit trail for security and compliance.

```sql
CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    action TEXT NOT NULL,
    user_id TEXT,
    verification_id TEXT,
    details JSONB,
    ip_address INET,
    user_agent TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_audit_logs_timestamp ON audit_logs(timestamp);
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_verification_id ON audit_logs(verification_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
```

### users

User management (can integrate with Supabase Auth).

```sql
CREATE TABLE users (
    id TEXT PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    role TEXT DEFAULT 'user' CHECK (role IN ('user', 'reviewer', 'admin')),
    institution_id TEXT REFERENCES institutions(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE
);

-- Indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_institution_id ON users(institution_id);
```

## JSONB Field Structures

### extracted_fields (in verifications table)

```json
{
  "name": "John Doe",
  "institution": "University of Technology",
  "course_name": "Computer Science",
  "issue_date": "2023-06-15",
  "certificate_id": "CS2023-001234",
  "grade": "First Class Honours",
  "additional_fields": {
    "graduation_date": "2023-07-01",
    "honors": "Magna Cum Laude"
  }
}
```

### risk_score (in verifications table)

```json
{
  "overall_score": 0.85,
  "confidence": 0.92,
  "risk_level": "low",
  "factors": [
    "High extraction confidence",
    "Perfect database match"
  ],
  "component_scores": {
    "extraction_confidence": 0.95,
    "database_match": 0.90,
    "image_quality": 0.85,
    "field_consistency": 0.80
  }
}
```

### database_check (in verifications table)

```json
{
  "match_found": true,
  "confidence": 0.95,
  "database_record": {
    "id": 12345,
    "certificate_id": "CS2023-001234",
    "student_name": "John Doe",
    "institution": "University of Technology"
  },
  "discrepancies": [],
  "checked_at": "2023-08-15T10:30:00Z"
}
```

### payload (in attestations table)

```json
{
  "verification_id": "ver_abc123def456",
  "extracted_fields": {
    "name": "John Doe",
    "institution": "University of Technology",
    "course_name": "Computer Science",
    "certificate_id": "CS2023-001234"
  },
  "timestamp": "2023-08-15T10:30:00Z",
  "image_hash": "sha256:abc123def456...",
  "risk_score": 0.85
}
```

## Views

### verification_summary

Aggregated view for dashboard statistics.

```sql
CREATE VIEW verification_summary AS
SELECT 
    DATE(processed_at) as date,
    status,
    COUNT(*) as count,
    AVG((risk_score->>'overall_score')::float) as avg_risk_score
FROM verifications 
WHERE processed_at >= NOW() - INTERVAL '90 days'
GROUP BY DATE(processed_at), status;
```

### institution_performance

Institution verification statistics.

```sql
CREATE VIEW institution_performance AS
SELECT 
    i.name,
    i.domain,
    COUNT(v.id) as total_verifications,
    COUNT(CASE WHEN v.status = 'verified' THEN 1 END) as verified_count,
    COUNT(CASE WHEN v.status = 'failed' THEN 1 END) as failed_count,
    COUNT(CASE WHEN v.status = 'requires_review' THEN 1 END) as pending_count,
    AVG((v.risk_score->>'overall_score')::float) as avg_risk_score
FROM institutions i
LEFT JOIN issued_certificates ic ON i.id = ic.institution_id
LEFT JOIN verifications v ON v.extracted_fields->>'institution' = i.name
WHERE v.processed_at >= NOW() - INTERVAL '30 days'
GROUP BY i.id, i.name, i.domain;
```

## Functions

### update_verification_status

Function to update verification status with audit logging.

```sql
CREATE OR REPLACE FUNCTION update_verification_status(
    p_verification_id TEXT,
    p_status TEXT,
    p_reviewer_id TEXT DEFAULT NULL,
    p_notes TEXT DEFAULT NULL
) RETURNS BOOLEAN AS $$
BEGIN
    UPDATE verifications 
    SET 
        status = p_status,
        reviewer_id = p_reviewer_id,
        review_notes = p_notes,
        updated_at = NOW()
    WHERE id = p_verification_id;
    
    -- Log the action
    INSERT INTO audit_logs (action, user_id, verification_id, details)
    VALUES (
        'verification_status_updated',
        p_reviewer_id,
        p_verification_id,
        jsonb_build_object(
            'new_status', p_status,
            'notes', p_notes
        )
    );
    
    RETURN FOUND;
END;
$$ LANGUAGE plpgsql;
```

### get_risk_distribution

Function to calculate risk distribution for dashboard.

```sql
CREATE OR REPLACE FUNCTION get_risk_distribution(
    p_days INTEGER DEFAULT 7
) RETURNS TABLE(risk_level TEXT, count INTEGER) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        (v.risk_score->>'risk_level')::TEXT as risk_level,
        COUNT(*)::INTEGER as count
    FROM verifications v
    WHERE v.processed_at >= NOW() - (p_days || ' days')::INTERVAL
    AND v.risk_score->>'risk_level' IS NOT NULL
    GROUP BY v.risk_score->>'risk_level'
    ORDER BY 
        CASE v.risk_score->>'risk_level'
            WHEN 'low' THEN 1
            WHEN 'medium' THEN 2
            WHEN 'high' THEN 3
            WHEN 'critical' THEN 4
        END;
END;
$$ LANGUAGE plpgsql;
```

## Row Level Security (RLS)

Enable RLS for multi-tenant security:

```sql
-- Enable RLS on tables
ALTER TABLE verifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE attestations ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;

-- Users can only see their own verifications
CREATE POLICY verification_access ON verifications
    FOR ALL USING (auth.uid()::text = user_id);

-- Reviewers can see verifications requiring review
CREATE POLICY reviewer_access ON verifications
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM users 
            WHERE id = auth.uid()::text 
            AND role IN ('reviewer', 'admin')
        )
    );

-- Admins can see all records
CREATE POLICY admin_access ON verifications
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM users 
            WHERE id = auth.uid()::text 
            AND role = 'admin'
        )
    );
```

## Backup and Maintenance

### Backup Strategy
- Daily full backups with 30-day retention
- Continuous WAL archiving for point-in-time recovery
- Weekly backup validation and restore testing

### Maintenance Tasks
- Monthly vacuum and reindex operations
- Quarterly statistics updates
- Archive old audit logs (>1 year) to cold storage
- Monitor and optimize slow queries
