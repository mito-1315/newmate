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
from .services.supabase_client import SupabaseClient
from .services.simple_fusion_engine import SimpleFusionEngine
from .services.certificate_issuance import CertificateIssuanceService
from .services.public_verification import PublicVerificationService
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
supabase_client = SupabaseClient()
fusion_engine = SimpleFusionEngine(supabase_client)
issuance_service = CertificateIssuanceService(supabase_client)
public_verification_service = PublicVerificationService(supabase_client)

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

# =============================================
# UNIVERSITY CERTIFICATE ISSUANCE ENDPOINTS
# =============================================

@app.post("/issue/certificate")
async def issue_certificate(certificate_data: dict, institution_id: str = "default"):
    """Issue a new certificate with QR code (University workflow)"""
    try:
        result = await issuance_service.issue_certificate(certificate_data, institution_id)
        return result
    except Exception as e:
        logger.error(f"Certificate issuance failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/issue/bulk")
async def bulk_issue_certificates(certificates_data: dict, institution_id: str = "default"):
    """Bulk issue certificates from CSV/ERP data"""
    try:
        certificates_list = certificates_data.get("certificates", [])
        if not certificates_list:
            raise HTTPException(status_code=400, detail="No certificates data provided")
        
        result = await issuance_service.bulk_issue_certificates(certificates_list, institution_id)
        return result
    except Exception as e:
        logger.error(f"Bulk certificate issuance failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# =============================================
# PUBLIC VERIFICATION ENDPOINTS (QR SCANNING)
# =============================================

@app.get("/verify/{attestation_id}")
async def verify_certificate_public(attestation_id: str):
    """Public certificate verification endpoint (Employer workflow)"""
    try:
        result = await public_verification_service.verify_by_attestation_id(attestation_id)
        return result
    except Exception as e:
        logger.error(f"Public verification failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/verify/qr")
async def verify_by_qr_data(qr_data: dict):
    """Verify certificate by QR code data"""
    try:
        qr_content = qr_data.get("qr_content")
        if not qr_content:
            raise HTTPException(status_code=400, detail="QR content is required")
        
        result = await public_verification_service.verify_by_qr_data(qr_content)
        return result
    except Exception as e:
        logger.error(f"QR verification failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/verify/{attestation_id}/image")
async def get_verified_certificate_image(attestation_id: str):
    """Get verified certificate image for display"""
    try:
        result = await public_verification_service.get_certificate_image(attestation_id)
        if not result:
            raise HTTPException(status_code=404, detail="Certificate image not found")
        return result
    except Exception as e:
        logger.error(f"Failed to get certificate image: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# =============================================
# INSTITUTION MANAGEMENT ENDPOINTS
# =============================================

@app.post("/institutions/register")
async def register_institution(institution_data: dict):
    """Register a new institution"""
    try:
        institution_id = await supabase_client.store_institution(institution_data)
        return {"institution_id": institution_id, "status": "registered"}
    except Exception as e:
        logger.error(f"Institution registration failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/institutions/{institution_id}/certificates/import")
async def import_certificates(institution_id: str, certificates_data: dict):
    """Import certificates for an institution"""
    try:
        certificates_list = certificates_data.get("certificates", [])
        if not certificates_list:
            raise HTTPException(status_code=400, detail="No certificates data provided")
        
        imported_count = await supabase_client.import_certificates_batch(certificates_list)
        return {"imported_count": imported_count, "status": "success"}
    except Exception as e:
        logger.error(f"Certificate import failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# =============================================
# ANALYTICS AND REPORTING ENDPOINTS
# =============================================

@app.get("/analytics/verification-stats")
async def get_verification_statistics(institution_id: Optional[str] = None):
    """Get verification statistics"""
    try:
        stats = await public_verification_service.get_verification_statistics(institution_id)
        return stats
    except Exception as e:
        logger.error(f"Failed to get verification statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# =============================================
# ADDITIONAL FRONTEND ENDPOINTS
# =============================================

@app.get("/reviews")
async def get_reviews(status: Optional[str] = None, search: Optional[str] = None):
    """Get manual review queue"""
    try:
        # Mock data for now
        reviews = [
            {
                "id": "1",
                "name": "John Doe",
                "course": "Computer Science",
                "year": "2023",
                "status": "pending",
                "confidence": 0.75,
                "extracted_data": {
                    "name": "John Doe",
                    "course": "Computer Science",
                    "year": "2023"
                }
            }
        ]
        return {"reviews": reviews}
    except Exception as e:
        logger.error(f"Failed to get reviews: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/reviews/decision")
async def submit_review_decision(decision_data: dict):
    """Submit manual review decision"""
    try:
        # Mock implementation
        return {"success": True, "message": "Review decision submitted"}
    except Exception as e:
        logger.error(f"Failed to submit review decision: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/attestations/{attestation_id}")
async def get_attestation(attestation_id: str):
    """Get attestation details"""
    try:
        # Mock data
        return {
            "id": attestation_id,
            "name": "Sample Student",
            "course": "Computer Science",
            "year": "2023",
            "status": "verified"
        }
    except Exception as e:
        logger.error(f"Failed to get attestation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/verifications/{verification_id}")
async def get_verification(verification_id: str):
    """Get verification details"""
    try:
        # Mock data
        return {
            "id": verification_id,
            "valid": True,
            "name": "Sample Student",
            "course": "Computer Science",
            "year": "2023"
        }
    except Exception as e:
        logger.error(f"Failed to get verification: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/verify-signature")
async def verify_signature(signature_data: dict):
    """Verify digital signature"""
    try:
        # Mock implementation
        return {"valid": True, "message": "Signature verified"}
    except Exception as e:
        logger.error(f"Failed to verify signature: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# =============================================
# NEW SYSTEM ENDPOINTS
# =============================================

@app.post("/issue/certificate")
async def issue_new_certificate(file: UploadFile = File(...), certificate_data: str = None):
    """Issue a new certificate with QR code generation"""
    try:
        import json
        
        # Parse certificate data
        cert_data = json.loads(certificate_data) if certificate_data else {}
        
        # Process the uploaded image
        image_data = await process_image(file)
        
        # Generate certificate with QR code
        result = await issuance_service.issue_certificate_with_qr(cert_data, image_data)
        
        return result
    except Exception as e:
        logger.error(f"Certificate issuance failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/issue/send-email")
async def send_certificate_email(email_data: dict):
    """Send certificate to student email"""
    try:
        # Mock implementation - in real app, integrate with email service
        certificate_id = email_data.get("certificate_id")
        student_email = email_data.get("student_email")
        
        return {
            "success": True,
            "message": f"Certificate sent to {student_email}",
            "certificate_id": certificate_id
        }
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/student/certificates")
async def get_student_certificates(student_id: Optional[str] = None):
    """Get certificates for a student"""
    try:
        # Mock data for now
        certificates = [
            {
                "id": "cert_123",
                "student_name": "John Doe",
                "roll_no": "CS2023001",
                "course_name": "Computer Science",
                "year_of_passing": "2023",
                "grade": "A+",
                "institution_name": "University of Technology",
                "image_url": "/api/certificates/cert_123/image",
                "qr_code_url": "/api/certificates/cert_123/qr",
                "pdf_url": "/api/certificates/cert_123/pdf",
                "issued_date": "2023-06-15",
                "status": "verified"
            }
        ]
        return {"certificates": certificates}
    except Exception as e:
        logger.error(f"Failed to get student certificates: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/legacy/verify")
async def submit_legacy_verification(file: UploadFile = File(...), verification_data: str = None):
    """Submit legacy certificate for verification"""
    try:
        import json
        
        # Parse verification data
        verify_data = json.loads(verification_data) if verification_data else {}
        
        # Process the uploaded image
        image_data = await process_image(file)
        
        # Store verification request
        request_id = await supabase_client.store_legacy_verification_request(verify_data, image_data)
        
        return {
            "success": True,
            "request_id": request_id,
            "message": "Legacy verification request submitted successfully"
        }
    except Exception as e:
        logger.error(f"Legacy verification submission failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/admin/legacy-queue")
async def get_legacy_verification_queue():
    """Get pending legacy verification requests for admin review"""
    try:
        # Mock data for now
        requests = [
            {
                "id": "legacy_001",
                "student_name": "Jane Smith",
                "roll_no": "CS2022001",
                "course_name": "Computer Science",
                "year_of_passing": "2022",
                "email": "jane.smith@email.com",
                "phone": "+1234567890",
                "image_url": "/api/legacy/legacy_001/image",
                "submitted_at": "2023-12-01T10:30:00Z",
                "status": "pending"
            }
        ]
        return {"requests": requests}
    except Exception as e:
        logger.error(f"Failed to get legacy queue: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/admin/legacy/approve")
async def approve_legacy_certificate(approval_data: dict):
    """Approve a legacy certificate verification"""
    try:
        request_id = approval_data.get("request_id")
        admin_notes = approval_data.get("admin_notes", "")
        
        # Mock implementation
        return {
            "success": True,
            "message": "Legacy certificate approved and QR code generated",
            "request_id": request_id,
            "certificate_id": f"cert_{request_id}"
        }
    except Exception as e:
        logger.error(f"Failed to approve legacy certificate: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/admin/legacy/reject")
async def reject_legacy_certificate(rejection_data: dict):
    """Reject a legacy certificate verification"""
    try:
        request_id = rejection_data.get("request_id")
        rejection_reason = rejection_data.get("rejection_reason", "")
        
        # Mock implementation
        return {
            "success": True,
            "message": "Legacy certificate verification rejected",
            "request_id": request_id
        }
    except Exception as e:
        logger.error(f"Failed to reject legacy certificate: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
