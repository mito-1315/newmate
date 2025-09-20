"""
Donut model and LLM wrapper for certificate field extraction
"""
import torch
from transformers import DonutProcessor, VisionEncoderDecoderModel
from PIL import Image
import json
import logging
from typing import Dict, Any, Optional
import asyncio
from concurrent.futures import ThreadPoolExecutor

from ..config import settings
from ..models import ExtractedFields

logger = logging.getLogger(__name__)

class LLMClient:
    """Client for Donut model and other LLM services"""
    
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.processor = None
        self.model = None
        self.executor = ThreadPoolExecutor(max_workers=2)
        self._load_donut_model()
    
    def _load_donut_model(self):
        """Load the Donut model for document understanding"""
        try:
            logger.info(f"Loading Donut model: {settings.DONUT_MODEL_PATH}")
            self.processor = DonutProcessor.from_pretrained(settings.DONUT_MODEL_PATH)
            self.model = VisionEncoderDecoderModel.from_pretrained(settings.DONUT_MODEL_PATH)
            
            if self.device == "cuda":
                self.model.half()
            
            self.model.to(self.device)
            self.model.eval()
            logger.info("Donut model loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load Donut model: {str(e)}")
            self.processor = None
            self.model = None
    
    async def extract_certificate_fields(self, image: Image.Image) -> ExtractedFields:
        """Extract fields from certificate image using Donut"""
        if not self.model or not self.processor:
            logger.warning("Donut model not available, returning empty fields")
            return ExtractedFields()
        
        try:
            # Run extraction in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self.executor, 
                self._extract_fields_sync, 
                image
            )
            return result
            
        except Exception as e:
            logger.error(f"Error extracting fields with Donut: {str(e)}")
            return ExtractedFields()
    
    def _extract_fields_sync(self, image: Image.Image) -> ExtractedFields:
        """Synchronous field extraction"""
        try:
            # Prepare image for Donut
            pixel_values = self.processor(image, return_tensors="pt").pixel_values
            pixel_values = pixel_values.to(self.device)
            
            if self.device == "cuda":
                pixel_values = pixel_values.half()
            
            # Task prompt for certificate parsing
            task_prompt = "<s_certificate>"
            decoder_input_ids = self.processor.tokenizer(
                task_prompt, 
                add_special_tokens=False, 
                return_tensors="pt"
            ).input_ids
            decoder_input_ids = decoder_input_ids.to(self.device)
            
            # Generate
            outputs = self.model.generate(
                pixel_values,
                decoder_input_ids=decoder_input_ids,
                max_length=self.model.decoder.config.max_position_embeddings,
                pad_token_id=self.processor.tokenizer.pad_token_id,
                eos_token_id=self.processor.tokenizer.eos_token_id,
                use_cache=True,
                bad_words_ids=[[self.processor.tokenizer.unk_token_id]],
                return_dict_in_generate=True,
            )
            
            # Decode output
            sequence = self.processor.batch_decode(outputs.sequences)[0]
            sequence = sequence.replace(self.processor.tokenizer.eos_token, "").replace(self.processor.tokenizer.pad_token, "")
            sequence = sequence.replace(task_prompt, "")
            
            # Parse JSON output
            try:
                parsed_data = json.loads(sequence)
                return self._map_to_extracted_fields(parsed_data)
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse Donut output as JSON: {sequence}")
                return self._extract_fallback_fields(sequence)
                
        except Exception as e:
            logger.error(f"Error in synchronous field extraction: {str(e)}")
            return ExtractedFields()
    
    def _map_to_extracted_fields(self, parsed_data: Dict[str, Any]) -> ExtractedFields:
        """Map Donut output to ExtractedFields model"""
        return ExtractedFields(
            name=parsed_data.get("name") or parsed_data.get("student_name"),
            institution=parsed_data.get("institution") or parsed_data.get("university"),
            course_name=parsed_data.get("course") or parsed_data.get("course_name"),
            issue_date=parsed_data.get("date") or parsed_data.get("issue_date"),
            certificate_id=parsed_data.get("id") or parsed_data.get("certificate_id"),
            grade=parsed_data.get("grade") or parsed_data.get("score"),
            additional_fields={k: v for k, v in parsed_data.items() 
                             if k not in ["name", "student_name", "institution", 
                                        "university", "course", "course_name", 
                                        "date", "issue_date", "id", "certificate_id", 
                                        "grade", "score"]}
        )
    
    def _extract_fallback_fields(self, text: str) -> ExtractedFields:
        """Fallback extraction using simple text processing"""
        # Basic pattern matching as fallback
        fields = ExtractedFields()
        
        # This is a simple fallback - in production you might want more sophisticated NLP
        lines = text.lower().split('\n')
        for line in lines:
            if 'name' in line and not fields.name:
                # Extract name after 'name'
                parts = line.split('name')
                if len(parts) > 1:
                    fields.name = parts[1].strip(' :').title()
            
            elif 'university' in line or 'institution' in line and not fields.institution:
                # Extract institution
                for word in ['university', 'institution', 'college']:
                    if word in line:
                        parts = line.split(word)
                        if len(parts) > 1:
                            fields.institution = parts[1].strip(' :').title()
                        break
        
        return fields
    
    async def validate_with_llm(self, extracted_fields: ExtractedFields, image_text: str) -> float:
        """Use LLM to validate extracted fields against image text"""
        # Placeholder for LLM validation
        # In production, you might use OpenAI/Anthropic APIs here
        try:
            # Simple confidence scoring based on field completeness
            filled_fields = sum(1 for field in [
                extracted_fields.name,
                extracted_fields.institution,
                extracted_fields.course_name,
                extracted_fields.issue_date
            ] if field)
            
            confidence = filled_fields / 4.0  # Basic confidence metric
            return min(confidence, 1.0)
            
        except Exception as e:
            logger.error(f"Error in LLM validation: {str(e)}")
            return 0.5  # Default confidence
    
    def __del__(self):
        """Cleanup resources"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)
