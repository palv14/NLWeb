# JSON to JSONL Conversion

This directory contains scripts and converted files for transforming JSON content files to JSONL (JSON Lines) format.

## What is JSONL?

JSONL (JSON Lines) is a convenient format for storing structured data that may be processed one record at a time. Each line is a valid JSON value, making it easy to process large datasets without loading everything into memory at once.

## Conversion Process

### Original JSON Structure
The original JSON files contained nested structures with arrays of content items:
```json
{
  "module_info": { ... },
  "lesson_metadata": [ ... ],
  "lesson_content": [ ... ],
  "quiz_content": [ ... ],
  "image_content": [ ... ],
  "video_content": [ ... ],
  "transcript_content": [ ... ]
}
```

### JSONL Format
Each object from the arrays becomes a separate line in the JSONL file, with a `source_key` field added to identify the original array:
```jsonl
{"module_info": {"module_number": "1.1", "module_title": "About this Module", ...}}
{"source_key": "lesson_metadata", "id": "...", "title": "...", ...}
{"source_key": "lesson_content", "id": "...", "title": "...", ...}
{"source_key": "quiz_content", "id": "...", "title": "...", ...}
```

## Files Created

### Conversion Scripts
- `convert_to_jsonl.py` - Main conversion script
- `verify_jsonl.py` - Verification script to validate JSONL files

### Converted Files
All JSONL files are stored in the `module_mapped_output_jsonl/` directory:

| Original JSON | JSONL File | Lines | Size |
|---------------|------------|-------|------|
| module_1.1_content.json | module_1.1_content.jsonl | 71 | 122KB |
| module_1.2_content.json | module_1.2_content.jsonl | 45 | 96KB |
| module_1.3_content.json | module_1.3_content.jsonl | 27 | 72KB |
| module_1.4_content.json | module_1.4_content.jsonl | 29 | 68KB |
| module_1.5_content.json | module_1.5_content.jsonl | 33 | 72KB |
| module_1.6_content.json | module_1.6_content.jsonl | 21 | 32KB |
| module_1.7_content.json | module_1.7_content.jsonl | 35 | 102KB |
| module_1.8_content.json | module_1.8_content.jsonl | 3 | 1.3KB |
| module_1.9_content.json | module_1.9_content.jsonl | 3 | 2.4KB |
| module_mapped_content.json | module_mapped_content.jsonl | 9 | 283KB |
| module_mapped_summary.json | module_mapped_summary.jsonl | 4 | 3.9KB |

**Total: 280 lines across all files**

## Usage

### Running the Conversion
```bash
python3 convert_to_jsonl.py
```

### Verifying the Files
```bash
python3 verify_jsonl.py
```

### Reading JSONL Files
```python
import json

# Read a JSONL file line by line
with open('module_1.1_content.jsonl', 'r') as f:
    for line in f:
        data = json.loads(line.strip())
        print(data['title'])  # Access any field
```

## Benefits of JSONL Format

1. **Streaming Processing**: Can process large files without loading everything into memory
2. **Parallel Processing**: Each line can be processed independently
3. **Easy Validation**: Each line is a complete JSON object
4. **Compatibility**: Works well with many data processing tools and databases
5. **Append Operations**: Easy to add new records by appending lines

## Content Types

The converted files contain various content types, each identified by the `source_key` field:

- `lesson_metadata` - Lesson structure and metadata
- `lesson_content` - Main lesson content (text, headings, paragraphs)
- `quiz_content` - Quiz and interactive content
- `image_content` - Image descriptions and metadata
- `video_content` - Video metadata and transcripts
- `transcript_content` - Separate transcript entries
- `module_info` - Module-level information

Each content item maintains its original structure with additional metadata including extraction timestamps, file paths, and content types. 