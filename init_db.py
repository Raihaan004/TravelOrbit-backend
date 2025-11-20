from auth.app.database import engine, Base
from auth.app import models as auth_models
from trip_plan import models as trip_models

print("Creating tables...")
Base.metadata.create_all(bind=engine)
print("Done.")
