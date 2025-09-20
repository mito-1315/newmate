"""
Enhanced Pydantic models for 3-layer certificate verification system
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List, Tuple, Union
from datetime import datetime
from enum import Enum

class VerificationStatus(str, Enum):
    """Status of certificate verification"""
    PENDING = "pending"
    VERIFIED = "verified"
    FAILED = "failed"
    REQUIRES_REVIEW = "requires_review"
    TAMPERED = "tampered"
    SIGNATURE_INVALID = "signature_invalid"

class RiskLevel(str, Enum):
    """Risk level assessment"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class TamperType(str, Enum):
    """Types of tampering detected"""
    COPY_MOVE = "copy_move"
    DOUBLE_COMPRESSION = "double_compression"
    SPLICING = "splicing"
    RESAMPLING = "resampling"
    NOISE_INCONSISTENCY = "noise_inconsistency"
    ELA_ANOMALY = "ela_anomaly"
    HASH_MISMATCH = "hash_mismatch"

class ExtractionMethod(str, Enum):
    """Methods used for field extraction"""
    DONUT_PRIMARY = "donut_primary"
    OCR_FALLBACK = "ocr_fallback"
    VLM_FALLBACK = "vlm_fallback"
    MANUAL_OVERRIDE = "manual_override"

class ExtractedFields(BaseModel):
    """Enhanced fields extracted from certificate with forensic metadata"""
    # Core certificate fields
    name: Optional[str] = None
    roll_no: Optional[str] = None
    certificate_id: Optional[str] = None
    course_name: Optional[str] = None
    institution: Optional[str] = None
    issue_date: Optional[str] = None
    year: Optional[str] = None
    grade: Optional[str] = None
    
    # Enhanced fields for forensic analysis
    photo_bbox: Optional[List[int]] = Field(None, description="Bounding box [x1,y1,x2,y2] for student photo")
    qr_payload: Optional[Dict[str, Any]] = Field(None, description="Decoded QR code data")
    seal_locations: List[List[int]] = Field(default_factory=list, description="Bounding boxes of detected seals")
    signature_locations: List[List[int]] = Field(default_factory=list, description="Bounding boxes of detected signatures")
    
    # Extraction metadata
    extraction_method: ExtractionMethod = ExtractionMethod.DONUT_PRIMARY
    field_confidences: Dict[str, float] = Field(default_factory=dict, description="Confidence per field")
    extraction_time: Optional[float] = Field(None, description="Time taken for extraction in seconds")
    
    additional_fields: Dict[str, Any] = Field(default_factory=dict)

class VerificationRequest(BaseModel):
    """Request model for certificate verification"""
    image_url: Optional[str] = None
    manual_fields: Optional[ExtractedFields] = None
    certificate_id: Optional[str] = None

class ForensicAnalysis(BaseModel):
    """Forensic analysis results for tamper detection"""
    # Global analysis
    copy_move_score: float = Field(0.0, ge=0.0, le=1.0, description="Copy-move tampering score")
    ela_score: float = Field(0.0, ge=0.0, le=1.0, description="Error Level Analysis score")
    double_compression_score: float = Field(0.0, ge=0.0, le=1.0, description="Double compression score")
    noise_analysis_score: float = Field(0.0, ge=0.0, le=1.0, description="Noise consistency score")
    
    # Hash integrity
    sha256_hash: Optional[str] = None
    perceptual_hash: Optional[str] = None
    hash_match: Optional[bool] = None
    
    # Regional analysis
    suspicious_regions: List[List[int]] = Field(default_factory=list, description="Suspicious regions [x1,y1,x2,y2]")
    tamper_types: List[TamperType] = Field(default_factory=list)
    
    # Overall assessment
    tamper_probability: float = Field(0.0, ge=0.0, le=1.0, description="Overall tampering probability")
    analysis_time: Optional[float] = None

class SignatureVerification(BaseModel):
    """Signature and seal verification results"""
    # Detected objects
    seals_detected: int = 0
    signatures_detected: int = 0
    
    # Verification results
    seal_matches: List[Dict[str, Any]] = Field(default_factory=list, description="Seal matching results")
    signature_matches: List[Dict[str, Any]] = Field(default_factory=list, description="Signature matching results")
    
    # Scores
    seal_authenticity_score: float = Field(0.0, ge=0.0, le=1.0)
    signature_authenticity_score: float = Field(0.0, ge=0.0, le=1.0)
    
    # QR verification
    qr_signature_valid: Optional[bool] = None
    qr_issuer_verified: Optional[bool] = None
    
    verification_time: Optional[float] = None

