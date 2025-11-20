from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from auth.app.routes.auth_routes import router as auth_router
from auth.app.routes.webhook_routes import router as webhook_router
from auth.app.routes.calendar_routes import router as calendar_router
from trip_plan.routes import router as trip_plan_router

app = FastAPI(title="TravelOrbit Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/auth")
app.include_router(webhook_router, prefix="/webhooks")
app.include_router(trip_plan_router)   # routes already start with /trip-plan

@app.get("/")
def root():
    return {"message": "TravelOrbit Backend running"}
