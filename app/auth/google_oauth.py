import requests
from sqlalchemy.orm import Session
from ..config import settings
from ..models import OtpCode

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"

def build_google_auth_url(state: str = "xyz") -> str:
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "online",
        "prompt": "consent",
        "state": state,
    }
    import urllib.parse
    return GOOGLE_AUTH_URL + "?" + urllib.parse.urlencode(params)

def exchange_code_for_tokens(code: str) -> dict:
    data = {
        "code": code,
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code",
    }
    resp = requests.post(GOOGLE_TOKEN_URL, data=data)
    resp.raise_for_status()
    return resp.json()

def get_google_userinfo(access_token: str) -> dict:
    headers = {"Authorization": f"Bearer {access_token}"}
    resp = requests.get(GOOGLE_USERINFO_URL, headers=headers)
    resp.raise_for_status()
    return resp.json()

def create_temp_google_identity(db: Session, google_data: dict) -> int:
    """
    Store Google data in an OtpCode row with purpose='google_identity'.
    Return the id as google_temp_id, which front-end / SalesIQ can use later.
    """
    otp_row = OtpCode(
        phone=None,
        code="",
        purpose="google_identity",
        expires_at=None,
        google_id=google_data.get("sub"),
        google_email=google_data.get("email"),
        google_name=google_data.get("name"),
    )
    db.add(otp_row)
    db.commit()
    db.refresh(otp_row)
    return otp_row.id
