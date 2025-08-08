#!/usr/bin/env python3
"""
Create the database with correct schema
"""
from app import app, db

def create_database():
    print("Creating database with correct schema...")
    with app.app_context():
        # Create all tables
        db.create_all()
        print("✅ Database created successfully!")
        
        # Print table info
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        print(f"📋 Created tables: {tables}")
        
        # Check User table columns
        if 'user' in tables:
            columns = [col['name'] for col in inspector.get_columns('user')]
            print(f"👤 User table columns: {columns}")

if __name__ == '__main__':
    create_database()