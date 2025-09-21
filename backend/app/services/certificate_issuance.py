"""
Certificate Issuance Service for Universities
Handles the complete issuance workflow from student data to QR-enabled certificates
"""
import json
import time
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import io
import qrcode

from ..models import ExtractedFields, AttestationData
from ..config import settings
from .qr_integrity import QRIntegrityService
from .supabase_client import SupabaseClient
from ..utils.helpers import generate_image_hash, generate_secure_token

logger = logging.getLogger(__name__)

class CertificateIssuanceService:
    """
    Service for universities to issue certificates with QR codes and digital attestation
    """
    
    def __init__(self, supabase_client: SupabaseClient):
        self.supabase_client = supabase_client
        self.qr_service = QRIntegrityService()
        
        # Certificate template settings
        self.template_width = 2480  # A4 at 300 DPI
        self.template_height = 3508
        self.qr_size = 400  # Increased from 200 to 400
        
    async def issue_certificate(self, 
                              certificate_data: Dict[str, Any], 
                              institution_id: str,
                              template_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Complete certificate issuance workflow for universities
        
        Args:
            certificate_data: Student and course information
            institution_id: Issuing institution identifier
            template_path: Optional custom certificate template
            
        Returns:
            Issuance result with QR code, image URLs, and verification data
        """
        try:
            issuance_id = self._generate_issuance_id(certificate_data)
            
            # Step 1: Validate and normalize certificate data
            normalized_data = self._normalize_certificate_data(certificate_data)
            
            # Step 2: Store certificate record in database
            certificate_record = await self._store_certificate_record(
                normalized_data, institution_id, issuance_id
            )
            
            # Step 3: Generate QR code with signed payload
            qr_data_url, signed_payload = await self.qr_service.generate_certificate_qr(
                normalized_data, institution_id, True
            )
            
            logger.info(f"QR data URL generated: {qr_data_url[:100] if qr_data_url else 'None'}...")
            logger.info(f"Signed payload keys: {list(signed_payload.keys()) if signed_payload else 'None'}")
            
            # Step 4: Store the original uploaded image (if available)
            original_image_url = None
            if certificate_data.get("image_data") and certificate_data.get("image_filename"):
                try:
                    original_image_url = await self._store_original_image(
                        certificate_data.get("image_data"), certificate_data.get("image_filename", "certificate.jpg")
                    )
                except Exception as e:
                    logger.warning(f"Failed to store original image: {str(e)}")
                    original_image_url = None
            
            # Step 5: Generate QR-only image (no full certificate)
            certificate_image = await self._generate_qr_only_image(
                normalized_data, qr_data_url
            )
            
            # Step 6: Calculate image fingerprints for QR image
            image_hashes = await self._calculate_image_fingerprints(certificate_image)
            
            # Step 7: Store QR certificate image and hashes
            qr_image_url = await self._store_certificate_image(
                certificate_image, issuance_id, image_hashes
            )
            
            # Step 8: Generate digital attestation
            attestation = await self._create_digital_attestation(
                certificate_record, signed_payload, image_hashes
            )
            
            # Step 9: Update certificate record with final data (use original image URL if available)
            await self._finalize_certificate_record(
                certificate_record["id"], original_image_url, image_hashes, attestation
            )
            
            # Step 9: Generate public verification URL
            verification_url = f"{settings.API_VERSION}/verify/{issuance_id}"
            
            return {
                "issuance_id": issuance_id,
                "certificate_id": normalized_data["certificate_id"],
                "status": "issued",
                "certificate_image_url": qr_image_url,  # QR-only image for download
                "original_image_url": original_image_url,  # Original uploaded image (may be None)
                "qr_code_data": qr_data_url,
                "verification_url": verification_url,
                "attestation": attestation,
                "issued_at": datetime.utcnow().isoformat(),
                "expires_at": signed_payload["payload"]["expires_at"]
            }
            
        except Exception as e:
            logger.error(f"Certificate issuance failed: {str(e)}")
            raise Exception(f"Certificate issuance failed: {str(e)}")
    
    async def bulk_issue_certificates(self, 
                                    certificates_data: List[Dict[str, Any]], 
                                    institution_id: str) -> Dict[str, Any]:
        """
        Bulk certificate issuance from CSV/ERP data
        """
        try:
            results = {
                "successful": [],
                "failed": [],
                "total": len(certificates_data)
            }
            
            for i, cert_data in enumerate(certificates_data):
                try:
                    result = await self.issue_certificate(cert_data, institution_id)
                    results["successful"].append({
                        "row": i + 1,
                        "certificate_id": result["certificate_id"],
                        "student_name": cert_data.get("student_name", ""),
                        "course_name": cert_data.get("course_name", ""),
                        "issuance_id": result["issuance_id"],
                        "verification_url": result["verification_url"],
                        "certificate_image_url": result.get("certificate_image_url"),
                        "qr_code_data": result.get("qr_code_data")
                    })
                    
                except Exception as e:
                    results["failed"].append({
                        "row": i + 1,
                        "certificate_id": cert_data.get("certificate_id", "unknown"),
                        "error": str(e)
                    })
            
            # Generate bulk issuance report
            report = await self._generate_bulk_report(results, institution_id)
            
            return {
                **results,
                "report_url": report["url"],
                "processed_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Bulk issuance failed: {str(e)}")
            raise
    
    def _normalize_certificate_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize and validate certificate data"""
        normalized = {
            "certificate_id": data.get("certificate_id") or data.get("cert_no"),
            "student_name": data.get("student_name") or data.get("name"),
            "roll_no": data.get("roll_no") or data.get("roll_number"),
            "course_name": data.get("course_name") or data.get("course"),
            "institution": data.get("institution"),
            "issue_date": data.get("issue_date") or datetime.now().strftime("%Y-%m-%d"),
            "year": data.get("year") or str(datetime.now().year),
            "grade": data.get("grade")
        }
        
        # Validation
        required_fields = ["certificate_id", "student_name", "course_name", "institution"]
        for field in required_fields:
            if not normalized.get(field):
                raise ValueError(f"Required field missing: {field}")
        
        return normalized
    
    async def _store_certificate_record(self, data: Dict[str, Any], 
                                      institution_id: str, 
                                      issuance_id: str) -> Dict[str, Any]:
        """Store certificate record in issued_certificates table"""
        try:
            logger.info(f"Storing certificate record for {data.get('student_name')}")
            logger.info(f"SupabaseClient type: {type(self.supabase_client)}")
            logger.info(f"SupabaseClient has client attribute: {hasattr(self.supabase_client, 'client')}")
            
            certificate_record = {
                "id": data["certificate_id"],  # Use 'id' as primary key
                "certificate_id": data["certificate_id"],
                "student_name": data["student_name"],
                "roll_number": data.get("roll_no", ""),
                "course_name": data["course_name"],
                "institution": data["institution"],
                "issue_date": data.get("issue_date", datetime.now().strftime("%Y-%m-%d")),
                "year": data.get("year", str(datetime.now().year)),
                "grade": data.get("grade", ""),
                "status": "issued"
            }
            
            logger.info(f"Certificate record prepared: {certificate_record}")
            
            # Insert into database
            result = self.supabase_client.client.table("issued_certificates").insert(certificate_record).execute()
            
            if result.data:
                logger.info(f"Certificate stored successfully: {result.data[0]}")
                return result.data[0]
            else:
                raise Exception("Failed to store certificate record")
                
        except Exception as e:
            logger.error(f"Failed to store certificate record: {str(e)}")
            raise
    
    async def _generate_certificate_image(self, 
                                        certificate_data: Dict[str, Any], 
                                        qr_data_url: str,
                                        template_path: Optional[str] = None) -> Image.Image:
        """Generate certificate image with QR code"""
        try:
            # Create certificate image (using template or generating one)
            if template_path:
                # Load custom template
                certificate_img = Image.open(template_path)
            else:
                # Generate basic certificate template
                certificate_img = self._generate_basic_template(certificate_data)
            
            # Add QR code to certificate
            certificate_with_qr = self._add_qr_to_certificate(certificate_img, qr_data_url)
            
            return certificate_with_qr
            
        except Exception as e:
            logger.error(f"Certificate image generation failed: {str(e)}")
            raise
    
    async def _generate_qr_only_image(self, 
                                     certificate_data: Dict[str, Any], 
                                     qr_data_url: str) -> Image.Image:
        """Generate QR-only image with certificate details"""
        try:
            # Create a larger canvas for QR code with details
            qr_canvas_width = 600
            qr_canvas_height = 800
            qr_canvas = Image.new('RGB', (qr_canvas_width, qr_canvas_height), 'white')
            draw = ImageDraw.Draw(qr_canvas)
            
            # Extract QR code from data URL
            if qr_data_url.startswith('data:image/png;base64,'):
                import base64
                qr_data = qr_data_url.split(',')[1]
                qr_bytes = base64.b64decode(qr_data)
                qr_img = Image.open(io.BytesIO(qr_bytes))
            else:
                raise ValueError("Invalid QR data URL format")
            
            # Resize QR code to be larger
            qr_size = 500  # Large QR code
            qr_img = qr_img.resize((qr_size, qr_size))
            
            # Position QR code in center
            qr_x = (qr_canvas_width - qr_size) // 2
            qr_y = 50  # Top margin
            
            # Paste QR code onto canvas
            qr_canvas.paste(qr_img, (qr_x, qr_y))
            
            # Add certificate details below QR code
            try:
                # Try to load a font
                font_large = ImageFont.truetype("arial.ttf", 24)
                font_medium = ImageFont.truetype("arial.ttf", 18)
                font_small = ImageFont.truetype("arial.ttf", 14)
            except:
                # Fallback to default font
                font_large = ImageFont.load_default()
                font_medium = ImageFont.load_default()
                font_small = ImageFont.load_default()
            
            # Certificate details
            details_y = qr_y + qr_size + 30
            details = [
                f"Certificate ID: {certificate_data.get('certificate_id', 'N/A')}",
                f"Student: {certificate_data.get('student_name', 'N/A')}",
                f"Course: {certificate_data.get('course_name', 'N/A')}",
                f"Institution: {certificate_data.get('institution', 'N/A')}",
                f"Roll No: {certificate_data.get('roll_no', 'N/A')}",
                f"Grade: {certificate_data.get('grade', 'N/A')}",
                f"Issued: {certificate_data.get('issue_date', 'N/A')}"
            ]
            
            # Draw details
            for i, detail in enumerate(details):
                draw.text((50, details_y + i * 30), detail, fill='black', font=font_medium)
            
            # Add instruction text
            instruction_y = details_y + len(details) * 30 + 20
            draw.text((50, instruction_y), "Scan QR code to verify certificate", 
                     fill='blue', font=font_small)
            
            return qr_canvas
            
        except Exception as e:
            logger.error(f"QR-only image generation failed: {str(e)}")
            raise

    def _generate_basic_template(self, data: Dict[str, Any]) -> Image.Image:
        """Generate a basic certificate template"""
        # Create a white background
        img = Image.new('RGB', (self.template_width, self.template_height), 'white')
        draw = ImageDraw.Draw(img)
        
        # Try to load fonts (fallback to default if not available)
        try:
            title_font = ImageFont.truetype("arial.ttf", 120)
            header_font = ImageFont.truetype("arial.ttf", 80)
            body_font = ImageFont.truetype("arial.ttf", 60)
        except:
            title_font = ImageFont.load_default()
            header_font = ImageFont.load_default()
            body_font = ImageFont.load_default()
        
        # Certificate border
        border_margin = 100
        draw.rectangle([border_margin, border_margin, 
                       self.template_width - border_margin, 
                       self.template_height - border_margin], 
                      outline='black', width=10)
        
        # Institution name
        institution_text = data["institution"]
        draw.text((self.template_width//2, 400), institution_text, 
                 fill='black', font=header_font, anchor='mm')
        
        # Certificate title
        title_text = "CERTIFICATE OF COMPLETION"
        draw.text((self.template_width//2, 600), title_text, 
                 fill='black', font=title_font, anchor='mm')
        
        # "This is to certify that"
        draw.text((self.template_width//2, 800), "This is to certify that", 
                 fill='black', font=body_font, anchor='mm')
        
        # Student name
        name_text = data["student_name"]
        draw.text((self.template_width//2, 1000), name_text, 
                 fill='black', font=header_font, anchor='mm')
        
        # Course completion text
        course_text = f"has successfully completed the course"
        draw.text((self.template_width//2, 1200), course_text, 
                 fill='black', font=body_font, anchor='mm')
        
        # Course name
        draw.text((self.template_width//2, 1400), data["course_name"], 
                 fill='black', font=header_font, anchor='mm')
        
        # Grade (if available)
        if data.get("grade"):
            grade_text = f"with grade: {data['grade']}"
            draw.text((self.template_width//2, 1600), grade_text, 
                     fill='black', font=body_font, anchor='mm')
        
        # Issue date
        date_text = f"Issued on: {data['issue_date']}"
        draw.text((self.template_width//2, 1900), date_text, 
                 fill='black', font=body_font, anchor='mm')
        
        # Certificate ID
        id_text = f"Certificate ID: {data['certificate_id']}"
        draw.text((self.template_width//2, 2100), id_text, 
                 fill='black', font=body_font, anchor='mm')
        
        return img
    
    def _add_qr_to_certificate(self, certificate_img: Image.Image, qr_data_url: str) -> Image.Image:
        """Add QR code to certificate image"""
        try:
            # Extract base64 data from data URL
            if qr_data_url.startswith('data:image/png;base64,'):
                import base64
                qr_data = qr_data_url.split(',')[1]
                qr_bytes = base64.b64decode(qr_data)
                qr_img = Image.open(io.BytesIO(qr_bytes))
            else:
                raise ValueError("Invalid QR data URL format")
            
            # Resize QR code
            qr_img = qr_img.resize((self.qr_size, self.qr_size))
            
            # Position QR code (bottom right corner)
            qr_x = certificate_img.width - self.qr_size - 150
            qr_y = certificate_img.height - self.qr_size - 150
            
            # Paste QR code onto certificate
            certificate_img.paste(qr_img, (qr_x, qr_y))
            
            # Add QR label
            draw = ImageDraw.Draw(certificate_img)
            try:
                label_font = ImageFont.truetype("arial.ttf", 40)
            except:
                label_font = ImageFont.load_default()
            
            draw.text((qr_x + self.qr_size//2, qr_y + self.qr_size + 20), 
                     "Scan to Verify", fill='black', font=label_font, anchor='mm')
            
            return certificate_img
            
        except Exception as e:
            logger.error(f"Failed to add QR code to certificate: {str(e)}")
            # Return original certificate if QR addition fails
            return certificate_img
    
    async def _calculate_image_fingerprints(self, image: Image.Image) -> Dict[str, str]:
        """Calculate image fingerprints for integrity verification"""
        try:
            # Convert image to bytes for SHA256
            img_bytes = io.BytesIO()
            image.save(img_bytes, format='PNG', optimize=True)
            img_data = img_bytes.getvalue()
            
            # Use QR service to calculate comprehensive hashes
            hashes = await self.qr_service.create_integrity_hash(image, {
                "image_size": len(img_data),
                "dimensions": image.size,
                "format": "PNG"
            })
            
            return hashes
            
        except Exception as e:
            logger.error(f"Image fingerprinting failed: {str(e)}")
            return {}
    
    async def _store_original_image(self, image_data: bytes, filename: str) -> str:
        """Store the original uploaded certificate image"""
        try:
            # Upload original image to Supabase Storage
            original_filename = f"certificates/original/{filename}"
            image_url = await self.supabase_client.upload_certificate_image(image_data, original_filename)
            logger.info(f"Original image stored: {image_url}")
            return image_url
        except Exception as e:
            logger.error(f"Failed to store original image: {str(e)}")
            raise

    async def _store_certificate_image(self, 
                                     image: Image.Image, 
                                     issuance_id: str,
                                     image_hashes: Dict[str, str]) -> str:
        """Store certificate image in Supabase Storage"""
        try:
            # Convert image to bytes
            img_bytes = io.BytesIO()
            image.save(img_bytes, format='PNG', optimize=True, quality=95)
            img_data = img_bytes.getvalue()
            
            # Upload to Supabase Storage
            filename = f"certificates/issued/{issuance_id}.png"
            try:
                image_url = await self.supabase_client.upload_certificate_image(img_data, filename)
                return image_url
            except Exception as upload_error:
                logger.warning(f"Image upload failed: {str(upload_error)}")
                # Fallback to base64 data URL
                import base64
                image_url = f"data:image/png;base64,{base64.b64encode(img_data).decode()}"
                logger.info("Using base64 data URL as fallback")
                return image_url
            
        except Exception as e:
            logger.error(f"Image storage failed: {str(e)}")
            raise
    
    async def _create_digital_attestation(self, 
                                        certificate_record: Dict[str, Any],
                                        signed_payload: Dict[str, Any],
                                        image_hashes: Dict[str, str]) -> AttestationData:
        """Create digital attestation for the issued certificate"""
        try:
            # Enhanced attestation payload
            attestation_payload = {
                "certificate_record": certificate_record,
                "qr_payload": signed_payload,
                "image_integrity": image_hashes,
                "issuance_timestamp": datetime.utcnow().isoformat(),
                "attestation_type": "certificate_issuance",
                "version": "1.0"
            }
            
            # Store attestation (with required signature field)
            attestation_data = {
                "verification_id": certificate_record["id"],
                "signature": signed_payload["signature"],
                "public_key": signed_payload["public_key"],
                "payload": signed_payload["payload"]
            }
            
            attestation_id = await self.supabase_client.store_attestation(attestation_data)
            
            return AttestationData(
                attestation_id=attestation_id,
                signature=signed_payload["signature"],
                public_key=signed_payload["public_key"],
                created_at=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Digital attestation creation failed: {str(e)}")
            raise
    
    async def _finalize_certificate_record(self, 
                                         certificate_id: str,
                                         image_url: str,
                                         image_hashes: Dict[str, str],
                                         attestation: AttestationData):
        """Finalize certificate record with image and attestation data"""
        try:
            update_data = {
                "status": "issued"
            }
            
            # Only add image data if available
            if image_url:
                update_data["image_url"] = image_url
            if image_hashes:
                update_data["image_hashes"] = image_hashes
            
            result = self.supabase_client.client.table("issued_certificates").update(update_data).eq("id", certificate_id).execute()
            logger.info(f"Updated certificate record with status: issued")
            if image_url:
                logger.info(f"Image URL: {image_url}")
            
        except Exception as e:
            logger.error(f"Failed to finalize certificate record: {str(e)}")
            raise
    
    async def _generate_bulk_report(self, results: Dict[str, Any], institution_id: str) -> Dict[str, Any]:
        """Generate bulk issuance report"""
        try:
            report_data = {
                "institution_id": institution_id,
                "total_processed": results["total"],
                "successful_count": len(results["successful"]),
                "failed_count": len(results["failed"]),
                "success_rate": len(results["successful"]) / results["total"] * 100,
                "successful_certificates": results["successful"],
                "failed_certificates": results["failed"],
                "generated_at": datetime.utcnow().isoformat()
            }
            
            # Store report (could be extended to generate PDF)
            report_id = generate_secure_token(16)
            
            # For now, return the report data
            # In production, you might store this in a reports table
            return {
                "report_id": report_id,
                "url": f"/api/reports/{report_id}",
                "data": report_data
            }
            
        except Exception as e:
            logger.error(f"Bulk report generation failed: {str(e)}")
            return {"report_id": "error", "url": None, "data": {}}
    
    def _generate_issuance_id(self, certificate_data: Dict[str, Any]) -> str:
        """Generate unique issuance ID"""
        import hashlib
        
        # Create deterministic ID based on certificate data and timestamp
        data_string = json.dumps({
            "certificate_id": certificate_data.get("certificate_id"),
            "student_name": certificate_data.get("student_name"),
            "timestamp": str(int(time.time()))
        }, sort_keys=True)
        
        hash_obj = hashlib.sha256(data_string.encode())
        return f"iss_{hash_obj.hexdigest()[:16]}"
