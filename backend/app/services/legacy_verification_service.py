"""
Legacy Certificate Verification Service
"""
import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from ..legacy_models import (
    LegacyVerificationRequest, 
    LegacyStatus, 
    LegacyReviewAction, 
    LegacyVerificationResult,
    LegacyCertificateSearch
)
from ..auth_models import UserProfile
from .supabase_client import SupabaseClient
from .certificate_issuance import CertificateIssuanceService
from .qr_integrity import QRIntegrityService

logger = logging.getLogger(__name__)

class LegacyVerificationService:
    def __init__(self, supabase_client: SupabaseClient):
        self.supabase_client = supabase_client
        self.issuance_service = CertificateIssuanceService(supabase_client, QRIntegrityService())
    
    async def submit_legacy_request(self, request_data: Dict[str, Any], student_user: UserProfile) -> LegacyVerificationRequest:
        """Submit a legacy certificate verification request"""
        try:
            request_id = str(uuid.uuid4())
            
            # Create legacy verification request
            legacy_request = LegacyVerificationRequest(
                request_id=request_id,
                student_name=request_data["student_name"],
                student_email=request_data["student_email"],
                roll_no=request_data["roll_no"],
                course_name=request_data["course_name"],
                year=request_data["year"],
                institution=request_data["institution"],
                certificate_image_url=request_data["certificate_image_url"],
                certificate_filename=request_data["certificate_filename"],
                file_size=request_data["file_size"],
                status=LegacyStatus.PENDING,
                submitted_at=datetime.utcnow(),
                additional_info=request_data.get("additional_info", {})
            )
            
            # Store in database
            await self._store_legacy_request(legacy_request)
            
            # Log audit event
            await self.supabase_client.log_audit_event(
                action="legacy_request_submitted",
                user_id=student_user.user_id,
                details={
                    "request_id": request_id,
                    "institution": request_data["institution"],
                    "course": request_data["course_name"]
                }
            )
            
            return legacy_request
            
        except Exception as e:
            logger.error(f"Error submitting legacy request: {str(e)}")
            raise
    
    async def get_pending_requests(self, institution_id: Optional[str] = None) -> List[LegacyVerificationRequest]:
        """Get pending legacy verification requests"""
        try:
            query = self.supabase_client.client.table("legacy_verification_requests").select("*")
            
            if institution_id:
                query = query.eq("institution", institution_id)
            
            query = query.eq("status", LegacyStatus.PENDING).order("submitted_at", desc=False)
            
            result = query.execute()
            
            requests = []
            for data in result.data:
                requests.append(LegacyVerificationRequest(
                    request_id=data["request_id"],
                    student_name=data["student_name"],
                    student_email=data["student_email"],
                    roll_no=data["roll_no"],
                    course_name=data["course_name"],
                    year=data["year"],
                    institution=data["institution"],
                    certificate_image_url=data["certificate_image_url"],
                    certificate_filename=data["certificate_filename"],
                    file_size=data["file_size"],
                    status=LegacyStatus(data["status"]),
                    submitted_at=datetime.fromisoformat(data["submitted_at"]),
                    reviewed_at=datetime.fromisoformat(data["reviewed_at"]) if data.get("reviewed_at") else None,
                    reviewer_id=data.get("reviewer_id"),
                    review_notes=data.get("review_notes"),
                    rejection_reason=data.get("rejection_reason"),
                    additional_info=data.get("additional_info", {})
                ))
            
            return requests
            
        except Exception as e:
            logger.error(f"Error getting pending requests: {str(e)}")
            return []
    
    async def review_legacy_request(self, action: LegacyReviewAction, reviewer: UserProfile) -> LegacyVerificationResult:
        """Review a legacy verification request"""
        try:
            # Get the request
            request = await self._get_legacy_request(action.request_id)
            if not request:
                raise ValueError("Legacy request not found")
            
            if request.status != LegacyStatus.PENDING:
                raise ValueError("Request is not pending review")
            
            # Update request status
            updated_request = LegacyVerificationRequest(
                **request.dict(),
                status=LegacyStatus.UNDER_REVIEW if action.action == "approve" else LegacyStatus.REJECTED,
                reviewed_at=datetime.utcnow(),
                reviewer_id=reviewer.user_id,
                review_notes=action.notes,
                rejection_reason=action.rejection_reason if action.action == "reject" else None
            )
            
            await self._update_legacy_request(updated_request)
            
            result = LegacyVerificationResult(
                request_id=action.request_id,
                status=updated_request.status,
                original_filename=request.certificate_filename,
                processing_notes=action.notes
            )
            
            # If approved, generate new digital certificate
            if action.action == "approve":
                try:
                    # Create certificate data for issuance
                    certificate_data = {
                        "student_name": request.student_name,
                        "certificate_id": f"LEGACY-{request.request_id}",
                        "course_name": request.course_name,
                        "institution": request.institution,
                        "issue_date": datetime.utcnow().strftime("%Y-%m-%d"),
                        "year": request.year,
                        "image_data_base64": None,  # Will use uploaded image
                        "image_url": request.certificate_image_url,
                        "source": "legacy_verified"
                    }
                    
                    # Issue new digital certificate
                    issuance_result = await self.issuance_service.issue_certificate(
                        certificate_data, 
                        reviewer.institution_id or "legacy"
                    )
                    
                    result.attestation_id = issuance_result["attestation_id"]
                    result.qr_code_url = issuance_result["qr_code_url"]
                    result.verified_certificate_url = request.certificate_image_url
                    result.verified_fields = certificate_data
                    result.verification_date = datetime.utcnow()
                    
                    # Update request with attestation info
                    updated_request.status = LegacyStatus.APPROVED
                    await self._update_legacy_request(updated_request)
                    
                except Exception as e:
                    logger.error(f"Error issuing digital certificate for legacy: {str(e)}")
                    result.processing_notes = f"Legacy verification approved but digital certificate generation failed: {str(e)}"
            
            # Log audit event
            await self.supabase_client.log_audit_event(
                action="legacy_request_reviewed",
                user_id=reviewer.user_id,
                details={
                    "request_id": action.request_id,
                    "action": action.action,
                    "attestation_id": result.attestation_id
                }
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error reviewing legacy request: {str(e)}")
            raise
    
    async def get_student_requests(self, student_user: UserProfile) -> List[LegacyVerificationRequest]:
        """Get legacy requests for a specific student"""
        try:
            result = self.supabase_client.client.table("legacy_verification_requests").select("*").eq(
                "student_email", student_user.email
            ).order("submitted_at", desc=True).execute()
            
            requests = []
            for data in result.data:
                requests.append(LegacyVerificationRequest(
                    request_id=data["request_id"],
                    student_name=data["student_name"],
                    student_email=data["student_email"],
                    roll_no=data["roll_no"],
                    course_name=data["course_name"],
                    year=data["year"],
                    institution=data["institution"],
                    certificate_image_url=data["certificate_image_url"],
                    certificate_filename=data["certificate_filename"],
                    file_size=data["file_size"],
                    status=LegacyStatus(data["status"]),
                    submitted_at=datetime.fromisoformat(data["submitted_at"]),
                    reviewed_at=datetime.fromisoformat(data["reviewed_at"]) if data.get("reviewed_at") else None,
                    reviewer_id=data.get("reviewer_id"),
                    review_notes=data.get("review_notes"),
                    rejection_reason=data.get("rejection_reason"),
                    additional_info=data.get("additional_info", {})
                ))
            
            return requests
            
        except Exception as e:
            logger.error(f"Error getting student requests: {str(e)}")
            return []
    
    async def search_legacy_certificates(self, search_criteria: LegacyCertificateSearch) -> List[Dict[str, Any]]:
        """Search legacy certificates in database"""
        try:
            query = self.supabase_client.client.table("legacy_verification_requests").select("*")
            
            if search_criteria.student_name:
                query = query.ilike("student_name", f"%{search_criteria.student_name}%")
            if search_criteria.roll_no:
                query = query.eq("roll_no", search_criteria.roll_no)
            if search_criteria.course_name:
                query = query.ilike("course_name", f"%{search_criteria.course_name}%")
            if search_criteria.year:
                query = query.eq("year", search_criteria.year)
            if search_criteria.institution:
                query = query.ilike("institution", f"%{search_criteria.institution}%")
            
            result = query.execute()
            return result.data
            
        except Exception as e:
            logger.error(f"Error searching legacy certificates: {str(e)}")
            return []
    
    async def _store_legacy_request(self, request: LegacyVerificationRequest):
        """Store legacy verification request in database"""
        try:
            result = self.supabase_client.client.table("legacy_verification_requests").insert({
                "request_id": request.request_id,
                "student_name": request.student_name,
                "student_email": request.student_email,
                "roll_no": request.roll_no,
                "course_name": request.course_name,
                "year": request.year,
                "institution": request.institution,
                "certificate_image_url": request.certificate_image_url,
                "certificate_filename": request.certificate_filename,
                "file_size": request.file_size,
                "status": request.status,
                "submitted_at": request.submitted_at.isoformat(),
                "additional_info": request.additional_info
            }).execute()
            
            if not result.data:
                raise Exception("Failed to store legacy request")
                
        except Exception as e:
            logger.error(f"Error storing legacy request: {str(e)}")
            raise
    
    async def _get_legacy_request(self, request_id: str) -> Optional[LegacyVerificationRequest]:
        """Get legacy verification request by ID"""
        try:
            result = self.supabase_client.client.table("legacy_verification_requests").select("*").eq(
                "request_id", request_id
            ).execute()
            
            if not result.data:
                return None
            
            data = result.data[0]
            return LegacyVerificationRequest(
                request_id=data["request_id"],
                student_name=data["student_name"],
                student_email=data["student_email"],
                roll_no=data["roll_no"],
                course_name=data["course_name"],
                year=data["year"],
                institution=data["institution"],
                certificate_image_url=data["certificate_image_url"],
                certificate_filename=data["certificate_filename"],
                file_size=data["file_size"],
                status=LegacyStatus(data["status"]),
                submitted_at=datetime.fromisoformat(data["submitted_at"]),
                reviewed_at=datetime.fromisoformat(data["reviewed_at"]) if data.get("reviewed_at") else None,
                reviewer_id=data.get("reviewer_id"),
                review_notes=data.get("review_notes"),
                rejection_reason=data.get("rejection_reason"),
                additional_info=data.get("additional_info", {})
            )
            
        except Exception as e:
            logger.error(f"Error getting legacy request: {str(e)}")
            return None
    
    async def _update_legacy_request(self, request: LegacyVerificationRequest):
        """Update legacy verification request"""
        try:
            result = self.supabase_client.client.table("legacy_verification_requests").update({
                "status": request.status,
                "reviewed_at": request.reviewed_at.isoformat() if request.reviewed_at else None,
                "reviewer_id": request.reviewer_id,
                "review_notes": request.review_notes,
                "rejection_reason": request.rejection_reason
            }).eq("request_id", request.request_id).execute()
            
            if not result.data:
                raise Exception("Failed to update legacy request")
                
        except Exception as e:
            logger.error(f"Error updating legacy request: {str(e)}")
            raise
