"""
Migration script to add include_guide_photographer and guide_photographer_cost columns to trips table
Run this once to update the database schema
"""
import sys
from sqlalchemy import text
from auth.app.database import engine

def migrate():
    """Add guide/photographer columns to trips table if they don't exist"""
    try:
        with engine.connect() as conn:
            # Check if include_guide_photographer exists
            check_query = text("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='trips' AND column_name='include_guide_photographer'
                )
            """)
            result = conn.execute(check_query)
            column_exists = result.scalar()
            
            if not column_exists:
                # Add the columns
                add_column_query = text("""
                    ALTER TABLE trips 
                    ADD COLUMN include_guide_photographer INTEGER DEFAULT 0,
                    ADD COLUMN guide_photographer_cost NUMERIC DEFAULT 0.0
                """)
                conn.execute(add_column_query)
                conn.commit()
                print("✅ Successfully added guide/photographer columns to trips table")
            else:
                print("ℹ️  Columns already exist")
                
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    print("Running migration: Adding guide/photographer columns...")
    migrate()
    print("Migration complete!")
