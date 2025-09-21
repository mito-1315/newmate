-- SQL functions for admin statistics
-- These should be created in your Supabase database

-- Function to get certificate status statistics
CREATE OR REPLACE FUNCTION get_certificate_status_stats()
RETURNS TABLE(status TEXT, count BIGINT) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COALESCE(ic.status, 'unknown') as status,
        COUNT(*) as count
    FROM issued_certificates ic
    GROUP BY ic.status
    ORDER BY count DESC;
END;
$$ LANGUAGE plpgsql;

-- Function to get institution statistics
CREATE OR REPLACE FUNCTION get_institution_stats(limit_count INTEGER DEFAULT 10)
RETURNS TABLE(institution TEXT, count BIGINT) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        ic.institution,
        COUNT(*) as count
    FROM issued_certificates ic
    WHERE ic.institution IS NOT NULL
    GROUP BY ic.institution
    ORDER BY count DESC
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql;

-- Function to get certificates by year
CREATE OR REPLACE FUNCTION get_certificates_by_year()
RETURNS TABLE(year TEXT, count BIGINT) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        ic.year,
        COUNT(*) as count
    FROM issued_certificates ic
    WHERE ic.year IS NOT NULL
    GROUP BY ic.year
    ORDER BY ic.year DESC;
END;
$$ LANGUAGE plpgsql;