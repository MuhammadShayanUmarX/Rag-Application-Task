#!/usr/bin/env python3
"""
Initialize the HR Copilot database with sample data
"""

import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.db.database import engine, SessionLocal
from app.db import models
from app.utils.sample_data import create_sample_data

def init_database():
    """Initialize the database and create sample data"""
    print("Initializing HR Copilot database...")
    
    # Create all tables
    models.Base.metadata.create_all(bind=engine)
    print("Database tables created.")
    
    # Create sample data
    db = SessionLocal()
    try:
        asyncio.run(create_sample_data(db))
        print("Sample data loaded successfully!")
    except Exception as e:
        print(f"Error loading sample data: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    init_database()
    print("Database initialization complete!")
    print("You can now run the application with: uvicorn app.main:app --reload")

