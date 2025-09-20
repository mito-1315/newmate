"""
Enhanced 3-Layer Fusion Engine
Combines Layer 1 (extraction) + Layer 2 (forensics) + Layer 3 (signatures) + QR integrity
Implements conservative decision thresholds and comprehensive risk assessment
"""
import logging
import time
from typing import Dict, Any, Optional
from datetime import datetime
import hashlib
import json
from PIL import Image

from ..models import (
    ExtractedFields, CertificateResponse, VerificationStatus, 
    RiskScore, RiskLevel, VerificationRequest, AttestationData,
    LayerResults, ForensicAnalysis, SignatureVerification, QRIntegrityCheck
)
from .layer1_extraction import Layer1ExtractionService
from .layer2_forensics import Layer2ForensicsService
from .layer3_signatures import Layer3SignatureService
from .qr_integrity import QRIntegrityService
from .supabase_client import SupabaseClient
from ..utils.helpers import generate_image_hash, create_qr_code, sign_data

logger = logging.getLogger(__name__)

class EnhancedFusionEngine:
    """
    Enhanced 3-Layer Fusion Engine implementing comprehensive certificate verification:
    
    Layer 1: Field Extraction (Donut + OCR + VLM fallback)
    Layer 2: Image Forensics (tamper detection, integrity checks)
    Layer 3: Seal & Signature Verification (object detection + matching)
    QR Integrity: Cryptographic verification and signing
    
    Implements conservative decision thresholds for high-stakes verification
    """
    
    def __init__(self, supabase_client: SupabaseClient):
        # Initialize all layer services
        self.layer1_service = Layer1ExtractionService()
        self.layer2_service = Layer2ForensicsService()
        self.layer3_service = Layer3SignatureService()
        self.qr_service = QRIntegrityService()
        self.supabase_client = supabase_client
        
        # Enhanced fusion weights for multi-layer scoring
        self.fusion_weights = {
            "extraction_confidence": 0.25,    # Layer 1
            "database_match": 0.30,           # Database verification
            "forensic_score": 0.25,           # Layer 2
            "signature_score": 0.15,          # Layer 3
            "qr_integrity": 0.05              # QR verification
        }
        
        # Conservative decision thresholds
        self.decision_thresholds = {
            "auto_approve": 0.85,     # High confidence auto-approval
            "manual_review": 0.60,    # Medium confidence requires review
            "auto_reject": 0.30       # Low confidence auto-rejection
        }
        
        # Risk factor weights for tamper detection
        self.tamper_weights = {
            "forensic_score": 0.40,
            "hash_integrity": 0.30,
            "signature_validity": 0.20,
            "qr_integrity": 0.10
        }
    
    async def verify_certificate(self, image_data: bytes, reference_hash: Optional[str] = None) -> CertificateResponse:
        """Enhanced 3-layer verification pipeline for certificate authentication"""
        verification_id = self._generate_verification_id(image_data)
        start_time = time.time()
        
        try:
            # Convert image data to PIL Image
            from PIL import Image
            import io
            
            image = Image.open(io.BytesIO(image_data))
            
            # Execute all layers in parallel for efficiency
            layer_start_time = time.time()
            
            # Layer 1: Field Extraction
            layer1_task = self.layer1_service.extract_fields(image)
            
            # Layer 2: Forensic Analysis
            layer2_task = self.layer2_service.analyze_image(image, reference_hash)
            
            # Execute layers 1 and 2 in parallel
            import asyncio
            layer1_result, layer2_result = await asyncio.gather(layer1_task, layer2_task)
            
            # Layer 3: Signature Verification (depends on Layer 1 for extracted fields)
            layer3_result = await self.layer3_service.verify_seals_and_signatures(
                image, layer1_result.dict()
            )
            
            # QR Integrity Check (if QR detected in Layer 1)
            qr_result = QRIntegrityCheck()
            if layer1_result.qr_payload:
                qr_result = await self.qr_service.verify_qr_integrity(
                    json.dumps(layer1_result.qr_payload), 
                    layer1_result.dict()
                )
            
            # Create layer results
            layer_processing_time = time.time() - layer_start_time
            layer_results = LayerResults(
                layer1_extraction=layer1_result,
                layer2_forensics=layer2_result,
                layer3_signatures=layer3_result,
                qr_integrity=qr_result,
                processing_time_ms={
                    "layer1_ms": layer1_result.extraction_time * 1000 if layer1_result.extraction_time else 0,
                    "layer2_ms": layer2_result.analysis_time * 1000 if layer2_result.analysis_time else 0,
                    "layer3_ms": layer3_result.verification_time * 1000 if layer3_result.verification_time else 0,
                    "total_layers_ms": layer_processing_time * 1000
                }
            )
            
            # Database verification using extracted fields
            db_check = await self.supabase_client.check_certificate_database(layer1_result)
            
            # Enhanced fusion scoring
            risk_score = await self._calculate_enhanced_risk_score(
                layer_results, db_check, image_data
            )
            
            # Decision engine with conservative thresholds
            status, requires_review, escalation_reasons, decision_rationale = self._make_verification_decision(
                risk_score, layer_results, db_check
            )
            
            # Generate attestation for verified certificates
            attestation = None
            if status == VerificationStatus.VERIFIED:
                attestation = await self._generate_enhanced_attestation(
                    verification_id, layer1_result, image_data, risk_score
                )
            
            # Calculate integrity checks
            integrity_checks = self._calculate_integrity_checks(layer_results, reference_hash)
            
            # Store comprehensive verification result
            verification_data = {
                "id": verification_id,
                "status": status.value,
                "layer_results": layer_results.dict(),
                "risk_score": risk_score.dict(),
                "database_check": db_check,
                "requires_manual_review": requires_review,
                "escalation_reasons": escalation_reasons,
                "decision_rationale": decision_rationale,
                "integrity_checks": integrity_checks,
                "processed_at": datetime.utcnow().isoformat(),
                "processing_time_ms": (time.time() - start_time) * 1000
            }
            
            await self.supabase_client.store_verification(verification_data)
            
            # Upload image and get URL
            image_url = await self.supabase_client.upload_certificate_image(
                image_data, f"{verification_id}.jpg"
            )
            
            # Calculate canonical hash for storage
            canonical_hash = generate_image_hash(image_data)
            
            return CertificateResponse(
                verification_id=verification_id,
                status=status,
                layer_results=layer_results,
                risk_score=risk_score,
                decision_rationale=decision_rationale,
                attestation=attestation,
                integrity_checks=integrity_checks,
                image_url=image_url,
                canonical_image_hash=canonical_hash,
                processed_at=datetime.utcnow(),
                processing_time_total_ms=(time.time() - start_time) * 1000,
                requires_manual_review=requires_review,
                auto_decision_confidence=risk_score.confidence,
                escalation_reasons=escalation_reasons
            )
            
        except Exception as e:
            logger.error(f"Enhanced verification pipeline failed: {str(e)}")
            
            # Store failed verification with error details
            error_data = {
                "id": verification_id,
                "status": VerificationStatus.FAILED.value,
                "error": str(e),
                "processed_at": datetime.utcnow().isoformat(),
                "processing_time_ms": (time.time() - start_time) * 1000
            }
            
            await self.supabase_client.store_verification(error_data)
            
            raise Exception(f"Enhanced verification failed: {str(e)}")
    
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
    
    async def _calculate_enhanced_risk_score(self, layer_results: LayerResults, 
                                            db_check: Dict[str, Any], 
                                            image_data: bytes) -> RiskScore:
        """Enhanced risk scoring using all layer outputs"""
        try:
            # Extract component scores
            extraction_confidence = self._calculate_extraction_confidence(layer_results.layer1_extraction)
            database_match_score = db_check.get("confidence", 0.0) if db_check.get("match_found") else 0.0
            forensic_score = 1.0 - layer_results.layer2_forensics.tamper_probability  # Invert tamper probability
            signature_score = (layer_results.layer3_signatures.seal_authenticity_score + 
                             layer_results.layer3_signatures.signature_authenticity_score) / 2.0
            qr_integrity_score = self._calculate_qr_integrity_score(layer_results.qr_integrity)
            
            # Calculate weighted overall score
            overall_score = (
                extraction_confidence * self.fusion_weights["extraction_confidence"] +
                database_match_score * self.fusion_weights["database_match"] +
                forensic_score * self.fusion_weights["forensic_score"] +
                signature_score * self.fusion_weights["signature_score"] +
                qr_integrity_score * self.fusion_weights["qr_integrity"]
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
            
            # Collect risk factors and authenticity indicators
            risk_factors = self._collect_risk_factors(layer_results, db_check)
            authenticity_indicators = self._collect_authenticity_indicators(layer_results, db_check)
            
            # Calculate confidence based on consistency across layers
            confidence = self._calculate_confidence_score(layer_results, overall_score)
            
            return RiskScore(
                extraction_confidence=extraction_confidence,
                database_match_score=database_match_score,
                forensic_score=forensic_score,
                signature_score=signature_score,
                qr_integrity_score=qr_integrity_score,
                overall_score=overall_score,
                confidence=confidence,
                risk_level=risk_level,
                risk_factors=risk_factors,
                authenticity_indicators=authenticity_indicators,
                fusion_weights=self.fusion_weights
            )
            
        except Exception as e:
            logger.error(f"Enhanced risk scoring failed: {str(e)}")
            return RiskScore(
                overall_score=0.5,
                confidence=0.0,
                risk_level=RiskLevel.HIGH,
                risk_factors=["Risk calculation error"],
                fusion_weights=self.fusion_weights
            )
    
    def _calculate_extraction_confidence(self, extraction_result: ExtractedFields) -> float:
        """Calculate confidence from extraction results"""
        if not extraction_result.field_confidences:
            return 0.5
        
        # Core fields for certificate verification
        core_fields = ["name", "certificate_id", "institution", "course_name"]
        
        total_confidence = 0.0
        valid_fields = 0
        
        for field in core_fields:
            if hasattr(extraction_result, field) and getattr(extraction_result, field):
                confidence = extraction_result.field_confidences.get(field, 0.5)
                total_confidence += confidence
                valid_fields += 1
        
        return total_confidence / max(valid_fields, 1)
    
    def _calculate_qr_integrity_score(self, qr_result: QRIntegrityCheck) -> float:
        """Calculate QR integrity score"""
        if not qr_result.qr_detected:
            return 0.5  # Neutral score if no QR
        
        if not qr_result.qr_decoded:
            return 0.2  # Low score for undecodable QR
        
        score = 0.5  # Base score for decoded QR
        
        if qr_result.signature_valid:
            score += 0.3
        
        if qr_result.issuer_verified:
            score += 0.2
        
        if qr_result.certificate_id_match:
            score += 0.1
        
        if qr_result.issue_date_match:
            score += 0.1
        
        return min(score, 1.0)
    
    def _collect_risk_factors(self, layer_results: LayerResults, db_check: Dict[str, Any]) -> List[str]:
        """Collect risk factors from all layers"""
        risk_factors = []
        
        # Layer 1 risk factors
        if layer_results.layer1_extraction.extraction_method != "donut_primary":
            risk_factors.append("Primary extraction method failed")
        
        avg_confidence = self._calculate_extraction_confidence(layer_results.layer1_extraction)
        if avg_confidence < 0.7:
            risk_factors.append("Low field extraction confidence")
        
        # Layer 2 risk factors
        forensics = layer_results.layer2_forensics
        if forensics.tamper_probability > 0.5:
            risk_factors.append("High tampering probability detected")
        
        if forensics.tamper_types:
            risk_factors.append(f"Tampering indicators: {', '.join(forensics.tamper_types)}")
        
        if forensics.hash_match is False:
            risk_factors.append("Image hash mismatch")
        
        # Layer 3 risk factors
        signatures = layer_results.layer3_signatures
        if signatures.seals_detected == 0:
            risk_factors.append("No institutional seals detected")
        
        if signatures.signatures_detected == 0:
            risk_factors.append("No signatures detected")
        
        if not signatures.qr_signature_valid:
            risk_factors.append("QR signature invalid")
        
        # Database risk factors
        if not db_check.get("match_found"):
            risk_factors.append("No database match found")
        
        if db_check.get("discrepancies"):
            risk_factors.append("Field discrepancies with database")
        
        return risk_factors
    
    def _collect_authenticity_indicators(self, layer_results: LayerResults, db_check: Dict[str, Any]) -> List[str]:
        """Collect positive authenticity indicators"""
        indicators = []
        
        # Layer 1 indicators
        if layer_results.layer1_extraction.extraction_method == "donut_primary":
            indicators.append("Primary AI extraction successful")
        
        if layer_results.layer1_extraction.qr_payload:
            indicators.append("QR code detected and decoded")
        
        # Layer 2 indicators
        forensics = layer_results.layer2_forensics
        if forensics.tamper_probability < 0.3:
            indicators.append("Low tampering probability")
        
        if forensics.hash_match is True:
            indicators.append("Image hash verification passed")
        
        # Layer 3 indicators
        signatures = layer_results.layer3_signatures
        if signatures.seals_detected > 0:
            indicators.append(f"{signatures.seals_detected} institutional seal(s) detected")
        
        if signatures.signatures_detected > 0:
            indicators.append(f"{signatures.signatures_detected} signature(s) detected")
        
        if signatures.qr_signature_valid:
            indicators.append("QR digital signature verified")
        
        # Database indicators
        if db_check.get("match_found"):
            indicators.append("Database record match found")
        
        if db_check.get("confidence", 0) > 0.8:
            indicators.append("High confidence database match")
        
        return indicators
    
    def _calculate_confidence_score(self, layer_results: LayerResults, overall_score: float) -> float:
        """Calculate confidence based on consistency across layers"""
        # Check for consistency between layers
        consistency_score = 1.0
        
        # Check forensics vs overall score consistency
        forensic_score = 1.0 - layer_results.layer2_forensics.tamper_probability
        if abs(forensic_score - overall_score) > 0.3:
            consistency_score -= 0.2
        
        # Check signature verification consistency
        signature_score = (layer_results.layer3_signatures.seal_authenticity_score + 
                         layer_results.layer3_signatures.signature_authenticity_score) / 2.0
        if abs(signature_score - overall_score) > 0.3:
            consistency_score -= 0.2
        
        # QR integrity consistency
        qr_score = self._calculate_qr_integrity_score(layer_results.qr_integrity)
        if qr_score > 0.5 and abs(qr_score - overall_score) > 0.4:
            consistency_score -= 0.1
        
        return max(consistency_score, 0.1)
    
    def _make_verification_decision(self, risk_score: RiskScore, 
                                  layer_results: LayerResults, 
                                  db_check: Dict[str, Any]) -> Tuple[VerificationStatus, bool, List[str], str]:
        """Conservative decision engine with escalation logic"""
        overall_score = risk_score.overall_score
        confidence = risk_score.confidence
        escalation_reasons = []
        
        # Check for immediate rejection criteria (tamper detection)
        if self._check_tamper_rejection_criteria(layer_results):
            return (VerificationStatus.TAMPERED, True, 
                   ["Tampering detected", "Requires expert review"], 
                   "Certificate rejected due to tampering indicators")
        
        # Check for signature/QR invalidity
        if self._check_signature_rejection_criteria(layer_results):
            return (VerificationStatus.SIGNATURE_INVALID, True,
                   ["Invalid digital signatures", "QR verification failed"],
                   "Certificate rejected due to invalid digital signatures")
        
        # Conservative decision logic
        if overall_score >= self.decision_thresholds["auto_approve"] and confidence >= 0.8:
            # High confidence automatic approval
            if not risk_score.risk_factors:
                return (VerificationStatus.VERIFIED, False, [],
                       f"High confidence verification (score: {overall_score:.2f})")
            else:
                escalation_reasons.append("Risk factors present despite high score")
                return (VerificationStatus.REQUIRES_REVIEW, True, escalation_reasons,
                       "High score but risk factors require review")
        
        elif overall_score <= self.decision_thresholds["auto_reject"]:
            # Low confidence automatic rejection
            return (VerificationStatus.FAILED, True, ["Low confidence score"],
                   f"Low confidence rejection (score: {overall_score:.2f})")
        
        else:
            # Manual review required
            if confidence < 0.6:
                escalation_reasons.append("Low confidence in assessment")
            
            if not db_check.get("match_found"):
                escalation_reasons.append("No database match")
            
            if risk_score.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
                escalation_reasons.append("High risk level detected")
            
            return (VerificationStatus.REQUIRES_REVIEW, True, escalation_reasons,
                   f"Manual review required (score: {overall_score:.2f}, confidence: {confidence:.2f})")
    
    def _check_tamper_rejection_criteria(self, layer_results: LayerResults) -> bool:
        """Check if certificate should be rejected due to tampering"""
        forensics = layer_results.layer2_forensics
        
        # High tampering probability
        if forensics.tamper_probability > 0.8:
            return True
        
        # Hash mismatch (if reference available)
        if forensics.hash_match is False:
            return True
        
        # Multiple tampering indicators
        if len(forensics.tamper_types) >= 3:
            return True
        
        return False
    
    def _check_signature_rejection_criteria(self, layer_results: LayerResults) -> bool:
        """Check if certificate should be rejected due to signature issues"""
        # QR signature explicitly invalid
        if (layer_results.qr_integrity.qr_detected and 
            layer_results.qr_integrity.qr_decoded and 
            not layer_results.qr_integrity.signature_valid):
            return True
        
        # No signatures or seals detected at all
        signatures = layer_results.layer3_signatures
        if (signatures.seals_detected == 0 and 
            signatures.signatures_detected == 0 and
            not layer_results.qr_integrity.qr_detected):
            return True
        
        return False
    
    def _calculate_integrity_checks(self, layer_results: LayerResults, 
                                  reference_hash: Optional[str]) -> Dict[str, bool]:
        """Calculate various integrity check results"""
        checks = {}
        
        # Hash integrity
        if reference_hash:
            checks["hash_match"] = layer_results.layer2_forensics.hash_match
        
        # Forensic integrity
        checks["tamper_free"] = layer_results.layer2_forensics.tamper_probability < 0.3
        
        # Signature integrity
        checks["signatures_valid"] = (
            layer_results.layer3_signatures.seal_authenticity_score > 0.7 or
            layer_results.layer3_signatures.signature_authenticity_score > 0.7
        )
        
        # QR integrity
        if layer_results.qr_integrity.qr_detected:
            checks["qr_valid"] = layer_results.qr_integrity.signature_valid
        
        return checks
    
    async def _generate_enhanced_attestation(self, verification_id: str, 
                                           extracted_fields: ExtractedFields,
                                           image_data: bytes,
                                           risk_score: RiskScore) -> AttestationData:
        """Generate enhanced attestation with comprehensive metadata"""
        try:
            # Create enhanced attestation payload
            payload = {
                "verification_id": verification_id,
                "extracted_fields": extracted_fields.dict(),
                "risk_assessment": {
                    "overall_score": risk_score.overall_score,
                    "risk_level": risk_score.risk_level,
                    "confidence": risk_score.confidence
                },
                "timestamp": datetime.utcnow().isoformat(),
                "image_hash": generate_image_hash(image_data),
                "attestation_version": "3.0"
            }
            
            # Generate QR code with signed payload
            qr_data_url, signed_payload = await self.qr_service.generate_certificate_qr(
                payload, "default", True
            )
            
            # Store attestation in database
            attestation_data = {
                "verification_id": verification_id,
                "signature": signed_payload["signature"],
                "public_key": signed_payload["public_key"],
                "payload": payload,
                "qr_code_url": qr_data_url,
                "created_at": datetime.utcnow().isoformat()
            }
            
            attestation_id = await self.supabase_client.store_attestation(attestation_data)
            
            return AttestationData(
                attestation_id=attestation_id,
                signature=signed_payload["signature"],
                public_key=signed_payload["public_key"],
                qr_code_url=qr_data_url,
                created_at=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Enhanced attestation generation failed: {str(e)}")
            raise
    
    def _generate_verification_id(self, data: bytes) -> str:
        """Generate unique verification ID"""
        hash_obj = hashlib.sha256(data + str(datetime.utcnow()).encode())
        return f"ver_{hash_obj.hexdigest()[:16]}"
