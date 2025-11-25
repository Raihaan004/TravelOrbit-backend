"""
Integration examples for TravelOrbit PDF Generator
Shows how to use with FastAPI, Flask, and existing database
"""

# ======================== FASTAPI INTEGRATION ========================

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from travel_pdf_generator_v4 import TravelPDFGenerator
import os
from datetime import datetime

app = FastAPI()
pdf_generator = TravelPDFGenerator()

@app.post("/api/v1/trips/{trip_id}/generate-pdf")
async def generate_trip_pdf(trip_id: int):
    """
    Generate and download PDF for a specific trip
    """
    try:
        # Get trip data from database (example)
        trip_data = get_trip_from_db(trip_id)
        
        if not trip_data:
            raise HTTPException(status_code=404, detail="Trip not found")
        
        # Generate PDF
        filename = f"itinerary_{trip_id}_{datetime.now().timestamp()}.pdf"
        pdf_generator.create_pdf(trip_data, filename)
        
        # Return PDF file
        return FileResponse(
            filename,
            media_type="application/pdf",
            filename=f"TravelOrbit_Itinerary_{trip_id}.pdf"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/trips/{trip_id}/pdf-status")
async def check_pdf_ready(trip_id: int):
    """
    Check if PDF is ready to download
    """
    filename = f"itinerary_{trip_id}.pdf"
    is_ready = os.path.exists(filename)
    
    return {
        "trip_id": trip_id,
        "pdf_ready": is_ready,
        "download_url": f"/api/v1/trips/{trip_id}/generate-pdf" if is_ready else None
    }


# ======================== FLASK INTEGRATION ========================

from flask import Flask, send_file, jsonify

app_flask = Flask(__name__)
pdf_generator_flask = TravelPDFGenerator()

@app_flask.route('/api/trips/<int:trip_id>/download-pdf', methods=['GET'])
def download_trip_pdf_flask(trip_id):
    """
    Flask route to download PDF itinerary
    """
    try:
        # Get trip from database
        trip_data = get_trip_from_db(trip_id)
        
        if not trip_data:
            return jsonify({"error": "Trip not found"}), 404
        
        # Generate PDF
        filename = f"trip_{trip_id}_itinerary.pdf"
        pdf_generator_flask.create_pdf(trip_data, filename)
        
        # Send file
        return send_file(
            filename,
            as_attachment=True,
            download_name=f"TravelOrbit_Itinerary_{trip_id}.pdf",
            mimetype="application/pdf"
        )
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ======================== DATABASE INTEGRATION ========================

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Trip, DayItinerary  # Your existing models

def get_trip_from_db(trip_id: int):
    """
    Example function to fetch trip data from database
    and convert to PDF generator format
    """
    # Create session (adjust based on your setup)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Query trip
        trip = session.query(Trip).filter(Trip.id == trip_id).first()
        
        if not trip:
            return None
        
        # Convert to PDF format
        trip_data = {
            'destination': trip.destination,
            'start_date': trip.start_date.strftime('%Y-%m-%d'),
            'end_date': trip.end_date.strftime('%Y-%m-%d'),
            'travelers': format_travelers(trip.travelers),
            'duration': f"{calculate_duration(trip.start_date, trip.end_date)} Days, {calculate_nights(trip.start_date, trip.end_date)} Nights",
            'package_type': trip.package_type,
            'hotel_name': trip.hotel.name if trip.hotel else 'Hotel',
            'hotel_rating': trip.hotel.rating if trip.hotel else '⭐⭐⭐',
            'total_cost': f"₹{trip.total_cost:,}",
            'itinerary': []
        }
        
        # Add each day's itinerary
        for day in session.query(DayItinerary).filter(DayItinerary.trip_id == trip_id).all():
            day_data = {
                'title': day.title,
                'description': day.description,
                'activities': [a.activity_name for a in day.activities]
            }
            trip_data['itinerary'].append(day_data)
        
        return trip_data
    
    finally:
        session.close()


def format_travelers(travelers_obj):
    """Format travelers object to string"""
    adults = travelers_obj.get('adults', 0)
    children = travelers_obj.get('children', 0)
    seniors = travelers_obj.get('seniors', 0)
    
    parts = []
    if adults:
        parts.append(f"{adults} Adult{'s' if adults > 1 else ''}")
    if children:
        parts.append(f"{children} Child{'ren' if children > 1 else ''}")
    if seniors:
        parts.append(f"{seniors} Senior{'s' if seniors > 1 else ''}")
    
    return ", ".join(parts)


def calculate_duration(start_date, end_date):
    """Calculate number of days"""
    return (end_date - start_date).days


def calculate_nights(start_date, end_date):
    """Calculate number of nights"""
    return (end_date - start_date).days - 1


# ======================== BACKGROUND TASK INTEGRATION ========================

from celery import Celery
import shutil

celery_app = Celery('travelorbit')

@celery_app.task
def generate_pdf_async(trip_id: int):
    """
    Generate PDF asynchronously using Celery
    """
    try:
        trip_data = get_trip_from_db(trip_id)
        filename = f"pdfs/itinerary_{trip_id}.pdf"
        
        pdf_generator = TravelPDFGenerator()
        pdf_generator.create_pdf(trip_data, filename)
        
        # Update trip status in DB
        update_trip_status(trip_id, "pdf_ready", filename)
        
        return {
            "status": "success",
            "trip_id": trip_id,
            "filename": filename
        }
    
    except Exception as e:
        update_trip_status(trip_id, "pdf_error", str(e))
        return {
            "status": "error",
            "trip_id": trip_id,
            "error": str(e)
        }


@app.post("/api/v1/trips/{trip_id}/generate-pdf-async")
async def generate_pdf_async_endpoint(trip_id: int):
    """
    Generate PDF asynchronously
    """
    task = generate_pdf_async.delay(trip_id)
    
    return {
        "status": "processing",
        "task_id": task.id,
        "trip_id": trip_id
    }


@app.get("/api/v1/tasks/{task_id}/status")
async def get_task_status(task_id: str):
    """
    Get status of PDF generation task
    """
    from celery.result import AsyncResult
    
    task = AsyncResult(task_id)
    
    return {
        "task_id": task_id,
        "status": task.status,
        "result": task.result
    }


# ======================== EMAIL INTEGRATION ========================

from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email import encoders
import smtplib

def send_pdf_via_email(trip_id: int, recipient_email: str):
    """
    Generate PDF and send via email
    """
    try:
        # Generate PDF
        trip_data = get_trip_from_db(trip_id)
        filename = f"itinerary_{trip_id}.pdf"
        
        pdf_generator = TravelPDFGenerator()
        pdf_generator.create_pdf(trip_data, filename)
        
        # Create email
        msg = MIMEMultipart()
        msg['From'] = "noreply@travelorbit.com"
        msg['To'] = recipient_email
        msg['Subject'] = f"Your TravelOrbit Itinerary - Trip {trip_id}"
        
        # Email body
        body = """
        Dear Traveler,
        
        Your personalized travel itinerary is ready!
        
        Please find your detailed itinerary attached.
        
        Have a wonderful journey!
        
        Best regards,
        TravelOrbit Team
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Attach PDF
        with open(filename, 'rb') as attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
        
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename= {filename}')
        msg.attach(part)
        
        # Send email
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login("your_email@gmail.com", "your_password")
        text = msg.as_string()
        server.sendmail(msg['From'], msg['To'], text)
        server.quit()
        
        return {"status": "sent", "recipient": recipient_email}
    
    except Exception as e:
        return {"status": "error", "error": str(e)}


@app.post("/api/v1/trips/{trip_id}/send-pdf-email")
async def send_pdf_email(trip_id: int, email: str):
    """
    Generate PDF and email to user
    """
    result = send_pdf_via_email(trip_id, email)
    return result


# ======================== BATCH PDF GENERATION ========================

def generate_pdfs_for_all_trips():
    """
    Generate PDFs for all trips (daily batch job)
    """
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        trips = session.query(Trip).all()
        results = []
        
        for trip in trips:
            try:
                trip_data = get_trip_from_db(trip.id)
                filename = f"pdfs/batch/itinerary_{trip.id}.pdf"
                
                pdf_generator = TravelPDFGenerator()
                pdf_generator.create_pdf(trip_data, filename)
                
                results.append({
                    "trip_id": trip.id,
                    "status": "success"
                })
            except Exception as e:
                results.append({
                    "trip_id": trip.id,
                    "status": "error",
                    "error": str(e)
                })
        
        return results
    
    finally:
        session.close()


# ======================== HELPER FUNCTIONS ========================

def get_trip_from_db(trip_id: int):
    """
    Example placeholder - implement based on your database
    """
    # This would connect to your actual database
    # For now, returning sample data
    pass


def update_trip_status(trip_id: int, status: str, value: str):
    """
    Update trip status in database
    """
    pass


# ======================== EXAMPLE USAGE ========================

if __name__ == "__main__":
    # Example 1: Generate PDF directly
    from travel_pdf_generator_v4 import TravelPDFGenerator, SAMPLE_TRIP
    
    generator = TravelPDFGenerator()
    generator.create_pdf(SAMPLE_TRIP, "sample_output.pdf")
    print("✓ Sample PDF generated")
    
    # Example 2: Send via email (if you have trip data)
    # result = send_pdf_via_email(123, "user@example.com")
    # print(result)
