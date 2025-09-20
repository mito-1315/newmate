"""
Utility functions for logging, hashing, image handling, and cryptography
"""
import logging
import hashlib
import imagehash
from PIL import Image
import io
import qrcode
import base64
from typing import Tuple, Optional
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import encode_dss_signature
import secrets
import json
from datetime import datetime

def setup_logging(level: str = "INFO") -> logging.Logger:
    """Setup application logging"""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('certificate_verifier.log')
        ]
    )
    
    # Set specific loggers
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    
    return logging.getLogger(__name__)

async def process_image(file) -> bytes:
    """Process uploaded image file"""
    try:
        # Read file contents
        contents = await file.read()
        
        # Validate image
        image = Image.open(io.BytesIO(contents))
        
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Resize if too large (max 2048x2048)
        max_size = (2048, 2048)
        if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
            image.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # Save processed image to bytes
        output = io.BytesIO()
        image.save(output, format='JPEG', quality=90, optimize=True)
        
        return output.getvalue()
        
    except Exception as e:
        raise ValueError(f"Invalid image file: {str(e)}")

def generate_image_hash(image_data: bytes) -> str:
    """Generate SHA256 hash of image data"""
    return hashlib.sha256(image_data).hexdigest()

def generate_perceptual_hash(image_data: bytes) -> str:
    """Generate perceptual hash for duplicate detection"""
    try:
        image = Image.open(io.BytesIO(image_data))
        phash = imagehash.phash(image)
        return str(phash)
    except Exception as e:
        logging.error(f"Error generating perceptual hash: {str(e)}")
        return ""

def generate_key_pair() -> Tuple[str, str]:
    """Generate ECDSA key pair for signing"""
    private_key = ec.generate_private_key(ec.SECP256R1())
    
    # Serialize private key
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    
    # Serialize public key
    public_key = private_key.public_key()
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    
    return private_pem.decode(), public_pem.decode()

def sign_data(data: str, private_key_pem: Optional[str] = None) -> Tuple[str, str]:
    """Sign data with ECDSA private key"""
    if not private_key_pem:
        # Generate new key pair for dev/testing
        private_key_pem, public_key_pem = generate_key_pair()
    else:
        # Load existing private key
        private_key = serialization.load_pem_private_key(
            private_key_pem.encode(),
            password=None
        )
        public_key_pem = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode()
    
    # Load private key
    private_key = serialization.load_pem_private_key(
        private_key_pem.encode(),
        password=None
    )
    
    # Sign the data
    signature = private_key.sign(
        data.encode(),
        ec.ECDSA(hashes.SHA256())
    )
    
    # Encode signature as base64
    signature_b64 = base64.b64encode(signature).decode()
    
    return signature_b64, public_key_pem

def verify_signature(data: str, signature_b64: str, public_key_pem: str) -> bool:
    """Verify ECDSA signature"""
    try:
        # Load public key
        public_key = serialization.load_pem_public_key(public_key_pem.encode())
        
        # Decode signature
        signature = base64.b64decode(signature_b64)
        
        # Verify signature
        public_key.verify(
            signature,
            data.encode(),
            ec.ECDSA(hashes.SHA256())
        )
        return True
        
    except Exception as e:
        logging.error(f"Signature verification failed: {str(e)}")
        return False

async def create_qr_code(verification_id: str, signature: str) -> str:
    """Create QR code for certificate verification"""
    try:
        # QR code data
        qr_data = {
            "verification_id": verification_id,
            "signature": signature,
            "verify_url": f"https://your-domain.com/verify/{verification_id}",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(json.dumps(qr_data))
        qr.make(fit=True)
        
        # Create QR code image
        qr_image = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to bytes
        img_buffer = io.BytesIO()
        qr_image.save(img_buffer, format='PNG')
        img_data = img_buffer.getvalue()
        
        # For now, return base64 encoded image
        # In production, you'd upload to storage and return URL
        return f"data:image/png;base64,{base64.b64encode(img_data).decode()}"
        
    except Exception as e:
        logging.error(f"Error creating QR code: {str(e)}")
        return ""

def validate_certificate_fields(fields: dict) -> list:
    """Validate certificate field formats"""
    errors = []
    
    # Name validation
    if 'name' in fields and fields['name']:
        if len(fields['name']) < 2:
            errors.append("Name too short")
        if not fields['name'].replace(' ', '').replace('-', '').isalpha():
            errors.append("Name contains invalid characters")
    
    # Date validation
    if 'issue_date' in fields and fields['issue_date']:
        try:
            # Try common date formats
            for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y']:
                try:
                    datetime.strptime(fields['issue_date'], fmt)
                    break
                except ValueError:
                    continue
            else:
                errors.append("Invalid date format")
        except Exception:
            errors.append("Invalid date")
    
    # Certificate ID validation
    if 'certificate_id' in fields and fields['certificate_id']:
        if len(fields['certificate_id']) < 3:
            errors.append("Certificate ID too short")
    
    return errors

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for storage"""
    import re
    # Remove or replace invalid characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Limit length
    sanitized = sanitized[:100]
    return sanitized

def calculate_file_hash(file_path: str) -> str:
    """Calculate SHA256 hash of file"""
    hash_sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()

def generate_secure_token(length: int = 32) -> str:
    """Generate cryptographically secure token"""
    return secrets.token_urlsafe(length)

class ImageProcessor:
    """Image processing utilities"""
    
    @staticmethod
    def enhance_for_ocr(image: Image.Image) -> Image.Image:
        """Enhance image for better OCR results"""
        # Convert to grayscale
        if image.mode != 'L':
            image = image.convert('L')
        
        # Enhance contrast
        from PIL import ImageEnhance
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.5)
        
        # Sharpen
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(1.2)
        
        return image
    
    @staticmethod
    def detect_text_regions(image_data: bytes) -> list:
        """Detect text regions in image (placeholder)"""
        # This would use libraries like OpenCV or specialized text detection models
        # For now, return empty list
        return []
    
    @staticmethod
    def preprocess_for_donut(image: Image.Image) -> Image.Image:
        """Preprocess image specifically for Donut model"""
        # Donut typically expects specific input sizes
        target_size = (1280, 960)  # Common Donut input size
        
        # Resize while maintaining aspect ratio
        image.thumbnail(target_size, Image.Resampling.LANCZOS)
        
        # Create new image with white background
        new_image = Image.new('RGB', target_size, (255, 255, 255))
        
        # Paste resized image centered
        x = (target_size[0] - image.size[0]) // 2
        y = (target_size[1] - image.size[1]) // 2
        new_image.paste(image, (x, y))
        
        return new_image
