from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
import json
from sqlalchemy.orm import Session
from uuid import uuid4
from datetime import datetime

from ..database import get_db
from .. import models, schemas
from ..auth.otp import (
    create_and_send_phone_otp_for_signup,
    create_and_send_google_phone_otp,
    create_and_send_email_otp,
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

# ========= EMAIL FLOW =========

@router.post("/email/login")
def email_login_send_otp(payload: schemas.EmailLoginRequest,
                         db: Session = Depends(get_db)):
    try:
        print(f"[OTP] Received request for email: {payload.email}")
        
        # Check if user exists
        user = db.query(models.User).filter(models.User.email == payload.email).first()
        
        if user:
            # Existing user: Send Email OTP
            # Check if there's a recent unverified OTP for this email
            existing_otp = db.query(models.OtpCode).filter(
                models.OtpCode.email == payload.email,
                models.OtpCode.purpose == "email_login",
                models.OtpCode.verified == False,
            ).first()
            
            if existing_otp:
                db.delete(existing_otp)
                db.commit()

            create_and_send_email_otp(db, payload.email)
            print(f"[OTP] Successfully sent OTP to {payload.email}")
            return {"status": "existing", "message": "OTP sent to email"}
        else:
            # New user: Return status so frontend can ask for phone
            print(f"[OTP] New user email: {payload.email}")
            return {"status": "new_user", "message": "User not found, proceed to phone verification"}

    except Exception as e:
        db.rollback()
        print(f"[OTP] ERROR in email_login_send_otp: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to process email: {str(e)}"
        )

@router.post("/email/verify", response_model=schemas.AuthResponse)
def email_login_verify(payload: schemas.EmailVerifyRequest,
                       db: Session = Depends(get_db)):
    otp_row = db.query(models.OtpCode).filter(
        models.OtpCode.email == payload.email,
        models.OtpCode.code == payload.code,
        models.OtpCode.purpose == "email_login",
        models.OtpCode.verified == False,
    ).first()

    if not otp_row:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP"
        )

    if otp_row.expires_at and otp_row.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP expired"
        )

    otp_row.verified = True
    db.commit()

    # Check if user exists
    user = db.query(models.User).filter(models.User.email == payload.email).first()
    
    if not user:
        # Create new user with dummy phone if needed
        register_id = f"REG-{uuid4().hex[:10]}"
        dummy_phone = f"no-phone-{uuid4().hex[:10]}"
        
        user = models.User(
            register_id=register_id,
            email=payload.email,
            name="User",
            phone=dummy_phone,
            auth_provider="email",
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

@router.get("/google/callback", response_class=HTMLResponse)
def google_callback(code: str, state: str = "xyz", db: Session = Depends(get_db)):
    """
    Google redirects here with ?code=...
    We exchange code for tokens, get userinfo, and store it as a temp identity.
    """
    tokens = exchange_code_for_tokens(code)
    access_token = tokens.get("access_token")
    if not access_token:
        return HTMLResponse(content="<h1>Error: No access token</h1>", status_code=400)

    userinfo = get_google_userinfo(access_token)
    
    # Check if user already exists
    user = db.query(models.User).filter(
        (models.User.email == userinfo.get("email")) | 
        (models.User.google_id == userinfo.get("sub")) # 'sub' is google id
    ).first()

    response_data = {}

    if user:
        # User exists, log them in directly
        # Update google_id if missing
        if not user.google_id:
            user.google_id = userinfo.get("sub")
            db.commit()
            
        response_data = {
            "status": "success",
            "user": {
                "name": user.name,
                "email": user.email,
                "phone": user.phone,
                "register_id": user.register_id,
                "auth_provider": user.auth_provider
            }
        }
    else:
        # New user or partial info
        google_temp_id = create_temp_google_identity(db, userinfo)
        response_data = {
            "status": "needs_phone",
            "google_temp_id": str(google_temp_id),
            "google_email": userinfo.get("email"),
            "google_name": userinfo.get("name")
        }

    # Return HTML that posts message to opener
    html_content = f"""
    <html>
    <body>
        <h1>Login Successful</h1>
        <p>Closing window...</p>
        <script>
            const data = {json.dumps(response_data)};
            if (window.opener) {{
                window.opener.postMessage({{ type: 'GOOGLE_LOGIN_RESULT', payload: data }}, '*');
                window.close();
            }} else {{
                document.body.innerHTML = "<h1>Login processed. You can close this window.</h1>";
            }}
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

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
