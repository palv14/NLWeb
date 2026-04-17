#!/usr/bin/env python3
"""
Modular Video Content Extractor
Extracts video content and transcripts from SCORM packages using Azure Speech Services
"""

import os
import json
import hashlib
import logging
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

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
    from moviepy import VideoFileClip
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False
    print("Warning: MoviePy not available. Install with: pip install moviepy")

try:
    import azure.cognitiveservices.speech as speechsdk
    AZURE_SPEECH_AVAILABLE = True
except ImportError:
    AZURE_SPEECH_AVAILABLE = False
    print("Warning: Azure Speech SDK not available. Install with: pip install azure-cognitiveservices-speech")

class VideoContentExtractor:
    """Extract video content and transcripts from SCORM packages."""
    
    def __init__(self, scorm_path: str, output_dir: str = "video_extraction_output"):
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
                            "extraction_method": "azure_speech_services",
                            "service": "azure_speech",
                            "item_id": item_id
                        }
                    }
                    self.extracted_content.append(transcript_doc)
                
                clip.close()
                
            except Exception as e:
                self.logger.error(f"Error processing video {video_file}: {e}")
    
    def extract_video_content(self) -> Dict[str, Any]:
        """Extract all video content from the SCORM package."""
        self.logger.info(f"Starting video content extraction from: {self.scorm_path}")
        
        # Extract video content
        self._extract_video_content()
        
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
        
        summary_file = self.output_dir / "video_extraction_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Saved extraction summary to {summary_file}")

def main():
    """Main function for video content extraction."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python3 extract_video_content.py <scorm_path> [output_dir]")
        sys.exit(1)
    
    scorm_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "video_extraction_output"
    
    print("🎬 Video Content Extractor")
    print("=" * 40)
    
    extractor = VideoContentExtractor(scorm_path, output_dir)
    results = extractor.extract_video_content()
    
    print(f"\n✅ Extraction complete!")
    print(f"📊 Total items: {results['total_items']}")
    print(f"📁 Output directory: {output_dir}")
    print(f"📋 Content types: {results['content_types']}")

if __name__ == "__main__":
    main() 