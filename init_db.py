from app.database import engine, Base
from app import models as auth_models       # existing User & OtpCode
from trip_plan import models as trip_models # NEW import

print("Creating tables...")
Base.metadata.create_all(bind=engine)
print("Done.")
