"""
Authentication Service using Supabase Auth
"""
import os
from typing import Optional, Dict, Any
from supabase import create_client, Client
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from datetime import datetime, timedelta
import logging

from ..auth_models import UserProfile, UserRole, UserStatus, LoginRequest, RegisterRequest, AuthResponse
from ..config import get_settings

logger = logging.getLogger(__name__)
security = HTTPBearer()

class AuthService:
    def __init__(self):
        self.settings = get_settings()
        self.supabase: Client = create_client(
            self.settings.supabase_url,
            self.settings.supabase_service_key
        )
        self.jwt_secret = self.settings.secret_key
        self.jwt_algorithm = "HS256"
        self.token_expiry = timedelta(hours=24)

    async def register_user(self, request: RegisterRequest) -> AuthResponse:
        """Register a new user"""
        try:
            # Create user in Supabase Auth
            auth_response = self.supabase.auth.sign_up({
                "email": request.email,
                "password": request.password,
                "options": {
                    "data": {
                        "full_name": request.full_name,
                        "role": request.role,
                        "institution_id": request.institution_id,
                        "student_id": request.student_id
                    }
                }
            })

            if not auth_response.user:
                raise HTTPException(status_code=400, detail="Registration failed")

            # Create user profile in database
            user_profile = UserProfile(
                user_id=auth_response.user.id,
                email=request.email,
                full_name=request.full_name,
                role=request.role,
                status=UserStatus.PENDING_VERIFICATION,
                institution_id=request.institution_id,
                student_id=request.student_id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

            # Store user profile
            await self._store_user_profile(user_profile)

            # Generate tokens
            access_token = self._create_access_token(user_profile)
            refresh_token = self._create_refresh_token(user_profile)

            return AuthResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                user=user_profile,
                expires_in=int(self.token_expiry.total_seconds())
            )

        except Exception as e:
            logger.error(f"Registration error: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Registration failed: {str(e)}")

    async def login_user(self, request: LoginRequest) -> AuthResponse:
        """Login user"""
        try:
            # Authenticate with Supabase
            auth_response = self.supabase.auth.sign_in_with_password({
                "email": request.email,
                "password": request.password
            })

            if not auth_response.user:
                raise HTTPException(status_code=401, detail="Invalid credentials")

            # Get user profile
            user_profile = await self._get_user_profile(auth_response.user.id)
            if not user_profile:
                raise HTTPException(status_code=404, detail="User profile not found")

            # Check if user is active
            if user_profile.status != UserStatus.ACTIVE:
                raise HTTPException(status_code=403, detail="Account is not active")

            # Update last login
            user_profile.last_login = datetime.utcnow()
            await self._update_user_profile(user_profile)

            # Generate tokens
            access_token = self._create_access_token(user_profile)
            refresh_token = self._create_refresh_token(user_profile)

            return AuthResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                user=user_profile,
                expires_in=int(self.token_expiry.total_seconds())
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            raise HTTPException(status_code=401, detail="Login failed")

    async def get_current_user(self, credentials: HTTPAuthorizationCredentials = Depends(security)) -> UserProfile:
        """Get current authenticated user"""
        try:
            # Verify JWT token
            payload = jwt.decode(
                credentials.credentials,
                self.jwt_secret,
                algorithms=[self.jwt_algorithm]
            )
            
            user_id = payload.get("sub")
            if not user_id:
                raise HTTPException(status_code=401, detail="Invalid token")

            # Get user profile
            user_profile = await self._get_user_profile(user_id)
            if not user_profile:
                raise HTTPException(status_code=404, detail="User not found")

            return user_profile

        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.JWTError:
            raise HTTPException(status_code=401, detail="Invalid token")
        except Exception as e:
            logger.error(f"Token verification error: {str(e)}")
            raise HTTPException(status_code=401, detail="Authentication failed")

    async def require_role(self, required_roles: list[UserRole]):
        """Dependency to require specific roles"""
        def role_checker(current_user: UserProfile = Depends(self.get_current_user)):
            if current_user.role not in required_roles:
                raise HTTPException(
                    status_code=403, 
                    detail=f"Access denied. Required roles: {required_roles}"
                )
            return current_user
        return role_checker

    def _create_access_token(self, user: UserProfile) -> str:
        """Create JWT access token"""
        payload = {
            "sub": user.user_id,
            "email": user.email,
            "role": user.role,
            "institution_id": user.institution_id,
            "exp": datetime.utcnow() + self.token_expiry,
            "iat": datetime.utcnow()
        }
        return jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)

    def _create_refresh_token(self, user: UserProfile) -> str:
        """Create JWT refresh token"""
        payload = {
            "sub": user.user_id,
            "type": "refresh",
            "exp": datetime.utcnow() + timedelta(days=30),
            "iat": datetime.utcnow()
        }
        return jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)

    async def _store_user_profile(self, user_profile: UserProfile):
        """Store user profile in database"""
        try:
            result = self.supabase.table("user_profiles").insert({
                "user_id": user_profile.user_id,
                "email": user_profile.email,
                "full_name": user_profile.full_name,
                "role": user_profile.role,
                "status": user_profile.status,
                "institution_id": user_profile.institution_id,
                "student_id": user_profile.student_id,
                "department": user_profile.department,
                "phone": user_profile.phone,
                "address": user_profile.address,
                "created_at": user_profile.created_at.isoformat(),
                "updated_at": user_profile.updated_at.isoformat(),
                "last_login": user_profile.last_login.isoformat() if user_profile.last_login else None
            }).execute()
            
            if not result.data:
                raise Exception("Failed to store user profile")
                
        except Exception as e:
            logger.error(f"Error storing user profile: {str(e)}")
            raise

    async def _get_user_profile(self, user_id: str) -> Optional[UserProfile]:
        """Get user profile from database"""
        try:
            result = self.supabase.table("user_profiles").select("*").eq("user_id", user_id).execute()
            
            if not result.data:
                return None
                
            data = result.data[0]
            return UserProfile(
                user_id=data["user_id"],
                email=data["email"],
                full_name=data["full_name"],
                role=UserRole(data["role"]),
                status=UserStatus(data["status"]),
                institution_id=data.get("institution_id"),
                institution_name=data.get("institution_name"),
                student_id=data.get("student_id"),
                department=data.get("department"),
                phone=data.get("phone"),
                address=data.get("address"),
                created_at=datetime.fromisoformat(data["created_at"]),
                updated_at=datetime.fromisoformat(data["updated_at"]),
                last_login=datetime.fromisoformat(data["last_login"]) if data.get("last_login") else None
            )
            
        except Exception as e:
            logger.error(f"Error getting user profile: {str(e)}")
            return None

    async def _update_user_profile(self, user_profile: UserProfile):
        """Update user profile in database"""
        try:
            result = self.supabase.table("user_profiles").update({
                "full_name": user_profile.full_name,
                "status": user_profile.status,
                "institution_id": user_profile.institution_id,
                "student_id": user_profile.student_id,
                "department": user_profile.department,
                "phone": user_profile.phone,
                "address": user_profile.address,
                "updated_at": user_profile.updated_at.isoformat(),
                "last_login": user_profile.last_login.isoformat() if user_profile.last_login else None
            }).eq("user_id", user_profile.user_id).execute()
            
            if not result.data:
                raise Exception("Failed to update user profile")
                
        except Exception as e:
            logger.error(f"Error updating user profile: {str(e)}")
            raise

# Global auth service instance
auth_service = AuthService()
