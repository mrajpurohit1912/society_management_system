from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.authentication.routes import router as auth_router

# Initialize modern FastAPI app with OpenAPI configurations
app = FastAPI(
    title="Society Management System API",
    description="Enterprise API backend for society management and user authentication",
    version="1.0.0",
)

import os

# Setup CORS (Cross-Origin Resource Sharing)
# Configure these origins according to production deployment domain
origins = [
    "http://localhost:3000",  # Default local React/Next.js port
    "http://127.0.0.1:3000",
]

allowed_origins_env = os.getenv("ALLOWED_ORIGINS")
if allowed_origins_env:
    origins.extend([origin.strip() for origin in allowed_origins_env.split(",") if origin.strip()])

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Feature Slices Routers
app.include_router(auth_router, prefix="/api/v1")

@app.get("/")
def read_root():
    return {"message": "Society Management System Backend is running."}
