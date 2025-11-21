from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.auth_routes import router as auth_router
from app.routes.webhook_routes import router as webhook_router
from trip_plan.routes import router as trip_plan_router
from trip_plan.payment_mock_routes import router as mock_payment_router  # NEW

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
app.include_router(trip_plan_router)       # /trip-plan/...
app.include_router(mock_payment_router)    # /trips/{trip_id}/payment/mock

@app.get("/")
def root():
    return {"message": "TravelOrbit Backend running"}
