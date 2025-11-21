from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import uuid4
from datetime import datetime

from ..database import get_db
from .. import models, schemas
from ..auth.otp import (
    create_and_send_phone_otp_for_signup,
    create_and_send_google_phone_otp,
)
from ..auth.google_oauth import (
    build_google_auth_url,
    exchange_code_for_tokens,
    get_google_userinfo,
    create_temp_google_identity,
)

router = APIRouter(prefix="", tags=["auth"])

# ========= NORMAL PHONE FLOW =========

@router.post("/phone/signup/send-otp")
def phone_signup_send_otp(payload: schemas.PhoneSignupRequest,
                          db: Session = Depends(get_db)):
    try:
        print(f"[OTP] Received request for phone: {payload.phone}")
        
        # Check if phone already exists as a registered user
        existing_user = db.query(models.User).filter(models.User.phone == payload.phone).first()
        if existing_user:
            print(f"[OTP] Phone {payload.phone} already registered")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Phone already registered"
            )

        # Check if there's a recent unverified OTP for this phone
        existing_otp = db.query(models.OtpCode).filter(
            models.OtpCode.phone == payload.phone,
            models.OtpCode.purpose == "phone_register",
            models.OtpCode.verified == False,
        ).first()
        
        if existing_otp:
            print(f"[OTP] Deleting existing unverified OTP for {payload.phone}")
            # Delete the old OTP to allow a new one
            db.delete(existing_otp)
            db.commit()

        print(f"[OTP] Creating new OTP for {payload.phone}")
        create_and_send_phone_otp_for_signup(db, payload)
        print(f"[OTP] Successfully sent OTP to {payload.phone}")
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"[OTP] ERROR in phone_signup_send_otp: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to send OTP: {str(e)}"
        )
    return {"message": "OTP sent for signup"}

@router.post("/phone/signup/verify", response_model=schemas.AuthResponse)
def phone_signup_verify(payload: schemas.PhoneOtpVerifyRequest,
                        db: Session = Depends(get_db)):
    otp_row = db.query(models.OtpCode).filter(
        models.OtpCode.phone == payload.phone,
        models.OtpCode.code == payload.code,
        models.OtpCode.purpose == "phone_register",
        models.OtpCode.verified == False,
    ).first()

    if not otp_row:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP"
        )

    # Basic expiry check
    if otp_row.expires_at and otp_row.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP expired"
        )

    # Mark OTP as verified
    otp_row.verified = True
    db.commit()

    # Create user
    register_id = f"REG-{uuid4().hex[:10]}"
    user = models.User(
        register_id=register_id,
        email=otp_row.email,
        name=otp_row.name or "User",
        age=otp_row.age,
        location=otp_row.location,
        phone=otp_row.phone,
        auth_provider="phone",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return schemas.AuthResponse(
        register_id=user.register_id,
        auth_provider=user.auth_provider,
        email=user.email,
        phone=user.phone,
        name=user.name,
    )

# ========= GOOGLE FLOW =========

@router.get("/google/url")
def get_google_auth_url():
    """
    For front-end or SalesIQ: call this GET to get the Google OAuth URL,
    then redirect the user there.
    """
    url = build_google_auth_url()
    return {"auth_url": url}

@router.get("/google/callback")
def google_callback(code: str, state: str = "xyz", db: Session = Depends(get_db)):
    """
    Google redirects here with ?code=...
    We exchange code for tokens, get userinfo, and store it as a temp identity.
    """
    tokens = exchange_code_for_tokens(code)
    access_token = tokens.get("access_token")
    if not access_token:
        raise HTTPException(status_code=400, detail="No access_token")

    userinfo = get_google_userinfo(access_token)
    google_temp_id = create_temp_google_identity(db, userinfo)

    # In a real app you might redirect to your front-end.
    # For now, we just return the temp id.
    return {
        "message": "Google login success. Now collect phone number and verify OTP.",
        "google_temp_id": str(google_temp_id),
        "google_email": userinfo.get("email"),
        "google_name": userinfo.get("name"),
    }

@router.post("/google/phone/send-otp")
def google_phone_send_otp(payload: schemas.GooglePhoneSendOtpRequest,
                          db: Session = Depends(get_db)):
    try:
        otp_id = create_and_send_google_phone_otp(db, payload.google_temp_id, payload.phone)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid google_temp_id")
    return {
        "message": "OTP sent to phone for Google flow",
        "google_phone_temp_id": str(otp_id),
    }

@router.post("/google/phone/verify", response_model=schemas.AuthResponse)
def google_phone_verify(payload: schemas.GooglePhoneVerifyRequest,
                        db: Session = Depends(get_db)):
    otp_row = db.query(models.OtpCode).filter(
        models.OtpCode.id == int(payload.google_temp_id),
        models.OtpCode.code == payload.code,
        models.OtpCode.purpose == "google_phone_verify",
        models.OtpCode.verified == False,
    ).first()

    if not otp_row:
        raise HTTPException(status_code=400, detail="Invalid OTP / temp id")

    otp_row.verified = True
    db.commit()

    # Check if user already exists by email or google_id
    user = db.query(models.User).filter(
        (models.User.email == otp_row.google_email) |
        (models.User.google_id == otp_row.google_id)
    ).first()

    if not user:
        from uuid import uuid4
        register_id = f"REG-{uuid4().hex[:10]}"
        user = models.User(
            register_id=register_id,
            email=otp_row.google_email,
            google_id=otp_row.google_id,
            name=otp_row.google_name or "Google User",
            phone=otp_row.phone,
            auth_provider="google",
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        # Update phone if missing
        if not user.phone:
            user.phone = otp_row.phone
            db.commit()
            db.refresh(user)

    return schemas.AuthResponse(
        register_id=user.register_id,
        auth_provider=user.auth_provider,
        email=user.email,
        phone=user.phone,
        name=user.name,
    )
