"""
Fusion engine to combine Donut + legacy models + database matching
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import hashlib
import json

from ..models import (
    ExtractedFields, CertificateResponse, VerificationStatus, 
    RiskScore, RiskLevel, VerificationRequest, AttestationData
)
from .llm_client import LLMClient
from .supabase_client import SupabaseClient
from ..utils.helpers import generate_image_hash, create_qr_code, sign_data

logger = logging.getLogger(__name__)

class FusionEngine:
    """
    Combines multiple verification methods:
    1. Donut/LLM extraction
    2. Legacy OCR/pattern matching
    3. Database verification
    4. Risk scoring
    5. Attestation generation
    """
    
    def __init__(self, llm_client: LLMClient, supabase_client: SupabaseClient):
        self.llm_client = llm_client
        self.supabase_client = supabase_client
        
        # Risk scoring weights
        self.risk_weights = {
            "extraction_confidence": 0.3,
            "database_match": 0.4,
            "image_quality": 0.1,
            "field_consistency": 0.2
        }
    
    async def verify_certificate(self, image_data: bytes) -> CertificateResponse:
        """Main verification pipeline for uploaded certificate image"""
        verification_id = self._generate_verification_id(image_data)
        
        try:
            # Step 1: Extract fields using Donut/LLM
            from PIL import Image
            import io
            
            image = Image.open(io.BytesIO(image_data))
            extracted_fields = await self.llm_client.extract_certificate_fields(image)
            
            # Step 2: Legacy extraction (placeholder)
            legacy_fields = await self._legacy_extraction(image)
            
            # Step 3: Fuse extraction results
            fused_fields = self._fuse_extracted_fields(extracted_fields, legacy_fields)
            
            # Step 4: Database verification
            db_check = await self.supabase_client.check_certificate_database(fused_fields)
            
            # Step 5: Calculate risk score
            risk_score = await self._calculate_risk_score(
                fused_fields, db_check, image_data
            )
            
            # Step 6: Determine if manual review is needed
            requires_review = self._requires_manual_review(risk_score, db_check)
            
            # Step 7: Generate attestation if verified
            attestation = None
            status = VerificationStatus.VERIFIED
            
            if requires_review:
                status = VerificationStatus.REQUIRES_REVIEW
            elif risk_score.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
                status = VerificationStatus.FAILED
            else:
                attestation = await self._generate_attestation(
                    verification_id, fused_fields, image_data
                )
            
            # Step 8: Store verification result
            verification_data = {
                "id": verification_id,
                "status": status.value,
                "extracted_fields": fused_fields.dict(),
                "risk_score": risk_score.dict(),
                "database_check": db_check,
                "requires_manual_review": requires_review,
                "processed_at": datetime.utcnow().isoformat(),
                "image_hash": generate_image_hash(image_data)
            }
            
            await self.supabase_client.store_verification(verification_data)
            
            # Step 9: Upload image and get URL
            image_url = await self.supabase_client.upload_certificate_image(
                image_data, f"{verification_id}.jpg"
            )
            
            return CertificateResponse(
                verification_id=verification_id,
                status=status,
                extracted_fields=fused_fields,
                risk_score=risk_score,
                attestation=attestation,
                image_url=image_url,
                processed_at=datetime.utcnow(),
                requires_manual_review=requires_review
            )
            
        except Exception as e:
            logger.error(f"Error in verification pipeline: {str(e)}")
            
            # Store failed verification
            verification_data = {
                "id": verification_id,
                "status": VerificationStatus.FAILED.value,
                "error": str(e),
                "processed_at": datetime.utcnow().isoformat()
            }
            
            await self.supabase_client.store_verification(verification_data)
            
            raise Exception(f"Verification failed: {str(e)}")
    
    async def verify_certificate_by_data(self, request: VerificationRequest) -> CertificateResponse:
        """Verify certificate using manual input or existing data"""
        verification_id = self._generate_verification_id(
            request.certificate_id.encode() if request.certificate_id else b"manual"
        )
        
        try:
            extracted_fields = request.manual_fields or ExtractedFields()
            
            # Database verification
            db_check = await self.supabase_client.check_certificate_database(extracted_fields)
            
            # Calculate risk score (without image analysis)
            risk_score = await self._calculate_risk_score_manual(extracted_fields, db_check)
            
            # Determine status
            status = VerificationStatus.VERIFIED
            requires_review = False
            
            if not db_check.get("match_found", False):
                status = VerificationStatus.REQUIRES_REVIEW
                requires_review = True
            elif risk_score.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
                status = VerificationStatus.FAILED
            
            # Generate attestation if verified
            attestation = None
            if status == VerificationStatus.VERIFIED:
                attestation = await self._generate_attestation(
                    verification_id, extracted_fields, b""
                )
            
            return CertificateResponse(
                verification_id=verification_id,
                status=status,
                extracted_fields=extracted_fields,
                risk_score=risk_score,
                attestation=attestation,
                image_url=request.image_url,
                processed_at=datetime.utcnow(),
                requires_manual_review=requires_review
            )
            
        except Exception as e:
            logger.error(f"Error in manual verification: {str(e)}")
            raise Exception(f"Manual verification failed: {str(e)}")
    
    async def _legacy_extraction(self, image) -> ExtractedFields:
        """Placeholder for legacy OCR/pattern matching"""
        # This would integrate with existing legacy systems
        # For now, return empty fields
        return ExtractedFields()
    
    def _fuse_extracted_fields(self, donut_fields: ExtractedFields, legacy_fields: ExtractedFields) -> ExtractedFields:
        """Fuse results from multiple extraction methods"""
        # Simple fusion strategy: prefer Donut results, fallback to legacy
        fused = ExtractedFields()
        
        # Take best available field from each source
        fused.name = donut_fields.name or legacy_fields.name
        fused.institution = donut_fields.institution or legacy_fields.institution
        fused.course_name = donut_fields.course_name or legacy_fields.course_name
        fused.issue_date = donut_fields.issue_date or legacy_fields.issue_date
        fused.certificate_id = donut_fields.certificate_id or legacy_fields.certificate_id
        fused.grade = donut_fields.grade or legacy_fields.grade
        
        # Merge additional fields
        fused.additional_fields = {**legacy_fields.additional_fields, **donut_fields.additional_fields}
        
        return fused
    
    async def _calculate_risk_score(self, fields: ExtractedFields, db_check: Dict[str, Any], image_data: bytes) -> RiskScore:
        """Calculate comprehensive risk score"""
        scores = {}
        factors = []
        
        # Extraction confidence
        field_count = sum(1 for field in [fields.name, fields.institution, fields.course_name, fields.issue_date] if field)
        scores["extraction_confidence"] = field_count / 4.0
        
        if scores["extraction_confidence"] < 0.5:
            factors.append("Low field extraction confidence")
        
        # Database match score
        if db_check.get("match_found"):
            scores["database_match"] = db_check.get("confidence", 0.0)
            if db_check.get("discrepancies"):
                factors.extend([f"Discrepancy: {d}" for d in db_check["discrepancies"]])
        else:
            scores["database_match"] = 0.0
            factors.append("No database match found")
        
        # Image quality assessment (basic)
        scores["image_quality"] = await self._assess_image_quality(image_data)
        if scores["image_quality"] < 0.7:
            factors.append("Poor image quality")
        
        # Field consistency
        scores["field_consistency"] = self._check_field_consistency(fields)
        if scores["field_consistency"] < 0.7:
            factors.append("Inconsistent field formats")
        
        # Calculate weighted overall score
        overall_score = sum(
            scores[key] * self.risk_weights[key] 
            for key in scores.keys()
        )
        
        # Determine risk level
        if overall_score >= 0.8:
            risk_level = RiskLevel.LOW
        elif overall_score >= 0.6:
            risk_level = RiskLevel.MEDIUM
        elif overall_score >= 0.4:
            risk_level = RiskLevel.HIGH
        else:
            risk_level = RiskLevel.CRITICAL
        
        return RiskScore(
            overall_score=overall_score,
            confidence=min(scores["extraction_confidence"] + scores["database_match"], 1.0),
            risk_level=risk_level,
            factors=factors
        )
    
    async def _calculate_risk_score_manual(self, fields: ExtractedFields, db_check: Dict[str, Any]) -> RiskScore:
        """Calculate risk score for manual verification"""
        scores = {}
        factors = []
        
        # Field completeness
        field_count = sum(1 for field in [fields.name, fields.institution, fields.course_name] if field)
        scores["extraction_confidence"] = field_count / 3.0
        
        # Database match
        if db_check.get("match_found"):
            scores["database_match"] = db_check.get("confidence", 0.0)
        else:
            scores["database_match"] = 0.0
            factors.append("No database match found")
        
        overall_score = (scores["extraction_confidence"] + scores["database_match"]) / 2.0
        
        if overall_score >= 0.8:
            risk_level = RiskLevel.LOW
        elif overall_score >= 0.6:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.HIGH
        
        return RiskScore(
            overall_score=overall_score,
            confidence=overall_score,
            risk_level=risk_level,
            factors=factors
        )
    
    async def _assess_image_quality(self, image_data: bytes) -> float:
        """Assess image quality for OCR/extraction"""
        # Placeholder for image quality assessment
        # Could check resolution, blur, contrast, etc.
        return 0.8  # Default good quality
    
    def _check_field_consistency(self, fields: ExtractedFields) -> float:
        """Check consistency of extracted fields"""
        # Placeholder for field validation logic
        # Could check date formats, name patterns, etc.
        consistency_score = 1.0
        
        # Check date format if present
        if fields.issue_date:
            # Simple date format check
            try:
                datetime.strptime(fields.issue_date, "%Y-%m-%d")
            except ValueError:
                try:
                    datetime.strptime(fields.issue_date, "%d/%m/%Y")
                except ValueError:
                    consistency_score -= 0.2
        
        return max(consistency_score, 0.0)
    
    def _requires_manual_review(self, risk_score: RiskScore, db_check: Dict[str, Any]) -> bool:
        """Determine if manual review is required"""
        if risk_score.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            return True
        
        if not db_check.get("match_found"):
            return True
        
        if db_check.get("confidence", 0) < 0.7:
            return True
        
        if db_check.get("discrepancies"):
            return True
        
        return False
    
    async def _generate_attestation(self, verification_id: str, fields: ExtractedFields, image_data: bytes) -> AttestationData:
        """Generate cryptographic attestation"""
        try:
            # Create attestation payload
            payload = {
                "verification_id": verification_id,
                "extracted_fields": fields.dict(),
                "timestamp": datetime.utcnow().isoformat(),
                "image_hash": generate_image_hash(image_data) if image_data else None
            }
            
            # Sign the payload
            signature, public_key = sign_data(json.dumps(payload, sort_keys=True))
            
            # Generate QR code
            qr_url = await create_qr_code(verification_id, signature)
            
            # Store attestation
            attestation_data = {
                "verification_id": verification_id,
                "signature": signature,
                "public_key": public_key,
                "payload": payload,
                "qr_code_url": qr_url,
                "created_at": datetime.utcnow().isoformat()
            }
            
            attestation_id = await self.supabase_client.store_attestation(attestation_data)
            
            return AttestationData(
                attestation_id=attestation_id,
                signature=signature,
                public_key=public_key,
                qr_code_url=qr_url,
                created_at=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Error generating attestation: {str(e)}")
            raise
    
    def _generate_verification_id(self, data: bytes) -> str:
        """Generate unique verification ID"""
        hash_obj = hashlib.sha256(data + str(datetime.utcnow()).encode())
        return f"ver_{hash_obj.hexdigest()[:16]}"
