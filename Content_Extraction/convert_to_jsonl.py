#!/usr/bin/env python3
"""
Script to convert JSON files to JSONL format.
Each object in the arrays within the JSON files will become a separate line in the JSONL file.
"""

import json
import os
import glob
from pathlib import Path

def convert_json_to_jsonl(json_file_path, jsonl_file_path):
    """
    Convert a JSON file to JSONL format.
    
    Args:
        json_file_path (str): Path to the input JSON file
        jsonl_file_path (str): Path to the output JSONL file
    """
    try:
        # Read the JSON file
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Open the JSONL file for writing
        with open(jsonl_file_path, 'w', encoding='utf-8') as f:
            # Handle different data structures
            if isinstance(data, dict):
                # If it's a dictionary, look for arrays to flatten
                for key, value in data.items():
                    if isinstance(value, list):
                        # Write each item in the array as a separate line
                        for item in value:
                            # Add the key as a field to identify the source
                            item_with_source = {
                                "source_key": key,
                                **item
                            }
                            f.write(json.dumps(item_with_source, ensure_ascii=False) + '\n')
                    else:
                        # For non-array values, write them as a single line
                        f.write(json.dumps({key: value}, ensure_ascii=False) + '\n')
            elif isinstance(data, list):
                # If it's directly a list, write each item as a separate line
                for item in data:
                    f.write(json.dumps(item, ensure_ascii=False) + '\n')
            else:
                # For other types, write as a single line
                f.write(json.dumps(data, ensure_ascii=False) + '\n')
        
        print(f"✓ Converted {json_file_path} to {jsonl_file_path}")
        
    except Exception as e:
        print(f"✗ Error converting {json_file_path}: {str(e)}")

def main():
    """Main function to convert all JSON files in the module_mapped_output directory."""
    
    # Get the directory containing this script
    script_dir = Path(__file__).parent
    module_output_dir = script_dir / "module_mapped_output"
    
    # Create output directory for JSONL files
    jsonl_output_dir = script_dir / "module_mapped_output_jsonl"
    jsonl_output_dir.mkdir(exist_ok=True)
    
    # Find all JSON files in the module_mapped_output directory
    json_files = glob.glob(str(module_output_dir / "*.json"))
    
    if not json_files:
        print("No JSON files found in module_mapped_output directory")
        return
    
    print(f"Found {len(json_files)} JSON files to convert:")
    
    # Convert each JSON file to JSONL
    for json_file in json_files:
        json_path = Path(json_file)
        jsonl_filename = json_path.stem + ".jsonl"
        jsonl_path = jsonl_output_dir / jsonl_filename
        
        print(f"\nConverting {json_path.name}...")
        convert_json_to_jsonl(str(json_path), str(jsonl_path))
    
    print(f"\n🎉 Conversion complete! JSONL files saved to: {jsonl_output_dir}")
    
    # List the created files
    jsonl_files = list(jsonl_output_dir.glob("*.jsonl"))
    print(f"\nCreated {len(jsonl_files)} JSONL files:")
    for jsonl_file in jsonl_files:
        print(f"  - {jsonl_file.name}")

if __name__ == "__main__":
    main() 