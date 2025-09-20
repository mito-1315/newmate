"""
Layer 3 - Seal & Signature Verification Service
Implements object detection and verification for seals and signatures:
- YOLOv8/Detectron2 for seal/signature detection
- Siamese CNN for signature verification
- Template matching + classifier for seal verification
- QR code detection and signature verification
"""
import time
import logging
import cv2
import numpy as np
from PIL import Image, ImageDraw
from typing import List, Dict, Any, Optional, Tuple
import asyncio
from concurrent.futures import ThreadPoolExecutor
import json
import base64
from pyzbar import pyzbar
import qrcode

# Deep learning imports (with fallbacks)
try:
    import torch
    import torchvision.transforms as transforms
    from torchvision.models import resnet18
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False

from ..models import SignatureVerification, QRIntegrityCheck, TamperType
from ..config import settings
from ..utils.helpers import verify_signature

logger = logging.getLogger(__name__)

class Layer3SignatureService:
    """
    Layer 3: Seal and signature verification using computer vision and ML
    Detects and verifies seals, signatures, and QR codes for authenticity
    """
    
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=2)
        
        # Initialize object detection models
        self.yolo_model = None
        self.seal_detector = None
        self.signature_detector = None
        
        # Initialize verification models
        self.siamese_model = None
        self.seal_classifier = None
        
        # Load known templates and signatures
        self.known_seals = {}
        self.known_signatures = {}
        self.institution_keys = {}
        
        # Detection parameters
        self.detection_confidence = 0.5
        self.verification_threshold = 0.8
        
        self._initialize_models()
        logger.info("Layer 3 Signature Service initialized")
    
    def _initialize_models(self):
        """Initialize detection and verification models"""
        try:
            # Initialize YOLO for object detection
            if YOLO_AVAILABLE:
                # In production, use a trained model for seals/signatures
                # self.yolo_model = YOLO('path/to/trained_model.pt')
                logger.info("YOLO model ready for initialization")
            
            # Initialize Siamese network for signature verification
            if TORCH_AVAILABLE:
                self.siamese_model = self._create_siamese_model()
                logger.info("Siamese model initialized")
            
            # Load institution public keys
            self._load_institution_keys()
            
        except Exception as e:
            logger.warning(f"Model initialization warning: {str(e)}")
    
    def _create_siamese_model(self):
        """Create Siamese network for signature verification"""
        if not TORCH_AVAILABLE:
            return None
        
        try:
            # Simple Siamese network based on ResNet
            class SiameseNetwork(torch.nn.Module):
                def __init__(self):
                    super(SiameseNetwork, self).__init__()
                    self.backbone = resnet18(pretrained=True)
                    self.backbone.fc = torch.nn.Linear(self.backbone.fc.in_features, 256)
                    
                def forward(self, x1, x2):
                    output1 = self.backbone(x1)
                    output2 = self.backbone(x2)
                    return output1, output2
            
            model = SiameseNetwork()
            model.eval()
            return model
            
        except Exception as e:
            logger.error(f"Failed to create Siamese model: {str(e)}")
            return None
    
    def _load_institution_keys(self):
        """Load institution public keys for QR verification"""
        try:
            # In production, load from database
            # For now, use placeholder keys
            self.institution_keys = {
                "university_tech": "-----BEGIN PUBLIC KEY-----\nMFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAE...",
                "college_eng": "-----BEGIN PUBLIC KEY-----\nMFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAE..."
            }
        except Exception as e:
            logger.error(f"Failed to load institution keys: {str(e)}")
    
    async def verify_seals_and_signatures(self, image: Image.Image, 
                                         extracted_fields: Dict[str, Any]) -> SignatureVerification:
        """
        Main verification pipeline for seals and signatures
        """
        start_time = time.time()
        
        try:
            cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            # Run detection and verification in parallel
            tasks = [
                self._detect_seals(cv_image),
                self._detect_signatures(cv_image),
                self._detect_and_verify_qr(image, extracted_fields)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            seal_results = results[0] if not isinstance(results[0], Exception) else {}
            signature_results = results[1] if not isinstance(results[1], Exception) else {}
            qr_results = results[2] if not isinstance(results[2], Exception) else {}
            
            # Verify detected seals
            seal_matches = await self._verify_detected_seals(cv_image, seal_results.get('detections', []))
            
            # Verify detected signatures
            signature_matches = await self._verify_detected_signatures(cv_image, signature_results.get('detections', []))
            
            # Calculate authenticity scores
            seal_score = self._calculate_seal_authenticity_score(seal_matches)
            signature_score = self._calculate_signature_authenticity_score(signature_matches)
            
            # Create verification result
            verification = SignatureVerification(
                seals_detected=len(seal_results.get('detections', [])),
                signatures_detected=len(signature_results.get('detections', [])),
                seal_matches=seal_matches,
                signature_matches=signature_matches,
                seal_authenticity_score=seal_score,
                signature_authenticity_score=signature_score,
                qr_signature_valid=qr_results.get('signature_valid', False),
                qr_issuer_verified=qr_results.get('issuer_verified', False),
                verification_time=time.time() - start_time
            )
            
            logger.info(f"Signature verification completed in {verification.verification_time:.2f}s")
            return verification
            
        except Exception as e:
            logger.error(f"Signature verification failed: {str(e)}")
            return SignatureVerification(
                verification_time=time.time() - start_time
            )
    
    async def _detect_seals(self, cv_image: np.ndarray) -> Dict[str, Any]:
        """Detect seals using object detection and traditional CV"""
        try:
            # Convert to PIL for processing
            pil_image = Image.fromarray(cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB))
            
            # Method 1: YOLO detection (if available)
            yolo_detections = await self._yolo_detect_seals(cv_image)
            
            # Method 2: Traditional CV detection
            cv_detections = await self._traditional_seal_detection(cv_image)
            
            # Combine and filter detections
            all_detections = yolo_detections + cv_detections
            filtered_detections = self._filter_duplicate_detections(all_detections)
            
            return {
                'detections': filtered_detections,
                'method': 'combined'
            }
            
        except Exception as e:
            logger.error(f"Seal detection failed: {str(e)}")
            return {'detections': []}
    
    async def _detect_signatures(self, cv_image: np.ndarray) -> Dict[str, Any]:
        """Detect signatures using multiple methods"""
        try:
            # Method 1: YOLO detection (if available)
            yolo_detections = await self._yolo_detect_signatures(cv_image)
            
            # Method 2: Traditional CV detection
            cv_detections = await self._traditional_signature_detection(cv_image)
            
            # Combine and filter detections
            all_detections = yolo_detections + cv_detections
            filtered_detections = self._filter_duplicate_detections(all_detections)
            
            return {
                'detections': filtered_detections,
                'method': 'combined'
            }
            
        except Exception as e:
            logger.error(f"Signature detection failed: {str(e)}")
            return {'detections': []}
    
    async def _yolo_detect_seals(self, cv_image: np.ndarray) -> List[Dict[str, Any]]:
        """Detect seals using YOLO model"""
        if not self.yolo_model:
            return []
        
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                self.executor,
                self._yolo_detect_seals_sync,
                cv_image
            )
        except Exception as e:
            logger.error(f"YOLO seal detection failed: {str(e)}")
            return []
    
    def _yolo_detect_seals_sync(self, cv_image: np.ndarray) -> List[Dict[str, Any]]:
        """Synchronous YOLO seal detection"""
        try:
            # Placeholder for YOLO detection
            # In production, this would run the trained YOLO model
            detections = []
            
            # results = self.yolo_model(cv_image)
            # for result in results:
            #     boxes = result.boxes
            #     for box in boxes:
            #         if box.conf > self.detection_confidence and box.cls == 0:  # seal class
            #             x1, y1, x2, y2 = box.xyxy[0].tolist()
            #             detections.append({
            #                 'bbox': [int(x1), int(y1), int(x2), int(y2)],
            #                 'confidence': float(box.conf),
            #                 'class': 'seal',
            #                 'method': 'yolo'
            #             })
            
            return detections
            
        except Exception as e:
            logger.error(f"YOLO seal detection sync failed: {str(e)}")
            return []
    
    async def _yolo_detect_signatures(self, cv_image: np.ndarray) -> List[Dict[str, Any]]:
        """Detect signatures using YOLO model"""
        if not self.yolo_model:
            return []
        
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                self.executor,
                self._yolo_detect_signatures_sync,
                cv_image
            )
        except Exception as e:
            logger.error(f"YOLO signature detection failed: {str(e)}")
            return []
    
    def _yolo_detect_signatures_sync(self, cv_image: np.ndarray) -> List[Dict[str, Any]]:
        """Synchronous YOLO signature detection"""
        try:
            # Placeholder for YOLO detection
            detections = []
            
            # Similar to seal detection but for signature class
            
            return detections
            
        except Exception as e:
            logger.error(f"YOLO signature detection sync failed: {str(e)}")
            return []
    
    async def _traditional_seal_detection(self, cv_image: np.ndarray) -> List[Dict[str, Any]]:
        """Detect seals using traditional computer vision"""
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                self.executor,
                self._traditional_seal_detection_sync,
                cv_image
            )
        except Exception as e:
            logger.error(f"Traditional seal detection failed: {str(e)}")
            return []
    
    def _traditional_seal_detection_sync(self, cv_image: np.ndarray) -> List[Dict[str, Any]]:
        """Synchronous traditional seal detection"""
        try:
            detections = []
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
            
            # Method 1: Circle detection for circular seals
            circles = cv2.HoughCircles(
                gray,
                cv2.HOUGH_GRADIENT,
                dp=1,
                minDist=50,
                param1=50,
                param2=30,
                minRadius=20,
                maxRadius=100
            )
            
            if circles is not None:
                circles = np.round(circles[0, :]).astype("int")
                for (x, y, r) in circles:
                    # Verify it's actually a seal by analyzing the region
                    if self._verify_circular_seal_region(gray, x, y, r):
                        detections.append({
                            'bbox': [x - r, y - r, x + r, y + r],
                            'confidence': 0.7,
                            'class': 'circular_seal',
                            'method': 'hough_circles'
                        })
            
            # Method 2: Contour detection for rectangular seals
            contours, _ = cv2.findContours(gray, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if 1000 < area < 10000:  # Filter by area
                    x, y, w, h = cv2.boundingRect(contour)
                    aspect_ratio = w / h
                    
                    # Check if it could be a rectangular seal
                    if 0.7 <= aspect_ratio <= 1.5:
                        if self._verify_rectangular_seal_region(gray, x, y, w, h):
                            detections.append({
                                'bbox': [x, y, x + w, y + h],
                                'confidence': 0.6,
                                'class': 'rectangular_seal',
                                'method': 'contour'
                            })
            
            return detections
            
        except Exception as e:
            logger.error(f"Traditional seal detection sync failed: {str(e)}")
            return []
    
    def _verify_circular_seal_region(self, gray: np.ndarray, x: int, y: int, r: int) -> bool:
        """Verify if a circular region contains a seal"""
        try:
            # Extract circular region
            mask = np.zeros(gray.shape, dtype=np.uint8)
            cv2.circle(mask, (x, y), r, 255, -1)
            
            # Extract region
            region = cv2.bitwise_and(gray, mask)
            circular_region = region[y-r:y+r, x-r:x+r]
            
            if circular_region.size == 0:
                return False
            
            # Check for text-like patterns (seals usually contain text)
            edges = cv2.Canny(circular_region, 50, 150)
            edge_density = np.sum(edges > 0) / edges.size
            
            # Check for regular patterns
            if 0.1 < edge_density < 0.4:  # Typical range for seals
                return True
            
            return False
            
        except Exception:
            return False
    
    def _verify_rectangular_seal_region(self, gray: np.ndarray, x: int, y: int, w: int, h: int) -> bool:
        """Verify if a rectangular region contains a seal"""
        try:
            region = gray[y:y+h, x:x+w]
            
            if region.size == 0:
                return False
            
            # Check for text patterns
            edges = cv2.Canny(region, 50, 150)
            edge_density = np.sum(edges > 0) / edges.size
            
            # Check for border-like structures
            border_thickness = 5
            if h > 2 * border_thickness and w > 2 * border_thickness:
                inner_region = region[border_thickness:-border_thickness, border_thickness:-border_thickness]
                border_region = region.copy()
                border_region[border_thickness:-border_thickness, border_thickness:-border_thickness] = 0
                
                border_density = np.sum(border_region > 0) / border_region.size
                
                if border_density > 0.3 and 0.1 < edge_density < 0.4:
                    return True
            
            return False
            
        except Exception:
            return False
    
    async def _traditional_signature_detection(self, cv_image: np.ndarray) -> List[Dict[str, Any]]:
        """Detect signatures using traditional computer vision"""
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                self.executor,
                self._traditional_signature_detection_sync,
                cv_image
            )
        except Exception as e:
            logger.error(f"Traditional signature detection failed: {str(e)}")
            return []
    
    def _traditional_signature_detection_sync(self, cv_image: np.ndarray) -> List[Dict[str, Any]]:
        """Synchronous traditional signature detection"""
        try:
            detections = []
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
            
            # Apply morphological operations to find signature-like regions
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
            
            # Threshold to get binary image
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            
            # Morphological closing to connect signature strokes
            morphed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=2)
            
            # Find contours
            contours, _ = cv2.findContours(morphed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                area = cv2.contourArea(contour)
                
                # Filter by size and aspect ratio
                aspect_ratio = w / h
                
                if (2.0 < aspect_ratio < 8.0 and  # Signatures are typically elongated
                    500 < area < 15000 and        # Reasonable size range
                    w > 50 and h > 15):           # Minimum dimensions
                    
                    if self._verify_signature_region(gray, x, y, w, h):
                        detections.append({
                            'bbox': [x, y, x + w, y + h],
                            'confidence': 0.6,
                            'class': 'signature',
                            'method': 'morphological'
                        })
            
            return detections
            
        except Exception as e:
            logger.error(f"Traditional signature detection sync failed: {str(e)}")
            return []
    
    def _verify_signature_region(self, gray: np.ndarray, x: int, y: int, w: int, h: int) -> bool:
        """Verify if a region contains a signature"""
        try:
            region = gray[y:y+h, x:x+w]
            
            if region.size == 0:
                return False
            
            # Check for handwriting-like characteristics
            edges = cv2.Canny(region, 30, 100)
            
            # Calculate edge statistics
            edge_density = np.sum(edges > 0) / edges.size
            
            # Check for connected components (strokes)
            _, binary = cv2.threshold(region, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(binary)
            
            # Filter out background
            component_areas = stats[1:, cv2.CC_STAT_AREA]  # Exclude background
            
            # Signatures typically have multiple connected components (strokes)
            if (0.05 < edge_density < 0.3 and          # Reasonable edge density
                len(component_areas) > 2 and           # Multiple strokes
                np.std(component_areas) > 10):         # Varied stroke sizes
                return True
            
            return False
            
        except Exception:
            return False
    
    async def _detect_and_verify_qr(self, image: Image.Image, extracted_fields: Dict[str, Any]) -> Dict[str, Any]:
        """Detect and verify QR codes in the certificate"""
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                self.executor,
                self._qr_detection_and_verification_sync,
                image,
                extracted_fields
            )
        except Exception as e:
            logger.error(f"QR detection and verification failed: {str(e)}")
            return {}
    
    def _qr_detection_and_verification_sync(self, image: Image.Image, 
                                          extracted_fields: Dict[str, Any]) -> Dict[str, Any]:
        """Synchronous QR detection and verification"""
        try:
            # Convert to OpenCV format
            cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            # Detect QR codes using pyzbar
            qr_codes = pyzbar.decode(cv_image)
            
            if not qr_codes:
                return {
                    'qr_detected': False,
                    'signature_valid': False,
                    'issuer_verified': False
                }
            
            # Process first QR code found
            qr_code = qr_codes[0]
            qr_data = qr_code.data.decode('utf-8')
            
            try:
                qr_payload = json.loads(qr_data)
            except json.JSONDecodeError:
                return {
                    'qr_detected': True,
                    'qr_decoded': False,
                    'signature_valid': False,
                    'issuer_verified': False
                }
            
            # Verify QR signature
            signature_valid = self._verify_qr_signature(qr_payload)
            
            # Verify issuer
            issuer_verified = self._verify_qr_issuer(qr_payload, extracted_fields)
            
            # Check field consistency
            field_consistency = self._check_qr_field_consistency(qr_payload, extracted_fields)
            
            return {
                'qr_detected': True,
                'qr_decoded': True,
                'qr_payload': qr_payload,
                'signature_valid': signature_valid,
                'issuer_verified': issuer_verified,
                'field_consistency': field_consistency
            }
            
        except Exception as e:
            logger.error(f"QR processing error: {str(e)}")
            return {
                'qr_detected': False,
                'signature_valid': False,
                'issuer_verified': False
            }
    
    def _verify_qr_signature(self, qr_payload: Dict[str, Any]) -> bool:
        """Verify QR code digital signature"""
        try:
            if 'signature' not in qr_payload or 'data' not in qr_payload:
                return False
            
            # Extract signature and data
            signature = qr_payload['signature']
            data = qr_payload['data']
            public_key = qr_payload.get('public_key')
            
            if not public_key:
                # Try to get public key from issuer
                issuer_id = qr_payload.get('issuer_id')
                if issuer_id in self.institution_keys:
                    public_key = self.institution_keys[issuer_id]
                else:
                    return False
            
            # Verify signature using the helper function
            data_str = json.dumps(data, sort_keys=True)
            return verify_signature(data_str, signature, public_key)
            
        except Exception as e:
            logger.error(f"QR signature verification failed: {str(e)}")
            return False
    
    def _verify_qr_issuer(self, qr_payload: Dict[str, Any], extracted_fields: Dict[str, Any]) -> bool:
        """Verify QR code issuer against extracted institution"""
        try:
            qr_issuer = qr_payload.get('data', {}).get('issuer', '').lower()
            extracted_institution = extracted_fields.get('institution', '').lower()
            
            if not qr_issuer or not extracted_institution:
                return False
            
            # Simple string matching (can be enhanced with fuzzy matching)
            return qr_issuer in extracted_institution or extracted_institution in qr_issuer
            
        except Exception as e:
            logger.error(f"QR issuer verification failed: {str(e)}")
            return False
    
    def _check_qr_field_consistency(self, qr_payload: Dict[str, Any], 
                                   extracted_fields: Dict[str, Any]) -> Dict[str, bool]:
        """Check consistency between QR fields and extracted fields"""
        try:
            qr_data = qr_payload.get('data', {})
            consistency = {}
            
            # Check certificate ID
            qr_cert_id = qr_data.get('certificate_id', '').upper()
            extracted_cert_id = extracted_fields.get('certificate_id', '').upper()
            consistency['certificate_id'] = qr_cert_id == extracted_cert_id
            
            # Check issue date
            qr_date = qr_data.get('issue_date', '')
            extracted_date = extracted_fields.get('issue_date', '')
            consistency['issue_date'] = qr_date == extracted_date
            
            # Check student name (more flexible matching)
            qr_name = qr_data.get('student_name', '').lower().strip()
            extracted_name = extracted_fields.get('name', '').lower().strip()
            consistency['name'] = qr_name == extracted_name
            
            return consistency
            
        except Exception as e:
            logger.error(f"QR field consistency check failed: {str(e)}")
            return {}
    
    def _filter_duplicate_detections(self, detections: List[Dict[str, Any]], 
                                   overlap_threshold: float = 0.5) -> List[Dict[str, Any]]:
        """Filter duplicate detections using Non-Maximum Suppression"""
        if not detections:
            return []
        
        # Sort by confidence
        detections.sort(key=lambda x: x.get('confidence', 0), reverse=True)
        
        filtered = []
        
        for detection in detections:
            bbox1 = detection['bbox']
            is_duplicate = False
            
            for existing in filtered:
                bbox2 = existing['bbox']
                
                # Calculate IoU
                iou = self._calculate_iou(bbox1, bbox2)
                
                if iou > overlap_threshold:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                filtered.append(detection)
        
        return filtered
    
    def _calculate_iou(self, bbox1: List[int], bbox2: List[int]) -> float:
        """Calculate Intersection over Union of two bounding boxes"""
        try:
            x1_1, y1_1, x2_1, y2_1 = bbox1
            x1_2, y1_2, x2_2, y2_2 = bbox2
            
            # Calculate intersection
            x1_i = max(x1_1, x1_2)
            y1_i = max(y1_1, y1_2)
            x2_i = min(x2_1, x2_2)
            y2_i = min(y2_1, y2_2)
            
            if x2_i <= x1_i or y2_i <= y1_i:
                return 0.0
            
            intersection = (x2_i - x1_i) * (y2_i - y1_i)
            
            # Calculate union
            area1 = (x2_1 - x1_1) * (y2_1 - y1_1)
            area2 = (x2_2 - x1_2) * (y2_2 - y1_2)
            union = area1 + area2 - intersection
            
            if union == 0:
                return 0.0
            
            return intersection / union
            
        except Exception:
            return 0.0
    
    async def _verify_detected_seals(self, cv_image: np.ndarray, 
                                   detections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Verify detected seals against known templates"""
        try:
            verified_seals = []
            
            for detection in detections:
                bbox = detection['bbox']
                x1, y1, x2, y2 = bbox
                
                # Extract seal region
                seal_region = cv_image[y1:y2, x1:x2]
                
                if seal_region.size == 0:
                    continue
                
                # Verify against known seals
                match_score = await self._match_seal_template(seal_region)
                
                verification_result = {
                    'detection': detection,
                    'match_score': match_score,
                    'verified': match_score > self.verification_threshold,
                    'template_matched': 'unknown'  # Would be specific template ID
                }
                
                verified_seals.append(verification_result)
            
            return verified_seals
            
        except Exception as e:
            logger.error(f"Seal verification failed: {str(e)}")
            return []
    
    async def _verify_detected_signatures(self, cv_image: np.ndarray, 
                                        detections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Verify detected signatures using Siamese network"""
        try:
            verified_signatures = []
            
            for detection in detections:
                bbox = detection['bbox']
                x1, y1, x2, y2 = bbox
                
                # Extract signature region
                signature_region = cv_image[y1:y2, x1:x2]
                
                if signature_region.size == 0:
                    continue
                
                # Verify using Siamese network
                match_score = await self._match_signature_siamese(signature_region)
                
                verification_result = {
                    'detection': detection,
                    'match_score': match_score,
                    'verified': match_score > self.verification_threshold,
                    'reference_matched': 'unknown'  # Would be specific signature ID
                }
                
                verified_signatures.append(verification_result)
            
            return verified_signatures
            
        except Exception as e:
            logger.error(f"Signature verification failed: {str(e)}")
            return []
    
    async def _match_seal_template(self, seal_region: np.ndarray) -> float:
        """Match seal against known templates"""
        try:
            # Placeholder for template matching
            # In production, this would use sophisticated template matching
            # or learned classifiers
            
            # Simple template matching approach
            gray_seal = cv2.cvtColor(seal_region, cv2.COLOR_BGR2GRAY)
            
            # Resize to standard size
            standard_size = (64, 64)
            resized_seal = cv2.resize(gray_seal, standard_size)
            
            # Calculate features (histogram, texture, etc.)
            hist = cv2.calcHist([resized_seal], [0], None, [256], [0, 256])
            
            # Placeholder score - in production, compare against known templates
            match_score = 0.5  # Placeholder
            
            return match_score
            
        except Exception as e:
            logger.error(f"Seal template matching failed: {str(e)}")
            return 0.0
    
    async def _match_signature_siamese(self, signature_region: np.ndarray) -> float:
        """Match signature using Siamese network"""
        try:
            if not self.siamese_model:
                return 0.5  # Neutral score if model not available
            
            # Placeholder for Siamese network verification
            # In production, this would:
            # 1. Preprocess the signature region
            # 2. Run through Siamese network against known signatures
            # 3. Return similarity score
            
            match_score = 0.5  # Placeholder
            
            return match_score
            
        except Exception as e:
            logger.error(f"Signature Siamese matching failed: {str(e)}")
            return 0.0
    
    def _calculate_seal_authenticity_score(self, seal_matches: List[Dict[str, Any]]) -> float:
        """Calculate overall seal authenticity score"""
        if not seal_matches:
            return 0.0
        
        # Take the maximum match score from all detected seals
        max_score = max(match['match_score'] for match in seal_matches)
        return max_score
    
    def _calculate_signature_authenticity_score(self, signature_matches: List[Dict[str, Any]]) -> float:
        """Calculate overall signature authenticity score"""
        if not signature_matches:
            return 0.0
        
        # Take the maximum match score from all detected signatures
        max_score = max(match['match_score'] for match in signature_matches)
        return max_score
