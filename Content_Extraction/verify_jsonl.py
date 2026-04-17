#!/usr/bin/env python3
"""
Script to verify that all JSONL files are valid and can be parsed correctly.
"""

import json
import glob
from pathlib import Path

def verify_jsonl_file(jsonl_file_path):
    """
    Verify that a JSONL file is valid and can be parsed.
    
    Args:
        jsonl_file_path (str): Path to the JSONL file to verify
        
    Returns:
        tuple: (is_valid, line_count, error_message)
    """
    try:
        line_count = 0
        with open(jsonl_file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if line:  # Skip empty lines
                    json.loads(line)
                    line_count += 1
        
        return True, line_count, None
        
    except json.JSONDecodeError as e:
        return False, line_count, f"JSON decode error at line {line_num}: {str(e)}"
    except Exception as e:
        return False, 0, f"Error reading file: {str(e)}"

def main():
    """Main function to verify all JSONL files."""
    
    # Get the directory containing this script
    script_dir = Path(__file__).parent
    jsonl_output_dir = script_dir / "module_mapped_output_jsonl"
    
    # Find all JSONL files
    jsonl_files = glob.glob(str(jsonl_output_dir / "*.jsonl"))
    
    if not jsonl_files:
        print("No JSONL files found in module_mapped_output_jsonl directory")
        return
    
    print(f"Verifying {len(jsonl_files)} JSONL files...\n")
    
    all_valid = True
    total_lines = 0
    
    # Verify each JSONL file
    for jsonl_file in sorted(jsonl_files):
        jsonl_path = Path(jsonl_file)
        is_valid, line_count, error_msg = verify_jsonl_file(str(jsonl_path))
        
        if is_valid:
            print(f"✓ {jsonl_path.name}: {line_count} lines")
            total_lines += line_count
        else:
            print(f"✗ {jsonl_path.name}: {error_msg}")
            all_valid = False
    
    print(f"\n{'='*50}")
    if all_valid:
        print(f"🎉 All {len(jsonl_files)} JSONL files are valid!")
        print(f"📊 Total lines across all files: {total_lines}")
    else:
        print("❌ Some JSONL files have errors. Please check the output above.")
    
    print(f"{'='*50}")

if __name__ == "__main__":
    main() 