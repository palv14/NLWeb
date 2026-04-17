# SCORM Content Extraction System

A comprehensive Python system for extracting learning content from any SCORM package and transforming it into formats suitable for Elasticsearch and NLWeb integration.

## 🚀 Features

### **Content Extraction**
- **Lesson Content**: Metadata, structured content, and quiz items
- **Video Content**: Metadata and Azure Speech Services transcription
- **PDF Content**: Text extraction with page-level details
- **Image Content**: Metadata and OCR text extraction
- **Audio Content**: Azure Speech Services transcription
- **Quiz Content**: Interactive assessment items

### **Advanced Capabilities**
- **Azure Speech Services**: Enterprise-grade video/audio transcription
- **OCR Processing**: Text extraction from images using Tesseract
- **Modular Architecture**: Selective extraction by content type
- **NLWeb Integration**: Compatible JSON schema with dynamic URLs
- **Comprehensive Metadata**: Rich extraction information
- **Generic SCORM Support**: Works with any SCORM package

## 📁 File Structure

```
Content_Extraction/
├── comprehensive_content_extractor.py    # Original comprehensive extractor
├── modular_extractor.py                  # Master script for selective extraction
├── extract_lesson_content.py             # Generic lesson content extractor
├── extract_video_content.py              # Video content + transcripts
├── extract_pdf_content.py                # PDF content
├── extract_quiz_content.py               # Quiz content only
├── extract_image_content.py              # Image content + OCR
├── azure_speech_integration.py           # Azure Speech Services
├── setup_azure_credentials.py            # Azure setup helper
├── verify_azure_credentials.py           # Azure credential verification
├── test_azure_simple.py                  # Azure testing script
├── web_app.py                            # Flask web interface
├── azure_startup.sh                      # Azure deployment script
├── Dockerfile                            # Docker containerization
├── docker-compose.yml                    # Docker orchestration
├── requirements.txt                      # Dependencies
├── README.md                            # This documentation
├── EXECUTION_GUIDE.md                   # Quick start guide
└── AZURE_SETUP.md                       # Azure setup guide
```

## 🛠️ Installation

### **System Dependencies**

```bash
# macOS
brew install tesseract
brew install portaudio

# Ubuntu/Debian
sudo apt-get install tesseract-ocr
sudo apt-get install portaudio19-dev
```

### **Python Dependencies**

```bash
# Install all dependencies
pip install -r Content_Extraction/requirements.txt
```

## 🎯 Quick Start

### **Modular Extraction (Recommended)**

```bash
# Extract specific content types
python3 Content_Extraction/modular_extractor.py <scorm_path> <content_type> [output_dir]

# Examples:
python3 Content_Extraction/modular_extractor.py /path/to/scorm lesson
python3 Content_Extraction/modular_extractor.py /path/to/scorm video
python3 Content_Extraction/modular_extractor.py /path/to/scorm pdf
python3 Content_Extraction/modular_extractor.py /path/to/scorm image
python3 Content_Extraction/modular_extractor.py /path/to/scorm quiz
python3 Content_Extraction/modular_extractor.py /path/to/scorm all
```

### **Comprehensive Extraction**

```bash
# Extract all content types at once
python3 Content_Extraction/test_comprehensive_extraction.py
```

## 📊 Content Types

| Content Type | Description |
|--------------|-------------|
| **Lesson Metadata** | Course structure and lesson information |
| **Lesson Content** | Actual learning content from lessons |
| **Quiz Content** | Interactive assessment items |
| **PDF Content** | Text extracted from PDF documents |
| **Video Content** | Video metadata and information |
| **Video Transcripts** | Transcribed audio from videos |
| **Image Content** | Image metadata and descriptions |
| **Image OCR Content** | Text extracted from images via OCR |

## 🎬 Video Transcription

The extractor uses **Azure Speech Services** for video and audio transcription:

### Azure Speech Services
- **Enterprise-grade** transcription
- **Supports** files up to 500MB and 4 hours
- **Better accuracy** and reliability
- **No rate limiting**
- **Handles large videos** that fail with other services

**Setup Azure Speech Services:**
```bash
# Install Azure Speech SDK
pip install azure-cognitiveservices-speech

# Set environment variables
export AZURE_SPEECH_KEY="your_subscription_key"
export AZURE_SPEECH_REGION="eastus"
```

**See [AZURE_SETUP.md](AZURE_SETUP.md) for detailed setup instructions.**

## 🖼️ Image OCR Processing

The extractor uses **Tesseract OCR** for text extraction from images:

### OCR Capabilities
- **Multiple formats**: JPG, PNG, GIF, BMP, TIFF, WebP
- **Rich metadata**: Dimensions, format, file size
- **Text extraction**: Separate OCR content items
- **High accuracy**: Tesseract engine

**Setup OCR:**
```bash
# macOS
brew install tesseract

# Ubuntu/Debian
sudo apt-get install tesseract-ocr

# Python wrapper
pip install pytesseract Pillow
```

## 🔧 Modular System Benefits

### **Selective Testing**
- Test only specific content types
- Faster development cycles
- Isolated debugging

### **Resource Efficiency**
- Save Azure credits by avoiding unnecessary transcription
- Reduce processing time for large SCORM packages
- Optimize for specific use cases

### **Flexible Deployment**
- Deploy only required extractors
- Customize extraction workflows
- Scale based on needs

## 📋 Output Formats

### **Individual Content Files**
Each content type generates separate JSON files:
- `lesson_metadata_content.json`
- `lesson_content_content.json`
- `quiz_content_content.json`
- `pdf_content_content.json`
- `video_content_content.json`
- `transcript_content_content.json`
- `image_content_content.json`
- `image_ocr_content_content.json`

