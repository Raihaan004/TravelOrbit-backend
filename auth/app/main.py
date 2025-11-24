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

