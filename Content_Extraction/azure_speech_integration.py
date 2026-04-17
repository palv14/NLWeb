#!/usr/bin/env python3
"""
Azure Speech Services Integration for Video Transcription
"""

import os
import time
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import json
from datetime import datetime

try:
    import azure.cognitiveservices.speech as speechsdk
    AZURE_SPEECH_AVAILABLE = True
except ImportError:
    AZURE_SPEECH_AVAILABLE = False
    print("Warning: Azure Speech SDK not available. Install with: pip install azure-cognitiveservices-speech")

try:
    from moviepy import VideoFileClip
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False
    print("Warning: MoviePy not available. Install with: pip install moviepy")

class AzureSpeechTranscriber:
    """Azure Speech Services transcriber for video files."""
    
    def __init__(self, subscription_key: str, region: str):
        """
        Initialize Azure Speech Services transcriber.
        
        Args:
            subscription_key: Azure Speech Services subscription key
            region: Azure region (e.g., 'eastus', 'westus2')
        """
        self.subscription_key = subscription_key
        self.region = region
        self.speech_config = speechsdk.SpeechConfig(
            subscription=subscription_key, 
            region=region
        )
        
        # Configure for long audio transcription
        self.speech_config.speech_recognition_language = "en-US"
        self.speech_config.enable_dictation()
        
        # For longer files, use conversation transcription
        self.speech_config.set_property(
            speechsdk.PropertyId.SpeechServiceConnection_EndSilenceTimeoutMs, "1000"
        )
        
        logging.info(f"Azure Speech Services initialized for region: {region}")
    
    def extract_audio_from_video(self, video_path: str) -> Optional[str]:
        """
        Extract audio from video file.
        
        Args:
            video_path: Path to video file
            
        Returns:
            Path to extracted audio file or None if failed
        """
        if not MOVIEPY_AVAILABLE:
            logging.error("MoviePy not available for audio extraction")
            return None
            
        try:
            video_file = Path(video_path)
            audio_file = video_file.with_suffix('.wav')
            
            print(f"🎵 Extracting audio from {video_file.name}...")
            clip = VideoFileClip(str(video_file))
            
            if clip.audio is None:
                logging.warning(f"No audio track found in {video_file.name}")
                clip.close()
                return None
            
            # Extract audio
            clip.audio.write_audiofile(str(audio_file), logger=None)
            clip.close()
            
            print(f"✅ Audio extracted: {audio_file.name}")
            return str(audio_file)
            
        except Exception as e:
            logging.error(f"Audio extraction failed: {e}")
            return None
    
    def transcribe_audio_file(self, audio_path: str) -> Optional[str]:
        """
        Transcribe audio file using Azure Speech Services.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Transcribed text or None if failed
        """
        if not AZURE_SPEECH_AVAILABLE:
            logging.error("Azure Speech SDK not available")
            return None
            
        try:
            # Configure audio input
            audio_config = speechsdk.AudioConfig(filename=audio_path)
            
            # Create speech recognizer
            speech_recognizer = speechsdk.SpeechRecognizer(
                speech_config=self.speech_config, 
                audio_config=audio_config
            )
            
            print(f"🗣️  Transcribing with Azure Speech Services...")
            
            # For longer files, use continuous recognition
            done = False
            transcript_parts = []
            
            def handle_result(evt):
                if evt.result.text:
                    transcript_parts.append(evt.result.text)
                    print(f"📝 Partial: {evt.result.text[:100]}...")
            
            def stop_cb(evt):
                nonlocal done
                done = True
                print("✅ Transcription completed")
            
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
            
            if full_transcript.strip():
                print(f"✅ Transcription successful! Length: {len(full_transcript)} characters")
                return full_transcript
            else:
                logging.warning("No transcript generated")
                return None
                
        except Exception as e:
            logging.error(f"Azure transcription failed: {e}")
            return None
    
    def transcribe_video(self, video_path: str, cleanup_audio: bool = True) -> Optional[Dict[str, Any]]:
        """
        Transcribe video file using Azure Speech Services.
        
        Args:
            video_path: Path to video file
            cleanup_audio: Whether to delete temporary audio file
            
        Returns:
            Transcription result dictionary or None if failed
        """
        video_file = Path(video_path)
        
        if not video_file.exists():
            logging.error(f"Video file not found: {video_path}")
            return None
        
        print(f"🎬 Processing video: {video_file.name}")
        
        # Extract audio
        audio_path = self.extract_audio_from_video(video_path)
        if not audio_path:
            return None
        
        try:
            # Transcribe audio
            transcript = self.transcribe_audio_file(audio_path)
            
            if transcript:
                # Get video metadata
                clip = VideoFileClip(video_path)
                duration = clip.duration
                clip.close()
                
                result = {
                    "video_file": str(video_path),
                    "transcript": transcript,
                    "duration": duration,
                    "transcript_length": len(transcript),
                    "extraction_method": "azure_speech_services",
                    "extracted_at": datetime.now().isoformat(),
                    "service": "azure_speech"
                }
                
                return result
            else:
                return None
                
        finally:
            # Cleanup temporary audio file
            if cleanup_audio and audio_path and Path(audio_path).exists():
                try:
                    os.remove(audio_path)
                    print(f"🧹 Cleaned up temporary audio: {Path(audio_path).name}")
                except Exception as e:
                    logging.warning(f"Failed to cleanup audio file: {e}")