### **NLWeb Integration**
Compatible JSON schema with:
- Dynamic URL generation
- Content categorization
- Rich metadata
- Searchable content

## 🌐 Environment Setup

### **Local Development**
```bash
# Clone the repository
git clone <repository-url>
cd Content_Extraction

# Install system dependencies
brew install tesseract portaudio  # macOS
# sudo apt-get install tesseract-ocr portaudio19-dev  # Ubuntu/Debian

# Install Python dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your Azure credentials
```

### **Azure Web App**
```bash
# Run the startup script
chmod +x azure_startup.sh
./azure_startup.sh

# Start web interface
./start_web_app.sh
```

### **Docker Environment**
```bash
# Build and run with Docker
docker build -t scorm-extractor .
docker run -p 8000:8000 -e AZURE_SPEECH_KEY=your_key scorm-extractor

# Or use docker-compose
docker-compose up -d
```

## 🔌 API Endpoints

### **Web Interface Endpoints**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Main web interface |
| `/health` | GET | System health check |
| `/extract` | POST | Extract content from SCORM package |
| `/results` | GET | List extraction results |
| `/download/<filename>` | GET | Download result file |

### **Health Check Response**
```json
{
  "status": "healthy",
  "timestamp": "2025-08-07T12:00:00.000000",
  "checks": {
    "tesseract": true,
    "python_packages": [...],
    "azure_credentials": true,
    "directories": [...]
  }
}
```

### **Extraction Request**
```json
{
  "contentType": "lesson",
  "scormPath": "/path/to/scorm",
  "outputDir": "output_directory"
}
```

### **Extraction Response**
```json
{
  "success": true,
  "message": "Successfully extracted lesson content",
  "output": "Extraction log...",
  "timestamp": "2025-08-07T12:00:00.000000"
}
```

## 🚀 Deployment Options

### **Option 1: Azure Web App (Recommended)**

#### **Quick Deployment**
1. **Upload files** to Azure Web App
2. **Run startup script:**
   ```bash
   chmod +x azure_startup.sh
   ./azure_startup.sh
   ```
3. **Set environment variables** in Azure Web App Configuration
4. **Start web interface:**
   ```bash
   ./start_web_app.sh
   ```

#### **Environment Variables**
```bash
AZURE_SPEECH_KEY=your_azure_speech_key
AZURE_SPEECH_REGION=eastus
COURSE_TITLE=your_course_title
SITE_NAME=your_site_name
BASE_URL=https://your-site.com
```

### **Option 2: Docker Deployment**

#### **Single Container**
```bash
# Build image
docker build -t scorm-extractor .

# Run container
docker run -d \
  -p 8000:8000 \
  -e AZURE_SPEECH_KEY=your_key \
  -e AZURE_SPEECH_REGION=eastus \
  -v /path/to/scorm:/app/scorm_packages:ro \
  -v /path/to/output:/app/extracted_content \
  scorm-extractor
```

#### **Docker Compose**
```bash
# Start all services
docker-compose up -d

# Access web interface
open http://localhost:8000
```

### **Option 3: Local Server**

#### **Direct Installation**
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export AZURE_SPEECH_KEY=your_key
export AZURE_SPEECH_REGION=eastus

# Start web interface
python3 web_app.py
```

## 🔄 Deployment Process

### **Step 1: Prepare Environment**
```bash
# Install system dependencies
brew install tesseract portaudio  # macOS
# sudo apt-get install tesseract-ocr portaudio19-dev  # Ubuntu/Debian

# Install Python dependencies
pip install -r requirements.txt
```

### **Step 2: Configure Azure Speech Services**
```bash
# Set up Azure credentials
export AZURE_SPEECH_KEY=your_subscription_key
export AZURE_SPEECH_REGION=eastus

# Or create .env file
echo "AZURE_SPEECH_KEY=your_key" > .env
echo "AZURE_SPEECH_REGION=eastus" >> .env
```

### **Step 3: Test Installation**
```bash
# Run health check
python3 health_check.py

# Test extraction
python3 modular_extractor.py /path/to/test/scorm lesson
```

### **Step 4: Deploy**
```bash
# For Azure Web App
./azure_startup.sh
./start_web_app.sh

# For Docker
docker-compose up -d

# For local server
python3 web_app.py
```

### **Step 5: Verify Deployment**
```bash
# Check web interface
curl http://localhost:8000/health

# Test extraction via API
curl -X POST http://localhost:8000/extract \
  -F "contentType=lesson" \
  -F "scormPath=/path/to/scorm"
```

## 📚 Documentation

- **[requirements.txt](requirements.txt)**: Complete dependency list
- **[AZURE_SETUP.md](AZURE_SETUP.md)**: Azure Speech Services setup
- **[EXECUTION_GUIDE.md](EXECUTION_GUIDE.md)**: Quick start guide

## 🎉 Success Metrics

- **✅ Generic SCORM Support**: Works with any SCORM package
- **✅ Modular Architecture**: Selective content extraction
- **✅ NLWeb Compatibility**: Dynamic URLs and rich metadata
- **✅ Azure Speech Services**: Enterprise-grade transcription
- **✅ Tesseract OCR**: High-accuracy image text extraction
- **✅ Web Interface**: User-friendly extraction management
- **✅ Docker Support**: Containerized deployment
- **✅ Health Monitoring**: Real-time system status

## 🔍 Troubleshooting

### **Common Issues**
1. **OCR not working**: Install tesseract system package
2. **Video transcription failing**: Check Azure credentials
3. **Missing dependencies**: Run `pip install -r requirements.txt`
4. **Permission errors**: Check file paths and permissions
5. **Web interface not loading**: Check if Flask is installed and port is available

### **Support**
For issues and questions, check the troubleshooting sections in the individual documentation files. 