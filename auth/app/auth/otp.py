import random
from datetime import datetime
from sqlalchemy.orm import Session
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from ..config import settings
from ..models import OtpCode
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def get_twilio_client():
    """Initialize Twilio client on-demand instead of at module import time"""
    return Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

def generate_otp(length: int = 6) -> str:
    return "".join(str(random.randint(0, 9)) for _ in range(length))

def send_otp_sms(phone: str, code: str):
    try:
        twilio_client = get_twilio_client()
        message = twilio_client.messages.create(
            body=f"Your verification code is: {code}",
            from_=settings.TWILIO_FROM_NUMBER,
            to=phone
        )
        print(f"SMS sent successfully. SID: {message.sid}")
    except TwilioRestException as e:
        print(f"Twilio error: {e.msg}")
        raise Exception(f"SMS sending failed: {e.msg}")
    except Exception as e:
        print(f"Error sending OTP SMS: {str(e)}")
        raise Exception(f"SMS sending failed: {str(e)}")

def send_otp_email(to_email: str, code: str):
    try:
        if not settings.SMTP_HOST or not settings.SMTP_USERNAME:
            print("SMTP not configured, skipping email")
            return

        msg = MIMEMultipart()
        msg['From'] = settings.SENDER_EMAIL
        msg['To'] = to_email
        msg['Subject'] = "Your Login Verification Code"

        body = f"Your verification code is: {code}\n\nThis code will expire in 5 minutes."
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
        server.starttls()
        server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        text = msg.as_string()
        server.sendmail(settings.SENDER_EMAIL, to_email, text)
        server.quit()
        print(f"Email OTP sent to {to_email}")
    except Exception as e:
        print(f"Error sending email OTP: {str(e)}")
        raise Exception(f"Email sending failed: {str(e)}")

def create_and_send_phone_otp_for_signup(db: Session, signup_data) -> None:
    print(f"[create_and_send_phone_otp_for_signup] Starting for phone: {signup_data.phone}")
    
    code = generate_otp()
    print(f"[create_and_send_phone_otp_for_signup] Generated OTP code: {code}")
    
    otp = OtpCode(
        phone=signup_data.phone,
        code=code,
        purpose="phone_register",
        expires_at=OtpCode.default_expiry(),
        name=signup_data.name,
        age=signup_data.age,
        location=signup_data.location,
        email=signup_data.email,
    )
    
    print(f"[create_and_send_phone_otp_for_signup] Adding OTP to database")
    db.add(otp)
    db.commit()
    db.refresh(otp)
    print(f"[create_and_send_phone_otp_for_signup] OTP saved to DB with id: {otp.id}")
    
    # Send SMS - let exceptions propagate to the route handler
    # If SMS fails, the route will rollback the transaction
    print(f"[create_and_send_phone_otp_for_signup] Sending SMS to {signup_data.phone}")
    send_otp_sms(signup_data.phone, code)

def create_and_send_google_phone_otp(db: Session, google_temp_id: str, phone: str) -> None:
    # google_temp_id is actually an OtpCode.id saved earlier
    otp_row = db.query(OtpCode).filter(
        OtpCode.id == int(google_temp_id),
        OtpCode.purpose == "google_identity"
    ).first()
    if not otp_row:
        raise ValueError("Invalid google_temp_id")

    code = generate_otp()
    otp_row2 = OtpCode(
        phone=phone,
        code=code,
        purpose="google_phone_verify",
        expires_at=OtpCode.default_expiry(),
        google_id=otp_row.google_id,
        google_email=otp_row.google_email,
        google_name=otp_row.google_name,
    )
    db.add(otp_row2)
    db.commit()
    db.refresh(otp_row2)

    send_otp_sms(phone, code)
    return otp_row2.id  # we can use this as another temp id

def create_and_send_email_otp_for_login(db: Session, email: str) -> None:
    code = generate_otp()
    
    # Invalidate old OTPs
    old_otps = db.query(OtpCode).filter(
        OtpCode.email == email,
        OtpCode.purpose == "email_login",
        OtpCode.verified == False
    ).all()
    for o in old_otps:
        db.delete(o)
    
    otp = OtpCode(
        email=email,
        code=code,
        purpose="email_login",
        expires_at=OtpCode.default_expiry(),
    )
    db.add(otp)
    db.commit()
    
    send_otp_email(email, code)
