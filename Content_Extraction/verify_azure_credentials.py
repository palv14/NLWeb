#!/usr/bin/env python3
"""
Azure Speech Services Credential Verification
"""

import os
import requests
from pathlib import Path

def verify_azure_credentials():
    """Verify Azure Speech Services credentials."""
    print("🔍 Azure Speech Services Credential Verification")
    print("=" * 50)
    
    # Load from .env file
    env_file = Path(".env")
    if env_file.exists():
        print("📁 Loading credentials from .env file...")
        with open(env_file, 'r') as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    try:
                        key, value = line.strip().split('=', 1)
                        os.environ[key] = value
                    except ValueError:
                        continue
    
    subscription_key = os.getenv('AZURE_SPEECH_KEY')
    region = os.getenv('AZURE_SPEECH_REGION')
    
    if not subscription_key or not region:
        print("❌ Credentials not found in environment")
        print("💡 Please run: python3 Content_Extraction/setup_azure_credentials.py")
        return False
    
    print(f"🔑 Subscription Key: {subscription_key[:8]}...{subscription_key[-4:]}")
    print(f"📍 Region: {region}")
    
    # Test the credentials with a simple API call
    print("\n🧪 Testing credentials with Azure API...")
    
    try:
        import azure.cognitiveservices.speech as speechsdk
        
        # Configure speech config
        speech_config = speechsdk.SpeechConfig(
            subscription=subscription_key, 
            region=region
        )
        
        # Test with a simple text-to-speech call (this will verify credentials)
        print("🎯 Testing with text-to-speech...")
        
        # Create a simple audio config (in-memory)
        audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)
        
        # Create speech synthesizer
        speech_synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=speech_config, 
            audio_config=audio_config
        )
        
        # Try to synthesize a simple text
        result = speech_synthesizer.speak_text_async("Hello, this is a test.").get()
        
        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            print("✅ Credentials are valid! Text-to-speech test successful.")
            return True
        else:
            print(f"❌ Text-to-speech failed: {result.reason}")
            return False
            
    except Exception as e:
        print(f"❌ Credential verification failed: {e}")
        print("\n💡 Common issues:")
        print("1. Subscription key is incorrect")
        print("2. Region doesn't match your Speech Service")
        print("3. Speech Service is not active")
        print("4. Free tier quota exceeded")
        return False

def show_azure_portal_instructions():
    """Show instructions for getting credentials from Azure Portal."""
    print("\n📋 How to get correct credentials from Azure Portal:")
    print("1. Go to: https://portal.azure.com")
    print("2. Search for 'Speech Services' in the search bar")
    print("3. Click on your Speech Service resource")
    print("4. In the left menu, click 'Keys and Endpoint'")
    print("5. Copy 'Key 1' (not Key 2)")
    print("6. Copy 'Region' (e.g., 'eastus', 'westus2')")
    print("7. Make sure your Speech Service is 'Running' (not stopped)")
    print("8. If using Free tier, check if you've exceeded the 5-hour monthly limit")

if __name__ == "__main__":
    success = verify_azure_credentials()
    if not success:
        show_azure_portal_instructions() 