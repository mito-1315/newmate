"""
Authentication and User Role Models
"""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime
from enum import Enum

class UserRole(str, Enum):
    """User roles in the system"""
    UNIVERSITY_ADMIN = "university_admin"
    STUDENT = "student"
    EMPLOYER = "employer"
    SUPER_ADMIN = "super_admin"

class UserStatus(str, Enum):
    """User account status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING_VERIFICATION = "pending_verification"
    SUSPENDED = "suspended"

class UserProfile(BaseModel):
    """User profile information"""
    user_id: str
    email: EmailStr
    full_name: str
    role: UserRole
    status: UserStatus = UserStatus.ACTIVE
    
    # Institution-specific fields
    institution_id: Optional[str] = None
    institution_name: Optional[str] = None
    student_id: Optional[str] = None  # For students
    department: Optional[str] = None
    
    # Contact information
    phone: Optional[str] = None
    address: Optional[str] = None
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None

class InstitutionProfile(BaseModel):
    """Institution profile for universities"""
    institution_id: str
    name: str
    domain: str
    contact_email: EmailStr
    contact_phone: Optional[str] = None
    address: Optional[str] = None
    
    # Verification settings
    public_key: str
    verification_endpoint: Optional[str] = None
    auto_approve_legacy: bool = False
    
    # Status
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

class LoginRequest(BaseModel):
    """Login request model"""
    email: EmailStr
    password: str
    remember_me: bool = False

class RegisterRequest(BaseModel):
    """Registration request model"""
    email: EmailStr
    password: str
    full_name: str
    role: UserRole
    institution_id: Optional[str] = None
    student_id: Optional[str] = None

class AuthResponse(BaseModel):
    """Authentication response"""
    access_token: str
    refresh_token: str
    user: UserProfile
    expires_in: int

class PasswordResetRequest(BaseModel):
    """Password reset request"""
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    """Password reset confirmation"""
    token: str
    new_password: str
