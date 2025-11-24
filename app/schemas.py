from pydantic import BaseModel, EmailStr
from typing import Optional

# ====== NORMAL (PHONE) SIGNUP ======

class PhoneSignupRequest(BaseModel):
    # Normal: may not have email, so email is optional
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    age: Optional[int] = None
    location: Optional[str] = None
    phone: str

class PhoneOtpVerifyRequest(BaseModel):
    phone: str
    code: str

class AuthResponse(BaseModel):
    register_id: str
    auth_provider: str
    email: Optional[EmailStr]
    phone: str
    name: str

# ====== GOOGLE FLOW ======

class GooglePhoneSendOtpRequest(BaseModel):
    google_temp_id: str  # some session token we give after Google callback
    phone: str

class GooglePhoneVerifyRequest(BaseModel):
    google_temp_id: str
    code: str

# ====== EMAIL FLOW ======

class EmailLoginRequest(BaseModel):
    email: EmailStr

class EmailVerifyRequest(BaseModel):
    email: EmailStr
    code: str

# ====== BASIC WEBHOOK / TEST ======

class SimpleMessage(BaseModel):
    message: str
