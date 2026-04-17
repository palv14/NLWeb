# Dockerfile for SCORM Content Extraction System
# Optimized for Azure Web App deployment

FROM python:3.9-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV DEBIAN_FRONTEND=noninteractive

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    portaudio19-dev \
    python3-dev \
    build-essential \
    libssl-dev \
    libffi-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p extracted_content \
    lesson_extraction_output \
    video_extraction_output \
    pdf_extraction_output \
    image_extraction_output \
    quiz_extraction_output

# Set permissions
RUN chmod +x *.py && \
    chmod +x azure_startup.sh

# Create health check endpoint
RUN echo '#!/usr/bin/env python3' > health_check.py && \
    echo 'import os, sys, json, subprocess' >> health_check.py && \
    echo 'from pathlib import Path' >> health_check.py && \
    echo 'def check_dependencies():' >> health_check.py && \
    echo '    status = {"tesseract": False, "python_packages": [], "azure_credentials": False}' >> health_check.py && \
    echo '    try:' >> health_check.py && \
    echo '        result = subprocess.run(["tesseract", "--version"], capture_output=True, text=True)' >> health_check.py && \
    echo '        status["tesseract"] = result.returncode == 0' >> health_check.py && \
    echo '    except: pass' >> health_check.py && \
    echo '    packages = ["PyPDF2", "moviepy", "PIL", "pytesseract", "beautifulsoup4", "lxml", "requests", "elasticsearch", "azure.cognitiveservices.speech", "dotenv"]' >> health_check.py && \
    echo '    for package in packages:' >> health_check.py && \
    echo '        try:' >> health_check.py && \
    echo '            __import__(package.replace("-", "_").replace(".", "_"))' >> health_check.py && \
    echo '            status["python_packages"].append({"package": package, "status": "installed"})' >> health_check.py && \
    echo '        except ImportError:' >> health_check.py && \
    echo '            status["python_packages"].append({"package": package, "status": "missing"})' >> health_check.py && \
    echo '    status["azure_credentials"] = bool(os.getenv("AZURE_SPEECH_KEY") and os.getenv("AZURE_SPEECH_REGION"))' >> health_check.py && \
    echo '    return status' >> health_check.py && \
    echo 'def main():' >> health_check.py && \
    echo '    status = check_dependencies()' >> health_check.py && \
    echo '    all_packages_installed = all(pkg["status"] == "installed" for pkg in status["python_packages"])' >> health_check.py && \
    echo '    overall_health = status["tesseract"] and all_packages_installed' >> health_check.py && \
    echo '    response = {"status": "healthy" if overall_health else "unhealthy", "checks": status}' >> health_check.py && \
    echo '    print(json.dumps(response, indent=2))' >> health_check.py && \
    echo '    sys.exit(0 if overall_health else 1)' >> health_check.py && \
    echo 'if __name__ == "__main__": main()' >> health_check.py && \
    chmod +x health_check.py

# Expose port (if needed for web interface)
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 health_check.py || exit 1

# Default command
CMD ["python3", "health_check.py"] 