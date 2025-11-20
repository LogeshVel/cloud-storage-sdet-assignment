import pytest
import requests
import concurrent.futures

class TestConcurrency:

    def test_tc17_concurrent_uploads(self, base_url, generate_file, cleanup_list):
        """TC17: Concurrent uploads of 100 files."""
        def upload_one(i):
            filename = f"conc_test_{i}.txt"
            path = generate_file(filename, size_in_mb=1.1)
            with open(path, "rb") as f:
                return requests.post(f"{base_url}/files", files={"file": (filename, f)})
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(upload_one, i) for i in range(100)]
            
            results = []
            for future in concurrent.futures.as_completed(futures):
                res = future.result()
                results.append(res)
                if res.status_code == 201:
                    cleanup_list.append(res.json().get("id"))

        # Verify all succeeded
        failures = [r for r in results if r.status_code != 201]
        assert len(failures) == 0, f"Some ({len(failures)}/100) concurrent uploads failed: {[r.status_code for r in failures]}"


    def test_tc18_burst_tiering(self, base_url, upload_file, cleanup_list):
        """TC19: Burst tiering (Upload 50 files, age them, run tiering) using threads."""
        # Uploading
        file_ids = []
        def upload_task(i):
            fid, _ = upload_file(f"burst_{i}.txt", size_mb=1.1)
            return fid
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(upload_task, i) for i in range(50)]
            for future in concurrent.futures.as_completed(futures):
                file_id = future.result()
                if file_id:
                    file_ids.append(file_id)
        assert len(file_ids) == 50, "Failed to upload all 50 files for burst test"
        # Tiering
        def age_task(fid):
            return requests.post(
                f"{base_url}/admin/files/{fid}/update-last-accessed", 
                json={"days_ago": 35}
            )
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(age_task, fid) for fid in file_ids]
            concurrent.futures.wait(futures)
        res = requests.post(f"{base_url}/admin/tiering/run")
        assert res.status_code == 200, "Admin Tiering API failed"
        # Get Metadata
        def check_status_task(fid):
            meta = requests.get(f"{base_url}/files/{fid}/metadata").json()
            return meta.get('tier') == "WARM"
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(check_status_task, fid) for fid in file_ids]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        assert all(results), f"Some files failed to move to Warm tier. Success rate: {sum(results)}/50"

    def test_tc19_bulk_upload_delete(self, base_url, upload_file, cleanup_list):
        """Test Bulk Upload and Bulk Delete operations."""
        file_count = 150
        file_ids = []
        # Bulk Upload
        print(f"\nStarting Bulk Upload of {file_count} files...")
        def upload_task(i):
            fid, _ = upload_file(f"burst_{i}.txt", size_mb=1.1)
            return fid
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(upload_task, i) for i in range(file_count)]
            for future in concurrent.futures.as_completed(futures):
                fid = future.result()
                if fid:
                    file_ids.append(fid)
                    cleanup_list.append(fid)
        
        assert len(file_ids) == file_count, f"Bulk upload failed. Expected {file_count}, got {len(file_ids)}"

        # Bulk Delete
        print(f"Starting Bulk Delete of {len(file_ids)} files...")
        def delete_task(fid):
            return requests.delete(f"{base_url}/files/{fid}")
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(delete_task, fid) for fid in file_ids]
            results = [f.result().status_code for f in concurrent.futures.as_completed(futures)]
        assert all(code == 204 for code in results), "Some files failed to delete during bulk operation"
