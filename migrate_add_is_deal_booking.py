"""
Migration script to add is_deal_booking column to trips table
Run this once to update the database schema
"""
import sys
from sqlalchemy import text
from auth.app.database import engine

def migrate():
    """Add is_deal_booking column to trips table if it doesn't exist"""
    try:
        with engine.connect() as conn:
            # Check if column exists
            check_query = text("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='trips' AND column_name='is_deal_booking'
                )
            """)
            result = conn.execute(check_query)
            column_exists = result.scalar()
            
            if not column_exists:
                # Add the column
                add_column_query = text("""
                    ALTER TABLE trips 
                    ADD COLUMN is_deal_booking INTEGER DEFAULT 0
                """)
                conn.execute(add_column_query)
                conn.commit()
                print("✅ Successfully added is_deal_booking column to trips table")
            else:
                print("ℹ️  is_deal_booking column already exists")
                
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    print("Running migration: Adding is_deal_booking column...")
    migrate()
    print("Migration complete!")
