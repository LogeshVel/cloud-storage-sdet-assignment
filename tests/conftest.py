import pytest
import requests
import uuid
import os
import hashlib

# service url
BASE_URL = "http://localhost:8000"

@pytest.fixture(scope="session")
def base_url():
    return BASE_URL

@pytest.fixture
def cleanup_list():
    """A list to store file IDs for cleanup after tests."""
    file_ids = []
    yield file_ids
    # Teardown: Delete files
    for file_id in file_ids:
        try:
            requests.delete(f"{BASE_URL}/files/{file_id}")
        except Exception as e:
            print(f'Got unexpected error while deleting the file. {e}')

@pytest.fixture
def generate_file():
    """Factory fixture to generate files of specific size and name on the fly."""
    created_files = []

    def _create(filename, size_in_mb=1, content_prefix=b"test"):
        file_path = f"/tmp/{filename}"
        # create file of specific size
        with open(file_path, "wb") as f:
            f.write(content_prefix)
            # Just trying to fill the space
            remaining = int(size_in_mb * 1024 * 1024) - len(content_prefix)
            if remaining > 0:
                if size_in_mb > 100:
                    f.seek(remaining, 1)
                    f.write(b'\0')
                else:
                    f.write(b"0" * remaining)
        created_files.append(file_path)
        return file_path

    yield _create
    
    # Cleanup local files
    for path in created_files:
        if os.path.exists(path):
            os.remove(path)

@pytest.fixture
def upload_file(base_url, cleanup_list, generate_file):
    """Helper fixture to upload a file and return the ID and response"""
    def _upload(filename="test.txt", size_mb=1):
        path = generate_file(filename, size_mb)
        with open(path, "rb") as f:
            response = requests.post(f"{base_url}/files", files={"file": (filename, f)})
        
        if response.status_code == 201:
            print(f"File upload Response body: {response.text}")
            data = response.json()
            file_id = data.get("file_id")
            cleanup_list.append(file_id)
            return file_id, response
        return None, response
    return _upload
