#!/usr/bin/env python3
"""
Modular SCORM Content Extractor
Allows selective extraction of different content types
"""

import sys
import os
from pathlib import Path

def show_usage():
    """Show usage information."""
    print("🔧 Modular SCORM Content Extractor")
    print("=" * 50)
    print("\nUsage:")
    print("  python3 modular_extractor.py <scorm_path> <content_type> [output_dir]")
    print("\nContent Types:")
    print("  lesson     - Extract lesson metadata and content")
    print("  video      - Extract video content and transcripts")
    print("  pdf        - Extract PDF content")
    print("  image      - Extract image content and descriptions")
    print("  quiz       - Extract quiz content")
    print("  all        - Extract all content types")
    print("\nExamples:")
    print("  python3 modular_extractor.py . lesson")
    print("  python3 modular_extractor.py . video video_output")
    print("  python3 modular_extractor.py . pdf pdf_output")
    print("  python3 modular_extractor.py . quiz quiz_output")
    print("  python3 modular_extractor.py . all comprehensive_output")

def run_lesson_extractor(scorm_path: str, output_dir: str):
    """Run lesson content extractor."""
    print("📚 Running Generic Lesson Content Extractor...")
    from extract_lesson_content import GenericLessonContentExtractor
    
    extractor = GenericLessonContentExtractor(scorm_path, output_dir)
    results = extractor.extract_lesson_content()
    
    print(f"✅ Lesson extraction complete!")
    print(f"📊 Total items: {results['total_items']}")
    print(f"📋 Content types: {results['content_types']}")
    print(f"🔍 SCORM type: {results['scorm_type']}")

def run_video_extractor(scorm_path: str, output_dir: str):
    """Run video content extractor."""
    print("🎬 Running Video Content Extractor...")
    from extract_video_content import VideoContentExtractor
    
    extractor = VideoContentExtractor(scorm_path, output_dir)
    results = extractor.extract_video_content()
    
    print(f"✅ Video extraction complete!")
    print(f"📊 Total items: {results['total_items']}")
    print(f"📋 Content types: {results['content_types']}")

def run_pdf_extractor(scorm_path: str, output_dir: str):
    """Run PDF content extractor."""
    print("📄 Running PDF Content Extractor...")
    from extract_pdf_content import PDFContentExtractor
    
    extractor = PDFContentExtractor(scorm_path, output_dir)
    results = extractor.extract_pdf_content()
    
    print(f"✅ PDF extraction complete!")
    print(f"📊 Total items: {results['total_items']}")
    print(f"📋 Content types: {results['content_types']}")

def run_quiz_extractor(scorm_path: str, output_dir: str):
    """Run quiz content extractor."""
    print("🧩 Running Quiz Content Extractor...")
    from extract_quiz_content import QuizContentExtractor
    
    extractor = QuizContentExtractor(scorm_path, output_dir)
    results = extractor.extract_quiz_content()
    
    print(f"✅ Quiz extraction complete!")
    print(f"📊 Total items: {results['total_items']}")
    print(f"📋 Content types: {results['content_types']}")

def run_image_extractor(scorm_path: str, output_dir: str):
    """Run image content extractor."""
    print("🖼️  Running Image Content Extractor...")
    from extract_image_content import ImageContentExtractor
    
    extractor = ImageContentExtractor(scorm_path, output_dir)
    results = extractor.extract_image_content()
    
    print(f"✅ Image extraction complete!")
    print(f"📊 Total items: {results['total_items']}")
    print(f"📋 Content types: {results['content_types']}")

def run_all_extractors(scorm_path: str, output_dir: str):
    """Run all content extractors."""
    print("🚀 Running All Content Extractors...")
    
    # Create subdirectories for each type
    lesson_dir = Path(output_dir) / "lesson"
    video_dir = Path(output_dir) / "video"
    pdf_dir = Path(output_dir) / "pdf"
    image_dir = Path(output_dir) / "image"
    quiz_dir = Path(output_dir) / "quiz"
    
    # Run each extractor
    run_lesson_extractor(scorm_path, str(lesson_dir))
    run_video_extractor(scorm_path, str(video_dir))
    run_pdf_extractor(scorm_path, str(pdf_dir))
    run_image_extractor(scorm_path, str(image_dir))
    run_quiz_extractor(scorm_path, str(quiz_dir))
    
    print(f"\n🎉 All extractions complete!")
    print(f"📁 Output directory: {output_dir}")
    print(f"📂 Subdirectories: lesson, video, pdf, image, quiz")

def main():
    """Main function."""
    if len(sys.argv) < 3:
        show_usage()
        sys.exit(1)
    
    scorm_path = sys.argv[1]
    content_type = sys.argv[2].lower()
    output_dir = sys.argv[3] if len(sys.argv) > 3 else f"{content_type}_extraction_output"
    
    # Validate content type
    valid_types = ["lesson", "video", "pdf", "image", "quiz", "all"]
    if content_type not in valid_types:
        print(f"❌ Invalid content type: {content_type}")
        print(f"Valid types: {', '.join(valid_types)}")
        sys.exit(1)
    
    # Check if SCORM path exists
    if not Path(scorm_path).exists():
        print(f"❌ SCORM path does not exist: {scorm_path}")
        sys.exit(1)
    
    # Run the appropriate extractor
    try:
        if content_type == "lesson":
            run_lesson_extractor(scorm_path, output_dir)
        elif content_type == "video":
            run_video_extractor(scorm_path, output_dir)
        elif content_type == "pdf":
            run_pdf_extractor(scorm_path, output_dir)
        elif content_type == "image":
            run_image_extractor(scorm_path, output_dir)
        elif content_type == "quiz":
            run_quiz_extractor(scorm_path, output_dir)
        elif content_type == "all":
            run_all_extractors(scorm_path, output_dir)
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure all required dependencies are installed")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error during extraction: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 