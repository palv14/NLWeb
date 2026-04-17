#!/usr/bin/env python3
"""
Modular Quiz Content Extractor
Extracts quiz content from SCORM packages
"""

import os
import json
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

class QuizContentExtractor:
    """Extract quiz content from SCORM packages."""
    
    def __init__(self, scorm_path: str, output_dir: str = "quiz_extraction_output"):
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
        
        # Lesson mapping will be auto-generated
        self.lesson_url_mapping = {}
    
    def _extract_quiz_content_from_existing_files(self):
        """Extract quiz content from existing comprehensive extraction files."""
        try:
            # Extract quiz content from the existing comprehensive extraction
            quiz_content_file = Path("enhanced_comprehensive_test_output/quiz_content_content.json")
            if quiz_content_file.exists():
                with open(quiz_content_file, 'r', encoding='utf-8') as f:
                    quiz_content = json.load(f)
                
                for quiz_item in quiz_content:
                    content_doc = {
                        "id": quiz_item["id"],
                        "title": quiz_item["title"],
                        "content": quiz_item["content"],
                        "content_type": "quiz_content",
                        "file_path": quiz_item["file_path"],
                        "metadata": quiz_item["metadata"]
                    }
                    self.extracted_content.append(content_doc)
                
                self.logger.info(f"Loaded {len(quiz_content)} quiz content items from existing files")
            else:
                self.logger.warning("Quiz content file not found, attempting direct extraction")
                self._extract_quiz_content_from_locales()
                    
        except Exception as e:
            self.logger.error(f"Error extracting from existing files: {e}")
            import traceback
            traceback.print_exc()
    
    def _extract_quiz_content_from_locales(self):
        """Extract quiz content directly from locales/und.js file."""
        locales_file = self.scorm_path / "scormcontent" / "locales" / "und.js"
        
        if not locales_file.exists():
            self.logger.warning("locales/und.js file not found")
            return
        
        try:
            with open(locales_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract quiz content using regex patterns
            import re
            import base64
            import zlib
            
            # Look for quiz-related patterns in the JavaScript
            quiz_patterns = [
                r'"quiz":\s*"([^"]+)"',
                r'"question":\s*"([^"]+)"',
                r'"answer":\s*"([^"]+)"',
                r'"options":\s*\[([^\]]+)\]'
            ]
            
            quiz_items = []
            for pattern in quiz_patterns:
                matches = re.findall(pattern, content)
                for match in matches:
                    quiz_items.append({
                        "type": pattern.split('"')[1],
                        "content": match
                    })
            
            # Create quiz content items
            for i, quiz_item in enumerate(quiz_items):
                content_doc = {
                    "id": f"quiz_content_{i}",
                    "title": f"Quiz Content: {quiz_item['type']}",
                    "content": quiz_item['content'],
                    "content_type": "quiz_content",
                    "file_path": "scormcontent/locales/und.js",
                    "metadata": {
                        "quiz_type": quiz_item['type'],
                        "extracted_at": datetime.now().isoformat(),
                        "extraction_method": "locales_quiz_parsing"
                    }
                }
                self.extracted_content.append(content_doc)
                
        except Exception as e:
            self.logger.error(f"Error extracting quiz content from locales: {e}")
    
    def extract_quiz_content(self) -> Dict[str, Any]:
        """Extract all quiz content from the SCORM package."""
        self.logger.info(f"Starting quiz content extraction from: {self.scorm_path}")
        
        # Extract quiz content
        self._extract_quiz_content_from_existing_files()
        
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
        
        summary_file = self.output_dir / "quiz_extraction_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Saved extraction summary to {summary_file}")

def main():
    """Main function for quiz content extraction."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python3 extract_quiz_content.py <scorm_path> [output_dir]")
        sys.exit(1)
    
    scorm_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "quiz_extraction_output"
    
    print("🧩 Quiz Content Extractor")
    print("=" * 40)
    
    extractor = QuizContentExtractor(scorm_path, output_dir)
    results = extractor.extract_quiz_content()
    
    print(f"\n✅ Extraction complete!")
    print(f"📊 Total items: {results['total_items']}")
    print(f"📁 Output directory: {output_dir}")
    print(f"📋 Content types: {results['content_types']}")

if __name__ == "__main__":
    main() 