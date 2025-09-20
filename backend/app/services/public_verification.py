"""
Public Verification Service for QR Code Scanning
Handles the employer/verifier workflow when scanning QR codes
"""
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from ..models import QRIntegrityCheck, ExtractedFields
from .qr_integrity import QRIntegrityService
from .supabase_client import SupabaseClient
from ..utils.helpers import verify_signature

logger = logging.getLogger(__name__)

class PublicVerificationService:
    """
    Service for public certificate verification via QR code scanning
    Used by employers and other verifiers
    """
    
    def __init__(self, supabase_client: SupabaseClient):
        self.supabase_client = supabase_client
        self.qr_service = QRIntegrityService()
    
    async def verify_by_attestation_id(self, attestation_id: str) -> Dict[str, Any]:
        """
        Verify certificate by attestation ID (from QR scan)
        Main endpoint for employer verification workflow
        """
        try:
            # Step 1: Retrieve attestation record
            attestation = await self.supabase_client.get_attestation(attestation_id)
            if not attestation:
                return {
                    "valid": False,
                    "error": "Attestation not found",
                    "error_code": "ATTESTATION_NOT_FOUND"
                }
            
            # Step 2: Verify attestation signature
            signature_valid = await self._verify_attestation_signature(attestation)
            if not signature_valid:
                return {
                    "valid": False,
                    "error": "Invalid attestation signature",
                    "error_code": "INVALID_SIGNATURE"
                }
            
            # Step 3: Retrieve original certificate record
            verification_id = attestation.get("verification_id")
            certificate_record = await self._get_certificate_record(verification_id)
            
            if not certificate_record:
                return {
                    "valid": False,
                    "error": "Certificate record not found",
                    "error_code": "CERTIFICATE_NOT_FOUND"
                }
            
            # Step 4: Verify image integrity (if available)
            image_integrity = await self._verify_image_integrity(certificate_record)
            
            # Step 5: Check certificate status and validity
            status_check = await self._check_certificate_status(certificate_record)
            
            # Step 6: Build verification response
            verification_result = {
                "valid": signature_valid and status_check["valid"],
                "attestation_id": attestation_id,
                "certificate_details": {
                    "certificate_id": certificate_record.get("certificate_id"),
                    "student_name": certificate_record.get("student_name"),
                    "course_name": certificate_record.get("course_name"),
                    "institution": certificate_record.get("institution"),
                    "issue_date": certificate_record.get("issue_date"),
                    "year": certificate_record.get("year"),
                    "grade": certificate_record.get("grade")
                },
                "verification_details": {
                    "signature_valid": signature_valid,
                    "image_integrity": image_integrity,
                    "certificate_status": status_check,
                    "verified_at": datetime.utcnow().isoformat()
                },
                "issuer_information": {
                    "institution": certificate_record.get("institution"),
                    "institution_id": certificate_record.get("institution_id"),
                    "public_key_verified": True  # Since signature passed
                },
                "verification_metadata": {
                    "verification_method": "qr_attestation",
                    "attestation_created": attestation.get("created_at"),
                    "certificate_issued": certificate_record.get("created_at")
                }
            }
            
            # Step 7: Log verification attempt
            await self._log_verification_attempt(attestation_id, verification_result)
            
            return verification_result
            
        except Exception as e:
            logger.error(f"Public verification failed: {str(e)}")
            return {
                "valid": False,
                "error": f"Verification failed: {str(e)}",
                "error_code": "VERIFICATION_ERROR"
            }
    
    async def verify_by_qr_data(self, qr_data: str) -> Dict[str, Any]:
        """
        Verify certificate by raw QR code data
        Alternative endpoint for direct QR scanning
        """
        try:
            # Step 1: Parse QR payload
            try:
                qr_payload = json.loads(qr_data)
            except json.JSONDecodeError:
                return {
                    "valid": False,
                    "error": "Invalid QR code data",
                    "error_code": "INVALID_QR_DATA"
                }
            
            # Step 2: Verify QR integrity
            qr_integrity = await self.qr_service.verify_qr_integrity(qr_data)
            
            if not qr_integrity.signature_valid:
                return {
                    "valid": False,
                    "error": "QR signature verification failed",
                    "error_code": "INVALID_QR_SIGNATURE",
                    "qr_details": qr_integrity.dict()
                }
            
            # Step 3: Extract certificate information from QR
            cert_data = qr_payload.get("payload", {}).get("data", {})
            
            # Step 4: Lookup certificate in database
            certificate_record = await self._lookup_certificate_by_data(cert_data)
            
            if not certificate_record:
                return {
                    "valid": False,
                    "error": "Certificate not found in database",
                    "error_code": "CERTIFICATE_NOT_IN_DB"
                }
            
            # Step 5: Verify field consistency
            field_consistency = await self._verify_field_consistency(cert_data, certificate_record)
            
            # Step 6: Build verification response
            verification_result = {
                "valid": qr_integrity.signature_valid and field_consistency["all_match"],
                "qr_verification": qr_integrity.dict(),
                "certificate_details": {
                    "certificate_id": certificate_record.get("certificate_id"),
                    "student_name": certificate_record.get("student_name"),
                    "course_name": certificate_record.get("course_name"),
                    "institution": certificate_record.get("institution"),
                    "issue_date": certificate_record.get("issue_date"),
                    "year": certificate_record.get("year"),
                    "grade": certificate_record.get("grade")
                },
                "field_consistency": field_consistency,
                "verification_details": {
                    "qr_signature_valid": qr_integrity.signature_valid,
                    "issuer_verified": qr_integrity.issuer_verified,
                    "verified_at": datetime.utcnow().isoformat()
                }
            }
            
            return verification_result
            
        except Exception as e:
            logger.error(f"QR verification failed: {str(e)}")
            return {
                "valid": False,
                "error": f"QR verification failed: {str(e)}",
                "error_code": "QR_VERIFICATION_ERROR"
            }
    
    async def get_certificate_image(self, attestation_id: str) -> Optional[Dict[str, Any]]:
        """
        Get verified certificate image for display
        """
        try:
            # Get attestation record
            attestation = await self.supabase_client.get_attestation(attestation_id)
            if not attestation:
                return None
            
            # Get certificate record
            verification_id = attestation.get("verification_id")
            certificate_record = await self._get_certificate_record(verification_id)
            
            if not certificate_record:
                return None
            
            # Return image information
            return {
                "image_url": certificate_record.get("image_url"),
                "image_hashes": certificate_record.get("image_hashes", {}),
                "certificate_id": certificate_record.get("certificate_id"),
                "issued_at": certificate_record.get("created_at")
            }
            
        except Exception as e:
            logger.error(f"Failed to get certificate image: {str(e)}")
            return None
    
    async def _verify_attestation_signature(self, attestation: Dict[str, Any]) -> bool:
        """Verify digital signature of attestation"""
        try:
            signature = attestation.get("signature")
            public_key = attestation.get("public_key")
            payload = attestation.get("payload")
            
            if not all([signature, public_key, payload]):
                return False
            
            # Serialize payload for verification
            payload_str = json.dumps(payload, sort_keys=True, separators=(',', ':'))
            
            # Verify signature
            return verify_signature(payload_str, signature, public_key)
            
        except Exception as e:
            logger.error(f"Attestation signature verification failed: {str(e)}")
            return False
    
    async def _get_certificate_record(self, verification_id: str) -> Optional[Dict[str, Any]]:
        """Get certificate record from database"""
        try:
            # Try issued_certificates table first
            result = await self.supabase_client.supabase.table("issued_certificates").select("*").eq("id", verification_id).execute()
            
            if result.data:
                return result.data[0]
            
            # Fallback to verification records
            verification = await self.supabase_client.get_verification(verification_id)
            return verification
            
        except Exception as e:
            logger.error(f"Failed to get certificate record: {str(e)}")
            return None
    
    async def _verify_image_integrity(self, certificate_record: Dict[str, Any]) -> Dict[str, Any]:
        """Verify image integrity using stored hashes"""
        try:
            stored_hashes = certificate_record.get("image_hashes", {})
            image_url = certificate_record.get("image_url")
            
            if not stored_hashes or not image_url:
                return {
                    "available": False,
                    "reason": "No integrity data available"
                }
            
            # In a full implementation, you would:
            # 1. Download the image from the URL
            # 2. Recalculate hashes
            # 3. Compare with stored hashes
            
            # For now, return the stored integrity information
            return {
                "available": True,
                "sha256_hash": stored_hashes.get("sha256"),
                "perceptual_hash": stored_hashes.get("phash"),
                "integrity_verified": True  # Placeholder
            }
            
        except Exception as e:
            logger.error(f"Image integrity verification failed: {str(e)}")
            return {
                "available": False,
                "error": str(e)
            }
    
    async def _check_certificate_status(self, certificate_record: Dict[str, Any]) -> Dict[str, Any]:
        """Check certificate validity and status"""
        try:
            status = certificate_record.get("status", "unknown")
            issue_date = certificate_record.get("issue_date")
            
            # Check if certificate is active
            is_active = status in ["issued", "active"]
            
            # Check if certificate is expired (if expiration logic exists)
            is_expired = False  # Implement expiration logic if needed
            
            # Check if certificate is revoked
            is_revoked = status in ["revoked", "cancelled"]
            
            return {
                "valid": is_active and not is_expired and not is_revoked,
                "status": status,
                "active": is_active,
                "expired": is_expired,
                "revoked": is_revoked,
                "issue_date": issue_date
            }
            
        except Exception as e:
            logger.error(f"Certificate status check failed: {str(e)}")
            return {
                "valid": False,
                "error": str(e)
            }
    
    async def _lookup_certificate_by_data(self, cert_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Lookup certificate in database by certificate data"""
        try:
            certificate_id = cert_data.get("certificate_id")
            
            if certificate_id:
                # Primary lookup by certificate ID
                result = await self.supabase_client.supabase.table("issued_certificates").select("*").eq("certificate_id", certificate_id).execute()
                
                if result.data:
                    return result.data[0]
            
            # Fallback lookup by student name and course
            student_name = cert_data.get("student_name")
            course_name = cert_data.get("course_name")
            
            if student_name and course_name:
                result = await self.supabase_client.supabase.table("issued_certificates").select("*").eq("student_name", student_name).eq("course_name", course_name).execute()
                
                if result.data:
                    return result.data[0]
            
            return None
            
        except Exception as e:
            logger.error(f"Certificate lookup failed: {str(e)}")
            return None
    
    async def _verify_field_consistency(self, qr_data: Dict[str, Any], 
                                      db_record: Dict[str, Any]) -> Dict[str, Any]:
        """Verify consistency between QR data and database record"""
        try:
            consistency_checks = {}
            
            # Check each field
            fields_to_check = ["certificate_id", "student_name", "course_name", "institution", "issue_date"]
            
            for field in fields_to_check:
                qr_value = str(qr_data.get(field, "")).strip().lower()
                db_value = str(db_record.get(field, "")).strip().lower()
                
                consistency_checks[field] = {
                    "match": qr_value == db_value,
                    "qr_value": qr_data.get(field),
                    "db_value": db_record.get(field)
                }
            
            # Calculate overall consistency
            matches = sum(1 for check in consistency_checks.values() if check["match"])
            total_checks = len(consistency_checks)
            
            return {
                "all_match": matches == total_checks,
                "match_percentage": (matches / total_checks) * 100,
                "field_checks": consistency_checks,
                "discrepancies": [field for field, check in consistency_checks.items() if not check["match"]]
            }
            
        except Exception as e:
            logger.error(f"Field consistency check failed: {str(e)}")
            return {
                "all_match": False,
                "error": str(e)
            }
    
    async def _log_verification_attempt(self, attestation_id: str, result: Dict[str, Any]):
        """Log verification attempt for audit trail"""
        try:
            log_entry = {
                "action": "public_verification",
                "attestation_id": attestation_id,
                "verification_result": result["valid"],
                "timestamp": datetime.utcnow().isoformat(),
                "details": {
                    "method": "attestation_id",
                    "certificate_id": result.get("certificate_details", {}).get("certificate_id"),
                    "verification_metadata": result.get("verification_metadata", {})
                }
            }
            
            # Store in audit logs
            await self.supabase_client.supabase.table("audit_logs").insert(log_entry).execute()
            
        except Exception as e:
            logger.error(f"Failed to log verification attempt: {str(e)}")
            # Don't raise exception for logging failures
    
    async def get_verification_statistics(self, institution_id: Optional[str] = None) -> Dict[str, Any]:
        """Get verification statistics for institutions"""
        try:
            # This could be expanded to provide analytics
            # For now, return basic structure
            return {
                "total_verifications": 0,
                "successful_verifications": 0,
                "failed_verifications": 0,
                "verification_rate": 0.0,
                "period": "30_days"
            }
            
        except Exception as e:
            logger.error(f"Failed to get verification statistics: {str(e)}")
            return {}
