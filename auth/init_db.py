from app.database import engine, Base
from app import models

print("Creating tables...")
Base.metadata.create_all(bind=engine)
print("Done.")
