#!/usr/bin/env python3
"""
Simple run script to start the certificate verification system
"""
import subprocess
import sys
import os
import time
import webbrowser
from pathlib import Path

def run_command(command, cwd=None, background=False):
    """Run a command in subprocess"""
    try:
        if background:
            return subprocess.Popen(command, shell=True, cwd=cwd)
        else:
            return subprocess.run(command, shell=True, cwd=cwd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed: {command}")
        print(f"   Error: {e}")
        return None

def check_dependencies():
    """Check if required dependencies are available"""
    print("🔍 Checking dependencies...")
    
    # Check Python
    try:
        import sys
        python_version = sys.version_info
        if python_version.major >= 3 and python_version.minor >= 11:
            print(f"✅ Python {python_version.major}.{python_version.minor} found")
        else:
            print(f"❌ Python 3.11+ required, found {python_version.major}.{python_version.minor}")
            return False
    except:
        print("❌ Python not found")
        return False
    
    # Check Node.js
    try:
        result = subprocess.run(["node", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"✅ Node.js {version} found")
        else:
            print("❌ Node.js not found")
            return False
    except:
        print("❌ Node.js not found")
        return False
    
    # Check if virtual environment exists
    venv_path = Path("backend/venv")
    if venv_path.exists():
        print("✅ Virtual environment found")
    else:
        print("⚠️  Virtual environment not found - will need to create one")
    
    return True

def setup_backend():
    """Setup backend environment"""
    print("\n🔧 Setting up backend...")
    
    backend_dir = Path("backend")
    if not backend_dir.exists():
        print("❌ Backend directory not found")
        return False
    
    # Create virtual environment if it doesn't exist
    venv_path = backend_dir / "venv"
    if not venv_path.exists():
        print("📦 Creating virtual environment...")
        result = run_command("python -m venv venv", cwd="backend")
        if not result:
            return False
    
    # Install dependencies
    if sys.platform.startswith("win"):
        pip_cmd = "venv\\Scripts\\pip"
        python_cmd = "venv\\Scripts\\python"
    else:
        pip_cmd = "venv/bin/pip"
        python_cmd = "venv/bin/python"
    
    print("📦 Installing Python dependencies...")
    result = run_command(f"{pip_cmd} install -r requirements.txt", cwd="backend")
    if not result:
        print("⚠️  Failed to install some dependencies - continuing anyway")
    
    return True

def setup_frontend():
    """Setup frontend environment"""
    print("\n🔧 Setting up frontend...")
    
    frontend_dir = Path("frontend")
    if not frontend_dir.exists():
        print("❌ Frontend directory not found")
        return False
    
    # Install npm dependencies
    print("📦 Installing Node.js dependencies...")
    result = run_command("npm install", cwd="frontend")
    if not result:
        return False
    
    return True

def check_env_files():
    """Check if environment files exist"""
    print("\n🔍 Checking environment files...")
    
    backend_env = Path("backend/.env")
    frontend_env = Path("frontend/.env")
    
    if not backend_env.exists():
        print("⚠️  Backend .env file not found")
        print("   Please create backend/.env with your Supabase credentials")
        print("   See SETUP_GUIDE.md for details")
        return False
    else:
        print("✅ Backend .env file found")
    
    if not frontend_env.exists():
        print("⚠️  Frontend .env file not found")
        print("   Please create frontend/.env with your configuration")
        print("   See SETUP_GUIDE.md for details")
        return False
    else:
        print("✅ Frontend .env file found")
    
    return True

def start_services():
    """Start backend and frontend services"""
    print("\n🚀 Starting services...")
    
    # Start backend
    print("🔗 Starting backend server...")
    if sys.platform.startswith("win"):
        backend_cmd = "venv\\Scripts\\python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
    else:
        backend_cmd = "venv/bin/python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
    
    backend_process = run_command(backend_cmd, cwd="backend", background=True)
    
    if not backend_process:
        print("❌ Failed to start backend")
        return None, None
    
    # Wait a bit for backend to start
    print("⏳ Waiting for backend to start...")
    time.sleep(3)
    
    # Start frontend
    print("🎨 Starting frontend server...")
    frontend_process = run_command("npm start", cwd="frontend", background=True)
    
    if not frontend_process:
        print("❌ Failed to start frontend")
        backend_process.terminate()
        return None, None
    
    return backend_process, frontend_process

def main():
    """Main function"""
    print("🎯 Certificate Verification System Launcher")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        print("\n❌ Dependency check failed. Please install required dependencies.")
        return
    
    # Check environment files
    if not check_env_files():
        print("\n❌ Environment file check failed. Please create .env files.")
        print("   Run: python scripts/create_env_template.py")
        return
    
    # Setup backend
    if not setup_backend():
        print("\n❌ Backend setup failed.")
        return
    
    # Setup frontend
    if not setup_frontend():
        print("\n❌ Frontend setup failed.")
        return
    
    # Start services
    backend_process, frontend_process = start_services()
    
    if backend_process and frontend_process:
        print("\n🎉 Services started successfully!")
        print("\n📊 Service URLs:")
        print("   Backend API: http://localhost:8000")
        print("   Frontend UI: http://localhost:3000")
        print("   API Docs: http://localhost:8000/docs")
        
        print("\n🧪 Testing setup...")
        time.sleep(5)  # Wait for services to fully start
        
        # Open browser
        try:
            webbrowser.open("http://localhost:3000")
            print("🌐 Opened browser to frontend")
        except:
            print("⚠️  Could not open browser automatically")
        
        print("\n⌨️  Press Ctrl+C to stop all services")
        
        try:
            # Wait for user to stop
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Stopping services...")
            backend_process.terminate()
            frontend_process.terminate()
            print("✅ Services stopped")
    else:
        print("\n❌ Failed to start services")

if __name__ == "__main__":
    main()
