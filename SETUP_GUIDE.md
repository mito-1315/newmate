# 🚀 Certificate Verification System - Setup Guide

## Prerequisites

Before starting, ensure you have the following installed:

- **Python 3.11+** (for backend)
- **Node.js 18+** (for frontend) 
- **Docker & Docker Compose** (for containerized deployment)
- **Git** (for cloning/version control)

## 📋 Step-by-Step Setup

### Step 1: Install Dependencies

#### Backend Dependencies
```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Install additional system dependencies for OCR (Windows)
# Download and install Tesseract: https://github.com/UB-Mannheim/tesseract/wiki
# Add Tesseract to PATH

# For PaddleOCR GPU support (optional)
# pip install paddlepaddle-gpu
```

#### Frontend Dependencies
```bash
# Navigate to frontend directory
cd frontend

# Install Node.js dependencies
npm install

# Install additional dependencies for QR scanning
npm install react-qr-reader qr-scanner
```

### Step 2: Supabase Setup

1. **Create Supabase Project**
   - Go to [https://supabase.com](https://supabase.com)
   - Click "New Project"
   - Choose organization and enter project details
   - Wait for project to be created (~2 minutes)

2. **Get Supabase Credentials**
   - Go to Project Settings > API
   - Copy the following:
     - `Project URL`
     - `anon public key`
     - `service_role key`

3. **Create Database Tables**
   - Go to SQL Editor in Supabase Dashboard
   - Run the following SQL to create all tables:

```sql
-- Create issued_certificates table (updated to match your schema)
CREATE TABLE IF NOT EXISTS issued_certificates (
    id TEXT PRIMARY KEY,
    certificate_id TEXT NOT NULL,
    student_name TEXT NOT NULL,
    course_name TEXT NOT NULL,
    institution TEXT NOT NULL,
    issue_date DATE NOT NULL,
    status TEXT DEFAULT 'issued',
    image_url TEXT,
    image_hashes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    roll_number TEXT,
    year TEXT NOT NULL,
    grade TEXT,
    qr_code_data TEXT,
    qr_code_hash TEXT,
    digital_signature TEXT,
    verification_url TEXT,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    issued_by TEXT DEFAULT 'system',
    CONSTRAINT issued_certificates_certificate_id_institution_key UNIQUE (certificate_id, institution)
);

-- Add missing columns that the backend expects
ALTER TABLE issued_certificates 
ADD COLUMN IF NOT EXISTS roll_no TEXT,
ADD COLUMN IF NOT EXISTS department TEXT,
ADD COLUMN IF NOT EXISTS cgpa TEXT,
ADD COLUMN IF NOT EXISTS institution_name TEXT,
ADD COLUMN IF NOT EXISTS additional_data JSONB DEFAULT '{}',
ADD COLUMN IF NOT EXISTS source TEXT DEFAULT 'digital' CHECK (source IN ('digital', 'legacy_verified')),
ADD COLUMN IF NOT EXISTS attestation_id TEXT,
ADD COLUMN IF NOT EXISTS image_hashes JSONB;

-- Create institutions table
CREATE TABLE IF NOT EXISTS institutions (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    domain TEXT UNIQUE,
    contact_email TEXT,
    public_key TEXT NOT NULL,
    verification_endpoints TEXT[],
    certificate_templates TEXT[],
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create verifications table
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

-- Create attestations table
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

-- Create audit_logs table
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    action TEXT NOT NULL,
    user_id TEXT,
    resource_type TEXT,
    resource_id TEXT,
    details JSONB,
    ip_address INET,
    user_agent TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_issued_certificates_student_name ON issued_certificates(student_name);
CREATE INDEX IF NOT EXISTS idx_issued_certificates_institution ON issued_certificates(institution);
CREATE INDEX IF NOT EXISTS idx_issued_certificates_course_name ON issued_certificates(course_name);
CREATE INDEX IF NOT EXISTS idx_issued_certificates_issue_date ON issued_certificates(issue_date);
CREATE INDEX IF NOT EXISTS idx_issued_certificates_status ON issued_certificates(status);
CREATE INDEX IF NOT EXISTS idx_verifications_status ON verifications(verification_id);
CREATE INDEX IF NOT EXISTS idx_verifications_processed_at ON verifications(created_at);
CREATE INDEX IF NOT EXISTS idx_attestations_verification_id ON attestations(attestation_id);

-- Enable Row Level Security (RLS)
ALTER TABLE issued_certificates ENABLE ROW LEVEL SECURITY;
ALTER TABLE verifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE attestations ENABLE ROW LEVEL SECURITY;

-- Create basic RLS policies (can be customized later)
CREATE POLICY IF NOT EXISTS "Enable read access for all users" ON issued_certificates FOR SELECT USING (true);
CREATE POLICY IF NOT EXISTS "Enable read access for all users" ON verifications FOR SELECT USING (true);
CREATE POLICY IF NOT EXISTS "Enable read access for all users" ON attestations FOR SELECT USING (true);
```

4. **Set up Storage Bucket**
   - Go to Storage in Supabase Dashboard
   - Create a new bucket called `certificates`
   - Set bucket to `Public` for certificate images
   - Create folder structure:
     ```
     certificates/
     ├── issued/          # For issued certificate images
     ├── uploaded/        # For verification uploads
     └── attestations/    # For attestation PDFs
     ```

### Step 3: Environment Configuration

1. **Backend Environment**
   Create `backend/.env` file:
```env
# Supabase Configuration
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=your-anon-key-here
SUPABASE_SERVICE_KEY=your-service-role-key-here

# API Configuration
API_VERSION=v1
DEBUG=True
ENVIRONMENT=development

# Security
SECRET_KEY=your-super-secret-key-here-change-in-production
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# File Upload Settings
MAX_FILE_SIZE=10485760  # 10MB
ALLOWED_EXTENSIONS=jpg,jpeg,png,pdf

# AI/ML Model Settings
DONUT_MODEL_PATH=models/donut
YOLO_MODEL_PATH=models/yolo
USE_GPU=False  # Set to True if you have CUDA

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
```

2. **Frontend Environment**
   Create `frontend/.env` file:
```env
REACT_APP_API_BASE_URL=http://localhost:8000/api
REACT_APP_SUPABASE_URL=https://your-project-id.supabase.co
REACT_APP_SUPABASE_ANON_KEY=your-anon-key-here
REACT_APP_ENVIRONMENT=development
```

### Step 4: Update Configuration Files

1. **Update backend/app/config.py**
```python
import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Supabase
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_ANON_KEY: str = os.getenv("SUPABASE_ANON_KEY", "")
    SUPABASE_SERVICE_KEY: str = os.getenv("SUPABASE_SERVICE_KEY", "")
    
    # API
    API_VERSION: str = "v1"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key")
    ALLOWED_HOSTS: list = os.getenv("ALLOWED_HOSTS", "localhost").split(",")
    
    # File uploads
    MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", "10485760"))
    ALLOWED_EXTENSIONS: set = set(os.getenv("ALLOWED_EXTENSIONS", "jpg,jpeg,png,pdf").split(","))
    
    # Models
    USE_GPU: bool = os.getenv("USE_GPU", "False").lower() == "true"
    
    class Config:
        env_file = ".env"

settings = Settings()
```

### Step 5: Initialize Default Institution

Run this script to create a default institution for testing:

```python
# scripts/setup_default_institution.py
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.services.supabase_client import SupabaseClient
from backend.app.services.qr_integrity import QRIntegrityService

async def setup_default_institution():
    supabase_client = SupabaseClient()
    qr_service = QRIntegrityService()
    
    # Generate default keys
    from backend.app.utils.helpers import generate_key_pair
    private_key, public_key = generate_key_pair()
    
    # Create default institution
    institution_data = {
        "id": "default",
        "name": "Default University",
        "domain": "default.edu",
        "contact_email": "admin@default.edu",
        "public_key": public_key,
        "verification_endpoints": ["http://localhost:8000"],
        "certificate_templates": ["default"],
        "is_active": True
    }
    
    try:
        result = await supabase_client.supabase.table("institutions").insert(institution_data).execute()
        print("✅ Default institution created successfully")
        
        # Add keys to QR service
        await qr_service.add_institution_key("default", private_key, public_key, "default_key_001")
        print("✅ Default keys added to QR service")
        
    except Exception as e:
        print(f"❌ Error creating default institution: {e}")

if __name__ == "__main__":
    asyncio.run(setup_default_institution())
```

### Step 6: Run the Application

#### Option A: Development Mode (Recommended for testing)

1. **Start Backend**
```bash
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

2. **Start Frontend** (in new terminal)
```bash
cd frontend
npm start
```

#### Option B: Docker Compose (Production-like)

1. **Update docker-compose.yml environment variables**
```yaml
# Add your actual Supabase credentials
environment:
  - SUPABASE_URL=https://your-project-id.supabase.co
  - SUPABASE_ANON_KEY=your-anon-key
  - SUPABASE_SERVICE_KEY=your-service-key
```

2. **Run with Docker**
```bash
docker-compose up -d
```

### Step 7: Test the Setup

1. **Check Backend Health**
```bash
curl http://localhost:8000/
# Should return: {"message": "Certificate Verifier API is running"}
```

2. **Access Frontend**
   - Open browser to `http://localhost:3000`
   - You should see the Certificate Verifier dashboard

3. **Test Certificate Issuance**
   - Go to "Issue" tab
   - Fill in sample certificate data:
     ```
     Certificate ID: TEST-001
     Student Name: John Doe
     Course: Computer Science
     Institution: Default University
     ```
   - Click "Issue Certificate"

4. **Test Verification**
   - Copy the verification URL from issuance result
   - Open in new tab to test public verification

### Step 8: Optional Enhancements

#### GPU Support (for better performance)
```bash
# Install CUDA toolkit
# Install GPU versions of dependencies
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
pip install paddlepaddle-gpu
```

#### Production Deployment
```bash
# Use production environment variables
# Set up reverse proxy (nginx)
# Configure SSL certificates
# Set up monitoring (Prometheus + Grafana)
```

## 🔧 Troubleshooting

### Common Issues:

1. **Supabase Connection Error**
   - Check your Supabase URL and keys
   - Ensure tables are created correctly
   - Verify RLS policies

2. **OCR Dependencies**
   - Install Tesseract: `https://github.com/UB-Mannheim/tesseract/wiki`
   - Add to PATH
   - Install language packs if needed

3. **Port Conflicts**
   - Backend: Change port in uvicorn command
   - Frontend: Set PORT environment variable

4. **File Upload Issues**
   - Check Supabase storage bucket permissions
   - Verify file size limits
   - Ensure CORS is configured

### Need Help?
- Check logs in `backend/logs/app.log`
- Use browser developer tools for frontend issues
- Verify environment variables are loaded correctly

## 🎉 You're Ready!

Once setup is complete, you can:
- ✅ Issue certificates with QR codes
- ✅ Verify certificates by scanning QR
- ✅ View analytics dashboard
- ✅ Manage institutions and users
- ✅ Review suspicious certificates

Your certificate verification system is now running! 🚀
