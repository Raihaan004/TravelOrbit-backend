"""
Migration script to add passenger-related columns to trips table
Adds: contact_phone (VARCHAR), passengers (JSONB)
Run this once to update the database schema
"""
import sys
from sqlalchemy import text, inspect
from auth.app.database import engine

def migrate():
    """Add passenger tracking columns to trips table if they don't exist"""
    try:
        with engine.connect() as conn:
            # Get existing columns
            inspector = inspect(engine)
            columns = [col['name'] for col in inspector.get_columns('trips')]
            
            # Add contact_phone if missing
            if 'contact_phone' not in columns:
                add_phone_query = text("""
                    ALTER TABLE trips 
                    ADD COLUMN contact_phone VARCHAR
                """)
                conn.execute(add_phone_query)
                conn.commit()
                print("✅ Added contact_phone column to trips table")
            else:
                print("ℹ️  contact_phone column already exists")
            
            # Add passengers (JSONB) if missing
            if 'passengers' not in columns:
                try:
                    # Try PostgreSQL JSONB first
                    add_passengers_query = text("""
                        ALTER TABLE trips 
                        ADD COLUMN passengers JSONB
                    """)
                    conn.execute(add_passengers_query)
                    conn.commit()
                    print("✅ Added passengers (JSONB) column to trips table")
                except Exception as pg_error:
                    print(f"ℹ️  JSONB not available, trying JSON: {str(pg_error)}")
                    try:
                        # Fallback to JSON for MySQL
                        add_passengers_query = text("""
                            ALTER TABLE trips 
                            ADD COLUMN passengers JSON
                        """)
                        conn.execute(add_passengers_query)
                        conn.commit()
                        print("✅ Added passengers (JSON) column to trips table")
                    except Exception as json_error:
                        # Ultimate fallback to TEXT for SQLite
                        add_passengers_query = text("""
                            ALTER TABLE trips 
                            ADD COLUMN passengers TEXT
                        """)
                        conn.execute(add_passengers_query)
                        conn.commit()
                        print("✅ Added passengers (TEXT) column to trips table")
            else:
                print("ℹ️  passengers column already exists")
                
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    print("Running migration: Adding passenger detail columns...")
    migrate()
    print("✅ Migration complete!")
