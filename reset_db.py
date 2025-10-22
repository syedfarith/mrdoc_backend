#!/usr/bin/env python3
"""
Database Reset Script
This script deletes and recreates the database with the correct schema.
Updated to include email field for doctors.
"""

import os
from database import Base, engine

def reset_database():
    # Delete the database file if it exists
    db_file = "healthcare.db"
    if os.path.exists(db_file):
        try:
            os.remove(db_file)
            print(f"✓ Deleted existing database: {db_file}")
        except Exception as e:
            print(f"❌ Could not delete database: {e}")
            return False
    
    # Create all tables
    try:
        Base.metadata.create_all(bind=engine)
        print("✓ Database tables created successfully with email support!")
        
        # Verify tables were created
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"✓ Created tables: {', '.join(tables)}")
        
        # Check if email column exists in doctors table
        doctor_columns = [col['name'] for col in inspector.get_columns('doctors')]
        if 'email' in doctor_columns:
            print("✓ Email column added to doctors table successfully!")
        else:
            print("❌ Warning: Email column not found in doctors table")
        
        return True
    except Exception as e:
        print(f"❌ Error creating database: {e}")
        return False

if __name__ == "__main__":
    print("Resetting Healthcare Booking System Database...")
    print("Adding email functionality for doctors...")
    if reset_database():
        print("Database reset completed successfully!")
        print("New features:")
        print("- Doctors now have email addresses")
        print("- Welcome emails sent to new doctors")
        print("- Appointment notifications sent to doctors")
    else:
        print("Database reset failed!")