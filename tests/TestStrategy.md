## Test Strategy: Cloud Storage Tiering System

Here you can find the testplan for the Cloud Storage Tiering system. 

Our Cloud storage tiering system has the following functionalities:

File related operation:

- File upload
- File download
- Get the file metadata
- Delete the file

Admin related operations:

- Trigger manual tiering
- Get the usage stats.

Tiering types

- Hot (less than 30 days)
- Warm (30 to 90 days)
- Cold (90+ days)

## Test Scope


| Component | Description |
| :--- | :--- |
| **File Operations** | Upload, Download, Metadata retrieval, Deletion. |
| **Tiering and Restoration Logic** | Validate tiering movement: Hot to Warm (30+ days no access), Warm to Cold (90+ days no access) |
| **Admin Operations** | Manual triggering of tiering rules with special logic for filesname with \_PRIORITY\_ (Always Hot) and LEGAL_ (180 days retention) and stats reporting. |
| **Corner Cases** | File sizes less and more than supported |
| **Concurrency Testing** | Concurrcent uploads and burst tiering |
| **Fault Injection & Negative Testing** | Negative and invalid values or files |

## Test Environment

Application: FastAPI Server (Localhost).

Test Framework: pytest (Python).

HTTP Client: requests library.


## Functional Testing Scenarios (Positive Flow)

### Basic CRUD

TC01 - File upload: Verify upload success of a valid file (e.g., 5MB). Check 201 status code and response body.

TC02 - Get Metadata: Verify metadata returned the correct file id, size, tier and others.

TC03 - Download File: Verify file content matches the original uploaded content (Hash validation).

TC04 - Delete File: Verify file deletion and subsequent 404 Not Found on get/metadata.

TC05 - Delete File idempotent: Verify file deletetion and try deleting the same file id which should return 404.

### Tiering Logic (State Transitions) using Last accessed API test

TC06 - Hot to Warm Transition: Simulate 31 days passing using last update api and check for the tier (Warm) state in the metadata api

TC07 - Warm to Cold Transition: Simulate 91 days passing using last update api and check for the tier (Cold) state in the metadata api

TC08 - Access Restoration (Warm/Cold to Hot): Access the file (download) which is in cold state and get the metadata of the file to check the tier. should be in Hot.

### Admin operation

TC09 - Trigger admin tiering with the File name that contains "\_PRIORITY\_" which changes to HOT Tier from other tier or stay in the same HOT tier if it is already

TC10 - Trigger admin tiering with the File name that starts with "LEGAL_". Test the Legal documents have extended retention in WARM tier (180 days instead of 90) as per the code in the server.

TC11 - Get the file stats

## Corner Case Scenarios

### File Sizes

The file will be uploaded successfully only if the file size is between 1MB to 10GB

TC12 - Zero Byte File: Should give the proper error message

TC13 - Small File : Upload 0.99MB file.

TC14 - Minimum size which will be acceptable: Upload 1.0MB file.

TC15 - Maximum size which will be acceptable: Upload 10GB file which should succeed.

TC16 - Large size file : Upload 10.1GB file.


## Concurrency Testing

TC17 - Concurrent Uploads: Use async calls to upload 50 files simultaneously. Check for race conditions or server 500 errors.

TC18 - Burst Tiering: Upload 100 files. Simulate /admin/tiering/run.

TC19 - Bulk file upload and delete: Upload 100 files and delete 100 files and verify the status

## Fault Injection & Negative Testing

TC20 - Negative values for the days. (update last accessed method accepts int value try -ve value or float value)

TC21 - Invalid File ID: Request metadata for non-existent ID. Expect 404 error.

TC22 - Method Not Allowed: Try PUT /files. Expect method not allowed or not exist

TC23 - Corrupt Data (Simulation): Simulate partial upload.

TC24 - Path Traversal: Try uploading a file with the name '../../../etc/passwd'. Expect some sanity check error.