import smtplib
import os
from dotenv import load_dotenv

load_dotenv()

host = os.getenv("SMTP_HOST")
port = int(os.getenv("SMTP_PORT"))
user = os.getenv("SMTP_USERNAME")
password = os.getenv("SMTP_PASSWORD")

print(f"Testing connection to {host}:{port}...")

try:
    server = smtplib.SMTP(host, port, timeout=10)
    print("Connected to server.")
    
    print("Starting TLS...")
    server.starttls()
    print("TLS started.")
    
    print(f"Logging in as {user}...")
    server.login(user, password)
    print("Login successful!")
    
    server.quit()
    print("Test passed.")
except Exception as e:
    print(f"Test failed: {e}")
