"""
Daily script to send feedback emails to users whose trips ended yesterday.
Run this script daily via cron or scheduler.
"""
import sys
import os
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

# Add the current directory to sys.path to allow imports
sys.path.append(os.getcwd())

from auth.app.database import SessionLocal
from trip_plan.models import Trip
from app.email_service import EmailService

def send_feedback_emails():
    db: Session = SessionLocal()
    try:
        # Find trips that ended yesterday
        yesterday = datetime.utcnow().date() - timedelta(days=1)
        print(f"Checking for trips that ended on {yesterday}...")

        # Query trips: ended yesterday AND feedback not sent AND status is 'paid' or 'planned'
        # Assuming we only want to send to valid trips
        trips = db.query(Trip).filter(
            Trip.end_date == yesterday,
            Trip.feedback_email_sent == 0,
            Trip.status.in_(["planned", "paid"]) 
        ).all()

        print(f"Found {len(trips)} trips eligible for feedback email.")

        for trip in trips:
            print(f"Sending feedback email to {trip.email} for trip {trip.id}...")
            success = EmailService.send_feedback_request_email(trip)
            
            if success:
                trip.feedback_email_sent = 1
                db.add(trip)
                print(f"✅ Email sent and trip updated.")
            else:
                print(f"❌ Failed to send email.")
        
        db.commit()
        print("Done processing feedback emails.")

    except Exception as e:
        print(f"Error sending feedback emails: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    send_feedback_emails()
