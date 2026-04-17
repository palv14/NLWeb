#!/usr/bin/env python3
"""
Enhanced Comprehensive SCORM Content Extractor
Extracts all learning content from SCORM packages with proper module/submodule tagging
Generates NLWeb-compatible JSON output with navigation URLs
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

class EnhancedComprehensiveContentExtractor:
    """Enhanced comprehensive content extractor with NLWeb schema support."""
    
    def __init__(self, scorm_path: str, output_dir: str = "enhanced_comprehensive_test_output"):
        self.scorm_path = Path(scorm_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Content storage
        self.extracted_content = []
        self.nlweb_content = []
        
        # Course metadata
        self.course_title = "Keys to Early Writing: Module 1 Writing Basics"
        self.site_name = "writing_course"
        self.base_url = "https://writing-course.com"
        
        # Lesson mapping for URL generation
        self.lesson_url_mapping = {
            "8BJ2M2GrEDAsngSw6IUxpSV7VbfD5nDQ": "1.1",
            "pZsdLwXV4F-pi45xaI7KxCByRfDuPMUg": "1.2", 
            "pti2Pyf48q0-1hT3SL5PzmqOURowwlC7": "1.3",
            "rCDrEvs3FA7oTTEH8YuH87bsniCuyhQe": "1.4",
            "IE1vz_PLVADRBD1wsICNLaCvOn0aXfgf": "1.5",
            "u-j6KGYJ6gAiR2Sgm5S0DZiPMB5U5n9f": "1.6",
            "63nV_h_FKpKMeDRU842rCBddilsanh73": "1.7"
        }
        
    def _generate_nlweb_url(self, lesson_id: str, content_type: str, item_id: str = None) -> str:
        """Generate NLWeb-compatible URL for navigation."""
        lesson_number = self.lesson_url_mapping.get(lesson_id, "unknown")
        
        if content_type == "lesson_metadata":
            return f"{self.base_url}/lesson/{lesson_number}"
        elif content_type == "lesson_content":
            return f"{self.base_url}/lesson/{lesson_number}/content"
        elif content_type == "quiz_content":
            return f"{self.base_url}/lesson/{lesson_number}/quiz"
        elif content_type == "pdf_content":
            return f"{self.base_url}/resources/pdf/{item_id}"
        elif content_type == "image_content":
            return f"{self.base_url}/resources/image/{item_id}"
        elif content_type == "video_content":
            return f"{self.base_url}/resources/video/{item_id}"
        elif content_type == "audio_content":
            return f"{self.base_url}/resources/audio/{item_id}"
        elif content_type == "transcript_content":
            return f"{self.base_url}/resources/transcript/{item_id}"
        else:
            return f"{self.base_url}/content/{content_type}/{item_id}"
    
    def _create_nlweb_entry(self, content_item: Dict, content_type: str) -> Dict:
        """Create NLWeb-compatible entry."""
        lesson_id = content_item.get("metadata", {}).get("lesson_id")
        item_id = content_item.get("metadata", {}).get("item_id", content_item.get("id"))
        
        # Generate URL
        url = self._generate_nlweb_url(lesson_id, content_type, item_id)
        
        # Create content name
        lesson_title = content_item.get("metadata", {}).get("lesson_title", "")
        item_type = content_item.get("metadata", {}).get("item_type", content_type)
        
        if lesson_title:
            name = f"Content Block: {item_type} - {lesson_title}"
        else:
            name = f"Content Block: {item_type} - {content_item.get('title', 'Unknown')}"
        
        # Create NLWeb entry
        nlweb_entry = {
            "id": hashlib.md5(url.encode()).hexdigest(),
            "schema_json": json.dumps(content_item, indent=2),
            "url": url,
            "name": name,
            "site": self.site_name
        }
        
        return nlweb_entry
    
    def _extract_course_structure_from_locales(self):
        """Extract course structure from the locales file."""
        locales_file = self.scorm_path / "scormcontent" / "locales" / "und.js"
        
        if not locales_file.exists():
            self.logger.warning(f"Locales file not found: {locales_file}")
            return
        
        try:
            with open(locales_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract course metadata
            course_match = re.search(r'course.*?title.*?"([^"]+)"', content, re.IGNORECASE)
            if course_match:
                self.course_title = course_match.group(1)
            
            # Extract lesson structure - look for lesson IDs and titles
            lesson_pattern = r'"([^"]{32})".*?"title".*?"([^"]+)"'
            lessons = re.findall(lesson_pattern, content)
            
            for lesson_id, lesson_title in lessons:
                if lesson_id in self.lesson_url_mapping:
                    content_doc = {
                        "id": f"lesson_metadata_{hashlib.md5(lesson_id.encode()).hexdigest()}",
                        "title": lesson_title,
                        "content": f"Lesson: {lesson_title}\nDescription: \nType: blocks\nIcon: Article",
                        "content_type": "lesson_metadata",
                        "file_path": str(locales_file.relative_to(self.scorm_path)),
                        "metadata": {
                            "source": "lesson_structure",
                            "lesson_id": lesson_id,
                            "lesson_title": lesson_title,
                            "lesson_type": "blocks",
                            "icon": "Article",
                            "extracted_at": datetime.now().isoformat(),
                            "extraction_method": "lesson_structure_parsing"
                        }
                    }
                    self.extracted_content.append(content_doc)
                    
                    # Create NLWeb entry
                    nlweb_entry = self._create_nlweb_entry(content_doc, "lesson_metadata")
                    self.nlweb_content.append(nlweb_entry)
                    
        except Exception as e:
            self.logger.error(f"Error extracting course structure: {e}")
    
    def _extract_learning_content_from_locales(self):
        """Extract actual learning content from locales file."""
        locales_file = self.scorm_path / "scormcontent" / "locales" / "und.js"
        
        if not locales_file.exists():
            return
        
        try:
            with open(locales_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract text content blocks - look for content items with lesson IDs
            # Pattern to find content items that belong to lessons
            text_pattern = r'"clid[^"]*".*?"content".*?"([^"]+)".*?"([^"]{32})"'
            text_matches = re.findall(text_pattern, content)
            
            for item_id, lesson_id in text_matches:
                if lesson_id in self.lesson_url_mapping:
                    lesson_title = f"Lesson {self.lesson_url_mapping[lesson_id]}"
                    
                    content_doc = {
                        "id": f"lesson_content_{hashlib.md5(item_id.encode()).hexdigest()}",
                        "title": f"Content from {lesson_title}",
                        "content": f"Content: {item_id}",
                        "content_type": "lesson_content",
                        "file_path": str(locales_file.relative_to(self.scorm_path)),
                        "metadata": {
                            "source": "lesson_content",
                            "lesson_id": lesson_id,
                            "lesson_title": lesson_title,
                            "item_id": item_id,
                            "item_type": "text",
                            "extracted_at": datetime.now().isoformat(),
                            "extraction_method": "lesson_content_parsing"
                        }
                    }
                    self.extracted_content.append(content_doc)
                    
                    # Create NLWeb entry
                    nlweb_entry = self._create_nlweb_entry(content_doc, "lesson_content")
                    self.nlweb_content.append(nlweb_entry)
            
            # Extract quiz/interactive content - look for interactive items
            quiz_pattern = r'"cll[^"]*".*?"title".*?"([^"]+)".*?"([^"]{32})"'
            quiz_matches = re.findall(quiz_pattern, content)
            
            for item_id, lesson_id in quiz_matches:
                if lesson_id in self.lesson_url_mapping:
                    lesson_title = f"Lesson {self.lesson_url_mapping[lesson_id]}"
                    
                    content_doc = {
                        "id": f"quiz_content_{hashlib.md5(item_id.encode()).hexdigest()}",
                        "title": f"Quiz: {item_id}",
                        "content": f"Interactive: {item_id}\nDescription: Quiz content for {lesson_title}",
                        "content_type": "quiz_content",
                        "file_path": str(locales_file.relative_to(self.scorm_path)),
                        "metadata": {
                            "source": "quiz_content",
                            "lesson_id": lesson_id,
                            "lesson_title": lesson_title,
                            "item_id": item_id,
                            "item_type": "interactive",
                            "extracted_at": datetime.now().isoformat(),
                            "extraction_method": "quiz_content_parsing"
                        }
                    }
                    self.extracted_content.append(content_doc)
                    
                    # Create NLWeb entry
                    nlweb_entry = self._create_nlweb_entry(content_doc, "quiz_content")
                    self.nlweb_content.append(nlweb_entry)
                    
        except Exception as e:
            self.logger.error(f"Error extracting learning content: {e}")
    
    def _extract_learning_content_from_locales_enhanced(self):
        """Enhanced extraction of learning content from locales file."""
        locales_file = self.scorm_path / "scormcontent" / "locales" / "und.js"
        
        if not locales_file.exists():
            return
        
        try:
            # Extract lesson metadata from the existing comprehensive extraction
            lesson_metadata_file = Path("comprehensive_test_output/lesson_metadata_content.json")
            if lesson_metadata_file.exists():
                with open(lesson_metadata_file, 'r', encoding='utf-8') as f:
                    lesson_metadata = json.load(f)
                
                for lesson in lesson_metadata:
                    lesson_id = lesson["metadata"]["lesson_id"]
                    lesson_title = lesson["title"]  # Use title instead of lesson_title
                    
                    # Add lesson metadata
                    content_doc = {
                        "id": lesson["id"],
                        "title": lesson["title"],
                        "content": lesson["content"],
                        "content_type": "lesson_metadata",
                        "file_path": lesson["file_path"],
                        "metadata": lesson["metadata"]
                    }
                    self.extracted_content.append(content_doc)
                    
                    # Create NLWeb entry
                    nlweb_entry = self._create_nlweb_entry(content_doc, "lesson_metadata")
                    self.nlweb_content.append(nlweb_entry)
            
            # Extract lesson content from the existing comprehensive extraction
            lesson_content_file = Path("comprehensive_test_output/lesson_content_content.json")
            if lesson_content_file.exists():
                with open(lesson_content_file, 'r', encoding='utf-8') as f:
                    lesson_content = json.load(f)
                
                for content_item in lesson_content:
                    content_doc = {
                        "id": content_item["id"],
                        "title": content_item["title"],
                        "content": content_item["content"],
                        "content_type": "lesson_content",
                        "file_path": content_item["file_path"],
                        "metadata": content_item["metadata"]
                    }
                    self.extracted_content.append(content_doc)
                    
                    # Create NLWeb entry
                    nlweb_entry = self._create_nlweb_entry(content_doc, "lesson_content")
                    self.nlweb_content.append(nlweb_entry)
            
            # Extract quiz content from the existing comprehensive extraction
            quiz_content_file = Path("comprehensive_test_output/quiz_content_content.json")
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
                    
                    # Create NLWeb entry
                    nlweb_entry = self._create_nlweb_entry(content_doc, "quiz_content")
                    self.nlweb_content.append(nlweb_entry)
                    
        except Exception as e:
            self.logger.error(f"Error extracting enhanced learning content: {e}")
            import traceback
            traceback.print_exc()
    
    def _extract_pdf_content(self):
        """Extract content from PDF files."""
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
                                    'page_number': page_num + 1,
                                    'paragraphs': paragraphs,
                                    'text': cleaned_text
                                })
                                all_text_content.append(f"--- Page {page_num + 1} ---")
                                all_text_content.append(cleaned_text)
                    
                    if all_text_content:
                        combined_text = '\n\n'.join(all_text_content)
                        item_id = hashlib.md5(str(pdf_file.relative_to(self.scorm_path)).encode()).hexdigest()
                        
                        # Extract document metadata
                        doc_info = {}
                        if hasattr(pdf_reader, 'metadata') and pdf_reader.metadata:
                            for key, value in pdf_reader.metadata.items():
                                if value and str(value).strip():
                                    doc_info[key] = str(value).strip()
                        
                        content_doc = {
                            "id": f"pdf_content_{item_id}",
                            "title": f"PDF Content: {pdf_file.stem}",
                            "content": combined_text,
                            "content_type": "pdf_content",
                            "file_path": str(pdf_file.relative_to(self.scorm_path)),
                            "metadata": {
                                "source": "pdf_file",
                                "pages": len(pdf_reader.pages),
                                "file_size": pdf_file.stat().st_size,
                                "extracted_at": datetime.now().isoformat(),
                                "extraction_method": "pdf_text_extraction",
                                "item_id": item_id,
                                "document_info": doc_info,
                                "page_details": page_details
                            }
                        }
                        self.extracted_content.append(content_doc)
                        
                        # Create NLWeb entry
                        nlweb_entry = self._create_nlweb_entry(content_doc, "pdf_content")
                        self.nlweb_content.append(nlweb_entry)
                        
            except Exception as e:
                self.logger.error(f"Error extracting PDF content from {pdf_file}: {e}")
    
    def _extract_video_content(self):
        """Extract content from video files including transcription."""
        if not MOVIEPY_AVAILABLE:
            self.logger.warning("MoviePy not available. Video processing will be skipped.")
            return
        
        for video_file in self.scorm_path.rglob('*.mp4'):
            try:
                clip = VideoFileClip(str(video_file))
                
                # Basic video metadata
                content = f"Video: {video_file.stem}\n"
                content += f"Duration: {clip.duration:.2f} seconds\n"
                content += f"Resolution: {clip.size[0]}x{clip.size[1]}\n"
                content += f"FPS: {clip.fps}\n"
                
                # Try to extract audio for transcription
                transcript = ""
                if clip.audio:
                    try:
                        # Try Azure Speech Services for transcription
                        if AZURE_SPEECH_AVAILABLE:
                            try:
                                azure_transcript = self._transcribe_with_azure_speech(str(video_file))
                                
                                if azure_transcript:
                                    transcript = azure_transcript
                                    content += f"Transcript: {transcript}\n"
                                    self.logger.info(f"Azure transcription successful for {video_file}")
                                else:
                                    self.logger.warning(f"Azure transcription failed for {video_file}")
                            except Exception as e:
                                self.logger.warning(f"Azure Speech Services transcription failed for {video_file}: {e}")
                        
                    except Exception as e:
                        self.logger.warning(f"Audio processing failed for {video_file}: {e}")
                
                item_id = hashlib.md5(str(video_file.relative_to(self.scorm_path)).encode()).hexdigest()
                
                content_doc = {
                    "id": f"video_content_{item_id}",
                    "title": f"Video Content: {video_file.stem}",
                    "content": content.strip(),
                    "content_type": "video_content",
                    "file_path": str(video_file.relative_to(self.scorm_path)),
                    "metadata": {
                        "source": "video_file",
                        "duration": clip.duration,
                        "resolution": clip.size,
                        "fps": clip.fps,
                        "file_size": video_file.stat().st_size,
                        "transcript_available": bool(transcript),
                        "transcript_length": len(transcript),
                        "extracted_at": datetime.now().isoformat(),
                        "extraction_method": "video_metadata_and_transcription",
                        "item_id": item_id
                    }
                }
                self.extracted_content.append(content_doc)
                
                # Create NLWeb entry
                nlweb_entry = self._create_nlweb_entry(content_doc, "video_content")
                self.nlweb_content.append(nlweb_entry)
                
                # If transcript was generated, create separate transcript content
                if transcript:
                    transcript_doc = {
                        "id": f"transcript_content_{item_id}",
                        "title": f"Video Transcript: {video_file.stem}",
                        "content": transcript,
                        "content_type": "transcript_content",
                        "file_path": str(video_file.relative_to(self.scorm_path)),
                        "metadata": {
                            "source": "video_transcript",
                            "video_file": str(video_file.relative_to(self.scorm_path)),
                            "duration": clip.duration,
                            "extracted_at": datetime.now().isoformat(),
                            "extraction_method": "speech_to_text_transcription",
                            "item_id": item_id
                        }
                    }
                    self.extracted_content.append(transcript_doc)
                    
                    # Create NLWeb entry for transcript
                    transcript_nlweb_entry = self._create_nlweb_entry(transcript_doc, "transcript_content")
                    self.nlweb_content.append(transcript_nlweb_entry)
                
                clip.close()
                
            except Exception as e:
                self.logger.error(f"Error processing video {video_file}: {e}")
    
    def _extract_audio_content(self):
        """Extract content from audio files using Azure Speech Services."""
        if not AZURE_SPEECH_AVAILABLE:
            self.logger.warning("Azure Speech SDK not available. Audio processing will be skipped.")
            return
        
        for audio_file in self.scorm_path.rglob('*.mp3'):
            try:
                # Get Azure credentials from environment
                subscription_key = os.getenv('AZURE_SPEECH_KEY')
                region = os.getenv('AZURE_SPEECH_REGION')
                
                if not subscription_key or not region:
                    self.logger.warning("Azure Speech Services credentials not found in environment")
                    continue
                
                # Configure Azure Speech Services
                speech_config = speechsdk.SpeechConfig(
                    subscription=subscription_key, 
                    region=region
                )
                speech_config.speech_recognition_language = "en-US"
                speech_config.enable_dictation()
                
                # Configure audio input
                audio_config = speechsdk.AudioConfig(filename=str(audio_file))
                
                # Create speech recognizer
                speech_recognizer = speechsdk.SpeechRecognizer(
                    speech_config=speech_config, 
                    audio_config=audio_config
                )
                
                # For longer files, use continuous recognition
                done = False
                transcript_parts = []
                
                def handle_result(evt):
                    if evt.result.text:
                        transcript_parts.append(evt.result.text)
                
                def stop_cb(evt):
                    nonlocal done
                    done = True
                
                # Connect event handlers
                speech_recognizer.recognized.connect(handle_result)
                speech_recognizer.session_stopped.connect(stop_cb)
                speech_recognizer.canceled.connect(stop_cb)
                
                # Start continuous recognition
                speech_recognizer.start_continuous_recognition()
                
                # Wait for completion
                while not done:
                    time.sleep(0.5)
                
                speech_recognizer.stop_continuous_recognition()
                
                # Combine all parts
                transcript = " ".join(transcript_parts)
                
                if transcript.strip():
                    content = f"Audio: {audio_file.stem}\n"
                    content += f"Transcript: {transcript}\n"
                    
                    item_id = hashlib.md5(str(audio_file.relative_to(self.scorm_path)).encode()).hexdigest()
                    
                    content_doc = {
                        "id": f"audio_content_{item_id}",
                        "title": f"Audio Content: {audio_file.stem}",
                        "content": content.strip(),
                        "content_type": "audio_content",
                        "file_path": str(audio_file.relative_to(self.scorm_path)),
                        "metadata": {
                            "source": "audio_file",
                            "file_size": audio_file.stat().st_size,
                            "transcript_available": True,
                            "transcript_length": len(transcript),
                            "extracted_at": datetime.now().isoformat(),
                            "extraction_method": "azure_speech_services",
                            "service": "azure_speech",
                            "item_id": item_id
                        }
                    }
                    self.extracted_content.append(content_doc)
                    
                    # Create NLWeb entry
                    nlweb_entry = self._create_nlweb_entry(content_doc, "audio_content")
                    self.nlweb_content.append(nlweb_entry)
                else:
                    self.logger.warning(f"No transcript generated for {audio_file}")
                    
            except Exception as e:
                self.logger.error(f"Error processing audio {audio_file}: {e}")
    
    def _extract_image_content(self):
        """Extract content from image files."""
        for image_file in self.scorm_path.rglob('*.jpg'):
            try:
                filename = image_file.stem
                item_id = hashlib.md5(str(image_file.relative_to(self.scorm_path)).encode()).hexdigest()
                
                descriptive_content = f"Image content: {filename}. "
                
                # OCR attempt
                ocr_text = ""
                if TESSERACT_AVAILABLE and PIL_AVAILABLE:
                    try:
                        ocr_text = pytesseract.image_to_string(str(image_file))
                        if ocr_text.strip():
                            descriptive_content += f"OCR Text: {ocr_text.strip()} "
                    except Exception as e:
                        self.logger.warning(f"OCR failed for {image_file}: {e}")
                
                # Filename analysis for educational terms
                educational_terms = ['instruction', 'teaching', 'learning', 'diagram', 'chart', 'graph', 'figure', 'illustration', 'example', 'checklist', 'infographic']
                found_terms = [term for part in filename.replace('_', ' ').replace('-', ' ').split() for term in educational_terms if term in part.lower()]
                if found_terms:
                    descriptive_content += f"This image appears to be educational content related to: {', '.join(set(found_terms))}. "
                
                content_doc = {
                    "id": f"image_content_{item_id}",
                    "title": f"Image Content: {filename}",
                    "content": descriptive_content.strip(),
                    "content_type": "image_content",
                    "file_path": str(image_file.relative_to(self.scorm_path)),
                    "metadata": {
                        "source": "image_file",
                        "file_size": image_file.stat().st_size,
                        "ocr_available": TESSERACT_AVAILABLE,
                        "ocr_text_length": len(ocr_text),
                        "extracted_at": datetime.now().isoformat(),
                        "extraction_method": "image_description_and_ocr",
                        "item_id": item_id
                    }
                }
                self.extracted_content.append(content_doc)
                
                # Create NLWeb entry
                nlweb_entry = self._create_nlweb_entry(content_doc, "image_content")
                self.nlweb_content.append(nlweb_entry)
                
            except Exception as e:
                self.logger.error(f"Error processing image {image_file}: {e}")
    
    def _transcribe_with_azure_speech(self, video_path: str) -> Optional[str]:
        """
        Transcribe video using Azure Speech Services.
        
        Args:
            video_path: Path to video file
            
        Returns:
            Transcribed text or None if failed
        """
        if not AZURE_SPEECH_AVAILABLE:
            logging.warning("Azure Speech SDK not available for transcription")
            return None
            
        # Get Azure credentials from environment
        subscription_key = os.getenv('AZURE_SPEECH_KEY')
        region = os.getenv('AZURE_SPEECH_REGION')
        
        if not subscription_key or not region:
            logging.warning("Azure Speech Services credentials not found in environment")
            return None
            
        try:
            # Configure Azure Speech Services
            speech_config = speechsdk.SpeechConfig(
                subscription=subscription_key, 
                region=region
            )
            speech_config.speech_recognition_language = "en-US"
            speech_config.enable_dictation()
            
            # Extract audio from video
            video_file = Path(video_path)
            audio_file = video_file.with_suffix('.wav')
            
            clip = VideoFileClip(str(video_file))
            if clip.audio is None:
                logging.warning(f"No audio track found in {video_file.name}")
                clip.close()
                return None
                
            # Extract audio
            clip.audio.write_audiofile(str(audio_file), logger=None)
            clip.close()
            
            # Configure audio input
            audio_config = speechsdk.AudioConfig(filename=str(audio_file))
            
            # Create speech recognizer
            speech_recognizer = speechsdk.SpeechRecognizer(
                speech_config=speech_config, 
                audio_config=audio_config
            )
            
            # For longer files, use continuous recognition
            done = False
            transcript_parts = []
            
            def handle_result(evt):
                if evt.result.text:
                    transcript_parts.append(evt.result.text)
            
            def stop_cb(evt):
                nonlocal done
                done = True
            
            # Connect event handlers
            speech_recognizer.recognized.connect(handle_result)
            speech_recognizer.session_stopped.connect(stop_cb)
            speech_recognizer.canceled.connect(stop_cb)
            
            # Start continuous recognition
            speech_recognizer.start_continuous_recognition()
            
            # Wait for completion
            while not done:
                time.sleep(0.5)
            
            speech_recognizer.stop_continuous_recognition()
            
            # Combine all parts
            full_transcript = " ".join(transcript_parts)
            
            # Cleanup temporary audio file
            if audio_file.exists():
                os.remove(audio_file)
            
            if full_transcript.strip():
                logging.info(f"Azure transcription successful for {video_file.name}")
                return full_transcript
            else:
                logging.warning(f"No transcript generated for {video_file.name}")
                return None
                
        except Exception as e:
            logging.error(f"Azure transcription failed for {video_path}: {e}")
            return None
    
    def extract_all_content(self) -> Dict[str, Any]:
        """Extract all content from the SCORM package."""
        self.logger.info(f"Starting comprehensive content extraction from: {self.scorm_path}")
        
        # Extract course structure and learning content
        self._extract_course_structure_from_locales()
        self._extract_learning_content_from_locales()
        
        # Try enhanced extraction if basic extraction didn't work
        if len([item for item in self.extracted_content if item["content_type"] in ["lesson_metadata", "lesson_content", "quiz_content"]]) == 0:
            self.logger.info("Basic extraction didn't find lesson content, trying enhanced extraction...")
            self._extract_learning_content_from_locales_enhanced()
        
        # Extract all other content types
        self._extract_pdf_content()
        self._extract_image_content()
        self._extract_video_content()
        self._extract_audio_content()
        
        # Save results
        self._save_results()
        
        return {
            "total_items": len(self.extracted_content),
            "nlweb_items": len(self.nlweb_content),
            "output_directory": str(self.output_dir)
        }
    
    def _save_results(self):
        """Save extraction results to files."""
        # Save detailed content by type
        content_by_type = {}
        for item in self.extracted_content:
            content_type = item["content_type"]
            if content_type not in content_by_type:
                content_by_type[content_type] = []
            content_by_type[content_type].append(item)
        
        # Save each content type to separate files
        for content_type, items in content_by_type.items():
            output_file = self.output_dir / f"{content_type}_content.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(items, f, indent=2, ensure_ascii=False)
        
        # Save NLWeb-compatible content
        nlweb_file = self.output_dir / "nlweb_content.json"
        with open(nlweb_file, 'w', encoding='utf-8') as f:
            json.dump(self.nlweb_content, f, indent=2, ensure_ascii=False)
        
        # Save summary
        summary = {
            "extraction_summary": {
                "total_items": len(self.extracted_content),
                "nlweb_items": len(self.nlweb_content),
                "content_types": {content_type: len(items) for content_type, items in content_by_type.items()},
                "course_title": self.course_title,
                "site_name": self.site_name,
                "base_url": self.base_url,
                "extracted_at": datetime.now().isoformat()
            }
        }
        
        summary_file = self.output_dir / "enhanced_comprehensive_extraction_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

def main():
    """Main function for command line usage."""
    if len(sys.argv) < 2:
        print("Usage: python comprehensive_content_extractor.py <scorm_path> [output_dir]")
        sys.exit(1)
    
    scorm_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "enhanced_comprehensive_test_output"
    
    extractor = EnhancedComprehensiveContentExtractor(scorm_path, output_dir)
    results = extractor.extract_all_content()
    
    print(f"✅ Extraction complete!")
    print(f"📊 Total items extracted: {results['total_items']}")
    print(f"🌐 NLWeb items generated: {results['nlweb_items']}")
    print(f"📁 Output directory: {results['output_directory']}")

if __name__ == "__main__":
    main() 