def test_azure_transcription():
    """Test Azure Speech Services transcription."""
    print("🧪 Testing Azure Speech Services Transcription")
    print("=" * 60)
    
    # Check if Azure Speech SDK is available
    if not AZURE_SPEECH_AVAILABLE:
        print("❌ Azure Speech SDK not available")
        print("💡 Install with: pip install azure-cognitiveservices-speech")
        return False
    
    # Check if MoviePy is available
    if not MOVIEPY_AVAILABLE:
        print("❌ MoviePy not available")
        print("💡 Install with: pip install moviepy")
        return False
    
    # Get Azure credentials from environment
    subscription_key = os.getenv('AZURE_SPEECH_KEY')
    region = os.getenv('AZURE_SPEECH_REGION')
    
    if not subscription_key or not region:
        print("❌ Azure Speech Services credentials not found")
        print("💡 Set environment variables:")
        print("   export AZURE_SPEECH_KEY='your_subscription_key'")
        print("   export AZURE_SPEECH_REGION='eastus'")
        return False
    
    print(f"✅ Azure Speech Services configured for region: {region}")
    
    # Find a test video
    video_files = list(Path("scormcontent/assets").glob("*.mp4"))
    if not video_files:
        print("❌ No video files found")
        return False
    
    # Sort by file size and pick a larger one that failed before
    video_files.sort(key=lambda x: x.stat().st_size, reverse=True)
    test_video = video_files[0]  # Largest video
    
    print(f"📹 Testing with video: {test_video.name}")
    print(f"📊 File size: {test_video.stat().st_size / 1024 / 1024:.1f} MB")
    
    # Initialize transcriber
    transcriber = AzureSpeechTranscriber(subscription_key, region)
    
    # Transcribe video
    result = transcriber.transcribe_video(str(test_video))
    
    if result:
        print("🎉 Azure transcription successful!")
        print(f"📝 Transcript length: {result['transcript_length']} characters")
        print(f"📺 Video duration: {result['duration']:.2f} seconds")
        print(f"📝 First 200 characters: {result['transcript'][:200]}...")
        return True
    else:
        print("❌ Azure transcription failed")
        return False

if __name__ == "__main__":
    success = test_azure_transcription()
    if success:
        print("\n🎉 Azure Speech Services test completed successfully!")
    else:
        print("\n❌ Azure Speech Services test failed!") 