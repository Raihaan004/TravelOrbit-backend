from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import routers from proper locations
from auth.app.routes.auth_routes import router as auth_router
from auth.app.routes.webhook_routes import router as webhook_router
from trip_plan.routes import router as trip_plan_router

app = FastAPI(title="TravelOrbit Backend")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth_router, prefix="/auth")
app.include_router(webhook_router, prefix="/webhooks")
app.include_router(trip_plan_router, prefix="/trip-plan")

@app.get("/")
def home():
    return {"message": "TravelOrbit Backend Running"}
