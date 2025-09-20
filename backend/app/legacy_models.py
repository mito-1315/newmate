"""
Legacy Certificate Verification Models
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

class LegacyStatus(str, Enum):
    """Status of legacy verification request"""
    PENDING = "pending"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"

class LegacyVerificationRequest(BaseModel):
    """Legacy certificate verification request from student"""
    request_id: str
    student_name: str
    student_email: EmailStr
    roll_no: str
    course_name: str
    year: str
    institution: str
    
    # Uploaded certificate
    certificate_image_url: str
    certificate_filename: str
    file_size: int
    
    # Status and tracking
    status: LegacyStatus = LegacyStatus.PENDING
    submitted_at: datetime
    reviewed_at: Optional[datetime] = None
    reviewer_id: Optional[str] = None
    
    # Review details
    review_notes: Optional[str] = None
    rejection_reason: Optional[str] = None
    
    # Additional metadata
    additional_info: Dict[str, Any] = Field(default_factory=dict)

class LegacyReviewAction(BaseModel):
    """Action taken on legacy verification request"""
    request_id: str
    action: str  # "approve" or "reject"
    reviewer_id: str
    notes: Optional[str] = None
    rejection_reason: Optional[str] = None

class LegacyVerificationResult(BaseModel):
    """Result of legacy verification process"""
    request_id: str
    status: LegacyStatus
    
    # If approved, generate new digital certificate
    attestation_id: Optional[str] = None
    qr_code_url: Optional[str] = None
    verified_certificate_url: Optional[str] = None
    
    # Verification details
    verified_fields: Optional[Dict[str, Any]] = None
    verification_date: Optional[datetime] = None
    
    # Metadata
    source: str = "legacy_verified"
    original_filename: str
    processing_notes: Optional[str] = None

class LegacyCertificateSearch(BaseModel):
    """Search criteria for legacy certificate verification"""
    student_name: Optional[str] = None
    roll_no: Optional[str] = None
    course_name: Optional[str] = None
    year: Optional[str] = None
    institution: Optional[str] = None
    date_range_start: Optional[datetime] = None
    date_range_end: Optional[datetime] = None

class LegacyBatchImport(BaseModel):
    """Batch import of legacy certificates"""
    institution_id: str
    certificates: List[Dict[str, Any]]
    import_notes: Optional[str] = None
    auto_approve: bool = False