class RiskScore(BaseModel):
    """Enhanced risk scoring with forensic analysis"""
    # Component scores
    extraction_confidence: float = Field(0.0, ge=0.0, le=1.0, description="Field extraction confidence")
    database_match_score: float = Field(0.0, ge=0.0, le=1.0, description="Database matching score")
    forensic_score: float = Field(0.0, ge=0.0, le=1.0, description="Forensic analysis score (1.0 = authentic)")
    signature_score: float = Field(0.0, ge=0.0, le=1.0, description="Signature/seal verification score")
    qr_integrity_score: float = Field(0.0, ge=0.0, le=1.0, description="QR code integrity score")
    
    # Overall assessment
    overall_score: float = Field(0.0, ge=0.0, le=1.0, description="Weighted overall score")
    confidence: float = Field(0.0, ge=0.0, le=1.0, description="Confidence in assessment")
    risk_level: RiskLevel
    
    # Decision factors
    risk_factors: List[str] = Field(default_factory=list, description="Risk factors identified")
    authenticity_indicators: List[str] = Field(default_factory=list, description="Positive authenticity indicators")
    
    # Fusion weights used
    fusion_weights: Dict[str, float] = Field(default_factory=dict, description="Weights used in fusion")

class AttestationData(BaseModel):
    """Attestation information"""
    attestation_id: str
    signature: str
    public_key: str
    qr_code_url: Optional[str] = None
    pdf_url: Optional[str] = None
    created_at: datetime

class QRIntegrityCheck(BaseModel):
    """QR code integrity and signature verification"""
    qr_detected: bool = False
    qr_decoded: bool = False
    qr_payload: Optional[Dict[str, Any]] = None
    signature_valid: bool = False
    issuer_verified: bool = False
    certificate_id_match: bool = False
    issue_date_match: bool = False
    error_message: Optional[str] = None

class LayerResults(BaseModel):
    """Results from each verification layer"""
    layer1_extraction: ExtractedFields
    layer2_forensics: ForensicAnalysis
    layer3_signatures: SignatureVerification
    qr_integrity: QRIntegrityCheck
    processing_time_ms: Dict[str, float] = Field(default_factory=dict)

class CertificateResponse(BaseModel):
    """Enhanced response model for 3-layer certificate verification"""
    verification_id: str
    status: VerificationStatus
    
    # Layer results
    layer_results: LayerResults
    
    # Fusion engine output
    risk_score: RiskScore
    decision_rationale: str = Field("", description="Human-readable explanation of the decision")
    
    # Attestation and integrity
    attestation: Optional[AttestationData] = None
    integrity_checks: Dict[str, bool] = Field(default_factory=dict)
    
    # Processing metadata
    image_url: Optional[str] = None
    canonical_image_hash: Optional[str] = None
    processed_at: datetime
    processing_time_total_ms: float = 0.0
    
    # Review workflow
    requires_manual_review: bool = False
    auto_decision_confidence: float = Field(0.0, ge=0.0, le=1.0)
    escalation_reasons: List[str] = Field(default_factory=list)
    review_notes: Optional[str] = None
    reviewer_id: Optional[str] = None

class ManualReviewRequest(BaseModel):
    """Request for manual review"""
    verification_id: str
    reviewer_notes: str
    approved: bool
    corrected_fields: Optional[ExtractedFields] = None

class InstitutionData(BaseModel):
    """Institution information"""
    name: str
    domain: str
    public_key: str
    contact_email: str
    verification_endpoint: Optional[str] = None

class CertificateImport(BaseModel):
    """Model for importing certificates via CSV"""
    student_name: str
    course_name: str
    institution: str
    issue_date: str
    certificate_id: str
    grade: Optional[str] = None
    additional_data: Dict[str, Any] = Field(default_factory=dict)

class AuditLog(BaseModel):
    """Audit log entry"""
    action: str
    user_id: Optional[str] = None
    verification_id: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime
    ip_address: Optional[str] = None
