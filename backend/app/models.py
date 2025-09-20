"""
Pydantic models for certificate verification system
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

class VerificationStatus(str, Enum):
    """Status of certificate verification"""
    PENDING = "pending"
    VERIFIED = "verified"
    FAILED = "failed"
    REQUIRES_REVIEW = "requires_review"

class RiskLevel(str, Enum):
    """Risk level assessment"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ExtractedFields(BaseModel):
    """Fields extracted from certificate"""
    name: Optional[str] = None
    institution: Optional[str] = None
    course_name: Optional[str] = None
    issue_date: Optional[str] = None
    certificate_id: Optional[str] = None
    grade: Optional[str] = None
    additional_fields: Dict[str, Any] = Field(default_factory=dict)

class VerificationRequest(BaseModel):
    """Request model for certificate verification"""
    image_url: Optional[str] = None
    manual_fields: Optional[ExtractedFields] = None
    certificate_id: Optional[str] = None

class RiskScore(BaseModel):
    """Risk scoring details"""
    overall_score: float = Field(..., ge=0.0, le=1.0, description="Overall risk score (0-1)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in assessment")
    risk_level: RiskLevel
    factors: List[str] = Field(default_factory=list, description="Risk factors identified")

class AttestationData(BaseModel):
    """Attestation information"""
    attestation_id: str
    signature: str
    public_key: str
    qr_code_url: Optional[str] = None
    pdf_url: Optional[str] = None
    created_at: datetime

class CertificateResponse(BaseModel):
    """Response model for certificate verification"""
    verification_id: str
    status: VerificationStatus
    extracted_fields: ExtractedFields
    risk_score: RiskScore
    attestation: Optional[AttestationData] = None
    image_url: Optional[str] = None
    processed_at: datetime
    requires_manual_review: bool = False
    review_notes: Optional[str] = None

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
