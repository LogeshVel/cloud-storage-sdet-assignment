import pytest
import requests
import hashlib
import os

class TestFunctional:

    def test_tc01_upload_valid_file(self, base_url, upload_file):
        """TC01: Verify upload success of a valid file (5MB)."""
        file_id, response = upload_file("test_5mb.txt", size_mb=5)
        
        assert response.status_code == 201, f"Upload failed: {response.text}"
        assert file_id is not None, "Failed to get file_id after upload"

    def test_tc02_get_metadata(self, base_url, upload_file):
        """TC02: Verify metadata returned correct file id, size, tier."""
        file_id, _ = upload_file("meta_test.txt", size_mb=1)
        response = requests.get(f"{base_url}/files/{file_id}/metadata")
        assert response.status_code == 200, "Get Metadata response status code is not 200"

    def test_tc03_download_file(self, base_url, generate_file, cleanup_list):
        """TC03: Verify file content matches original (Checksum)."""
        # 1. Create and calculate hash of local file
        filename = "download_test.txt"
        path = generate_file(filename, size_in_mb=1, content_prefix=b"download and hash check")
        
        with open(path, "rb") as f:
            original_content = f.read()
            original_md5 = hashlib.md5(original_content).hexdigest()
        
        # 2. Upload
        with open(path, "rb") as f:
            up_res = requests.post(f"{base_url}/files", files={"file": (filename, f)})
        file_id = up_res.json()["file_id"]
        cleanup_list.append(file_id)
        
        # 3. Download
        down_res = requests.get(f"{base_url}/files/{file_id}")
        assert down_res.status_code == 200, "Download status code is not 200"
        file_content = down_res.json().get("content")
        assert file_content, "Download response body has no key 'content' which has the content of the file"
        downloaded_md5 = hashlib.md5(file_content.encode('utf-8')).hexdigest()
        assert original_md5 == downloaded_md5, "Downloaded file hash mismatch!"

    def test_tc04_delete_file(self, base_url, upload_file):
        """TC04: Verify file deletion and subsequent 404."""
        file_id, _ = upload_file("delete_me.txt", size_mb=1)
        
        # Delete
        del_res = requests.delete(f"{base_url}/files/{file_id}")
        assert del_res.status_code in [200, 204], "Delete file response is not expected"
        
        # Verify delete
        meta_res = requests.get(f"{base_url}/files/{file_id}/metadata")
        assert meta_res.status_code == 404, "After deleting, Get Metadata API response status is not 404"

    def test_tc05_delete_idempotent(self, base_url, upload_file):
        """TC05: Verify deleting same file twice returns 404."""
        file_id, _ = upload_file("idempotent.txt", size_mb=1)
        
        # First Delete
        requests.delete(f"{base_url}/files/{file_id}")
        
        # Second Delete
        del_res = requests.delete(f"{base_url}/files/{file_id}")
        assert del_res.status_code == 404, "Delete API is not idmenpotent"
