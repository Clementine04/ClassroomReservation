"""
Script to check database connectivity on Render
Run this with: python check_db.py
"""
import os
import sys
import time
from sqlalchemy import create_engine, inspect, text

def check_database():
    """Check database connectivity and report status"""
    print("=" * 50)
    print("DATABASE CONNECTION TEST")
    print("=" * 50)
    
    # List all environment variables related to database
    print("\nEnvironment variables:")
    for key, value in os.environ.items():
        if any(keyword in key.upper() for keyword in ['DATABASE', 'DB', 'POSTGRES', 'RENDER']):
            masked_value = value[:5] + '...' if len(value) > 10 else value
            print(f"  {key}: {masked_value}")
    
    # Get database URL
    db_url = os.environ.get('DATABASE_URL', '')
    if not db_url:
        print("\nERROR: DATABASE_URL not set!")
        return False
    
    print(f"\nDatabase URL: {db_url[:15]}...")
    
    # Fix postgres:// URLs
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
        print(f"Fixed to: {db_url[:15]}...")
    
    try:
        print("\nAttempting to connect to database...")
        engine = create_engine(db_url)
        
        print("Testing connection...")
        conn = engine.connect()
        
        print("Connection successful!")
        
        print("\nRetrieving database metadata...")
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"Available tables: {tables}")
        
        print("\nRunning test query...")
        result = conn.execute(text("SELECT 1"))
        print(f"Query result: {result.fetchone()}")
        
        print("\nDatabase connection test PASSED!")
        return True
    except Exception as e:
        print(f"\nERROR connecting to database: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = check_database()
    sys.exit(0 if success else 1) 