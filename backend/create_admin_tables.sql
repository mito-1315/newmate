-- Create tables for admin dashboard functionality

-- Verification logs table to track all verification attempts
CREATE TABLE IF NOT EXISTS verification_logs (
    id SERIAL PRIMARY KEY,
    certificate_id VARCHAR(255),
    verification_id VARCHAR(255),
    status VARCHAR(50) NOT NULL, -- 'verified', 'failed', 'suspicious'
    ip_address INET,
    user_agent TEXT,
    verification_method VARCHAR(50), -- 'qr_scan', 'manual', 'api'
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Blacklisted certificates table
CREATE TABLE IF NOT EXISTS blacklisted_certificates (
    id SERIAL PRIMARY KEY,
    certificate_id VARCHAR(255) UNIQUE NOT NULL,
    reason TEXT NOT NULL,
    blacklisted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    blacklisted_by VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Blacklisted IP addresses table
CREATE TABLE IF NOT EXISTS blacklisted_ips (
    id SERIAL PRIMARY KEY,
    ip_address INET UNIQUE NOT NULL,
    reason TEXT NOT NULL,
    blacklisted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    blacklisted_by VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_verification_logs_certificate_id ON verification_logs(certificate_id);
CREATE INDEX IF NOT EXISTS idx_verification_logs_status ON verification_logs(status);
CREATE INDEX IF NOT EXISTS idx_verification_logs_created_at ON verification_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_verification_logs_ip_address ON verification_logs(ip_address);

CREATE INDEX IF NOT EXISTS idx_blacklisted_certificates_certificate_id ON blacklisted_certificates(certificate_id);
CREATE INDEX IF NOT EXISTS idx_blacklisted_ips_ip_address ON blacklisted_ips(ip_address);

-- Insert some sample data for testing
INSERT INTO verification_logs (certificate_id, verification_id, status, ip_address, user_agent, verification_method) VALUES
('CERT123456', 'VER123456', 'verified', '192.168.1.100', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36', 'qr_scan'),
('CERT123457', 'VER123457', 'failed', '192.168.1.101', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36', 'qr_scan'),
('CERT123458', 'VER123458', 'verified', '192.168.1.102', 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36', 'manual'),
('CERT123459', 'VER123459', 'suspicious', '192.168.1.103', 'curl/7.68.0', 'api'),
('CERT123460', 'VER123460', 'verified', '192.168.1.104', 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15', 'qr_scan')
ON CONFLICT DO NOTHING;

-- Insert some sample blacklisted data
INSERT INTO blacklisted_certificates (certificate_id, reason, blacklisted_by) VALUES
('CERT999999', 'Forged certificate detected', 'admin'),
('CERT888888', 'Suspicious activity', 'admin')
ON CONFLICT (certificate_id) DO NOTHING;

INSERT INTO blacklisted_ips (ip_address, reason, blacklisted_by) VALUES
('192.168.1.200', 'Multiple failed verification attempts', 'admin'),
('10.0.0.100', 'Suspicious verification patterns', 'admin')
ON CONFLICT (ip_address) DO NOTHING;
