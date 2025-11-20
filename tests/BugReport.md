# Bug Report

## Bug #1

**Title**: Negative value is accepted for the update-last-accessed API endpoint.
**Steps**: update-last-accessed API is used to update the last accessed time stamp. However there is no input validation is done for the days_ago filed. We can able to pass the -ve value for this failed and make the last accessed timestamp to appear as future which is not reasonable and correct design.

**Expected vs Actual**: Expected: Input validation (accepts only the positive values). Actual: No Input validation for -ve values can be passed.

**Logs**: 

    File upload Response body: {"file_id":"6fc425e8-e6e1-4577-a1d2-13f37aa07f90","filename":"neg_date.txt","size":1048576,"tier":"HOT","created_at":"2025-11-20T17:44:31.756090","last_accessed":"2025-11-20T17:44:31.756090","content_type":"application/octet-stream","etag":"ae4790b5-cfd1-4cc2-8929-199804b987ac"}

    Metadata of neg_date file after last update with -5 : {'file_id': '6fc425e8-e6e1-4577-a1d2-13f37aa07f90', 'filename': 'neg_date.txt', 'size': 1048576, 'tier': 'HOT', 'created_at': '2025-11-20T17:44:31.756090', 'last_accessed': '2025-11-25T17:44:31.758601', 'content_type': 'application/octet-stream', 'etag': 'ae4790b5-cfd1-4cc2-8929-199804b987ac'}

**Testcase #**: TC19


## Bug #2

**Title**: File with malicious name is uploaded
**Steps**: Upload the file with the name "../../etc/passwd" or "/etc/passwd". which is malicious might casue some issue in the server if we try to operate this file with the admin privilege.
**Expected vs Actual**: Expected: File name validation. Should not contain the unix like path structure. Actual: No file name validation, the server accepts whatever passed.
**Logs**: {'file_id': 'da21dc78-b53f-43d0-84e7-8486de48f5eb', 'filename': '../../etc/passwd', 'size': 2097152, 'tier': 'HOT', 'created_at': '2025-11-20T17:44:32.718086', 'last_accessed': '2025-11-20T17:44:32.718086', 'content_type': 'application/octet-stream', 'etag': 'dfdf2275-06ed-4de5-adac-ff4c1ca96819'}
**Testcase #**: TC23

## Bug #3

**Title**: Tier failed to change from HOT to COLD. Last accessed - 100 Days ago
**Steps**: Upload a file with the valid file size and name. Get the metadata and see the tier it should be HOT. Change the last accessed timestamp with the API to 100 days. Now trigger the tiering. Now get the file metadata and validate the tier it should be COLD since the last accessed day is 100 days. But it is in WARM. Filename is 'restore.txt' which is not in the special rule like PRIORITY, LEGAL.
**Expected vs Actual**: Expected: If the file last accessed is greater than 90 days then it should be of COLD tier for the normal files. Actual: It is in WARM tier.
**Logs**: File upload  Response body: {"file_id":"d828ceb5-6d2d-4002-be71-2c40148df49f","filename":"restore.txt","size":2097152,"tier":"HOT","created_at":"2025-11-20T18:03:08.189074","last_accessed":"2025-11-20T18:03:08.189074","content_type":"application/octet-stream","etag":"b530a7e8-cc63-4444-851c-f072a91116e4"}
    Tiering response body: {'status': 'success', 'files_moved': 1}
    Response after changing the last accessed to 100 days ago
    {'file_id': 'd828ceb5-6d2d-4002-be71-2c40148df49f', 'filename': 'restore.txt', 'size': 2097152, 'tier': 'WARM', 'created_at': '2025-11-20T18:03:08.189074', 'last_accessed': '2025-08-12T18:03:08.191767', 'content_type': 'application/octet-stream', 'etag': 'b530a7e8-cc63-4444-851c-f072a91116e4'}
**Testcase #**: TC08