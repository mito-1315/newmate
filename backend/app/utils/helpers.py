"""
Utility functions for certificate verification system
"""
import hashlib
import logging
import qrcode
import base64
import io
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric.utils import encode_dss_signature, decode_dss_signature
from cryptography.exceptions import InvalidSignature
import json

def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """Setup logging configuration"""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('logs/app.log', mode='a')
        ]
    )
    return logging.getLogger(__name__)

def generate_image_hash(image_data: bytes) -> str:
    """Generate SHA256 hash of image data"""
    return hashlib.sha256(image_data).hexdigest()

def generate_secure_token(length: int = 32) -> str:
    """Generate secure random token"""
    import secrets
    return secrets.token_urlsafe(length)

def create_qr_code(data: str, size: int = 10) -> str:
    """Create QR code image and return as base64 data URL"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=size,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64
    img_buffer = io.BytesIO()
    img.save(img_buffer, format='PNG')
    img_data = img_buffer.getvalue()
    img_base64 = base64.b64encode(img_data).decode('utf-8')
    
    return f"data:image/png;base64,{img_base64}"

def generate_key_pair() -> Tuple[str, str]:
    """Generate ECDSA key pair for signing"""
    try:
        # Generate private key
        private_key = ec.generate_private_key(ec.SECP256R1())
        
        # Get public key
        public_key = private_key.public_key()
        
        # Serialize private key
        private_pem = private_key.private_key_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ).decode('utf-8')
        
        # Serialize public key
        public_pem = public_key.public_key_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode('utf-8')
        
        return private_pem, public_pem
        
    except Exception as e:
        raise Exception(f"Key generation failed: {str(e)}")

def sign_data(data: str, private_key_pem: str) -> Tuple[str, str]:
    """Sign data with private key and return signature + public key"""
    try:
        # Load private key
        private_key = serialization.load_pem_private_key(
            private_key_pem.encode('utf-8'),
            password=None
        )
        
        # Sign data
        signature = private_key.sign(
            data.encode('utf-8'),
            ec.ECDSA(hashes.SHA256())
        )
        
        # Encode signature as base64
        signature_b64 = base64.b64encode(signature).decode('utf-8')
        
        # Get public key
        public_key = private_key.public_key()
        public_key_pem = public_key.public_key_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode('utf-8')
        
        return signature_b64, public_key_pem
        
    except Exception as e:
        raise Exception(f"Signing failed: {str(e)}")

def verify_signature(data: str, signature_b64: str, public_key_pem: str) -> bool:
    """Verify signature with public key"""
    try:
        # Load public key
        public_key = serialization.load_pem_public_key(
            public_key_pem.encode('utf-8')
        )
        
        # Decode signature
        signature = base64.b64decode(signature_b64)
        
        # Verify signature
        public_key.verify(
            signature,
            data.encode('utf-8'),
            ec.ECDSA(hashes.SHA256())
        )
        
        return True
        
    except InvalidSignature:
        return False
    except Exception as e:
        logging.error(f"Signature verification error: {str(e)}")
        return False

def process_image(image_data: bytes) -> Dict[str, Any]:
    """Process uploaded image and extract metadata"""
    try:
        from PIL import Image
        
        # Open image
        img = Image.open(io.BytesIO(image_data))
        
        # Get basic metadata
        metadata = {
            "format": img.format,
            "mode": img.mode,
            "size": img.size,
            "has_transparency": img.mode in ("RGBA", "LA") or "transparency" in img.info,
            "file_size": len(image_data)
        }
        
        # Get EXIF data if available
        if hasattr(img, '_getexif') and img._getexif():
            metadata["exif"] = dict(img._getexif())
        
        return metadata
        
    except Exception as e:
        logging.error(f"Image processing error: {str(e)}")
        return {"error": str(e)}

def normalize_text(text: str) -> str:
    """Normalize text for better matching"""
    import re
    
    # Convert to lowercase
    text = text.lower()
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove special characters except alphanumeric and spaces
    text = re.sub(r'[^a-z0-9\s]', '', text)
    
    return text.strip()

def calculate_similarity(text1: str, text2: str) -> float:
    """Calculate text similarity using simple Levenshtein distance"""
    def levenshtein_distance(s1, s2):
        if len(s1) < len(s2):
            return levenshtein_distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
    
    # Normalize texts
    norm_text1 = normalize_text(text1)
    norm_text2 = normalize_text(text2)
    
    if not norm_text1 or not norm_text2:
        return 0.0
    
    # Calculate distance
    distance = levenshtein_distance(norm_text1, norm_text2)
    max_len = max(len(norm_text1), len(norm_text2))
    
    # Convert to similarity (0-1)
    similarity = 1 - (distance / max_len)
    return max(0.0, similarity)

def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0B"
    
    size_names = ["B", "KB", "MB", "GB"]
    import math
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    
    return f"{s} {size_names[i]}"

def validate_file_type(filename: str, allowed_extensions: set) -> bool:
    """Validate file type based on extension"""
    if not filename:
        return False
    
    extension = filename.lower().split('.')[-1] if '.' in filename else ''
    return extension in allowed_extensions

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage"""
    import re
    
    # Remove path components
    filename = filename.split('/')[-1].split('\\')[-1]
    
    # Remove dangerous characters
    filename = re.sub(r'[^\w\-_\.]', '_', filename)
    
    # Limit length
    if len(filename) > 255:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        filename = name[:250] + ('.' + ext if ext else '')
    
    return filename

def create_audit_log_entry(action: str, user_id: Optional[str] = None, 
                          resource_type: Optional[str] = None,
                          resource_id: Optional[str] = None,
                          details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Create audit log entry"""
    return {
        "action": action,
        "user_id": user_id,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "details": details or {},
        "timestamp": datetime.utcnow().isoformat()
    }

def mask_sensitive_data(data: Dict[str, Any], sensitive_keys: set = None) -> Dict[str, Any]:
    """Mask sensitive data in dictionary"""
    if sensitive_keys is None:
        sensitive_keys = {"password", "secret", "key", "token", "signature"}
    
    masked_data = {}
    for key, value in data.items():
        if any(sensitive_key in key.lower() for sensitive_key in sensitive_keys):
            masked_data[key] = "*" * min(len(str(value)), 8) if value else None
        elif isinstance(value, dict):
            masked_data[key] = mask_sensitive_data(value, sensitive_keys)
        else:
            masked_data[key] = value
    
    return masked_data