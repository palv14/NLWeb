#!/usr/bin/env python3
"""
Generic Lesson Content Extractor
Extracts lesson metadata and content from any SCORM package
"""

import os
import json
import logging
import re
import base64
import zlib
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

class GenericLessonContentExtractor:
    """Extract lesson metadata and content from any SCORM package."""
    
    def __init__(self, scorm_path: str, output_dir: str = "lesson_extraction_output"):
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
    
    def _detect_scorm_type(self) -> str:
        """Detect the type of SCORM package."""
        # Check for Articulate Rise
        if (self.scorm_path / "scormcontent" / "locales" / "und.js").exists():
            return "articulate_rise"
        
        # Check for standard SCORM
        if (self.scorm_path / "imsmanifest.xml").exists():
            return "standard_scorm"
        
        # Check for other common patterns
        if (self.scorm_path / "index.html").exists():
            return "html_based"
        
        return "unknown"
    
    def _extract_from_articulate_rise(self):
        """Extract content from Articulate Rise SCORM packages."""
        locales_file = self.scorm_path / "scormcontent" / "locales" / "und.js"
        
        if not locales_file.exists():
            self.logger.warning("locales/und.js file not found")
            return
        
        try:
            with open(locales_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract lesson metadata
            lesson_pattern = r'"([^"]{32})":\s*{\s*"title":\s*"([^"]+)"'
            lessons = re.findall(lesson_pattern, content)
            
            # Generate lesson mapping
            for i, (lesson_id, title) in enumerate(lessons, 1):
                self.lesson_url_mapping[lesson_id] = f"{i}.{i}"
            
            for lesson_id, title in lessons:
                lesson_number = self.lesson_url_mapping.get(lesson_id, "unknown")
                
                lesson_metadata = {
                    "id": f"lesson_metadata_{lesson_id}",
                    "title": f"Lesson: {lesson_number} {title}",
                    "content": f"Lesson {lesson_number}: {title}",
                    "content_type": "lesson_metadata",
                    "file_path": f"scormcontent/locales/und.js",
                    "metadata": {
                        "lesson_id": lesson_id,
                        "lesson_number": lesson_number,
                        "lesson_title": title,
                        "scorm_type": "articulate_rise",
                        "extracted_at": datetime.now().isoformat(),
                        "extraction_method": "articulate_rise_parsing"
                    }
                }
                self.extracted_content.append(lesson_metadata)
            
            # Extract lesson content
            base64_pattern = r'"content":\s*"([A-Za-z0-9+/=]+)"'
            base64_matches = re.findall(base64_pattern, content)
            
            lesson_titles = {lesson_id: title for lesson_id, title in lessons}
            
            for i, base64_content in enumerate(base64_matches[:len(lesson_titles)]):
                try:
                    # Decode base64
                    decoded = base64.b64decode(base64_content)
                    
                    # Try to decompress
                    try:
                        decompressed = zlib.decompress(decoded)
                        content_text = decompressed.decode('utf-8')
                    except:
                        content_text = decoded.decode('utf-8', errors='ignore')
                    
                    # Get lesson info
                    lesson_ids = list(lesson_titles.keys())
                    if i < len(lesson_ids):
                        lesson_id = lesson_ids[i]
                        lesson_title = lesson_titles[lesson_id]
                        lesson_number = self.lesson_url_mapping.get(lesson_id, "unknown")
                        
                        lesson_content = {
                            "id": f"lesson_content_{lesson_id}",
                            "title": f"Lesson Content: {lesson_number} {lesson_title}",
                            "content": content_text,
                            "content_type": "lesson_content",
                            "file_path": f"scormcontent/locales/und.js",
                            "metadata": {
                                "lesson_id": lesson_id,
                                "lesson_number": lesson_number,
                                "lesson_title": lesson_title,
                                "scorm_type": "articulate_rise",
                                "extracted_at": datetime.now().isoformat(),
                                "extraction_method": "articulate_rise_content_parsing"
                            }
                        }
                        self.extracted_content.append(lesson_content)
                        
                except Exception as e:
                    self.logger.warning(f"Error processing lesson content {i}: {e}")
                    
        except Exception as e:
            self.logger.error(f"Error extracting from Articulate Rise: {e}")
    
    def _extract_from_standard_scorm(self):
        """Extract content from standard SCORM packages."""
        manifest_file = self.scorm_path / "imsmanifest.xml"
        
        if not manifest_file.exists():
            self.logger.warning("imsmanifest.xml file not found")
            return
        
        try:
            import xml.etree.ElementTree as ET
            
            tree = ET.parse(manifest_file)
            root = tree.getroot()
            
            # Extract organizations
            organizations = root.findall('.//{http://www.imsproject.org/xsd/imscp_rootv1p1p2}organization')
            
            for org_idx, org in enumerate(organizations):
                items = org.findall('.//{http://www.imsproject.org/xsd/imscp_rootv1p1p2}item')
                
                for item_idx, item in enumerate(items):
                    title_elem = item.find('.//{http://www.imsproject.org/xsd/imscp_rootv1p1p2}title')
                    title = title_elem.text if title_elem is not None else f"Item {item_idx + 1}"
                    
                    lesson_id = f"org_{org_idx}_item_{item_idx}"
                    lesson_number = f"{org_idx + 1}.{item_idx + 1}"
                    
                    # Create lesson metadata
                    lesson_metadata = {
                        "id": f"lesson_metadata_{lesson_id}",
                        "title": f"Lesson: {lesson_number} {title}",
                        "content": f"Lesson {lesson_number}: {title}",
                        "content_type": "lesson_metadata",
                        "file_path": "imsmanifest.xml",
                        "metadata": {
                            "lesson_id": lesson_id,
                            "lesson_number": lesson_number,
                            "lesson_title": title,
                            "scorm_type": "standard_scorm",
                            "extracted_at": datetime.now().isoformat(),
                            "extraction_method": "standard_scorm_parsing"
                        }
                    }
                    self.extracted_content.append(lesson_metadata)
                    
        except Exception as e:
            self.logger.error(f"Error extracting from standard SCORM: {e}")
    
    def _extract_from_html_based(self):
        """Extract content from HTML-based SCORM packages."""
        html_files = list(self.scorm_path.rglob('*.html')) + list(self.scorm_path.rglob('*.htm'))
        
        for i, html_file in enumerate(html_files):
            try:
                with open(html_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Extract title from HTML
                title_match = re.search(r'<title[^>]*>(.*?)</title>', content, re.IGNORECASE)
                title = title_match.group(1).strip() if title_match else html_file.stem
                
                # Extract text content
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(content, 'html.parser')
                
                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.decompose()
                
                text_content = soup.get_text()
                lines = (line.strip() for line in text_content.splitlines())
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                text_content = ' '.join(chunk for chunk in chunks if chunk)
                
                lesson_id = f"html_{i}"
                lesson_number = f"{i + 1}.{i + 1}"
                
                # Create lesson content
                lesson_content = {
                    "id": f"lesson_content_{lesson_id}",
                    "title": f"Lesson Content: {lesson_number} {title}",
                    "content": text_content,
                    "content_type": "lesson_content",
                    "file_path": str(html_file.relative_to(self.scorm_path)),
                    "metadata": {
                        "lesson_id": lesson_id,
                        "lesson_number": lesson_number,
                        "lesson_title": title,
                        "scorm_type": "html_based",
                        "extracted_at": datetime.now().isoformat(),
                        "extraction_method": "html_content_parsing"
                    }
                }
                self.extracted_content.append(lesson_content)
                
            except Exception as e:
                self.logger.warning(f"Error processing HTML file {html_file}: {e}")
    
    def _extract_quiz_content(self):
        """Extract quiz content from various sources."""
        # Look for quiz-related files
        quiz_patterns = [
            '*.xml', '*.json', '*.js', '*.html', '*.htm'
        ]
        
        quiz_files = []
        for pattern in quiz_patterns:
            quiz_files.extend(self.scorm_path.rglob(pattern))
        
        quiz_content_found = []
        
        for quiz_file in quiz_files:
            try:
                with open(quiz_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Look for quiz-related patterns
                quiz_patterns = [
                    r'quiz', r'question', r'answer', r'assessment', r'test',
                    r'multiple.*choice', r'true.*false', r'matching'
                ]
                
                for pattern in quiz_patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        quiz_content_found.append({
                            "file": str(quiz_file.relative_to(self.scorm_path)),
                            "content": content[:1000] + "..." if len(content) > 1000 else content,
                            "pattern": pattern
                        })
                        break
                        
            except Exception as e:
                continue
        
        # Create quiz content items
        for i, quiz_item in enumerate(quiz_content_found):
            quiz_content = {
                "id": f"quiz_content_{i}",
                "title": f"Quiz Content: {Path(quiz_item['file']).stem}",
                "content": quiz_item['content'],
                "content_type": "quiz_content",
                "file_path": quiz_item['file'],
                "metadata": {
                    "quiz_id": f"quiz_{i}",
                    "source_file": quiz_item['file'],
                    "detected_pattern": quiz_item['pattern'],
                    "extracted_at": datetime.now().isoformat(),
                    "extraction_method": "quiz_pattern_detection"
                }
            }
            self.extracted_content.append(quiz_content)
    
    def extract_lesson_content(self) -> Dict[str, Any]:
        """Extract all lesson content from the SCORM package."""
        self.logger.info(f"Starting generic lesson content extraction from: {self.scorm_path}")
        
        # Detect SCORM type
        scorm_type = self._detect_scorm_type()
        self.logger.info(f"Detected SCORM type: {scorm_type}")
        
        # Extract based on SCORM type
        if scorm_type == "articulate_rise":
            self._extract_from_articulate_rise()
        elif scorm_type == "standard_scorm":
            self._extract_from_standard_scorm()
        elif scorm_type == "html_based":
            self._extract_from_html_based()
        else:
            self.logger.warning(f"Unknown SCORM type: {scorm_type}")
            # Try HTML-based extraction as fallback
            self._extract_from_html_based()
        
        # Extract quiz content
        self._extract_quiz_content()
        
        # Save results
        self._save_results()
        
        return {
            "total_items": len(self.extracted_content),
            "content_types": self._get_content_type_breakdown(),
            "course_title": self.course_title,
            "site_name": self.site_name,
            "base_url": self.base_url,
            "scorm_type": scorm_type,
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
                "scorm_type": self._detect_scorm_type(),
                "extracted_at": datetime.now().isoformat()
            }
        }
        
        summary_file = self.output_dir / "lesson_extraction_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Saved extraction summary to {summary_file}")

def main():
    """Main function for lesson content extraction."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python3 extract_lesson_content.py <scorm_path> [output_dir]")
        sys.exit(1)
    
    scorm_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "lesson_extraction_output"
    
    print("📚 Generic Lesson Content Extractor")
    print("=" * 40)
    
    extractor = GenericLessonContentExtractor(scorm_path, output_dir)
    results = extractor.extract_lesson_content()
    
    print(f"\n✅ Extraction complete!")
    print(f"📊 Total items: {results['total_items']}")
    print(f"📁 Output directory: {output_dir}")
    print(f"📋 Content types: {results['content_types']}")
    print(f"🔍 SCORM type: {results['scorm_type']}")

if __name__ == "__main__":
    main() 