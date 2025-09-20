"""
Simple FastAPI server for testing - minimal dependencies
"""
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uvicorn
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Certificate Verifier API",
    description="AI-powered certificate verification system",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class VerificationRequest(BaseModel):
    name: Optional[str] = None
    roll_no: Optional[str] = None
    certificate_no: Optional[str] = None
    course: Optional[str] = None
    month: Optional[str] = None
    year: Optional[str] = None
    grade: Optional[str] = None

class CertificateResponse(BaseModel):
    success: bool
    verification_status: str
    confidence: float
    extracted_data: dict
    message: str

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Certificate Verifier API is running", "status": "healthy"}

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "message": "Server is running properly",
        "version": "1.0.0",
        "gemini_api_key": "AIzaSyApje8wDzq4SwS0yjDxhy4ss2wVeH3rjts"
    }

@app.post("/upload", response_model=CertificateResponse)
async def upload_certificate(file: UploadFile = File(...)):
    """Upload and process certificate image"""
    try:
        logger.info(f"Received file: {file.filename}")
        
        # Mock response for testing
        mock_data = {
            "name": "Sample Student",
            "roll_no": "12345",
            "certificate_no": "CERT001",
            "course": "Computer Science",
            "month": "June",
            "year": "2023",
            "grade": "A+",
            "institution": "Sample University"
        }
        
        return CertificateResponse(
            success=True,
            verification_status="mock_verified",
            confidence=0.85,
            extracted_data=mock_data,
            message="Mock extraction completed - Gemini API key is available"
        )
        
    except Exception as e:
        logger.error(f"Error processing certificate: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/verify", response_model=CertificateResponse)
async def verify_certificate(request: VerificationRequest):
    """Verify certificate using manual input"""
    try:
        logger.info("Manual verification request received")
        
        extracted_data = request.dict()
        
        # Calculate confidence based on provided fields
        confidence = 0.0
        if extracted_data.get("name"):
            confidence += 0.2
        if extracted_data.get("course"):
            confidence += 0.2
        if extracted_data.get("year"):
            confidence += 0.2
        if extracted_data.get("grade"):
            confidence += 0.2
        if extracted_data.get("certificate_no"):
            confidence += 0.2
        
        verification_status = "verified" if confidence > 0.6 else "needs_review"
        
        return CertificateResponse(
            success=True,
            verification_status=verification_status,
            confidence=confidence,
            extracted_data=extracted_data,
            message="Manual verification completed"
        )
        
    except Exception as e:
        logger.error(f"Error verifying certificate: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/certificates/{certificate_id}")
async def get_certificate(certificate_id: str):
    """Get certificate details by ID"""
    return {
        "id": certificate_id,
        "name": "Sample Student",
        "status": "verified",
        "message": "Mock certificate data"
    }

if __name__ == "__main__":
    print("🚀 Starting Certificate Verifier API...")
    print("📍 Server will be available at: http://localhost:8000")
    print("📚 API Documentation: http://localhost:8000/docs")
    print("🔑 Gemini API Key: AIzaSyApje8wDzq4SwS0yjDxhy4ss2wVeH3rjts")
    uvicorn.run(
        "simple_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
