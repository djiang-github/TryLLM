import boto3
import os
from botocore.config import Config

def get_oss_client():
    """Configure OSS client with credentials."""
    return boto3.client(
        's3',
        region_name='cn-shanghai',
        aws_access_key_id=os.environ.get('jiwei_tos_ak'),
        aws_secret_access_key=os.environ.get('jiwei_tos_sk'),
        endpoint_url='http://jiwei-tos.tos-s3-cn-shanghai.volces.com',
        config=Config(signature_version='s3v4')
    )

def upload_file(filename: str, bucket: str = 'jiwei-tos'):
    """Upload a file to OSS bucket."""
    if not os.path.exists(filename):
        print(f"File not found: {filename}")
        return False
        
    try:
        client = get_oss_client()
        print(f"Uploading {filename} to bucket {bucket}...")
        client.upload_file(filename, bucket, filename)
        print(f"Successfully uploaded {filename}")
        return True
    except Exception as e:
        print(f"Error uploading {filename}: {str(e)}")
        return False

def upload_data_files():
    """Upload both data files to OSS."""
    files_to_upload = ['animal_data.json', 'animal_data_partial.json']
    results = []
    
    for filename in files_to_upload:
        if os.path.exists(filename):
            print(f"\nUploading {filename}...")
            success = upload_file(filename)
            results.append((filename, success))
        else:
            print(f"\nSkipping {filename} - file not found")
            results.append((filename, False))
    
    return results

if __name__ == "__main__":
    print("Starting data upload to OSS...")
    results = upload_data_files()
    
    print("\nUpload Summary:")
    for filename, success in results:
        status = "Success" if success else "Failed"
        print(f"{filename}: {status}")
