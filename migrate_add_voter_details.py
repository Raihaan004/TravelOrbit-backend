from sqlalchemy import create_engine, text
from app.config import settings

def migrate():
    engine = create_engine(settings.DATABASE_URL)
    with engine.connect() as conn:
        # Add voter_name column
        try:
            conn.execute(text("ALTER TABLE group_votes ADD COLUMN voter_name VARCHAR"))
            print("Added voter_name column to group_votes")
        except Exception as e:
            print(f"voter_name column might already exist: {e}")

        # Add voter_phone column
        try:
            conn.execute(text("ALTER TABLE group_votes ADD COLUMN voter_phone VARCHAR"))
            print("Added voter_phone column to group_votes")
        except Exception as e:
            print(f"voter_phone column might already exist: {e}")
            
        conn.commit()

if __name__ == "__main__":
    migrate()
