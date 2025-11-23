from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.auth_routes import router as auth_router
from app.routes.webhook_routes import router as webhook_router
from app.whatsapp_routes import router as whatsapp_router
from app.whatsapp_service import WHATSAPP_ENABLED
from trip_plan.routes import router as trip_plan_router
from trip_plan.payment_mock_routes import router as mock_payment_router  # NEW
from trip_plan.deal_routes import router as deal_router

app = FastAPI(title="TravelOrbit Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/auth")
app.include_router(whatsapp_router)
app.include_router(deal_router)          # /deals endpoints (shown before auth)
app.include_router(webhook_router, prefix="/webhooks")
app.include_router(trip_plan_router)       # /trip-plan/...
app.include_router(mock_payment_router)    # /trips/{trip_id}/payment/mock

@app.get("/")
def root():
    whatsapp_status = "✅ ACTIVE" if WHATSAPP_ENABLED else "⚠️ NOT CONFIGURED"
    return {
        "message": "TravelOrbit Backend running",
        "whatsapp": whatsapp_status,
        "endpoints": {
            "deals": "/deals",
            "trip_plan": "/trip-plan",
            "whatsapp_status": "/whatsapp/status",
            "whatsapp_setup": "/whatsapp/setup-guide"
        }
    }
