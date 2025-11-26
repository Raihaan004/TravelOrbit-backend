from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import os

from app.routes.auth_routes import router as auth_router
from app.routes.webhook_routes import router as webhook_router
from app.whatsapp_routes import router as whatsapp_router
from app.whatsapp_service import WHATSAPP_ENABLED
from trip_plan.routes import router as trip_plan_router
from trip_plan.payment_routes import router as payment_router  # NEW
from trip_plan.deal_routes import router as deal_router
from trip_plan.group_routes import router as group_router # NEW

app = FastAPI(title="TravelOrbit Backend")

app.mount("/static", StaticFiles(directory="trip-frontend"), name="static")

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
app.include_router(payment_router)    # /trips/{trip_id}/payment/...
app.include_router(group_router)      # /groups/...

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

@app.post("/")
async def root_post_handler(request: Request):
    """
    Catch-all for misconfigured webhooks pointing to root.
    Returns a message that the bot can display to the user/admin.
    """
    return {
        "replies": [
            {
                "text": "⚠️ Configuration Error: The Webhook URL is set to the root domain. Please update it in Zoho SalesIQ to: .../webhooks/salesiq"
            }
        ]
    }

@app.get("/vote/{short_code}")
def serve_vote_page(short_code: str):
    # Serve the static HTML file
    # The frontend JS will extract the short_code from the URL
    file_path = os.path.join("trip-frontend", "vote.html")
    if os.path.exists(file_path):
        return FileResponse(file_path)
    return {"error": "Vote page not found"}
