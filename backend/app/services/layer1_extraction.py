"""
Layer 1 - Field Extraction Service
Implements Donut primary + OCR fallback + VLM fallback for robust field extraction
"""
import time
import asyncio
import logging
from typing import Dict, Any, Optional, List, Tuple
from PIL import Image
import cv2
import numpy as np
import json
from concurrent.futures import ThreadPoolExecutor
import re
from datetime import datetime

# OCR imports
try:
    import paddleocr
    PADDLE_AVAILABLE = True
except ImportError:
    PADDLE_AVAILABLE = False

try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

# VLM imports (placeholder for BLIP-2/LLaVA)
try:
    from transformers import BlipProcessor, BlipForConditionalGeneration
    VLM_AVAILABLE = True
except ImportError:
    VLM_AVAILABLE = False

from ..models import ExtractedFields, ExtractionMethod
from ..config import settings
from .llm_client import LLMClient

logger = logging.getLogger(__name__)

class Layer1ExtractionService:
    """
    Layer 1: Multi-modal field extraction with fallback mechanisms
    Primary: Donut model for document understanding
    Fallback: OCR ensemble + rule-based extraction
    Extreme fallback: VLM for complex cases
    """
    
    def __init__(self):
        self.llm_client = LLMClient()
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Initialize OCR engines
        self.paddle_ocr = None
        self.tesseract_config = r'--oem 3 --psm 6'
        
        # Initialize VLM (placeholder)
        self.vlm_processor = None
        self.vlm_model = None
        
        # Confidence thresholds
        self.donut_confidence_threshold = 0.7
        self.ocr_confidence_threshold = 0.6
        
        self._initialize_engines()
    
    def _initialize_engines(self):
        """Initialize OCR and VLM engines"""
        try:
            if PADDLE_AVAILABLE:
                self.paddle_ocr = paddleocr.PaddleOCR(
                    use_angle_cls=True, 
                    lang='en',
                    show_log=False
                )
                logger.info("PaddleOCR initialized successfully")
            
            if VLM_AVAILABLE:
                # Initialize BLIP-2 or similar VLM
                self.vlm_processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
                self.vlm_model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
                logger.info("VLM model initialized successfully")
                
        except Exception as e:
            logger.warning(f"Error initializing extraction engines: {str(e)}")
    
    async def extract_fields(self, image: Image.Image, use_fallback: bool = True) -> ExtractedFields:
        """
        Main extraction pipeline with progressive fallback
        """
        start_time = time.time()
        
        try:
            # Step 1: Try Donut primary extraction
            donut_result = await self._extract_with_donut(image)
            
            # Check if Donut result is confident enough
            if self._is_extraction_confident(donut_result):
                donut_result.extraction_time = time.time() - start_time
                donut_result.extraction_method = ExtractionMethod.DONUT_PRIMARY
                logger.info("Donut extraction successful with high confidence")
                return donut_result
            
            if not use_fallback:
                return donut_result
            
            # Step 2: OCR ensemble fallback
            logger.info("Donut confidence low, trying OCR fallback")
            ocr_result = await self._extract_with_ocr_ensemble(image)
            
            # Fuse Donut and OCR results
            fused_result = self._fuse_extraction_results(donut_result, ocr_result)
            
            if self._is_extraction_confident(fused_result):
                fused_result.extraction_time = time.time() - start_time
                fused_result.extraction_method = ExtractionMethod.OCR_FALLBACK
                logger.info("OCR fallback successful")
                return fused_result
            
            # Step 3: VLM extreme fallback for ambiguous cases
            logger.info("OCR confidence still low, trying VLM fallback")
            vlm_result = await self._extract_with_vlm(image, fused_result)
            
            vlm_result.extraction_time = time.time() - start_time
            vlm_result.extraction_method = ExtractionMethod.VLM_FALLBACK
            
            return vlm_result
            
        except Exception as e:
            logger.error(f"Extraction pipeline failed: {str(e)}")
            # Return minimal result with error info
            result = ExtractedFields()
            result.extraction_time = time.time() - start_time
            result.additional_fields = {"extraction_error": str(e)}
            return result
    
    async def _extract_with_donut(self, image: Image.Image) -> ExtractedFields:
        """Extract fields using Donut model with enhanced prompting"""
        try:
            # Use existing LLM client but with enhanced prompting
            result = await self.llm_client.extract_certificate_fields(image)
            
            # Enhanced post-processing for Donut results
            result = self._post_process_donut_result(result, image)
            
            return result
            
        except Exception as e:
            logger.error(f"Donut extraction failed: {str(e)}")
            return ExtractedFields()
    
    async def _extract_with_ocr_ensemble(self, image: Image.Image) -> ExtractedFields:
        """Extract using OCR ensemble with rule-based processing"""
        try:
            # Convert PIL to OpenCV format
            cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            # Run OCR engines in parallel
            tasks = []
            
            if self.paddle_ocr:
                tasks.append(self._run_paddle_ocr(cv_image))
            
            if TESSERACT_AVAILABLE:
                tasks.append(self._run_tesseract_ocr(image))
            
            ocr_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Combine OCR results
            combined_text = self._combine_ocr_results(ocr_results)
            
            # Rule-based field extraction
            extracted_fields = self._extract_fields_from_text(combined_text, image)
            
            return extracted_fields
            
        except Exception as e:
            logger.error(f"OCR ensemble extraction failed: {str(e)}")
            return ExtractedFields()
    
    async def _extract_with_vlm(self, image: Image.Image, previous_result: ExtractedFields) -> ExtractedFields:
        """Extract using Vision-Language Model for complex cases"""
        try:
            if not self.vlm_model or not self.vlm_processor:
                logger.warning("VLM not available, returning previous result")
                return previous_result
            
            # Generate descriptive caption
            inputs = self.vlm_processor(image, return_tensors="pt")
            out = self.vlm_model.generate(**inputs, max_length=150)
            caption = self.vlm_processor.decode(out[0], skip_special_tokens=True)
            
            # Use LLM to extract structured fields from caption
            vlm_fields = self._extract_from_caption(caption, previous_result)
            
            return vlm_fields
            
        except Exception as e:
            logger.error(f"VLM extraction failed: {str(e)}")
            return previous_result
    
    async def _run_paddle_ocr(self, cv_image: np.ndarray) -> List[Tuple[List, Tuple, str]]:
        """Run PaddleOCR extraction"""
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self.executor, 
                self.paddle_ocr.ocr, 
                cv_image
            )
            return result[0] if result and result[0] else []
        except Exception as e:
            logger.error(f"PaddleOCR failed: {str(e)}")
            return []
    
    async def _run_tesseract_ocr(self, image: Image.Image) -> str:
        """Run Tesseract OCR extraction"""
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self.executor,
                pytesseract.image_to_string,
                image,
                self.tesseract_config
            )
            return result
        except Exception as e:
            logger.error(f"Tesseract OCR failed: {str(e)}")
            return ""
    
    def _combine_ocr_results(self, ocr_results: List[Any]) -> str:
        """Combine results from multiple OCR engines"""
        combined_text = ""
        
        for result in ocr_results:
            if isinstance(result, Exception):
                continue
                
            if isinstance(result, list):  # PaddleOCR format
                for item in result:
                    if len(item) >= 2:
                        text = item[1][0] if isinstance(item[1], tuple) else item[1]
                        combined_text += f"{text}\n"
            elif isinstance(result, str):  # Tesseract format
                combined_text += f"{result}\n"
        
        return combined_text
    
    def _extract_fields_from_text(self, text: str, image: Image.Image) -> ExtractedFields:
        """Rule-based field extraction from OCR text"""
        fields = ExtractedFields()
        
        # Clean and normalize text
        text = self._clean_ocr_text(text)
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        # Field extraction patterns
        patterns = {
            'name': [
                r'(?:name|student|candidate)[\s:]+([a-zA-Z\s]+)',
                r'(?:this is to certify that)[\s]*([a-zA-Z\s]+)',
                r'(?:mr|ms|miss)[\s\.]*([a-zA-Z\s]+)'
            ],
            'roll_no': [
                r'(?:roll|reg|registration)[\s]*(?:no|number)[\s:]*([a-zA-Z0-9]+)',
                r'(?:student id|id)[\s:]*([a-zA-Z0-9]+)'
            ],
            'certificate_id': [
                r'(?:certificate|cert)[\s]*(?:no|number|id)[\s:]*([a-zA-Z0-9-]+)',
                r'(?:serial|ref)[\s]*(?:no|number)[\s:]*([a-zA-Z0-9-]+)'
            ],
            'course_name': [
                r'(?:course|program|degree|bachelor|master|diploma)[\s:]*([a-zA-Z\s&]+)',
                r'(?:in the field of|majoring in)[\s]*([a-zA-Z\s&]+)'
            ],
            'institution': [
                r'(?:university|college|institute|school)[\s]*(?:of|for)?[\s]*([a-zA-Z\s&]+)',
                r'([a-zA-Z\s&]*university|college|institute)'
            ],
            'issue_date': [
                r'(?:issued|dated|given)[\s]*(?:on|this)?[\s]*([0-9]{1,2}[/-][0-9]{1,2}[/-][0-9]{2,4})',
                r'([0-9]{1,2}[\s]*(?:st|nd|rd|th)?[\s]*[a-zA-Z]+[\s]*[0-9]{2,4})',
                r'([0-9]{4}[/-][0-9]{1,2}[/-][0-9]{1,2})'
            ],
            'year': [
                r'(?:year|class of|batch)[\s]*([0-9]{4})',
                r'(?:academic year)[\s]*([0-9]{4}-?[0-9]{2,4}?)'
            ],
            'grade': [
                r'(?:grade|cgpa|gpa|percentage|marks)[\s:]*([a-zA-Z0-9\.\s%]+)',
                r'(?:first class|second class|third class|distinction|honors)',
                r'([0-9]\.[0-9]+)[\s]*(?:cgpa|gpa)'
            ]
        }
        
        # Extract fields using patterns
        confidences = {}
        
        for field_name, field_patterns in patterns.items():
            best_match = None
            best_confidence = 0.0
            
            for pattern in field_patterns:
                for line in lines:
                    match = re.search(pattern, line, re.IGNORECASE)
                    if match:
                        value = match.group(1).strip()
                        confidence = self._calculate_pattern_confidence(pattern, line, value)
                        
                        if confidence > best_confidence:
                            best_match = value
                            best_confidence = confidence
            
            if best_match:
                setattr(fields, field_name, best_match)
                confidences[field_name] = best_confidence
        
        fields.field_confidences = confidences
        
        # Detect bounding boxes for important regions
        fields = self._detect_object_locations(fields, image)
        
        return fields
    
    def _detect_object_locations(self, fields: ExtractedFields, image: Image.Image) -> ExtractedFields:
        """Detect locations of photos, seals, signatures using simple heuristics"""
        try:
            # Convert to OpenCV format
            cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
            
            # Detect potential photo regions (rectangular dark regions)
            photo_bbox = self._detect_photo_region(gray)
            if photo_bbox:
                fields.photo_bbox = photo_bbox
            
            # Detect potential seal/stamp regions (circular or square dark regions)
            seal_locations = self._detect_seal_regions(gray)
            fields.seal_locations = seal_locations
            
            # Detect potential signature regions (elongated irregular regions)
            signature_locations = self._detect_signature_regions(gray)
            fields.signature_locations = signature_locations
            
        except Exception as e:
            logger.warning(f"Object detection failed: {str(e)}")
        
        return fields
    
    def _detect_photo_region(self, gray_image: np.ndarray) -> Optional[List[int]]:
        """Detect student photo region using contour analysis"""
        try:
            # Apply edge detection
            edges = cv2.Canny(gray_image, 50, 150)
            
            # Find contours
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Look for rectangular contours that could be photos
            for contour in contours:
                # Approximate contour
                epsilon = 0.02 * cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, epsilon, True)
                
                # Check if it's roughly rectangular
                if len(approx) == 4:
                    x, y, w, h = cv2.boundingRect(contour)
                    
                    # Check aspect ratio and size constraints
                    aspect_ratio = w / h
                    area = w * h
                    
                    # Typical photo dimensions
                    if 0.7 <= aspect_ratio <= 1.5 and 1000 <= area <= 50000:
                        return [x, y, x + w, y + h]
            
            return None
            
        except Exception:
            return None
    
    def _detect_seal_regions(self, gray_image: np.ndarray) -> List[List[int]]:
        """Detect seal/stamp regions"""
        seal_locations = []
        
        try:
            # Use HoughCircles to detect circular seals
            circles = cv2.HoughCircles(
                gray_image,
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
                    # Convert circle to bounding box
                    seal_locations.append([x - r, y - r, x + r, y + r])
            
        except Exception:
            pass
        
        return seal_locations
    
    def _detect_signature_regions(self, gray_image: np.ndarray) -> List[List[int]]:
        """Detect signature regions using morphological operations"""
        signature_locations = []
        
        try:
            # Apply morphological operations to detect signature-like regions
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
            morphed = cv2.morphologyEx(gray_image, cv2.MORPH_CLOSE, kernel)
            
            # Threshold to get binary image
            _, binary = cv2.threshold(morphed, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            
            # Find contours
            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                
                # Check if it could be a signature (elongated shape)
                aspect_ratio = w / h
                area = w * h
                
                if aspect_ratio > 2.0 and 500 <= area <= 10000:
                    signature_locations.append([x, y, x + w, y + h])
            
        except Exception:
            pass
        
        return signature_locations
    
    def _post_process_donut_result(self, result: ExtractedFields, image: Image.Image) -> ExtractedFields:
        """Post-process Donut results with image analysis"""
        # Add object detection to Donut results
        result = self._detect_object_locations(result, image)
        
        # Normalize field values
        result = self._normalize_field_values(result)
        
        return result
    
    def _normalize_field_values(self, fields: ExtractedFields) -> ExtractedFields:
        """Normalize and clean extracted field values"""
        if fields.name:
            fields.name = self._clean_name(fields.name)
        
        if fields.issue_date:
            fields.issue_date = self._normalize_date(fields.issue_date)
        
        if fields.certificate_id:
            fields.certificate_id = fields.certificate_id.upper().strip()
        
        if fields.roll_no:
            fields.roll_no = fields.roll_no.upper().strip()
        
        return fields
    
    def _clean_name(self, name: str) -> str:
        """Clean and format name field"""
        # Remove extra whitespace and capitalize properly
        name = re.sub(r'\s+', ' ', name.strip())
        return ' '.join(word.capitalize() for word in name.split())
    
    def _normalize_date(self, date_str: str) -> str:
        """Normalize date to standard format"""
        # Try to parse various date formats and convert to ISO format
        date_patterns = [
            r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})',
            r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})',
            r'(\d{1,2})\s*(\w+)\s*(\d{4})'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, date_str)
            if match:
                try:
                    # Convert to standard format (you may want to use dateutil.parser)
                    return date_str  # Placeholder - implement proper date parsing
                except:
                    continue
        
        return date_str
    
    def _clean_ocr_text(self, text: str) -> str:
        """Clean OCR text for better pattern matching"""
        # Remove special characters and normalize whitespace
        text = re.sub(r'[^\w\s\-/:.]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def _calculate_pattern_confidence(self, pattern: str, line: str, value: str) -> float:
        """Calculate confidence score for pattern match"""
        base_confidence = 0.5
        
        # Boost confidence based on pattern specificity
        if 'certificate' in pattern.lower():
            base_confidence += 0.2
        if 'name' in pattern.lower():
            base_confidence += 0.15
        
        # Boost confidence based on value quality
        if len(value) > 3:
            base_confidence += 0.1
        if re.match(r'^[A-Za-z\s]+$', value):  # Only letters and spaces
            base_confidence += 0.1
        
        return min(base_confidence, 1.0)
    
    def _is_extraction_confident(self, fields: ExtractedFields) -> bool:
        """Check if extraction results are confident enough"""
        if not fields.field_confidences:
            return False
        
        # Check if we have core fields with good confidence
        core_fields = ['name', 'certificate_id', 'institution']
        confident_core_fields = 0
        
        for field in core_fields:
            if hasattr(fields, field) and getattr(fields, field):
                confidence = fields.field_confidences.get(field, 0.0)
                if confidence >= 0.7:
                    confident_core_fields += 1
        
        return confident_core_fields >= 2
    
    def _fuse_extraction_results(self, donut_result: ExtractedFields, ocr_result: ExtractedFields) -> ExtractedFields:
        """Fuse results from Donut and OCR with intelligent selection"""
        fused = ExtractedFields()
        
        # Merge field confidences
        donut_confidences = donut_result.field_confidences or {}
        ocr_confidences = ocr_result.field_confidences or {}
        
        # For each field, take the result with higher confidence
        all_fields = set(donut_confidences.keys()) | set(ocr_confidences.keys())
        
        for field in all_fields:
            donut_conf = donut_confidences.get(field, 0.0)
            ocr_conf = ocr_confidences.get(field, 0.0)
            
            donut_value = getattr(donut_result, field, None)
            ocr_value = getattr(ocr_result, field, None)
            
            if donut_conf > ocr_conf and donut_value:
                setattr(fused, field, donut_value)
                fused.field_confidences[field] = donut_conf
            elif ocr_value:
                setattr(fused, field, ocr_value)
                fused.field_confidences[field] = ocr_conf
        
        # Merge location data
        fused.photo_bbox = donut_result.photo_bbox or ocr_result.photo_bbox
        fused.seal_locations = list(set(donut_result.seal_locations + ocr_result.seal_locations))
        fused.signature_locations = list(set(donut_result.signature_locations + ocr_result.signature_locations))
        
        return fused
    
    def _extract_from_caption(self, caption: str, previous_result: ExtractedFields) -> ExtractedFields:
        """Extract fields from VLM caption (placeholder implementation)"""
        # This would use the caption to fill missing fields or correct existing ones
        # For now, just return the previous result
        result = previous_result
        result.additional_fields["vlm_caption"] = caption
        return result
