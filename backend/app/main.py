"""
FastAPI entrypoint with API routes for certificate verification
"""
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uvicorn

from .config import settings
from .models import CertificateResponse, VerificationRequest
from .services.llm_client import LLMClient
from .services.supabase_client import SupabaseClient
from .services.fusion_engine import FusionEngine
from .utils.helpers import setup_logging, process_image

# Setup logging
logger = setup_logging()

# Initialize FastAPI app
app = FastAPI(
    title="Certificate Verifier API",
    description="AI-powered certificate verification system",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
llm_client = LLMClient()
supabase_client = SupabaseClient()
fusion_engine = FusionEngine(llm_client, supabase_client)

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Certificate Verifier API is running"}

@app.post("/upload", response_model=CertificateResponse)
async def upload_certificate(file: UploadFile = File(...)):
    """Upload and process certificate image"""
    try:
        # Process the uploaded image
        image_data = await process_image(file)
        
        # Run through fusion engine for verification
        result = await fusion_engine.verify_certificate(image_data)
        
        return result
    except Exception as e:
        logger.error(f"Error processing certificate: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/verify", response_model=CertificateResponse)
async def verify_certificate(request: VerificationRequest):
    """Verify certificate using manual input or image URL"""
    try:
        result = await fusion_engine.verify_certificate_by_data(request)
        return result
    except Exception as e:
        logger.error(f"Error verifying certificate: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/certificates/{certificate_id}")
async def get_certificate(certificate_id: str):
    """Get certificate details by ID"""
    try:
        result = await supabase_client.get_certificate(certificate_id)
        if not result:
            raise HTTPException(status_code=404, detail="Certificate not found")
        return result
    except Exception as e:
        logger.error(f"Error retrieving certificate: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
