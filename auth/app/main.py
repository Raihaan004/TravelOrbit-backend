from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import auth_routes, webhook_routes

app = FastAPI(title="TravelOrbit Auth Backend")

# -------- ENABLE CORS --------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or ["http://localhost:3000"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# -----------------------------

app.include_router(auth_routes.router, prefix="/auth")
app.include_router(webhook_routes.router)

@app.get("/")
def root():
    return {"message": "Auth API running"}

@app.get("/test-twilio")
def test_twilio():
    """Test Twilio connection"""
    from .config import settings
    from .auth.otp import get_twilio_client
    
    try:
        client = get_twilio_client()
        account = client.api.accounts(settings.TWILIO_ACCOUNT_SID).fetch()
        return {
            "status": "success",
            "message": "Twilio connection successful",
            "account_sid": account.sid,
            "friendly_name": account.friendly_name
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
