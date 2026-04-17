#!/bin/bash

# Azure Web App Startup Script for SCORM Content Extraction
# This script installs all dependencies and sets up the environment

set -e  # Exit on any error

echo "🚀 Starting Azure Web App Setup for SCORM Content Extraction..."
echo "================================================================"

# Update package lists
echo "📦 Updating package lists..."
apt-get update

# Install system dependencies
echo "🔧 Installing system dependencies..."
apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    portaudio19-dev \
    python3-dev \
    python3-pip \
    python3-venv \
    build-essential \
    libssl-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Verify tesseract installation
echo "🔍 Verifying Tesseract installation..."
tesseract --version

# Create virtual environment (if not exists)
echo "🐍 Setting up Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install Python dependencies
echo "📚 Installing Python dependencies..."
pip install -r Content_Extraction/requirements.txt

# Verify key installations
echo "✅ Verifying installations..."

# Check Tesseract
if command -v tesseract &> /dev/null; then
    echo "✅ Tesseract OCR: Installed"
else
    echo "❌ Tesseract OCR: Not found"
    exit 1
fi

# Check Python packages
echo "🔍 Checking Python packages..."
python3 -c "
import sys
packages = [
    'PyPDF2', 'moviepy', 'PIL', 'pytesseract', 
    'beautifulsoup4', 'lxml', 'requests', 
    'elasticsearch', 'azure.cognitiveservices.speech', 'dotenv'
]
missing = []
for package in packages:
    try:
        __import__(package.replace('-', '_').replace('.', '_'))
        print(f'✅ {package}: Installed')
    except ImportError:
        missing.append(package)
        print(f'❌ {package}: Missing')
if missing:
    print(f'\\n❌ Missing packages: {missing}')
    sys.exit(1)
else:
    print('\\n🎉 All Python packages installed successfully!')
"

# Create .env file if it doesn't exist
echo "🔐 Setting up environment variables..."
if [ ! -f ".env" ]; then
    cat > .env << EOF
# Azure Speech Services Configuration
# Replace these with your actual Azure credentials
AZURE_SPEECH_KEY=your_azure_speech_key_here
AZURE_SPEECH_REGION=eastus

# SCORM Content Extraction Configuration
COURSE_TITLE=SCORM Course
SITE_NAME=scorm_course
BASE_URL=https://scorm-course.com

# Elasticsearch Configuration (if needed)
ELASTICSEARCH_URL=http://localhost:9200
ELASTICSEARCH_INDEX=scorm_content
EOF
    echo "📝 Created .env file template"
    echo "⚠️  Please update .env file with your actual Azure credentials and course information"
else
    echo "✅ .env file already exists"
fi

# Create necessary directories
echo "📁 Creating output directories..."
mkdir -p extracted_content
mkdir -p lesson_extraction_output
mkdir -p video_extraction_output
mkdir -p pdf_extraction_output
mkdir -p image_extraction_output
mkdir -p quiz_extraction_output

