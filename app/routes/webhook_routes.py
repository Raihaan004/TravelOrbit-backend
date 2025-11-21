from fastapi import APIRouter
from ..schemas import SimpleMessage

router = APIRouter(prefix="/webhook", tags=["webhook"])

@router.get("/ping")
def ping():
    return {"status": "ok", "message": "Backend alive"}

@router.post("/salesiq")
def salesiq_webhook(payload: SimpleMessage):
    # Example: Zoho SalesIQ bot plug can POST {"message": "..."} here.
    # You can check message and call internal functions.
    incoming = payload.message.lower()
    if "hello" in incoming:
        reply = "Hi from FastAPI backend 👋"
    else:
        reply = "I received your message: " + payload.message

    return {"reply": reply}
