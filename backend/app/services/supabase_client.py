"""
Supabase PostgREST & Storage API client
"""
import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import hashlib
import json

from supabase import create_client, Client
from PIL import Image
import io

from ..config import settings
from ..models import (
    CertificateResponse, ExtractedFields, VerificationStatus, 
    RiskScore, AttestationData, InstitutionData, AuditLog
)

logger = logging.getLogger(__name__)

class SupabaseClient:
    """Client for Supabase database and storage operations"""
    
    def __init__(self):
        self.client: Client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_ANON_KEY
        )
        self.storage_bucket = settings.STORAGE_BUCKET
    
    async def store_verification(self, verification_data: Dict[str, Any]) -> str:
        """Store verification result in database"""
        try:
            result = self.client.table("verifications").insert(verification_data).execute()
            
            if result.data:
                verification_id = result.data[0]["id"]
                logger.info(f"Stored verification: {verification_id}")
                return verification_id
            else:
                raise Exception("Failed to store verification")
                
        except Exception as e:
            logger.error(f"Error storing verification: {str(e)}")
            raise
    
    async def get_verification(self, verification_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve verification by ID"""
        try:
            result = self.client.table("verifications").select("*").eq("id", verification_id).execute()
            
            if result.data:
                return result.data[0]
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving verification {verification_id}: {str(e)}")
            return None
    
    async def upload_certificate_image(self, image_data: bytes, filename: str) -> str:
        """Upload certificate image to Supabase Storage"""
        try:
            # Generate unique filename with hash
            image_hash = hashlib.sha256(image_data).hexdigest()[:16]
            storage_path = f"certificates/{image_hash}_{filename}"
            
            # Upload to storage bucket
            result = self.client.storage.from_(self.storage_bucket).upload(
                storage_path, 
                image_data,
                file_options={"content-type": "image/jpeg"}
            )
            
            if result.status_code == 200:
                # Get public URL
                public_url = self.client.storage.from_(self.storage_bucket).get_public_url(storage_path)
                logger.info(f"Uploaded image: {storage_path}")
                return public_url
            else:
                raise Exception(f"Upload failed: {result.status_code}")
                
        except Exception as e:
            logger.error(f"Error uploading image: {str(e)}")
            raise
    
    async def store_attestation(self, attestation_data: Dict[str, Any]) -> str:
        """Store attestation data"""
        try:
            result = self.client.table("attestations").insert(attestation_data).execute()
            
            if result.data:
                attestation_id = result.data[0]["id"]
                logger.info(f"Stored attestation: {attestation_id}")
                return attestation_id
            else:
                raise Exception("Failed to store attestation")
                
        except Exception as e:
            logger.error(f"Error storing attestation: {str(e)}")
            raise
    
    async def get_attestation(self, attestation_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve attestation by ID"""
        try:
            result = self.client.table("attestations").select("*").eq("id", attestation_id).execute()
            
            if result.data:
                return result.data[0]
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving attestation {attestation_id}: {str(e)}")
            return None
    
    async def check_certificate_database(self, extracted_fields: ExtractedFields) -> Dict[str, Any]:
        """Check against issued certificates database"""
        try:
            query = self.client.table("issued_certificates").select("*")
            
            # Build query based on available fields
            if extracted_fields.certificate_id:
                query = query.eq("certificate_id", extracted_fields.certificate_id)
            elif extracted_fields.name and extracted_fields.course_name:
                query = query.eq("student_name", extracted_fields.name).eq("course_name", extracted_fields.course_name)
            else:
                return {"match_found": False, "confidence": 0.0}
            
            result = query.execute()
            
            if result.data:
                # Found potential match
                match = result.data[0]
                confidence = self._calculate_match_confidence(extracted_fields, match)
                
                return {
                    "match_found": True,
                    "confidence": confidence,
                    "database_record": match,
                    "discrepancies": self._find_discrepancies(extracted_fields, match)
                }
            else:
                return {"match_found": False, "confidence": 0.0}
                
        except Exception as e:
            logger.error(f"Error checking certificate database: {str(e)}")
            return {"match_found": False, "confidence": 0.0, "error": str(e)}
    
    def _calculate_match_confidence(self, extracted: ExtractedFields, database_record: Dict[str, Any]) -> float:
        """Calculate confidence score for database match"""
        total_fields = 0
        matching_fields = 0
        
        field_mappings = {
            "name": "student_name",
            "course_name": "course_name",
            "institution": "institution",
            "issue_date": "issue_date",
            "certificate_id": "certificate_id"
        }
        
        for extracted_field, db_field in field_mappings.items():
            extracted_value = getattr(extracted, extracted_field)
            db_value = database_record.get(db_field)
            
            if extracted_value and db_value:
                total_fields += 1
                if str(extracted_value).lower().strip() == str(db_value).lower().strip():
                    matching_fields += 1
        
        return matching_fields / total_fields if total_fields > 0 else 0.0
    
    def _find_discrepancies(self, extracted: ExtractedFields, database_record: Dict[str, Any]) -> List[str]:
        """Find discrepancies between extracted and database fields"""
        discrepancies = []
        
        field_mappings = {
            "name": "student_name",
            "course_name": "course_name", 
            "institution": "institution",
            "issue_date": "issue_date"
        }
        
        for extracted_field, db_field in field_mappings.items():
            extracted_value = getattr(extracted, extracted_field)
            db_value = database_record.get(db_field)
            
            if extracted_value and db_value:
                if str(extracted_value).lower().strip() != str(db_value).lower().strip():
                    discrepancies.append(f"{extracted_field}: '{extracted_value}' vs '{db_value}'")
        
        return discrepancies
    
    async def store_institution(self, institution_data: InstitutionData) -> str:
        """Store institution information"""
        try:
            data = institution_data.dict()
            result = self.client.table("institutions").insert(data).execute()
            
            if result.data:
                return result.data[0]["id"]
            else:
                raise Exception("Failed to store institution")
                
        except Exception as e:
            logger.error(f"Error storing institution: {str(e)}")
            raise
    
    async def get_institution_by_domain(self, domain: str) -> Optional[InstitutionData]:
        """Get institution by email domain"""
        try:
            result = self.client.table("institutions").select("*").eq("domain", domain).execute()
            
            if result.data:
                return InstitutionData(**result.data[0])
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving institution by domain {domain}: {str(e)}")
            return None
    
    async def log_audit_event(self, audit_log: AuditLog):
        """Log audit event"""
        try:
            data = audit_log.dict()
            data["timestamp"] = data["timestamp"].isoformat()
            
            self.client.table("audit_logs").insert(data).execute()
            logger.debug(f"Logged audit event: {audit_log.action}")
            
        except Exception as e:
            logger.error(f"Error logging audit event: {str(e)}")
    
    async def get_certificate(self, certificate_id: str) -> Optional[Dict[str, Any]]:
        """Get certificate details by ID from issued certificates"""
        try:
            result = self.client.table("issued_certificates").select("*").eq("certificate_id", certificate_id).execute()
            
            if result.data:
                return result.data[0]
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving certificate {certificate_id}: {str(e)}")
            return None
    
    async def import_certificates_batch(self, certificates: List[Dict[str, Any]]) -> int:
        """Import multiple certificates in batch"""
        try:
            result = self.client.table("issued_certificates").insert(certificates).execute()
            
            if result.data:
                return len(result.data)
            return 0
            
        except Exception as e:
            logger.error(f"Error importing certificates batch: {str(e)}")
            raise
