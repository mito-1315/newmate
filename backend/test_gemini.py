#!/usr/bin/env python3
"""
Test script for Gemini certificate extraction
"""
import os
import sys
from dotenv import load_dotenv

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from services.gemini_extraction import GeminiExtractionService

def test_gemini_extraction():
    """Test the Gemini extraction service"""
    try:
        # Load environment variables
        load_dotenv()
        
        # Check if API key is available
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            print("❌ GEMINI_API_KEY not found in environment variables")
            print("Please add GEMINI_API_KEY to your .env file")
            return False
        
        print("✅ GEMINI_API_KEY found")
        
        # Initialize the service
        extraction_service = GeminiExtractionService()
        print("✅ Gemini extraction service initialized")
        
        # Test with a sample image (if available)
        test_image_path = "cer3.jpg"  # Same as in your example
        if os.path.exists(test_image_path):
            print(f"✅ Found test image: {test_image_path}")
            
            # Extract data
            result = extraction_service.extract_from_file_path(test_image_path)
            
            if result["success"]:
                print("✅ Extraction successful!")
                print("\nExtracted data:")
                import json
                print(json.dumps(result["data"], indent=2))
            else:
                print("❌ Extraction failed:")
                print(result["error"])
        else:
            print(f"⚠️  Test image not found: {test_image_path}")
            print("Please add a certificate image named 'cer3.jpg' to test extraction")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("Testing Gemini Certificate Extraction")
    print("=" * 40)
    test_gemini_extraction()
