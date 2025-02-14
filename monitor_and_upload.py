import os
import time
from upload_data_to_oss import upload_file

def monitor_and_upload():
    """Monitor data files and upload when updated."""
    last_sizes = {
        'animal_data.json': 0,
        'animal_data_partial.json': 0
    }
    
    while True:
        for filename in last_sizes:
            if os.path.exists(filename):
                current_size = os.path.getsize(filename)
                if current_size > last_sizes[filename]:
                    print(f"\nNew data detected in {filename}")
                    print(f"Previous size: {last_sizes[filename]} bytes")
                    print(f"Current size: {current_size} bytes")
                    
                    # Upload updated file
                    upload_file(filename)
                    last_sizes[filename] = current_size
        
        time.sleep(60)  # Check every minute

if __name__ == "__main__":
    print("Starting data monitoring and upload...")
    monitor_and_upload()
