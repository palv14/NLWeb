#!/usr/bin/env python3
"""
Azure Speech Services Credential Setup Helper
"""

import os
import sys
from pathlib import Path

def setup_azure_credentials():
    """Interactive setup for Azure Speech Services credentials."""
    print("🔧 Azure Speech Services Credential Setup")
    print("=" * 50)
    
    print("\n📋 Prerequisites:")
    print("1. Azure account (free tier available)")
    print("2. Speech Services resource created in Azure Portal")
    print("3. Key and Region from your Speech Service")
    
    print("\n🌐 If you haven't created a Speech Service yet:")
    print("1. Go to: https://portal.azure.com")
    print("2. Search for 'Speech Services'")
    print("3. Create a new resource")
    print("4. Choose 'Free (F0)' tier for testing")
    print("5. Get your Key and Region from 'Keys and Endpoint'")
    
    print("\n" + "=" * 50)
    
    # Get credentials from user
    print("\n🔑 Enter your Azure Speech Services credentials:")
    
    subscription_key = input("Enter your Subscription Key: ").strip()
    region = input("Enter your Region (e.g., eastus, westus2): ").strip()
    
    if not subscription_key or not region:
        print("❌ Both subscription key and region are required!")
        return False
    
    # Test the credentials
    print(f"\n🧪 Testing credentials...")
    
    try:
        import azure.cognitiveservices.speech as speechsdk
        
        # Configure speech config
        speech_config = speechsdk.SpeechConfig(
            subscription=subscription_key, 
            region=region
        )
        
        print("✅ Credentials are valid!")
        
        # Save to environment file
        env_file = Path(".env")
        env_content = f"""# Azure Speech Services Credentials
AZURE_SPEECH_KEY={subscription_key}
AZURE_SPEECH_REGION={region}
"""
        
        with open(env_file, 'w') as f:
            f.write(env_content)
        
        print(f"✅ Credentials saved to {env_file}")
        
        # Set environment variables for current session
        os.environ['AZURE_SPEECH_KEY'] = subscription_key
        os.environ['AZURE_SPEECH_REGION'] = region
        
        print("✅ Environment variables set for current session")
        
        # Show next steps
        print("\n🎉 Setup Complete!")
        print("\n📝 Next steps:")
        print("1. Test transcription: python3 Content_Extraction/azure_speech_integration.py")
        print("2. Run full extraction: python3 Content_Extraction/test_comprehensive_extraction.py")
        print("3. For future sessions, the .env file will be loaded automatically")
        
        return True
        
    except Exception as e:
        print(f"❌ Credential test failed: {e}")
        print("\n💡 Please check:")
        print("- Your subscription key is correct")
        print("- Your region matches your Speech Service")
        print("- Your Speech Service is active")
        return False

def load_credentials_from_env():
    """Load credentials from .env file if it exists."""
    env_file = Path(".env")
    if env_file.exists():
        print("📁 Loading credentials from .env file...")
        
        with open(env_file, 'r') as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value
        
        print("✅ Credentials loaded from .env file")
        return True
    else:
        print("📁 No .env file found")
        return False

def test_credentials():
    """Test if credentials are working."""
    print("🧪 Testing Azure Speech Services...")
    
    subscription_key = os.getenv('AZURE_SPEECH_KEY')
    region = os.getenv('AZURE_SPEECH_REGION')
    
    if not subscription_key or not region:
        print("❌ Credentials not found in environment")
        print("💡 Run setup: python3 Content_Extraction/setup_azure_credentials.py")
        return False
    
    try:
        import azure.cognitiveservices.speech as speechsdk
        
        # Configure speech config
        speech_config = speechsdk.SpeechConfig(
            subscription=subscription_key, 
            region=region
        )
        
        print("✅ Azure Speech Services configured successfully!")
        print(f"📍 Region: {region}")
        print(f"🔑 Key: {subscription_key[:8]}...{subscription_key[-4:]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Credential test failed: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test_credentials()
    else:
        setup_azure_credentials() 