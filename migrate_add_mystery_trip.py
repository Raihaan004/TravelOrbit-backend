"""
Migration script to add is_mystery_trip and mystery_preferences columns to trips table
Run this once to update the database schema
"""
import sys
from sqlalchemy import text
from auth.app.database import engine

def migrate():
    """Add is_mystery_trip and mystery_preferences columns to trips table if they don't exist"""
    try:
        with engine.connect() as conn:
            # Check if is_mystery_trip column exists
            check_query = text("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='trips' AND column_name='is_mystery_trip'
                )
            """)
            result = conn.execute(check_query)
            column_exists = result.scalar()
            
            if not column_exists:
                # Add the column
                add_column_query = text("""
                    ALTER TABLE trips 
                    ADD COLUMN is_mystery_trip INTEGER DEFAULT 0
                """)
                conn.execute(add_column_query)
                conn.commit()
                print("✅ Successfully added is_mystery_trip column to trips table")
            else:
                print("ℹ️  is_mystery_trip column already exists")

            # Check if mystery_preferences column exists
            check_query_pref = text("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='trips' AND column_name='mystery_preferences'
                )
            """)
            result_pref = conn.execute(check_query_pref)
            column_exists_pref = result_pref.scalar()
            
            if not column_exists_pref:
                # Add the column
                add_column_query_pref = text("""
                    ALTER TABLE trips 
                    ADD COLUMN mystery_preferences JSONB DEFAULT NULL
                """)
                conn.execute(add_column_query_pref)
                conn.commit()
                print("✅ Successfully added mystery_preferences column to trips table")
            else:
                print("ℹ️  mystery_preferences column already exists")
                
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    print("Running migration: Adding mystery trip columns...")
    migrate()
    print("Migration complete!")
