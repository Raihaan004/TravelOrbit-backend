"""
Migration script to add short_code column to groups table
Run this once to update the database schema
"""
import sys
from sqlalchemy import text
from auth.app.database import engine

def migrate():
    """Add short_code column to groups table if it doesn't exist"""
    try:
        with engine.connect() as conn:
            # Check if column exists
            check_query = text("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='groups' AND column_name='short_code'
                )
            """)
            result = conn.execute(check_query)
            column_exists = result.scalar()
            
            if not column_exists:
                # Add the column
                add_column_query = text("""
                    ALTER TABLE groups 
                    ADD COLUMN short_code VARCHAR
                """)
                conn.execute(add_column_query)
                
                # Add unique index
                add_index_query = text("""
                    CREATE UNIQUE INDEX ix_groups_short_code ON groups (short_code)
                """)
                conn.execute(add_index_query)
                
                conn.commit()
                print("✅ Successfully added short_code column to groups table")
            else:
                print("ℹ️  short_code column already exists")
                
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    print("Running migration: Adding short_code column...")
    migrate()
    print("Migration complete!")
