import pytest
import requests
from pathlib import Path

class TestBoundariesAndFaults:

    def test_tc12_zero_byte_file(self, base_url, generate_file):
        """TC12: Upload 0 byte file."""
        path = generate_file(filename="zero.txt", size_in_mb=0, content_prefix=b"")
        file_path_chk = Path(path)
        if file_path_chk.exists():
            fs = file_path_chk.stat().st_size
            print(f"File size: {fs} bytes")
        assert fs == 0, "File size is not Zero bytes."
        
        with open(path, "rb") as f:
            res = requests.post(f"{base_url}/files", files={"file": ("zero.txt", f)})
        
        assert res.status_code == 400, "Zero byte file upload is success. which shouldn't"

    def test_tc13_small_file(self, base_url, upload_file):
        """TC13: Test 0.99MB should not be uploaded."""
        # Upload 0.9MB file
        _, response = upload_file("small.txt", size_mb=0.9)
        assert response.status_code == 400, "File size(0.9MB) less than 1MB upload success"

    def test_tc14_exact_minimum_file_size(self, base_url, upload_file):
        """TC14: Test 1MB should be uploaded."""
        # Upload 1MB file
        _, response = upload_file("1mb.txt", size_mb=1)
        assert response.status_code == 201, "1MB File upload failed."

    def test_tc15_exact_maximum_file_size(self, base_url, upload_file):
        """TC15: Test 10GB should be uploaded."""
        # Upload 10GB file
        # _, response = upload_file("10gb.txt", size_mb=10 * 1024)
        # assert response.status_code == 201, "10GB File upload failed."
        print("To avoid creating the file of 10GB and crashing something in my local, I commented this test")

    def test_tc16_file_too_large(self, base_url, upload_file):
        """TC13: Test 10.1GB file should not be uploaded."""
        # Upload 10.1GB file
        # _, response = upload_file("small.txt", size_mb=10 * 1024 + 100)
        # assert response.status_code == 400, "File size(10.1GB) greater than 10GB upload success"
        print("To avoid creating the file of 10GB and crashing something in my local, I commented this test")

    def test_tc19_negative_days(self, base_url, upload_file):
        """TC19: Negative values for days."""
        file_id, _ = upload_file("neg_date.txt")
        
        payload = {"days_ago": -5}
        res = requests.post(f"{base_url}/admin/files/{file_id}/update-last-accessed", json=payload)
        meta = requests.get(f"{base_url}/files/{file_id}/metadata").json()
        print(f"Metadata of neg_date file: {meta}")
        # API should reject future dates or handle gracefully
        assert res.status_code in [400, 422], "Negative value to days is accepted"

    def test_tc20_invalid_file_id(self, base_url):
        """TC20: Request metadata for invalid ID."""
        res = requests.get(f"{base_url}/files/invalid-id-999/metadata")
        assert res.status_code == 404, "Success on invalid file id"

    def test_tc21_method_not_allowed(self, base_url):
        """TC21: Try PUT method."""
        res = requests.put(f"{base_url}/files")
        assert res.status_code == 405, "PUT method is allowed for file upload endpoint"

    def test_tc23_path_traversal(self, base_url, generate_file):
        """TC23: Path traversal in filename."""
        # Attempt to upload with a malicious filename
        malicious_name = "../../etc/passwd"
        path = generate_file("normal_name_in_local.txt", 2)
        with open(path, "rb") as f:
            response = requests.post(f"{base_url}/files", files={"file": (malicious_name, f)})
        if response.status_code == 201:
            print("File with malicious name is upload. Lets check for the file name sanitation")
            data = response.json()
            print(data)
            assert data['filename'] != malicious_name, "File is uploaded with the malicious name. Which shouldn't"
