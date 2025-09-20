#!/usr/bin/env python3
"""
Startup script for HR Copilot
"""

import os
import sys
import subprocess
import time

def check_requirements():
    """Check if all requirements are installed"""
    try:
        import fastapi
        import uvicorn
        import sqlalchemy
        import openai
        import chromadb
        print("✓ All required packages are installed")
        return True
    except ImportError as e:
        print(f"✗ Missing required package: {e}")
        print("Please run: pip install -r requirements.txt")
        return False

def check_env():
    """Check if environment variables are set"""
    if not os.path.exists('.env'):
        print("✗ .env file not found")
        print("Please copy env.example to .env and configure it")
        return False
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    if not os.getenv('OPENAI_API_KEY'):
        print("✗ OPENAI_API_KEY not set in .env file")
        print("Please add your OpenAI API key to the .env file")
        return False
    
    print("✓ Environment variables configured")
    return True

def init_database():
    """Initialize database if needed"""
    if not os.path.exists('hr_copilot.db'):
        print("Initializing database...")
        try:
            subprocess.run([sys.executable, 'init_db.py'], check=True)
            print("✓ Database initialized")
        except subprocess.CalledProcessError:
            print("✗ Failed to initialize database")
            return False
    else:
        print("✓ Database already exists")
    
    return True

def start_server():
    """Start the FastAPI server"""
    print("Starting HR Copilot server...")
    print("Server will be available at: http://localhost:8000")
    print("Press Ctrl+C to stop the server")
    print("-" * 50)
    
    try:
        subprocess.run([
            sys.executable, '-m', 'uvicorn', 
            'app.main:app', 
            '--reload', 
            '--host', '0.0.0.0', 
            '--port', '8000'
        ])
    except KeyboardInterrupt:
        print("\nServer stopped")

def main():
    """Main startup function"""
    print("HR Policies & Benefits Copilot")
    print("=" * 40)
    
    # Check requirements
    if not check_requirements():
        sys.exit(1)
    
    # Check environment
    if not check_env():
        sys.exit(1)
    
    # Initialize database
    if not init_database():
        sys.exit(1)
    
    # Start server
    start_server()

if __name__ == "__main__":
    main()

