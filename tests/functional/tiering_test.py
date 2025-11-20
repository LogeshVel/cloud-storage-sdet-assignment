import pytest
import requests
import time

class TestTieringLogic:
    
    def set_time_travel(self, base_url, file_id, days):
        """Helper to call the mock time API."""
        payload = {"days_ago": days}
        res = requests.post(f"{base_url}/admin/files/{file_id}/update-last-accessed", json=payload)
        assert res.status_code == 200, f"Time travel failed: {res.text}"

    def trigger_tiering(self, base_url):
        """Helper to trigger the manual tiering job."""
        res = requests.post(f"{base_url}/admin/tiering/run")
        assert res.status_code == 200, f"Tiering run failed: {res.text}"
        print(f"Tiering response body: {res.json()}")

    def test_tc06_hot_to_warm(self, base_url, upload_file):
        """TC06: Verify Hot to Warm transition (31 days)."""
        file_id, _ = upload_file("tier_hw.txt", size_mb=2) # >1MB
        
        # Simulate 31 days passed
        days = 31
        self.set_time_travel(base_url, file_id, days)
        
        # Trigger Tiering
        self.trigger_tiering(base_url)
        
        # Check Status
        meta = requests.get(f"{base_url}/files/{file_id}/metadata").json()
        assert meta["tier"] == "WARM", f"Tier failed to change from HOT to WARM - last accessed {days} Days ago"

    def test_tc07_warm_to_cold(self, base_url, upload_file):
        """TC07: Verify Warm to Cold transition (91 days)."""
        file_id, _ = upload_file("tier_wc.txt", size_mb=2)
        
        # Simulate 61 days passed - for Hot to Warm
        days = 61
        self.set_time_travel(base_url, file_id, days)
        self.trigger_tiering(base_url)
        # Simulate 91 days passed - for Warm to COld
        days = 91
        self.set_time_travel(base_url, file_id, days)
        self.trigger_tiering(base_url)
        
        meta = requests.get(f"{base_url}/files/{file_id}/metadata").json()
        assert meta["tier"] == "COLD", f"Tier failed to change from WARM to COLD - last accessed {days} Days ago"

    def test_tc08_access_restoration(self, base_url, upload_file):
        """TC08: Verify downloading a Cold file restores it to Hot."""
        file_id, _ = upload_file("restore.txt", size_mb=2)
        
        # Move to Cold
        days = 100
        self.set_time_travel(base_url, file_id, days)
        self.trigger_tiering(base_url)
        
        # Verify it is Cold
        meta = requests.get(f"{base_url}/files/{file_id}/metadata").json()
        print(f"Response after changing the last accessed to {days} days ago")
        print(meta)
        assert meta["tier"] == "COLD", f"Tier failed to change from HOT to COLD. Last accessed - {days} Days ago"
        
        # Access file (Download)
        requests.get(f"{base_url}/files/{file_id}")
        
        # Check if restored to Hot
        meta_after = requests.get(f"{base_url}/files/{file_id}/metadata").json()
        
        assert meta_after["tier"] == "HOT", f"Tier failed to change to HOT after accessing the file"

    def test_tc09_priority_override(self, base_url, upload_file):
        """TC09: File name with _PRIORITY_ should stay HOT."""
        file_id, _ = upload_file("project_PRIORITY_doc.txt", size_mb=2)
        
        # Simulate 40 days as the last accessed (Should be Warm normally)
        days = 40
        self.set_time_travel(base_url, file_id, days)
        self.trigger_tiering(base_url)
        
        meta = requests.get(f"{base_url}/files/{file_id}/metadata").json()
        assert meta["tier"] == "HOT", f"Priority file(last accessed: {days} days ago) moved to Warm unexpectedly"

    def test_tc10_legal_retention(self, base_url, upload_file):
        """TC10: File starting with LEGAL_ has extended retention in Warm (180 days)."""
        file_id, _ = upload_file("LEGAL_contract.pdf", size_mb=2)
        
        # Simulate 100 days (Should be Cold normally, but Legal stays Warm until 180 days)
        days = 100
        self.set_time_travel(base_url, file_id, days)
        self.trigger_tiering(base_url)
        
        meta = requests.get(f"{base_url}/files/{file_id}/metadata").json()
        assert meta["tier"] == "WARM", f"Legal file moved to Cold too early. Last accessed {days} days ago"

    def test_tc11_admin_stats(self, base_url):
        """TC11: Verify admin stats endpoint."""
        res = requests.get(f"{base_url}/admin/stats")
        expected_code = 200
        assert res.status_code == expected_code, f"Get admin stats returned status code: {res.status_code}. Expected: {expected_code}"
        assert res.text, "Get admin stats returned empty response body"
