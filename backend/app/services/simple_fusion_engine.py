"""
Simplified Fusion Engine using Gemini API for certificate verification
Replaces complex multi-layer approach with AI-powered extraction
"""
import logging
from typing import Dict, Any, Optional
from .gemini_extraction import gemini_extraction_service
from .supabase_client import SupabaseClient

logger = logging.getLogger(__name__)

class SimpleFusionEngine:
    """Simplified fusion engine using Gemini API for certificate processing"""
    
    def __init__(self, supabase_client: SupabaseClient):
        self.supabase_client = supabase_client
        self.gemini_service = gemini_extraction_service
        
    async def verify_certificate(self, image_data: bytes) -> Dict[str, Any]:
        """
        Verify certificate using Gemini AI extraction
        
        Args:
            image_data: Raw image bytes
            
        Returns:
            Dictionary containing verification results
        """
        try:
            logger.info("Starting certificate verification with Gemini AI")
            
            # Extract data using Gemini
            extraction_result = self.gemini_service.extract_certificate_data(image_data)
            
            if not extraction_result["success"]:
                return {
                    "success": False,
                    "error": extraction_result["error"],
                    "verification_status": "failed",
                    "confidence": 0.0
                }
            
            extracted_data = extraction_result["data"]
            
            # Basic validation of extracted data
            validation_result = self._validate_extracted_data(extracted_data)
            
            # Store in database
            try:
                certificate_id = await self._store_certificate(extracted_data, image_data)
                logger.info(f"Certificate stored with ID: {certificate_id}")
            except Exception as e:
                logger.error(f"Failed to store certificate: {e}")
                certificate_id = None
            
            # Calculate confidence score based on extracted fields
            confidence = self._calculate_confidence(extracted_data, validation_result)
            
            return {
                "success": True,
                "verification_status": "verified" if confidence > 0.7 else "needs_review",
                "confidence": confidence,
                "extracted_data": extracted_data,
                "certificate_id": certificate_id,
                "validation_results": validation_result,
                "raw_ai_response": extraction_result.get("raw_response")
            }
            
        except Exception as e:
            logger.error(f"Error in certificate verification: {e}")
            return {
                "success": False,
                "error": f"Verification failed: {str(e)}",
                "verification_status": "failed",
                "confidence": 0.0
            }
    
    async def verify_certificate_by_data(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verify certificate using provided data (for manual input)
        
        Args:
            request_data: Dictionary containing certificate data
            
        Returns:
            Dictionary containing verification results
        """
        try:
            logger.info("Verifying certificate with provided data")
            
            # Validate the provided data
            validation_result = self._validate_extracted_data(request_data)
            
            # Store in database
            try:
                certificate_id = await self._store_certificate(request_data, None)
                logger.info(f"Certificate stored with ID: {certificate_id}")
            except Exception as e:
                logger.error(f"Failed to store certificate: {e}")
                certificate_id = None
            
            # Calculate confidence
            confidence = self._calculate_confidence(request_data, validation_result)
            
            return {
                "success": True,
                "verification_status": "verified" if confidence > 0.7 else "needs_review",
                "confidence": confidence,
                "extracted_data": request_data,
                "certificate_id": certificate_id,
                "validation_results": validation_result
            }
            
        except Exception as e:
            logger.error(f"Error in manual verification: {e}")
            return {
                "success": False,
                "error": f"Verification failed: {str(e)}",
                "verification_status": "failed",
                "confidence": 0.0
            }
    
    def _validate_extracted_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate extracted certificate data"""
        validation_results = {
            "has_name": bool(data.get("name")),
            "has_roll_no": bool(data.get("roll_no")),
            "has_certificate_no": bool(data.get("certificate_no")),
            "has_course": bool(data.get("course")),
            "has_date_info": bool(data.get("month") or data.get("year")),
            "has_grade": bool(data.get("grade")),
            "has_institution": bool(data.get("institution")),
            "valid_year": self._is_valid_year(data.get("year")),
            "valid_grade": self._is_valid_grade(data.get("grade"))
        }
        
        # Calculate validation score
        total_fields = len(validation_results)
        valid_fields = sum(1 for valid in validation_results.values() if valid)
        validation_results["score"] = valid_fields / total_fields
        
        return validation_results
    
    def _is_valid_year(self, year: Any) -> bool:
        """Check if year is valid"""
        if not year:
            return False
        try:
            year_int = int(str(year))
            return 1900 <= year_int <= 2030
        except (ValueError, TypeError):
            return False
    
    def _is_valid_grade(self, grade: Any) -> bool:
        """Check if grade is valid"""
        if not grade:
            return False
        grade_str = str(grade).upper()
        valid_grades = ["A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D", "F", "PASS", "FAIL"]
        return grade_str in valid_grades or grade_str.isdigit()
    
    def _calculate_confidence(self, data: Dict[str, Any], validation: Dict[str, Any]) -> float:
        """Calculate confidence score for the verification"""
        base_score = validation["score"]
        
        # Bonus for having critical fields
        if validation["has_name"] and validation["has_course"]:
            base_score += 0.1
        
        if validation["has_certificate_no"]:
            base_score += 0.1
            
        if validation["valid_year"]:
            base_score += 0.1
            
        return min(base_score, 1.0)
    
    async def _store_certificate(self, data: Dict[str, Any], image_data: Optional[bytes]) -> str:
        """Store certificate data in database"""
        try:
            # Prepare certificate data for storage
            certificate_data = {
                "name": data.get("name"),
                "roll_no": data.get("roll_no"),
                "certificate_no": data.get("certificate_no"),
                "course": data.get("course"),
                "month": data.get("month"),
                "year": data.get("year"),
                "grade": data.get("grade"),
                "institution": data.get("institution"),
                "issued_date": data.get("issued_date"),
                "verification_status": "pending",
                "extraction_method": "gemini_ai"
            }
            
            # Store in Supabase
            result = await self.supabase_client.store_certificate(certificate_data)
            return result.get("id") if result else None
            
        except Exception as e:
            logger.error(f"Error storing certificate: {e}")
            raise e