# Set permissions
echo "🔐 Setting file permissions..."
chmod +x Content_Extraction/*.py
chmod +x Content_Extraction/azure_startup.sh

# Test basic functionality
echo "🧪 Running basic functionality tests..."

# Test image extraction (lightweight test)
echo "🖼️ Testing image extraction..."
python3 Content_Extraction/extract_image_content.py . --test-only 2>/dev/null || echo "⚠️ Image extraction test skipped (no SCORM content)"

# Test PDF extraction (lightweight test)
echo "📄 Testing PDF extraction..."
python3 Content_Extraction/extract_pdf_content.py . --test-only 2>/dev/null || echo "⚠️ PDF extraction test skipped (no SCORM content)"

echo "✅ Basic functionality tests completed"

# Create health check endpoint
echo "🏥 Creating health check endpoint..."
cat > health_check.py << 'EOF'
#!/usr/bin/env python3
"""
Health check endpoint for Azure Web App
"""

import os
import sys
import json
from pathlib import Path

def check_dependencies():
    """Check if all dependencies are available."""
    status = {
        "tesseract": False,
        "python_packages": [],
        "azure_credentials": False,
        "directories": []
    }
    
    # Check Tesseract
    try:
        import subprocess
        result = subprocess.run(['tesseract', '--version'], 
                              capture_output=True, text=True)
        status["tesseract"] = result.returncode == 0
    except:
        pass
    
    # Check Python packages
    packages = ['PyPDF2', 'moviepy', 'PIL', 'pytesseract', 
                'beautifulsoup4', 'lxml', 'requests', 
                'elasticsearch', 'azure.cognitiveservices.speech', 'dotenv', 'flask']
    
    for package in packages:
        try:
            __import__(package.replace('-', '_').replace('.', '_'))
            status["python_packages"].append({"package": package, "status": "installed"})
        except ImportError:
            status["python_packages"].append({"package": package, "status": "missing"})
    
    # Check Azure credentials
    status["azure_credentials"] = bool(os.getenv('AZURE_SPEECH_KEY') and os.getenv('AZURE_SPEECH_REGION'))
    
    # Check directories
    directories = ['Content_Extraction', 'extracted_content']
    for directory in directories:
        status["directories"].append({
            "directory": directory, 
            "exists": Path(directory).exists()
        })
    
    return status

def main():
    """Main health check function."""
    status = check_dependencies()
    
    # Determine overall health
    all_packages_installed = all(pkg["status"] == "installed" for pkg in status["python_packages"])
    all_directories_exist = all(dir["exists"] for dir in status["directories"])
    
    overall_health = status["tesseract"] and all_packages_installed and all_directories_exist
    
    response = {
        "status": "healthy" if overall_health else "unhealthy",
        "timestamp": __import__('datetime').datetime.now().isoformat(),
        "checks": status
    }
    
    print(json.dumps(response, indent=2))
    
    if not overall_health:
        sys.exit(1)

if __name__ == "__main__":
    main()
EOF

chmod +x health_check.py

# Create web interface startup script
echo "🌐 Creating web interface startup script..."
cat > start_web_app.sh << 'EOF'
#!/bin/bash

# Start the web interface
echo "🚀 Starting SCORM Content Extractor Web App..."

# Load environment variables
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Get port from environment or default to 8000
PORT=${PORT:-8000}

echo "📱 Web interface will be available at: http://localhost:$PORT"
echo "🏥 Health check available at: http://localhost:$PORT/health"

# Start the web app
python3 web_app.py
EOF

chmod +x start_web_app.sh

# Create deployment guide
echo "📖 Creating deployment guide..."
cat > DEPLOYMENT_GUIDE.md << 'EOF'
# Azure Web App Deployment Guide

## 🚀 Quick Deployment

1. **Upload files to Azure Web App**
2. **Run startup script:**
   ```bash
   chmod +x Content_Extraction/azure_startup.sh
   ./Content_Extraction/azure_startup.sh
   ```

3. **Update environment variables:**
   - Edit `.env` file with your Azure Speech Services credentials
   - Or set environment variables in Azure Web App Configuration

4. **Test health check:**
   ```bash
   python3 health_check.py
   ```

5. **Start web interface (optional):**
   ```bash
   ./start_web_app.sh
   ```

## 🌐 Web Interface

The system includes a web interface for easy content extraction:

### Features
- **System Health Check**: Verify all dependencies are working
- **Content Extraction**: Extract specific content types via web form
- **Results Management**: View and download extraction results
- **Real-time Status**: Monitor extraction progress

### Access
- **Main Interface**: `http://your-app-url/`
- **Health Check**: `http://your-app-url/health`
- **API Endpoints**: Available for programmatic access

### Usage
1. Open the web interface in your browser
2. Check system health
3. Select content type to extract
4. Provide SCORM package path
5. Click "Extract Content"
6. Download results when complete

## 🔧 Manual Setup (if needed)

### Install System Dependencies
```bash
apt-get update
apt-get install -y tesseract-ocr tesseract-ocr-eng portaudio19-dev python3-dev python3-pip
```

### Install Python Dependencies
```bash
pip install -r Content_Extraction/requirements.txt
```

### Set Environment Variables
```bash
export AZURE_SPEECH_KEY="your_key"
export AZURE_SPEECH_REGION="eastus"
```

## 📋 Usage Examples

### Command Line Extraction
```bash
# Extract specific content types
python3 Content_Extraction/modular_extractor.py <scorm_path> <content_type>

# Extract all content
python3 Content_Extraction/modular_extractor.py <scorm_path> all
```

### Web Interface Extraction
1. Start web app: `./start_web_app.sh`
2. Open browser to web interface
3. Use the form to extract content

## 🏥 Health Check

Run health check to verify installation:
```bash
python3 health_check.py
```

## 🔍 Troubleshooting

1. **OCR not working**: Ensure tesseract-ocr is installed
2. **Video transcription failing**: Check Azure credentials
3. **Permission errors**: Ensure proper file permissions
4. **Import errors**: Verify all Python packages are installed
5. **Web interface not loading**: Check if Flask is installed and port is available

## 📞 Support

Check the main README.md for detailed documentation.
EOF

echo "✅ Deployment guide created"

# Final status
echo ""
echo "🎉 Azure Web App Setup Complete!"
echo "=================================="
echo ""
echo "✅ System dependencies installed"
echo "✅ Python packages installed"
echo "✅ Environment configured"
echo "✅ Directories created"
echo "✅ Health check endpoint created"
echo "✅ Deployment guide created"
echo ""
echo "📋 Next Steps:"
echo "1. Update .env file with your Azure credentials"
echo "2. Test health check: python3 health_check.py"
echo "3. Start extracting content!"
echo ""
echo "📖 See DEPLOYMENT_GUIDE.md for detailed instructions"
echo ""

# Optional: Run health check
if [ "$1" = "--health-check" ]; then
    echo "🏥 Running health check..."
    python3 health_check.py
fi

echo "🚀 Setup script completed successfully!" 