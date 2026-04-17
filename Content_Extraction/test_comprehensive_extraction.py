#!/usr/bin/env python3
"""
Test script for the enhanced comprehensive content extractor with NLWeb schema support
"""

import sys
import os
from pathlib import Path

# Add the current directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from comprehensive_content_extractor import EnhancedComprehensiveContentExtractor

def main():
    """Test the enhanced comprehensive content extractor."""
    print("🧪 Testing Enhanced Comprehensive Content Extractor with NLWeb Schema")
    print("=" * 70)
    
    # Get the current directory (should be the SCORM package directory)
    current_dir = Path.cwd()
    print(f"📁 Current directory: {current_dir}")
    
    # Check if we're in a SCORM package
    imsmanifest_file = current_dir / "imsmanifest.xml"
    if not imsmanifest_file.exists():
        print("❌ Error: imsmanifest.xml not found. Please run this script from a SCORM package directory.")
        sys.exit(1)
    
    print("✅ Found SCORM package structure")
    
    # Create extractor
    extractor = EnhancedComprehensiveContentExtractor(str(current_dir))
    
    # Extract all content
    print("\n🔄 Starting comprehensive content extraction...")
    results = extractor.extract_all_content()
    
    # Display results
    print("\n" + "=" * 70)
    print("📊 EXTRACTION RESULTS")
    print("=" * 70)
    print(f"✅ Total content items extracted: {results['total_items']}")
    print(f"🌐 NLWeb-compatible items generated: {results['nlweb_items']}")
    print(f"📁 Output directory: {results['output_directory']}")
    
    # Check output files
    output_dir = Path(results['output_directory'])
    if output_dir.exists():
        print(f"\n📂 Output files created:")
        for file_path in output_dir.glob("*.json"):
            file_size = file_path.stat().st_size
            print(f"   📄 {file_path.name} ({file_size:,} bytes)")
    
    # Show sample NLWeb content
    nlweb_file = output_dir / "nlweb_content.json"
    if nlweb_file.exists():
        print(f"\n🌐 Sample NLWeb-compatible content:")
        try:
            import json
            with open(nlweb_file, 'r', encoding='utf-8') as f:
                nlweb_content = json.load(f)
            
            if nlweb_content:
                sample = nlweb_content[0]
                print(f"   📋 Sample entry:")
                print(f"      ID: {sample['id']}")
                print(f"      Name: {sample['name']}")
                print(f"      URL: {sample['url']}")
                print(f"      Site: {sample['site']}")
                print(f"      Schema JSON length: {len(sample['schema_json'])} characters")
        except Exception as e:
            print(f"   ⚠️  Could not read NLWeb content: {e}")
    
    print(f"\n🎉 Extraction complete! Check the output directory for detailed results.")

if __name__ == "__main__":
    main() 