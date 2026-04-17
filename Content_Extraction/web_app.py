#!/usr/bin/env python3
"""
Simple Flask Web Interface for SCORM Content Extraction
Designed for Azure Web App deployment
"""

import os
import json
import subprocess
from pathlib import Path
from datetime import datetime
from flask import Flask, request, jsonify, render_template_string, send_file
from werkzeug.utils import secure_filename

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

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max file size

# HTML template for the web interface
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SCORM Content Extractor</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        .header { background: #0078d4; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        .section { background: #f5f5f5; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        .form-group { margin-bottom: 15px; }
        label { display: block; margin-bottom: 5px; font-weight: bold; }
        input, select, textarea { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
        button { background: #0078d4; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
        button:hover { background: #106ebe; }
        .status { padding: 10px; border-radius: 4px; margin: 10px 0; }
        .success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        .info { background: #d1ecf1; color: #0c5460; border: 1px solid #bee5eb; }
        .results { background: white; padding: 15px; border-radius: 4px; border: 1px solid #ddd; }
        pre { background: #f8f9fa; padding: 10px; border-radius: 4px; overflow-x: auto; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 SCORM Content Extractor</h1>
        <p>Extract learning content from any SCORM package for NLWeb integration</p>
    </div>

    <div class="section">
        <h2>🏥 System Health Check</h2>
        <button onclick="checkHealth()">Check System Health</button>
        <div id="healthResult"></div>
    </div>

    <div class="section">
        <h2>📁 Content Extraction</h2>
        <form id="extractionForm">
            <div class="form-group">
                <label for="contentType">Content Type:</label>
                <select id="contentType" name="contentType" required>
                    <option value="">Select content type...</option>
                    <option value="lesson">Lesson Content (Metadata + Content + Quiz)</option>
                    <option value="video">Video Content + Transcripts</option>
                    <option value="pdf">PDF Content</option>
                    <option value="image">Image Content + OCR</option>
                    <option value="quiz">Quiz Content Only</option>
                    <option value="all">All Content Types</option>
                </select>
            </div>
            
            <div class="form-group">
                <label for="scormPath">SCORM Package Path:</label>
                <input type="text" id="scormPath" name="scormPath" value="." placeholder="Path to SCORM package">
            </div>
            
            <div class="form-group">
                <label for="outputDir">Output Directory:</label>
                <input type="text" id="outputDir" name="outputDir" placeholder="Output directory (optional)">
            </div>
            
            <button type="submit">Extract Content</button>
        </form>
        <div id="extractionResult"></div>
    </div>

    <div class="section">
        <h2>📊 Recent Results</h2>
        <button onclick="listResults()">List Recent Results</button>
        <div id="resultsList"></div>
    </div>

    <script>
        async function checkHealth() {
            const resultDiv = document.getElementById('healthResult');
            resultDiv.innerHTML = '<div class="info">Checking system health...</div>';
            
            try {
                const response = await fetch('/health');
                const data = await response.json();
                
                if (data.status === 'healthy') {
                    resultDiv.innerHTML = '<div class="success">✅ System is healthy!</div>';
                } else {
                    resultDiv.innerHTML = '<div class="error">❌ System has issues</div>';
                }
                
                resultDiv.innerHTML += '<pre>' + JSON.stringify(data, null, 2) + '</pre>';
            } catch (error) {
                resultDiv.innerHTML = '<div class="error">❌ Health check failed: ' + error.message + '</div>';
            }
        }

        async function extractContent(event) {
            event.preventDefault();
            const resultDiv = document.getElementById('extractionResult');
            const formData = new FormData(event.target);
            
            resultDiv.innerHTML = '<div class="info">Extracting content...</div>';
            
            try {
                const response = await fetch('/extract', {
                    method: 'POST',
                    body: formData
                });
                
                const data = await response.json();
                
                if (data.success) {
                    resultDiv.innerHTML = '<div class="success">✅ Extraction completed successfully!</div>';
                } else {
                    resultDiv.innerHTML = '<div class="error">❌ Extraction failed</div>';
                }
                
                resultDiv.innerHTML += '<pre>' + JSON.stringify(data, null, 2) + '</pre>';
            } catch (error) {
                resultDiv.innerHTML = '<div class="error">❌ Extraction failed: ' + error.message + '</div>';
            }
        }

        async function listResults() {
            const resultDiv = document.getElementById('resultsList');
            resultDiv.innerHTML = '<div class="info">Loading results...</div>';
            
            try {
                const response = await fetch('/results');
                const data = await response.json();
                
                if (data.success) {
                    let html = '<div class="success">📊 Found ' + data.results.length + ' result files</div>';
                    data.results.forEach(result => {
                        html += '<div class="results">';
                        html += '<strong>' + result.name + '</strong><br>';
                        html += 'Size: ' + result.size + ' bytes<br>';
                        html += 'Modified: ' + result.modified + '<br>';
                        html += '<a href="/download/' + result.name + '" target="_blank">Download</a>';
                        html += '</div>';
                    });
                    resultDiv.innerHTML = html;
                } else {
                    resultDiv.innerHTML = '<div class="error">❌ Failed to load results</div>';
                }
            } catch (error) {
                resultDiv.innerHTML = '<div class="error">❌ Failed to load results: ' + error.message + '</div>';
            }
        }

        document.getElementById('extractionForm').addEventListener('submit', extractContent);
        
        // Auto-check health on page load
        window.onload = function() {
            checkHealth();
        };
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """Main web interface."""
    return render_template_string(HTML_TEMPLATE)

@app.route('/health')
def health_check():
    """Health check endpoint."""
    try:
        # Run the health check script
        result = subprocess.run(['python3', 'health_check.py'], 
                              capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            return jsonify(json.loads(result.stdout))
        else:
            return jsonify({
                "status": "unhealthy",
                "error": result.stderr,
                "timestamp": datetime.now().isoformat()
            })
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        })

@app.route('/extract', methods=['POST'])
def extract_content():
    """Extract content from SCORM package."""
    try:
        content_type = request.form.get('contentType')
        scorm_path = request.form.get('scormPath', '.')
        output_dir = request.form.get('outputDir', '')
        
        if not content_type:
            return jsonify({"success": False, "error": "Content type is required"})
        
        # Validate content type
        valid_types = ['lesson', 'video', 'pdf', 'image', 'quiz', 'all']
        if content_type not in valid_types:
            return jsonify({"success": False, "error": f"Invalid content type. Valid types: {valid_types}"})
        
        # Build command
        cmd = ['python3', 'modular_extractor.py', scorm_path, content_type]
        if output_dir:
            cmd.append(output_dir)
        
        # Run extraction
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            return jsonify({
                "success": True,
                "message": f"Successfully extracted {content_type} content",
                "output": result.stdout,
                "timestamp": datetime.now().isoformat()
            })
        else:
            return jsonify({
                "success": False,
                "error": result.stderr,
                "output": result.stdout,
                "timestamp": datetime.now().isoformat()
            })
            
    except subprocess.TimeoutExpired:
        return jsonify({
            "success": False,
            "error": "Extraction timed out (5 minutes)",
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        })

@app.route('/results')
def list_results():
    """List recent extraction results."""
    try:
        results = []
        output_dirs = [
            'extracted_content',
            'lesson_extraction_output',
            'video_extraction_output',
            'pdf_extraction_output',
            'image_extraction_output',
            'quiz_extraction_output'
        ]
        
        for output_dir in output_dirs:
            if Path(output_dir).exists():
                for file_path in Path(output_dir).rglob('*.json'):
                    stat = file_path.stat()
                    results.append({
                        "name": str(file_path),
                        "size": stat.st_size,
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })
        
        return jsonify({
            "success": True,
            "results": results,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        })

@app.route('/download/<path:filename>')
def download_file(filename):
    """Download extraction result file."""
    try:
        file_path = Path(filename)
        if file_path.exists() and file_path.is_file():
            return send_file(file_path, as_attachment=True)
        else:
            return jsonify({"error": "File not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Get port from environment or default to 8000
    port = int(os.environ.get('PORT', 8000))
    
    print(f"🚀 Starting SCORM Content Extractor Web App on port {port}")
    print(f"📱 Web interface available at: http://localhost:{port}")
    print(f"🏥 Health check available at: http://localhost:{port}/health")
    
    app.run(host='0.0.0.0', port=port, debug=False) 