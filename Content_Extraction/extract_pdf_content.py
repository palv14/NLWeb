#!/usr/bin/env python3
"""
Modular PDF Content Extractor
Extracts text content from PDF files in SCORM packages
"""

import os
import json
import hashlib
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

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
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    print("Warning: PyPDF2 not available. Install with: pip install PyPDF2")

class PDFContentExtractor:
    """Extract text content from PDF files in SCORM packages."""
    
    def __init__(self, scorm_path: str, output_dir: str = "pdf_extraction_output"):
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
    
    def _extract_pdf_content(self):
        """Extract content from PDF files."""
        if not PDF_AVAILABLE:
            self.logger.warning("PyPDF2 not available. PDF extraction will be skipped.")
            return
        
        for pdf_file in self.scorm_path.rglob('*.pdf'):
            try:
                with open(pdf_file, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    
                    # Extract text from all pages
                    full_text = ""
                    page_details = []
                    
                    for page_num, page in enumerate(pdf_reader.pages, 1):
                        page_text = page.extract_text()
                        if page_text.strip():
                            full_text += f"\n--- Page {page_num} ---\n{page_text}\n"
                            page_details.append({
                                "page_number": page_num,
                                "text_length": len(page_text),
                                "text_preview": page_text[:200] + "..." if len(page_text) > 200 else page_text
                            })
                    
                    # Get document metadata
                    doc_info = {}
                    if pdf_reader.metadata:
                        for key, value in pdf_reader.metadata.items():
                            if value:
                                doc_info[key] = str(value)
                    
                    item_id = hashlib.md5(str(pdf_file.relative_to(self.scorm_path)).encode()).hexdigest()
                    
                    content_doc = {
                        "id": f"pdf_content_{item_id}",
                        "title": f"PDF Content: {pdf_file.stem}",
                        "content": full_text.strip(),
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
                    
            except Exception as e:
                self.logger.error(f"Error extracting PDF content from {pdf_file}: {e}")
    
    def extract_pdf_content(self) -> Dict[str, Any]:
        """Extract all PDF content from the SCORM package."""
        self.logger.info(f"Starting PDF content extraction from: {self.scorm_path}")
        
        # Extract PDF content
        self._extract_pdf_content()
        
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
        
        summary_file = self.output_dir / "pdf_extraction_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Saved extraction summary to {summary_file}")

def main():
    """Main function for PDF content extraction."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python3 extract_pdf_content.py <scorm_path> [output_dir]")
        sys.exit(1)
    
    scorm_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "pdf_extraction_output"
    
    print("📄 PDF Content Extractor")
    print("=" * 40)
    
    extractor = PDFContentExtractor(scorm_path, output_dir)
    results = extractor.extract_pdf_content()
    
    print(f"\n✅ Extraction complete!")
    print(f"📊 Total items: {results['total_items']}")
    print(f"📁 Output directory: {output_dir}")
    print(f"📋 Content types: {results['content_types']}")

if __name__ == "__main__":
    main() 