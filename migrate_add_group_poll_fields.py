"""
Migration script to add poll fields to groups table
Run this once to update the database schema
"""
import sys
from sqlalchemy import text
from auth.app.database import engine

def migrate():
    """Add from_city, expected_count, destination_options columns to groups table"""
    try:
        with engine.connect() as conn:
            # Check if columns exist
            check_query = text("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name='groups'
            """)
            result = conn.execute(check_query)
            existing_columns = [row[0] for row in result]
            
            if 'from_city' not in existing_columns:
                conn.execute(text("ALTER TABLE groups ADD COLUMN from_city VARCHAR"))
                print("✅ Added from_city")
                
            if 'expected_count' not in existing_columns:
                conn.execute(text("ALTER TABLE groups ADD COLUMN expected_count INTEGER"))
                print("✅ Added expected_count")
                
            if 'destination_options' not in existing_columns:
                conn.execute(text("ALTER TABLE groups ADD COLUMN destination_options JSONB"))
                print("✅ Added destination_options")
                
            conn.commit()
            print("Migration complete!")
                
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    print("Running migration: Adding poll fields to groups...")
    migrate()
