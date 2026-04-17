#!/usr/bin/env python3
"""
Module-Mapped SCORM Content Extractor
Extracts all learning content from SCORM packages and maps it to specific module/lesson names
Generates organized output grouped by module rather than file paths
"""

import os
import sys
import json
import base64
import hashlib
import logging
import re
import zlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import mimetypes
import time
from collections import defaultdict

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # If python-dotenv is not available, try to load .env manually
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
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    print("Warning: PyPDF2 not available. PDF extraction will be skipped.")

try:
    from moviepy import VideoFileClip
    MOVIEPY_AVAILABLE = True
except ImportError:
    try:
        import moviepy
        from moviepy import VideoFileClip
        MOVIEPY_AVAILABLE = True
    except ImportError:
        MOVIEPY_AVAILABLE = False
        print("Warning: MoviePy not available. Video processing will be skipped.")

# Azure Speech Services for transcription
try:
    import azure.cognitiveservices.speech as speechsdk
    AZURE_SPEECH_AVAILABLE = True
except ImportError:
    AZURE_SPEECH_AVAILABLE = False
    print("Warning: Azure Speech SDK not available. Install with: pip install azure-cognitiveservices-speech")

try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    print("Warning: pytesseract not available. Image OCR will be skipped.")

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("Warning: PIL not available. Image processing will be skipped.")

