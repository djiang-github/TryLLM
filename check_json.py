import json
import sys
from pathlib import Path

def check_json_file(filename):
    try:
        with open(filename, 'r') as f:
            data = json.load(f)
            print(f"\nNumber of entries in {filename}: {len(data)}")
            if len(data) > 0:
                print("\nFirst entry sample:")
                print(json.dumps(data[0], indent=2))
    except Exception as e:
        print(f"Error reading {filename}: {str(e)}")

for json_file in Path('.').glob('animal_data*.json'):
    check_json_file(json_file)
