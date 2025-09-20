"""
Gemini API-based certificate data extraction service
Replaces complex layer protection with simple AI extraction
"""
import os
import google.generativeai as genai
from dotenv import load_dotenv
import json
import base64
from PIL import Image
import io
from typing import Dict, Any, Optional
import logging

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class GeminiExtractionService:
    """Service for extracting certificate data using Google's Gemini API"""
    
    def __init__(self):
        """Initialize the Gemini API service"""
        # Ensure .env is loaded
        load_dotenv()
        self.api_key = os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash-preview-05-20')
        
    def extract_certificate_data(self, image_data: bytes) -> Dict[str, Any]:
        """
        Extract certificate data from image using Gemini API
        
        Args:
            image_data: Raw image bytes
            
        Returns:
            Dictionary containing extracted certificate data
        """
        try:
            # Create PIL Image from bytes
            image = Image.open(io.BytesIO(image_data))
            
            # Define extraction prompt
            prompt_text = """
            From this certificate image, extract the following information and return it as a JSON object:

            {
                "name": "full_name_of_student",
                "roll_no": "student_roll_number", 
                "certificate_no": "certificate_identification_number",
                "course": "course_name",
                "month": "month_of_completion",
                "year": "year_of_completion",
                "grade": "final_grade_or_score",
                "institution": "institution_name",
                "issued_date": "date_when_certificate_was_issued"
            }

            Make sure the response is a single, valid JSON object and nothing else.
            If any field is not present in the certificate, return null for that field.
            """
            
            # Prepare prompt parts
            prompt_parts = [prompt_text, image]
            
            logger.info("Calling Gemini API for certificate extraction...")
            response = self.model.generate_content(prompt_parts)
            
            # Extract JSON from response
            json_start = response.text.find('{')
            json_end = response.text.rfind('}') + 1
            
            if json_start != -1 and json_end != -1:
                json_string = response.text[json_start:json_end]
                extracted_data = json.loads(json_string)
                
                logger.info("Successfully extracted certificate data")
                return {
                    "success": True,
                    "data": extracted_data,
                    "raw_response": response.text
                }
            else:
                logger.error(f"Could not find valid JSON in response: {response.text}")
                return {
                    "success": False,
                    "error": "Could not extract valid JSON from API response",
                    "raw_response": response.text
                }
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            return {
                "success": False,
                "error": f"Failed to parse JSON response: {str(e)}",
                "raw_response": response.text if 'response' in locals() else None
            }
        except Exception as e:
            logger.error(f"Error in certificate extraction: {e}")
            return {
                "success": False,
                "error": f"Extraction failed: {str(e)}",
                "raw_response": None
            }
    
    def extract_from_base64(self, base64_image: str) -> Dict[str, Any]:
        """
        Extract certificate data from base64 encoded image
        
        Args:
            base64_image: Base64 encoded image string
            
        Returns:
            Dictionary containing extracted certificate data
        """
        try:
            # Decode base64 image
            image_data = base64.b64decode(base64_image)
            return self.extract_certificate_data(image_data)
        except Exception as e:
            logger.error(f"Error decoding base64 image: {e}")
            return {
                "success": False,
                "error": f"Failed to decode base64 image: {str(e)}",
                "raw_response": None
            }
    
    def extract_from_file_path(self, file_path: str) -> Dict[str, Any]:
        """
        Extract certificate data from image file
        
        Args:
            file_path: Path to the image file
            
        Returns:
            Dictionary containing extracted certificate data
        """
        try:
            with open(file_path, "rb") as image_file:
                image_data = image_file.read()
            return self.extract_certificate_data(image_data)
        except FileNotFoundError:
            logger.error(f"Image file not found: {file_path}")
            return {
                "success": False,
                "error": f"Image file not found: {file_path}",
                "raw_response": None
            }
        except Exception as e:
            logger.error(f"Error reading image file: {e}")
            return {
                "success": False,
                "error": f"Failed to read image file: {str(e)}",
                "raw_response": None
            }

# Global instance
gemini_extraction_service = GeminiExtractionService()