class ModuleMappedContentExtractor:
    """Module-mapped content extractor that organizes content by lesson/module names."""
    
    def __init__(self, scorm_path: str, output_dir: str = "module_mapped_output"):
        self.scorm_path = Path(scorm_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Content storage organized by module
        self.module_content = defaultdict(lambda: {
            "module_info": {},
            "lesson_metadata": [],
            "lesson_content": [],
            "quiz_content": [],
            "pdf_content": [],
            "image_content": [],
            "video_content": [],
            "audio_content": [],
            "transcript_content": []
        })
        
        # Course metadata
        self.course_title = "Keys to Early Writing: Module 1 Writing Basics"
        self.site_name = "writing_course"
        self.base_url = "https://writing-course.com"
        
        # Lesson mapping for URL generation and module identification
        self.lesson_url_mapping = {
            "8BJ2M2GrEDAsngSw6IUxpSV7VbfD5nDQ": "1.1",
            "pZsdLwXV4F-pi45xaI7KxCByRfDuPMUg": "1.2", 
            "pti2Pyf48q0-1hT3SL5PzmqOURowwlC7": "1.3",
            "rCDrEvs3FA7oTTEH8YuH87bsniCuyhQe": "1.4",
            "IE1vz_PLVADRBD1wsICNLaCvOn0aXfgf": "1.5",
            "u-j6KGYJ6gAiR2Sgm5S0DZiPMB5U5n9f": "1.6",
            "63nV_h_FKpKMeDRU842rCBddilsanh73": "1.7"
        }
        
        # Module titles mapping
        self.module_titles = {
            "1.1": "About this Module",
            "1.2": "Connections to Models of Writing Instruction",
            "1.3": "What Do We Know About K-2 Writing?",
            "1.4": "Research About Effective Writing Instruction",
            "1.5": "Teaching Principles",
            "1.6": "Composing vs. Transcription Skills",
            "1.7": "Overview of Spelling and Handwriting Instruction"
        }
    
    def _get_module_from_lesson_id(self, lesson_id: str) -> str:
        """Get module number from lesson ID."""
        return self.lesson_url_mapping.get(lesson_id, "unknown")
    
    def _get_module_title(self, module_number: str) -> str:
        """Get full module title from module number."""
        return self.module_titles.get(module_number, f"Module {module_number}")
    
    def _add_content_to_module(self, module_number: str, content_type: str, content_item: Dict):
        """Add content item to the appropriate module and content type."""
        if module_number != "unknown":
            self.module_content[module_number][content_type].append(content_item)
    
    def _extract_course_structure_from_locales(self):
        """Extract course structure from existing lesson metadata."""
        lesson_metadata_file = Path("../enhanced_comprehensive_test_output/lesson_metadata_content.json")
        
        if not lesson_metadata_file.exists():
            self.logger.warning(f"Lesson metadata file not found: {lesson_metadata_file}")
            return
        
        try:
            with open(lesson_metadata_file, 'r', encoding='utf-8') as f:
                lesson_metadata = json.load(f)
            
            for lesson in lesson_metadata:
                lesson_id = lesson["metadata"]["lesson_id"]
                lesson_title = lesson["title"]
                
                # Extract module number from title (e.g., "Lesson: 1.1 About this Module")
                module_match = re.search(r'Lesson: (\d+\.\d+)', lesson_title)
                if module_match:
                    module_number = module_match.group(1)
                    module_title = lesson_title.replace(f"Lesson: {module_number} ", "")
                    
                    # Initialize module info if not exists
                    if module_number not in self.module_content:
                        self.module_content[module_number]["module_info"] = {
                            "module_number": module_number,
                            "module_title": module_title,
                            "lesson_id": lesson_id,
                            "lesson_title": lesson_title,
                            "total_content_items": 0
                        }
                    
                    # Add lesson metadata to the module
                    self._add_content_to_module(module_number, "lesson_metadata", lesson)
                    
        except Exception as e:
            self.logger.error(f"Error extracting course structure: {e}")
            import traceback
            traceback.print_exc()
    
    def _determine_module_from_filename(self, filename: str) -> str:
        """Determine which module a file belongs to based on its filename."""
        filename_lower = filename.lower()
        
        # Enhanced module keywords mapping with more specific content indicators
        module_keywords = {
            "1.1": ["about", "module", "overview", "introduction", "learning-objectives", "target"],
            "1.2": ["connections", "models", "writing instruction", "instructional models", "joan sedita", "mentor texts"],
            "1.3": ["k-2", "kindergarten", "early writing", "what we know", "elementary overview", "ies"],
            "1.4": ["research", "effective", "evidence-based", "practice guide"],
            "1.5": ["teaching principles", "principles", "instructional strategies"],
            "1.6": ["composing", "transcription", "skills", "oral language", "struggling students"],
            "1.7": ["spelling", "handwriting", "overview", "foundational skills", "letter formation", "printable"]
        }
        
        for module_num, keywords in module_keywords.items():
            for keyword in keywords:
                if keyword in filename_lower:
                    return module_num
        
        # Default to first module if no match found
        return "1.1"
    
    def _determine_module_from_content(self, content: str, title: str = "") -> str:
        """Determine which module content belongs to based on content analysis."""
        content_lower = content.lower()
        title_lower = title.lower()
        combined_text = f"{content_lower} {title_lower}"
        
        # Enhanced content-based module mapping
        module_content_keywords = {
            "1.1": ["learning objectives", "about this module", "overview", "introduction"],
            "1.2": ["mentor text", "joan sedita", "emulate", "models of writing", "connections"],
            "1.3": ["elementary school", "k-2", "kindergarten", "what we know", "ies overview"],
            "1.4": ["research", "effective writing instruction", "practice guide", "evidence-based"],
            "1.5": ["teaching principles", "instructional strategies", "explicit instruction"],
            "1.6": ["composing", "transcription", "oral language", "struggling students", "dictate"],
            "1.7": ["spelling", "handwriting", "foundational skills", "letter formation", "pencil grip"]
        }
        
        for module_num, keywords in module_content_keywords.items():
            for keyword in keywords:
                if keyword in combined_text:
                    return module_num
        
        # Default to first module if no match found
        return "1.1"
    
    def _extract_learning_content_from_existing_output(self):
        """Extract learning content from existing comprehensive extraction output."""
        try:
            # Extract lesson content from the existing comprehensive extraction
            lesson_content_file = Path("../enhanced_comprehensive_test_output/lesson_content_content.json")
            if lesson_content_file.exists():
                with open(lesson_content_file, 'r', encoding='utf-8') as f:
                    lesson_content = json.load(f)
                
                for content_item in lesson_content:
                    lesson_id = content_item.get("metadata", {}).get("lesson_id")
                    module_number = self._get_module_from_lesson_id(lesson_id)
                    module_title = self._get_module_title(module_number)
                    
                    # Update content with module information
                    content_item["metadata"]["module_number"] = module_number
                    content_item["metadata"]["module_title"] = module_title
                    content_item["title"] = f"Content: {module_number} {module_title}"
                    
                    self._add_content_to_module(module_number, "lesson_content", content_item)
            
            # Extract quiz content from the existing comprehensive extraction
            quiz_content_file = Path("../enhanced_comprehensive_test_output/quiz_content_content.json")
            if quiz_content_file.exists():
                with open(quiz_content_file, 'r', encoding='utf-8') as f:
                    quiz_content = json.load(f)
                
                for quiz_item in quiz_content:
                    lesson_id = quiz_item.get("metadata", {}).get("lesson_id")
                    module_number = self._get_module_from_lesson_id(lesson_id)
                    module_title = self._get_module_title(module_number)
                    
                    # Update content with module information
                    quiz_item["metadata"]["module_number"] = module_number
                    quiz_item["metadata"]["module_title"] = module_title
                    quiz_item["title"] = f"Quiz: {module_number} {module_title}"
                    
                    self._add_content_to_module(module_number, "quiz_content", quiz_item)
            
            # Extract image content from existing output and map to modules
            image_content_file = Path("../enhanced_comprehensive_test_output/image_content_content.json")
            if image_content_file.exists():
                with open(image_content_file, 'r', encoding='utf-8') as f:
                    image_content = json.load(f)
                
                for image_item in image_content:
                    # Determine module based on image title and content
                    image_title = image_item.get("title", "")
                    image_content_text = image_item.get("content", "")
                    module_number = self._determine_module_from_content(image_content_text, image_title)
                    
                    # Also try filename-based mapping
                    file_path = image_item.get("file_path", "")
                    if file_path:
                        filename = Path(file_path).stem
                        filename_module = self._determine_module_from_filename(filename)
                        if filename_module != "1.1":  # If filename gives us a specific module, use it
                            module_number = filename_module
                    
                    module_title = self._get_module_title(module_number)
                    
                    # Update content with module information
                    image_item["metadata"]["module_number"] = module_number
                    image_item["metadata"]["module_title"] = module_title
                    image_item["title"] = f"Image: {module_number} {module_title} - {image_title}"
                    
                    self._add_content_to_module(module_number, "image_content", image_item)
            
            # Extract video content from existing output and map to modules
            video_content_file = Path("../enhanced_comprehensive_test_output/video_content_content.json")
            if video_content_file.exists():
                with open(video_content_file, 'r', encoding='utf-8') as f:
                    video_content = json.load(f)
                
                for video_item in video_content:
                    # Determine module based on video title and transcript content
                    video_title = video_item.get("title", "")
                    video_content_text = video_item.get("content", "")
                    module_number = self._determine_module_from_content(video_content_text, video_title)
                    
                    # Also try filename-based mapping
                    file_path = video_item.get("file_path", "")
                    if file_path:
                        filename = Path(file_path).stem
                        filename_module = self._determine_module_from_filename(filename)
                        if filename_module != "1.1":  # If filename gives us a specific module, use it
                            module_number = filename_module
                    
                    module_title = self._get_module_title(module_number)
                    
                    # Update content with module information
                    video_item["metadata"]["module_number"] = module_number
                    video_item["metadata"]["module_title"] = module_title
                    video_item["title"] = f"Video: {module_number} {module_title} - {video_title}"
                    
                    self._add_content_to_module(module_number, "video_content", video_item)
            
            # Extract PDF content from existing output and map to modules
            pdf_content_file = Path("../enhanced_comprehensive_test_output/pdf_content_content.json")
            if pdf_content_file.exists():
                with open(pdf_content_file, 'r', encoding='utf-8') as f:
                    pdf_content = json.load(f)
                
                for pdf_item in pdf_content:
                    # Determine module based on PDF title and content
                    pdf_title = pdf_item.get("title", "")
                    pdf_content_text = pdf_item.get("content", "")
                    module_number = self._determine_module_from_content(pdf_content_text, pdf_title)
                    
                    # Also try filename-based mapping
                    file_path = pdf_item.get("file_path", "")
                    if file_path:
                        filename = Path(file_path).stem
                        filename_module = self._determine_module_from_filename(filename)
                        if filename_module != "1.1":  # If filename gives us a specific module, use it
                            module_number = filename_module
                    
                    module_title = self._get_module_title(module_number)
                    
                    # Update content with module information
                    pdf_item["metadata"]["module_number"] = module_number
                    pdf_item["metadata"]["module_title"] = module_title
                    pdf_item["title"] = f"PDF: {module_number} {module_title} - {pdf_title}"
                    
                    self._add_content_to_module(module_number, "pdf_content", pdf_item)
            
            # Extract transcript content from existing output and map to modules
            transcript_content_file = Path("../enhanced_comprehensive_test_output/transcript_content_content.json")
            if transcript_content_file.exists():
                with open(transcript_content_file, 'r', encoding='utf-8') as f:
                    transcript_content = json.load(f)
                
                for transcript_item in transcript_content:
                    # Determine module based on transcript content
                    transcript_title = transcript_item.get("title", "")
                    transcript_content_text = transcript_item.get("content", "")
                    module_number = self._determine_module_from_content(transcript_content_text, transcript_title)
                    
                    module_title = self._get_module_title(module_number)
                    
                    # Update content with module information
                    transcript_item["metadata"]["module_number"] = module_number
                    transcript_item["metadata"]["module_title"] = module_title
                    transcript_item["title"] = f"Transcript: {module_number} {module_title} - {transcript_title}"
                    
                    self._add_content_to_module(module_number, "transcript_content", transcript_item)
                    
        except Exception as e:
            self.logger.error(f"Error extracting learning content: {e}")
            import traceback
            traceback.print_exc()
    
    def _extract_pdf_content(self):
        """Extract content from PDF files and map to modules."""
        if not PDF_AVAILABLE:
            self.logger.warning("PyPDF2 not available. PDF extraction will be skipped.")
            return
            
        for pdf_file in self.scorm_path.rglob('*.pdf'):
            try:
                with open(pdf_file, 'rb') as f:
                    pdf_reader = PyPDF2.PdfReader(f)
                    all_text_content = []
                    page_details = []
                    
                    for page_num, page in enumerate(pdf_reader.pages):
                        page_text = page.extract_text()
                        if page_text:
                            cleaned_text = page_text.strip()
                            if cleaned_text:
                                paragraphs = [p.strip() for p in cleaned_text.split('\n') if p.strip()]
                                page_details.append({
                                    "page_number": page_num + 1,
                                    "paragraphs": paragraphs,
                                    "word_count": len(cleaned_text.split())
                                })
                                all_text_content.append(cleaned_text)
                    
                    if all_text_content:
                        # Try to determine which module this PDF belongs to based on filename
                        pdf_name = pdf_file.stem.lower()
                        module_number = self._determine_module_from_filename(pdf_name)
                        
                        content_doc = {
                            "id": f"pdf_{hashlib.md5(str(pdf_file).encode()).hexdigest()}",
                            "title": f"PDF: {pdf_file.name}",
                            "content": "\n\n".join(all_text_content),
                            "content_type": "pdf_content",
                            "file_path": str(pdf_file.relative_to(self.scorm_path)),
                            "metadata": {
                                "source": "pdf_extraction",
                                "file_name": pdf_file.name,
                                "file_size": pdf_file.stat().st_size,
                                "page_count": len(pdf_reader.pages),
                                "page_details": page_details,
                                "total_words": sum(len(text.split()) for text in all_text_content),
                                "module_number": module_number,
                                "module_title": self._get_module_title(module_number),
                                "extracted_at": datetime.now().isoformat(),
                                "extraction_method": "pdf_text_extraction"
                            }
                        }
                        
                        self._add_content_to_module(module_number, "pdf_content", content_doc)
                        
            except Exception as e:
                self.logger.error(f"Error extracting PDF content from {pdf_file}: {e}")
    
    def _extract_video_content(self):
        """Extract content from video files and map to modules."""
        video_extensions = ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm']
        
        for video_file in self.scorm_path.rglob('*'):
            if video_file.suffix.lower() in video_extensions:
                try:
                    # Try to determine which module this video belongs to
                    video_name = video_file.stem.lower()
                    module_number = self._determine_module_from_filename(video_name)
                    
                    content_doc = {
                        "id": f"video_{hashlib.md5(str(video_file).encode()).hexdigest()}",
                        "title": f"Video: {video_file.name}",
                        "content": f"Video file: {video_file.name}\nPath: {video_file.relative_to(self.scorm_path)}",
                        "content_type": "video_content",
                        "file_path": str(video_file.relative_to(self.scorm_path)),
                        "metadata": {
                            "source": "video_extraction",
                            "file_name": video_file.name,
                            "file_size": video_file.stat().st_size,
                            "module_number": module_number,
                            "module_title": self._get_module_title(module_number),
                            "extracted_at": datetime.now().isoformat(),
                            "extraction_method": "video_file_identification"
                        }
                    }
                    
                    self._add_content_to_module(module_number, "video_content", content_doc)
                    
                except Exception as e:
                    self.logger.error(f"Error processing video file {video_file}: {e}")
    
    def _extract_image_content(self):
        """Extract content from image files and map to modules."""
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp']
        
        for image_file in self.scorm_path.rglob('*'):
            if image_file.suffix.lower() in image_extensions:
                try:
                    # Try to determine which module this image belongs to
                    image_name = image_file.stem.lower()
                    module_number = self._determine_module_from_filename(image_name)
                    
                    content_doc = {
                        "id": f"image_{hashlib.md5(str(image_file).encode()).hexdigest()}",
                        "title": f"Image: {image_file.name}",
                        "content": f"Image file: {image_file.name}\nPath: {image_file.relative_to(self.scorm_path)}",
                        "content_type": "image_content",
                        "file_path": str(image_file.relative_to(self.scorm_path)),
                        "metadata": {
                            "source": "image_extraction",
                            "file_name": image_file.name,
                            "file_size": image_file.stat().st_size,
                            "module_number": module_number,
                            "module_title": self._get_module_title(module_number),
                            "extracted_at": datetime.now().isoformat(),
                            "extraction_method": "image_file_identification"
                        }
                    }
                    
                    self._add_content_to_module(module_number, "image_content", content_doc)
                    
                except Exception as e:
                    self.logger.error(f"Error processing image file {image_file}: {e}")
    
    def _update_module_statistics(self):
        """Update statistics for each module."""
        for module_number, module_data in self.module_content.items():
            total_items = (
                len(module_data["lesson_metadata"]) +
                len(module_data["lesson_content"]) +
                len(module_data["quiz_content"]) +
                len(module_data["pdf_content"]) +
                len(module_data["image_content"]) +
                len(module_data["video_content"]) +
                len(module_data["audio_content"]) +
                len(module_data["transcript_content"])
            )
            
            if "module_info" in module_data:
                module_data["module_info"]["total_content_items"] = total_items
    
    def extract_all_content(self) -> Dict[str, Any]:
        """Extract all content and organize by modules."""
        self.logger.info("Starting module-mapped content extraction...")
        
        # Extract course structure
        self._extract_course_structure_from_locales()
        
        # Extract all content from existing output (includes images, videos, PDFs, etc.)
        self._extract_learning_content_from_existing_output()
        
        # Update module statistics
        self._update_module_statistics()
        
        # Create summary
        summary = {
            "course_title": self.course_title,
            "total_modules": len(self.module_content),
            "extraction_timestamp": datetime.now().isoformat(),
            "modules": {}
        }
        
        for module_number, module_data in self.module_content.items():
            summary["modules"][module_number] = {
                "module_info": module_data["module_info"],
                "content_counts": {
                    "lesson_metadata": len(module_data["lesson_metadata"]),
                    "lesson_content": len(module_data["lesson_content"]),
                    "quiz_content": len(module_data["quiz_content"]),
                    "pdf_content": len(module_data["pdf_content"]),
                    "image_content": len(module_data["image_content"]),
                    "video_content": len(module_data["video_content"]),
                    "audio_content": len(module_data["audio_content"]),
                    "transcript_content": len(module_data["transcript_content"])
                }
            }
        
        return summary
    
    def _save_results(self):
        """Save all results to files."""
        # Save complete module-mapped content
        module_mapped_file = self.output_dir / "module_mapped_content.json"
        with open(module_mapped_file, 'w', encoding='utf-8') as f:
            json.dump(dict(self.module_content), f, indent=2, ensure_ascii=False)
        
        # Save summary
        summary_file = self.output_dir / "module_mapped_summary.json"
        summary = self.extract_all_content()
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        # Save individual module files
        for module_number, module_data in self.module_content.items():
            module_file = self.output_dir / f"module_{module_number}_content.json"
            with open(module_file, 'w', encoding='utf-8') as f:
                json.dump(module_data, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Results saved to {self.output_dir}")
        return {
            "module_mapped_content": str(module_mapped_file),
            "module_mapped_summary": str(summary_file),
            "individual_modules": [f"module_{num}_content.json" for num in self.module_content.keys()]
        }

def main():
    """Main execution function."""
    if len(sys.argv) < 2:
        print("Usage: python module_mapped_extractor.py <scorm_path> [output_dir]")
        sys.exit(1)
    
    scorm_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "module_mapped_output"
    
    extractor = ModuleMappedContentExtractor(scorm_path, output_dir)
    
    try:
        summary = extractor.extract_all_content()
        saved_files = extractor._save_results()
        
        print("\n=== Module-Mapped Content Extraction Complete ===")
        print(f"Course: {summary['course_title']}")
        print(f"Total Modules: {summary['total_modules']}")
        print(f"Output Directory: {output_dir}")
        
        print("\n=== Module Summary ===")
        for module_number, module_info in summary["modules"].items():
            module_title = module_info["module_info"]["module_title"]
            total_items = module_info["module_info"]["total_content_items"]
            print(f"Module {module_number}: {module_title} - {total_items} content items")
        
        print(f"\nResults saved to: {saved_files}")
        
    except Exception as e:
        print(f"Error during extraction: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 