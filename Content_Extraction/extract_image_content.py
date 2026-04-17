#!/usr/bin/env python3
"""
Modular Image Content Extractor
Extracts image content and descriptions from SCORM packages with OCR capabilities
"""

import os
import json
import hashlib
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    env_file = Path(".env")
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    try:
                        key, value = line.strip().split('=', 1)
                        os.environ[key] = value
                    except ValueError:
                        continue

# Import required libraries
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("Warning: Pillow not available. Install with: pip install Pillow")

try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    print("Warning: pytesseract not available. Install with: pip install pytesseract")

class ImageContentExtractor:
    """Extract image content and descriptions from SCORM packages."""
    
    def __init__(self, scorm_path: str, output_dir: str = "image_extraction_output"):
        self.scorm_path = Path(scorm_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Content storage
        self.extracted_content = []
        
        # Course metadata from environment or defaults
        self.course_title = os.getenv('COURSE_TITLE', 'SCORM Course')
        self.site_name = os.getenv('SITE_NAME', 'scorm_course')
        self.base_url = os.getenv('BASE_URL', 'https://scorm-course.com')
    
    def _extract_text_from_image(self, image_path: str) -> str:
        """Extract text from image using OCR."""
        if not PIL_AVAILABLE or not TESSERACT_AVAILABLE:
            return ""
        
        try:
            image = Image.open(image_path)
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Extract text using OCR
            text = pytesseract.image_to_string(image)
            return text.strip()
            
        except Exception as e:
            self.logger.warning(f"OCR failed for {image_path}: {e}")
            return ""
    
    def _extract_image_content(self):
        """Extract content from image files."""
        # Supported image formats
        image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.gif', '*.bmp', '*.tiff', '*.webp']
        
        for extension in image_extensions:
            for image_file in self.scorm_path.rglob(extension):
                try:
                    # Get image metadata
                    if PIL_AVAILABLE:
                        with Image.open(image_file) as img:
                            width, height = img.size
                            format_type = img.format
                            mode = img.mode
                    else:
                        width, height = 0, 0
                        format_type = image_file.suffix[1:].upper()
                        mode = "unknown"
                    
                    # Extract text from image using OCR
                    ocr_text = self._extract_text_from_image(str(image_file))
                    
                    # Create content description
                    content = f"Image: {image_file.stem}\n"
                    content += f"Format: {format_type}\n"
                    content += f"Dimensions: {width}x{height}\n"
                    content += f"Color Mode: {mode}\n"
                    content += f"File Size: {image_file.stat().st_size} bytes\n"
                    
                    if ocr_text:
                        content += f"Extracted Text: {ocr_text}\n"
                    
                    # Generate item ID
                    item_id = hashlib.md5(str(image_file.relative_to(self.scorm_path)).encode()).hexdigest()
                    
                    content_doc = {
                        "id": f"image_content_{item_id}",
                        "title": f"Image Content: {image_file.stem}",
                        "content": content.strip(),
                        "content_type": "image_content",
                        "file_path": str(image_file.relative_to(self.scorm_path)),
                        "metadata": {
                            "source": "image_file",
                            "file_name": image_file.name,
                            "file_extension": image_file.suffix,
                            "width": width,
                            "height": height,
                            "format": format_type,
                            "color_mode": mode,
                            "file_size": image_file.stat().st_size,
                            "ocr_text_available": bool(ocr_text),
                            "ocr_text_length": len(ocr_text),
                            "extracted_at": datetime.now().isoformat(),
                            "extraction_method": "image_metadata_and_ocr",
                            "item_id": item_id
                        }
                    }
                    
                    # Add OCR text as separate content if available
                    if ocr_text:
                        ocr_doc = {
                            "id": f"image_ocr_{item_id}",
                            "title": f"Image OCR Text: {image_file.stem}",
                            "content": ocr_text,
                            "content_type": "image_ocr_content",
                            "file_path": str(image_file.relative_to(self.scorm_path)),
                            "metadata": {
                                "source": "image_ocr",
                                "image_file": str(image_file.relative_to(self.scorm_path)),
                                "extracted_at": datetime.now().isoformat(),
                                "extraction_method": "optical_character_recognition",
                                "ocr_engine": "tesseract",
                                "item_id": item_id
                            }
                        }
                        self.extracted_content.append(ocr_doc)
                    
                    self.extracted_content.append(content_doc)
                    
                except Exception as e:
                    self.logger.error(f"Error processing image {image_file}: {e}")
    
    def extract_image_content(self) -> Dict[str, Any]:
        """Extract all image content from the SCORM package."""
        self.logger.info(f"Starting image content extraction from: {self.scorm_path}")
        
        # Extract image content
        self._extract_image_content()
        
        # Save results
        self._save_results()
        
        return {
            "total_items": len(self.extracted_content),
            "content_types": self._get_content_type_breakdown(),
            "course_title": self.course_title,
            "site_name": self.site_name,
            "base_url": self.base_url,
            "extracted_at": datetime.now().isoformat()
        }
    
    def _get_content_type_breakdown(self) -> Dict[str, int]:
        """Get breakdown of content types."""
        breakdown = {}
        for item in self.extracted_content:
            content_type = item.get("content_type", "unknown")
            breakdown[content_type] = breakdown.get(content_type, 0) + 1
        return breakdown
    
    def _save_results(self):
        """Save extracted content to files."""
        # Save individual content type files
        content_by_type = {}
        for item in self.extracted_content:
            content_type = item.get("content_type", "unknown")
            if content_type not in content_by_type:
                content_by_type[content_type] = []
            content_by_type[content_type].append(item)
        
        for content_type, items in content_by_type.items():
            filename = f"{content_type}_content.json"
            filepath = self.output_dir / filename
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(items, f, indent=2, ensure_ascii=False)
            self.logger.info(f"Saved {len(items)} {content_type} items to {filename}")
        
        # Save summary
        summary = {
            "extraction_summary": {
                "total_items": len(self.extracted_content),
                "content_types": self._get_content_type_breakdown(),
                "course_title": self.course_title,
                "site_name": self.site_name,
                "base_url": self.base_url,
                "extracted_at": datetime.now().isoformat()
            }
        }
        
        summary_file = self.output_dir / "image_extraction_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Saved extraction summary to {summary_file}")

def main():
    """Main function for image content extraction."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python3 extract_image_content.py <scorm_path> [output_dir]")
        sys.exit(1)
    
    scorm_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "image_extraction_output"
    
    print("🖼️  Image Content Extractor")
    print("=" * 40)
    
    extractor = ImageContentExtractor(scorm_path, output_dir)
    results = extractor.extract_image_content()
    
    print(f"\n✅ Extraction complete!")
    print(f"📊 Total items: {results['total_items']}")
    print(f"📁 Output directory: {output_dir}")
    print(f"📋 Content types: {results['content_types']}")

if __name__ == "__main__":
    main() 