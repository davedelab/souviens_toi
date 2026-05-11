
import time
import pathlib
import hashlib
import mimetypes
import tempfile
import os

def benchmark_sync_processing(file_paths):
    start_time = time.time()
    results = []
    for p in file_paths:
        data = pathlib.Path(p).read_bytes()
        sha = hashlib.sha256(data).hexdigest()
        mime = mimetypes.guess_type(p)[0] or 'application/octet-stream'
        title = pathlib.Path(p).name
        results.append((title, sha, mime))
    end_time = time.time()
    return end_time - start_time, results

def main():
    # Create some dummy large files
    num_files = 5
    file_size_mb = 10
    temp_dir = tempfile.mkdtemp()
    file_paths = []
    for i in range(num_files):
        p = os.path.join(temp_dir, f"test_file_{i}.dat")
        with open(p, "wb") as f:
            f.write(os.urandom(file_size_mb * 1024 * 1024))
        file_paths.append(p)

    print(f"Benchmarking processing of {num_files} files of {file_size_mb}MB each...")
    duration, _ = benchmark_sync_processing(file_paths)
    print(f"Total time taken: {duration:.4f} seconds")
    print(f"Average time per file: {duration/num_files:.4f} seconds")

    # Cleanup
    for p in file_paths:
        os.remove(p)
    os.rmdir(temp_dir)

if __name__ == "__main__":
    main()
