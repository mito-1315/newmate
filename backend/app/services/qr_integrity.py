"""
QR Integrity and Signing Service
Implements secure QR code generation, signing, and verification:
- ECDSA/RSA signed QR payloads
- Image fingerprinting and hash integrity
- Certificate issuance QR generation
- Public verification QR codes
"""
import json
import time
import logging
import hashlib
import base64
import qrcode
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from PIL import Image
import io

from ..models import QRIntegrityCheck
from ..config import settings
from ..utils.helpers import sign_data, verify_signature, generate_key_pair, generate_image_hash

logger = logging.getLogger(__name__)

class QRIntegrityService:
    """
    Service for QR code generation, signing, and integrity verification
    Implements secure QR payload creation with cryptographic signatures
    """
    
    def __init__(self):
        # Load or generate institution keys
        self.institution_keys = {}
        self.default_private_key = None
        self.default_public_key = None
        
        # QR generation parameters
        self.qr_error_correction = qrcode.constants.ERROR_CORRECT_M
        self.qr_box_size = 10
        self.qr_border = 4
        
        # Signature parameters
        self.signature_algorithm = "ECDSA"
        self.hash_algorithm = "SHA256"
        
        # Initialize default keys
        self._initialize_keys()
        
        logger.info("QR Integrity Service initialized")
    
    def _initialize_keys(self):
        """Initialize default signing keys"""
        try:
            # In production, load from secure key storage
            # For development, generate temporary keys
            if not self.default_private_key:
                private_key, public_key = generate_key_pair()
                self.default_private_key = private_key
                self.default_public_key = public_key
                logger.info("Generated default signing keys")
            
            # Load institution-specific keys
            self._load_institution_keys()
            
        except Exception as e:
            logger.error(f"Key initialization failed: {str(e)}")
    
    def _load_institution_keys(self):
        """Load institution-specific signing keys"""
        try:
            # In production, load from database or secure storage
            # Placeholder implementation
            self.institution_keys = {
                "default": {
                    "private_key": self.default_private_key,
                    "public_key": self.default_public_key,
                    "key_id": "default_key_001"
                }
            }
        except Exception as e:
            logger.error(f"Institution key loading failed: {str(e)}")
    
    async def generate_certificate_qr(self, 
                                    certificate_data: Dict[str, Any], 
                                    institution_id: str = "default",
                                    include_verification_url: bool = True) -> Tuple[str, Dict[str, Any]]:
        """
        Generate secure QR code for certificate issuance
        Returns QR code data URL and the signed payload
        """
        try:
            # Get institution keys
            institution_keys = self.institution_keys.get(institution_id, self.institution_keys["default"])
            
            # Create QR payload
            qr_payload = await self._create_qr_payload(certificate_data, institution_id, include_verification_url)
            
            # Sign the payload
            signed_payload = await self._sign_qr_payload(qr_payload, institution_keys)
            
            # Generate QR code image with just the verification URL
            certificate_id = certificate_data.get("certificate_id")
            verification_url = f"http://localhost:8000/verify/{certificate_id}/page"
            qr_image_data = await self._generate_simple_qr(verification_url)
            
            logger.info(f"Generated QR code for certificate {certificate_data.get('certificate_id', 'unknown')}")
            
            return qr_image_data, signed_payload
            
        except Exception as e:
            logger.error(f"QR generation failed: {str(e)}")
            raise Exception(f"Failed to generate certificate QR: {str(e)}")
    
    async def verify_qr_integrity(self, qr_data: str, 
                                extracted_fields: Optional[Dict[str, Any]] = None) -> QRIntegrityCheck:
        """
        Verify QR code integrity and signature
        """
        try:
            # Parse QR data
            try:
                qr_payload = json.loads(qr_data)
            except json.JSONDecodeError:
                return QRIntegrityCheck(
                    qr_detected=True,
                    qr_decoded=False,
                    error_message="Invalid JSON in QR code"
                )
            
            # Verify signature
            signature_valid = await self._verify_qr_signature(qr_payload)
            
            # Verify issuer
            issuer_verified = await self._verify_issuer(qr_payload)
            
            # Check field consistency if extracted fields provided
            certificate_id_match = False
            issue_date_match = False
            
            if extracted_fields:
                certificate_id_match = self._check_certificate_id_match(qr_payload, extracted_fields)
                issue_date_match = self._check_issue_date_match(qr_payload, extracted_fields)
            
            return QRIntegrityCheck(
                qr_detected=True,
                qr_decoded=True,
                qr_payload=qr_payload,
                signature_valid=signature_valid,
                issuer_verified=issuer_verified,
                certificate_id_match=certificate_id_match,
                issue_date_match=issue_date_match
            )
            
        except Exception as e:
            logger.error(f"QR verification failed: {str(e)}")
            return QRIntegrityCheck(
                qr_detected=True,
                qr_decoded=False,
                error_message=str(e)
            )
    
    async def _create_qr_payload(self, certificate_data: Dict[str, Any], 
                               institution_id: str, 
                               include_verification_url: bool) -> Dict[str, Any]:
        """Create the core QR payload before signing"""
        try:
            # Extract comprehensive certificate information
            core_data = {
                "certificate_id": certificate_data.get("certificate_id"),
                "student_name": certificate_data.get("name") or certificate_data.get("student_name"),
                "roll_no": certificate_data.get("roll_no"),
                "course_name": certificate_data.get("course_name"),
                "institution": certificate_data.get("institution"),
                "institution_name": certificate_data.get("institution_name"),
                "department": certificate_data.get("department"),
                "issue_date": certificate_data.get("issue_date"),
                "year": certificate_data.get("year"),
                "grade": certificate_data.get("grade"),
                "cgpa": certificate_data.get("cgpa"),
                "status": certificate_data.get("status", "issued"),
                "source": certificate_data.get("source", "digital")
            }
            
            # Remove None values
            core_data = {k: v for k, v in core_data.items() if v is not None}
            
            # Create payload
            payload = {
                "version": "1.0",
                "type": "certificate_verification",
                "issuer_id": institution_id,
                "issued_at": datetime.utcnow().isoformat(),
                "expires_at": (datetime.utcnow() + timedelta(days=365*10)).isoformat(),  # 10 years
                "data": core_data
            }
            
            # Add verification URL if requested
            if include_verification_url:
                certificate_id = core_data.get("certificate_id")
                payload["verification_url"] = f"http://localhost:8000/verify/{certificate_id}/page"
            
            # Add image hash if available
            if "image_hash" in certificate_data:
                payload["image_hash"] = certificate_data["image_hash"]
            
            return payload
            
        except Exception as e:
            logger.error(f"QR payload creation failed: {str(e)}")
            raise
    
    async def _sign_qr_payload(self, payload: Dict[str, Any], 
                             institution_keys: Dict[str, str]) -> Dict[str, Any]:
        """Sign the QR payload with institution private key"""
        try:
            # Serialize payload for signing
            payload_str = json.dumps(payload, sort_keys=True, separators=(',', ':'))
            
            # Sign the payload
            private_key = institution_keys["private_key"]
            signature, public_key = sign_data(payload_str, private_key)
            
            # Create signed payload
            signed_payload = {
                "payload": payload,
                "signature": signature,
                "public_key": public_key,
                "key_id": institution_keys.get("key_id", "unknown"),
                "algorithm": self.signature_algorithm,
                "signed_at": datetime.utcnow().isoformat()
            }
            
            return signed_payload
            
        except Exception as e:
            logger.error(f"QR payload signing failed: {str(e)}")
            raise
    
    async def _generate_simple_qr(self, url: str) -> str:
        """Generate a simple QR code with just a URL"""
        try:
            # Create QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=self.qr_error_correction,
                box_size=self.qr_box_size,
                border=self.qr_border,
            )
            qr.add_data(url)
            qr.make(fit=True)
            
            # Create QR code image
            qr_img = qr.make_image(fill_color="black", back_color="white")
            
            # Convert to base64 data URL
            img_buffer = io.BytesIO()
            qr_img.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            
            import base64
            img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
            data_url = f"data:image/png;base64,{img_base64}"
            
            return data_url
            
        except Exception as e:
            logger.error(f"Simple QR generation failed: {str(e)}")
            raise

    async def _generate_qr_image(self, signed_payload: Dict[str, Any]) -> str:
        """Generate QR code image from signed payload"""
        try:
            # Convert payload to JSON string
            payload_json = json.dumps(signed_payload, separators=(',', ':'))
            
            # Create QR code
            qr = qrcode.QRCode(
                version=None,  # Auto-determine version
                error_correction=self.qr_error_correction,
                box_size=self.qr_box_size,
                border=self.qr_border,
            )
            
            qr.add_data(payload_json)
            qr.make(fit=True)
            
            # Create QR code image
            qr_image = qr.make_image(fill_color="black", back_color="white")
            
            # Convert to base64 data URL
            img_buffer = io.BytesIO()
            qr_image.save(img_buffer, format='PNG')
            img_data = img_buffer.getvalue()
            
            # Return as data URL
            img_base64 = base64.b64encode(img_data).decode('utf-8')
            data_url = f"data:image/png;base64,{img_base64}"
            
            return data_url
            
        except Exception as e:
            logger.error(f"QR image generation failed: {str(e)}")
            raise
    
    async def _verify_qr_signature(self, qr_payload: Dict[str, Any]) -> bool:
        """Verify the QR code digital signature"""
        try:
            if "signature" not in qr_payload or "payload" not in qr_payload:
                return False
            
            signature = qr_payload["signature"]
            payload = qr_payload["payload"]
            public_key = qr_payload.get("public_key")
            
            if not public_key:
                # Try to get public key from issuer
                issuer_id = payload.get("issuer_id")
                if issuer_id in self.institution_keys:
                    public_key = self.institution_keys[issuer_id]["public_key"]
                else:
                    logger.warning(f"No public key found for issuer: {issuer_id}")
                    return False
            
            # Serialize payload for verification
            payload_str = json.dumps(payload, sort_keys=True, separators=(',', ':'))
            
            # Verify signature
            return verify_signature(payload_str, signature, public_key)
            
        except Exception as e:
            logger.error(f"QR signature verification failed: {str(e)}")
            return False
    
    async def _verify_issuer(self, qr_payload: Dict[str, Any]) -> bool:
        """Verify the QR code issuer is known and trusted"""
        try:
            payload = qr_payload.get("payload", {})
            issuer_id = payload.get("issuer_id")
            
            if not issuer_id:
                return False
            
            # Check if issuer is in our trusted list
            if issuer_id in self.institution_keys:
                return True
            
            # In production, this could query a database of trusted institutions
            logger.warning(f"Unknown issuer: {issuer_id}")
            return False
            
        except Exception as e:
            logger.error(f"Issuer verification failed: {str(e)}")
            return False
    
    def _check_certificate_id_match(self, qr_payload: Dict[str, Any], 
                                   extracted_fields: Dict[str, Any]) -> bool:
        """Check if certificate ID in QR matches extracted field"""
        try:
            qr_cert_id = qr_payload.get("payload", {}).get("data", {}).get("certificate_id", "").upper().strip()
            extracted_cert_id = extracted_fields.get("certificate_id", "").upper().strip()
            
            return qr_cert_id == extracted_cert_id and qr_cert_id != ""
            
        except Exception:
            return False
    
    def _check_issue_date_match(self, qr_payload: Dict[str, Any], 
                               extracted_fields: Dict[str, Any]) -> bool:
        """Check if issue date in QR matches extracted field"""
        try:
            qr_date = qr_payload.get("payload", {}).get("data", {}).get("issue_date", "").strip()
            extracted_date = extracted_fields.get("issue_date", "").strip()
            
            # Normalize dates for comparison
            qr_date_norm = self._normalize_date(qr_date)
            extracted_date_norm = self._normalize_date(extracted_date)
            
            return qr_date_norm == extracted_date_norm and qr_date_norm != ""
            
        except Exception:
            return False
    
    def _normalize_date(self, date_str: str) -> str:
        """Normalize date string for comparison"""
        if not date_str:
            return ""
        
        # Try to parse and reformat date
        try:
            # Common date formats
            from datetime import datetime
            
            for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y"]:
                try:
                    dt = datetime.strptime(date_str, fmt)
                    return dt.strftime("%Y-%m-%d")  # Standard format
                except ValueError:
                    continue
            
            # If no format matches, return original
            return date_str.strip()
            
        except Exception:
            return date_str.strip()
    
    def _generate_verification_id(self, certificate_data: Dict[str, Any]) -> str:
        """Generate unique verification ID for certificate"""
        try:
            # Create deterministic ID based on certificate data
            cert_string = json.dumps(certificate_data, sort_keys=True)
            hash_obj = hashlib.sha256(cert_string.encode())
            return f"qr_{hash_obj.hexdigest()[:16]}"
            
        except Exception:
            # Fallback to timestamp-based ID
            return f"qr_{int(time.time())}"
    
    async def generate_verification_qr(self, verification_id: str, 
                                     verification_url: str = None) -> str:
        """Generate QR code for public verification"""
        try:
            if not verification_url:
                verification_url = f"{settings.API_VERSION}/verify/{verification_id}"
            
            # Create simple verification payload
            verification_payload = {
                "type": "verification_link",
                "verification_id": verification_id,
                "url": verification_url,
                "generated_at": datetime.utcnow().isoformat()
            }
            
            # Generate QR code (no signature needed for verification links)
            qr_image_data = await self._generate_qr_image(verification_payload)
            
            return qr_image_data
            
        except Exception as e:
            logger.error(f"Verification QR generation failed: {str(e)}")
            raise
    
    async def create_integrity_hash(self, image: Image.Image, 
                                  certificate_data: Dict[str, Any]) -> Dict[str, str]:
        """Create integrity hashes for image and data"""
        try:
            # Generate image hash
            img_hash = generate_image_hash(image.tobytes())
            
            # Generate perceptual hash
            import imagehash
            phash = str(imagehash.phash(image))
            
            # Generate data hash
            data_string = json.dumps(certificate_data, sort_keys=True)
            data_hash = hashlib.sha256(data_string.encode()).hexdigest()
            
            # Combined integrity hash
            combined_data = f"{img_hash}:{data_hash}"
            combined_hash = hashlib.sha256(combined_data.encode()).hexdigest()
            
            return {
                "image_hash": img_hash,
                "perceptual_hash": phash,
                "data_hash": data_hash,
                "integrity_hash": combined_hash
            }
            
        except Exception as e:
            logger.error(f"Integrity hash creation failed: {str(e)}")
            return {}
    
    async def verify_integrity_hash(self, image: Image.Image, 
                                  certificate_data: Dict[str, Any],
                                  expected_hashes: Dict[str, str]) -> Dict[str, bool]:
        """Verify integrity hashes against expected values"""
        try:
            # Generate current hashes
            current_hashes = await self.create_integrity_hash(image, certificate_data)
            
            # Compare hashes
            verification_results = {}
            
            for hash_type, expected_hash in expected_hashes.items():
                current_hash = current_hashes.get(hash_type)
                verification_results[hash_type] = (current_hash == expected_hash)
            
            return verification_results
            
        except Exception as e:
            logger.error(f"Integrity hash verification failed: {str(e)}")
            return {}
    
    def get_public_key(self, institution_id: str = "default") -> Optional[str]:
        """Get public key for institution"""
        try:
            institution_keys = self.institution_keys.get(institution_id)
            if institution_keys:
                return institution_keys["public_key"]
            return None
            
        except Exception as e:
            logger.error(f"Public key retrieval failed: {str(e)}")
            return None
    
    async def add_institution_key(self, institution_id: str, 
                                private_key: str, 
                                public_key: str,
                                key_id: str = None) -> bool:
        """Add or update institution signing keys"""
        try:
            if not key_id:
                key_id = f"{institution_id}_key_{int(time.time())}"
            
            self.institution_keys[institution_id] = {
                "private_key": private_key,
                "public_key": public_key,
                "key_id": key_id,
                "added_at": datetime.utcnow().isoformat()
            }
            
            logger.info(f"Added keys for institution: {institution_id}")
            return True
            
        except Exception as e:
            logger.error(f"Institution key addition failed: {str(e)}")
            return False
