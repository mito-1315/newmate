#!/usr/bin/env python3
"""
Create environment file templates with placeholder values
"""
import os
from pathlib import Path

def create_backend_env():
    """Create backend .env template"""
    backend_env_content = """# Supabase Configuration
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=your-anon-key-here
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key-here

# API Configuration
API_VERSION=v1
DEBUG=True
ENVIRONMENT=development

# Security
SECRET_KEY=your-super-secret-key-here-change-in-production
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# File Upload Settings
MAX_FILE_SIZE=10485760
ALLOWED_EXTENSIONS=jpg,jpeg,png,pdf
STORAGE_BUCKET=certificates

# AI/ML Model Settings
DONUT_MODEL_PATH=models/donut
YOLO_MODEL_PATH=models/yolo
USE_GPU=False

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
"""
    
    backend_env_path = Path("backend/.env")
    
    if backend_env_path.exists():
        print(f"⚠️  Backend .env file already exists at {backend_env_path}")
        response = input("Do you want to overwrite it? (y/N): ")
        if response.lower() != 'y':
            print("   Skipping backend .env creation")
            return False
    
    # Create backend directory if it doesn't exist
    backend_env_path.parent.mkdir(exist_ok=True)
    
    with open(backend_env_path, 'w') as f:
        f.write(backend_env_content)
    
    print(f"✅ Created backend .env template at {backend_env_path}")
    return True

def create_frontend_env():
    """Create frontend .env template"""
    frontend_env_content = """# API Configuration
REACT_APP_API_BASE_URL=http://localhost:8000/api

# Supabase Configuration (for frontend features)
REACT_APP_SUPABASE_URL=https://your-project-id.supabase.co
REACT_APP_SUPABASE_ANON_KEY=your-anon-key-here

# Environment
REACT_APP_ENVIRONMENT=development

# Optional: Analytics and tracking
# REACT_APP_GOOGLE_ANALYTICS_ID=GA-XXXXXXX
# REACT_APP_SENTRY_DSN=https://your-sentry-dsn
"""
    
    frontend_env_path = Path("frontend/.env")
    
    if frontend_env_path.exists():
        print(f"⚠️  Frontend .env file already exists at {frontend_env_path}")
        response = input("Do you want to overwrite it? (y/N): ")
        if response.lower() != 'y':
            print("   Skipping frontend .env creation")
            return False
    
    # Create frontend directory if it doesn't exist
    frontend_env_path.parent.mkdir(exist_ok=True)
    
    with open(frontend_env_path, 'w') as f:
        f.write(frontend_env_content)
    
    print(f"✅ Created frontend .env template at {frontend_env_path}")
    return True

def create_docker_env():
    """Create docker-compose .env template"""
    docker_env_content = """# Docker Compose Environment Variables

# Supabase Configuration
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=your-anon-key-here
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key-here

# Database (if using local PostgreSQL)
POSTGRES_USER=certverifier
POSTGRES_PASSWORD=your-db-password-here
POSTGRES_DB=certificate_verification

# API Configuration
SECRET_KEY=your-super-secret-key-for-production
DEBUG=False
ENVIRONMENT=production

# Ports (change if you have conflicts)
BACKEND_PORT=8000
FRONTEND_PORT=3000

# Storage
STORAGE_BUCKET=certificates
MAX_FILE_SIZE=10485760

# GPU Support (set to true if you have NVIDIA GPU)
USE_GPU=false
"""
    
    docker_env_path = Path(".env")
    
    if docker_env_path.exists():
        print(f"⚠️  Docker .env file already exists at {docker_env_path}")
        response = input("Do you want to overwrite it? (y/N): ")
        if response.lower() != 'y':
            print("   Skipping docker .env creation")
            return False
    
    with open(docker_env_path, 'w') as f:
        f.write(docker_env_content)
    
    print(f"✅ Created docker .env template at {docker_env_path}")
    return True

def print_next_steps():
    """Print next steps for user"""
    print("\n" + "=" * 60)
    print("🎯 Next Steps:")
    print("=" * 60)
    print("\n1. 📝 UPDATE ENVIRONMENT FILES:")
    print("   - Replace 'your-project-id' with your actual Supabase project ID")
    print("   - Replace 'your-anon-key-here' with your Supabase anon key")
    print("   - Replace 'your-service-role-key-here' with your Supabase service role key")
    print("   - Generate a strong SECRET_KEY for production")
    
    print("\n2. 🏗️  SETUP SUPABASE:")
    print("   - Create a new project at https://supabase.com")
    print("   - Go to Project Settings > API to get your keys")
    print("   - Run the SQL commands from SETUP_GUIDE.md to create tables")
    print("   - Create a 'certificates' storage bucket")
    
    print("\n3. 🚀 START THE SYSTEM:")
    print("   - Run: python run.py")
    print("   - Or follow manual steps in SETUP_GUIDE.md")
    
    print("\n4. 🧪 TEST THE SETUP:")
    print("   - Run: python scripts/test_setup.py")
    
    print("\n📚 For detailed instructions, see SETUP_GUIDE.md")

def main():
    """Main function"""
    print("🔧 Certificate Verification System - Environment Setup")
    print("=" * 60)
    
    print("\nThis script will create environment file templates with placeholder values.")
    print("You'll need to replace the placeholder values with your actual configuration.")
    
    response = input("\nDo you want to continue? (Y/n): ")
    if response.lower() == 'n':
        print("❌ Environment setup cancelled")
        return
    
    print("\n📁 Creating environment files...")
    
    # Create backend .env
    backend_created = create_backend_env()
    
    # Create frontend .env
    frontend_created = create_frontend_env()
    
    # Create docker .env
    docker_created = create_docker_env()
    
    if backend_created or frontend_created or docker_created:
        print("\n✅ Environment template files created successfully!")
        print_next_steps()
    else:
        print("\n⚠️  No new files were created")

if __name__ == "__main__":
    main()
