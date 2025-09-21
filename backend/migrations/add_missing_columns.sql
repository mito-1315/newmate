-- Migration: Add missing columns to issued_certificates table
-- Run this in your Supabase SQL editor

-- Add missing columns to issued_certificates table
ALTER TABLE issued_certificates 
ADD COLUMN IF NOT EXISTS additional_data JSONB DEFAULT '{}',
ADD COLUMN IF NOT EXISTS department TEXT,
ADD COLUMN IF NOT EXISTS cgpa TEXT,
ADD COLUMN IF NOT EXISTS institution_name TEXT,
ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'issued',
ADD COLUMN IF NOT EXISTS source TEXT DEFAULT 'digital';

-- Update existing records to have default values
UPDATE issued_certificates 
SET 
    additional_data = '{}' WHERE additional_data IS NULL,
    status = 'issued' WHERE status IS NULL,
    source = 'digital' WHERE source IS NULL;

-- Add indexes for better performance
CREATE INDEX IF NOT EXISTS idx_issued_certificates_status ON issued_certificates(status);
CREATE INDEX IF NOT EXISTS idx_issued_certificates_source ON issued_certificates(source);
CREATE INDEX IF NOT EXISTS idx_issued_certificates_institution_name ON issued_certificates(institution_name);

-- Verify the table structure
SELECT column_name, data_type, is_nullable, column_default 
FROM information_schema.columns 
WHERE table_name = 'issued_certificates' 
ORDER BY ordinal_position;
