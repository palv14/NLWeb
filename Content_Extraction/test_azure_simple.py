#!/usr/bin/env python3
"""
Simple Azure Speech Services Test
"""

import os
import time
from pathlib import Path

def test_azure_simple():
    """Simple test of Azure Speech Services."""
    print("🧪 Simple Azure Speech Services Test")
    print("=" * 40)
    
    # Check credentials
    subscription_key = os.getenv('AZURE_SPEECH_KEY')
    region = os.getenv('AZURE_SPEECH_REGION')
    
    if not subscription_key or not region:
        print("❌ Credentials not found")
        return False
    
    print(f"✅ Credentials found: {region}")
    
    try:
        import azure.cognitiveservices.speech as speechsdk
        
        # Configure speech config
        speech_config = speechsdk.SpeechConfig(
            subscription=subscription_key, 
            region=region
        )
        speech_config.speech_recognition_language = "en-US"
        
        # Test with a small video
        video_files = list(Path("scormcontent/assets").glob("*.mp4"))
        if not video_files:
            print("❌ No video files found")
            return False
        
        # Sort by size and pick the smallest
        video_files.sort(key=lambda x: x.stat().st_size)
        test_video = video_files[0]
        
        print(f"📹 Testing with: {test_video.name}")
        print(f"📊 Size: {test_video.stat().st_size / 1024 / 1024:.1f} MB")
        
        # Extract audio
        from moviepy import VideoFileClip
        clip = VideoFileClip(str(test_video))
        
        if clip.audio is None:
            print("❌ No audio track found")
            clip.close()
            return False
        
        print(f"🎵 Audio duration: {clip.duration:.2f} seconds")
        
        # Extract audio to file
        audio_file = test_video.with_suffix('.wav')
        print(f"🎵 Extracting audio to: {audio_file.name}")
        clip.audio.write_audiofile(str(audio_file), logger=None)
        clip.close()
        
        # Test transcription
        print("🗣️  Testing transcription...")
        
        # Configure audio input
        audio_config = speechsdk.AudioConfig(filename=str(audio_file))
        
        # Create speech recognizer
        speech_recognizer = speechsdk.SpeechRecognizer(
            speech_config=speech_config, 
            audio_config=audio_config
        )
        
        # Use simple recognition instead of continuous
        print("🎯 Using simple recognition...")
        result = speech_recognizer.recognize_once()
        
        if result.reason == speechsdk.ResultReason.RecognizedSpeech:
            transcript = result.text
            print(f"✅ Transcription successful!")
            print(f"📝 Transcript: {transcript}")
            
            # Clean up
            os.remove(audio_file)
            return True
            
        elif result.reason == speechsdk.ResultReason.NoMatch:
            print(f"❌ No speech recognized: {result.no_match_details}")
        elif result.reason == speechsdk.ResultReason.Canceled:
            print(f"❌ Recognition canceled: {result.cancellation_details.reason}")
            if result.cancellation_details.reason == speechsdk.CancellationReason.Error:
                print(f"Error details: {result.cancellation_details.error_details}")
        
        # Clean up
        os.remove(audio_file)
        return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_azure_simple()
    if success:
        print("\n🎉 Simple test successful!")
    else:
        print("\n❌ Simple test failed!") 