#!/usr/bin/env python3
"""Script to download the entire ColliderML dataset with performance metrics."""

import time
import argparse
from pathlib import Path
from typing import List, Dict, Any
import json
from colliderml.core.io import DataDownloader

def get_all_files(downloader: DataDownloader) -> List[str]:
    """Get all files recursively from the server.
    
    Args:
        downloader: DataDownloader instance
        
    Returns:
        List of all file paths
    """
    all_files = []
    base_dir = "pda_batch_parallel_testing"
    
    # List all proc_X directories
    proc_dirs = [d for d in downloader.list_files(base_dir) if d.startswith("proc_")]
    print(f"Found {len(proc_dirs)} process directories")
    
    # Get files from each directory
    for proc_dir in proc_dirs:
        dir_path = f"{base_dir}/{proc_dir}"
        files = [f"{dir_path}/{f}" for f in downloader.list_files(dir_path)]
        print(f"{proc_dir}: {len(files)} files")
        all_files.extend(files)
    
    return all_files

def format_size(size_bytes: int) -> str:
    """Format size in bytes to human readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.2f} TB"

def main():
    parser = argparse.ArgumentParser(description="Download the entire ColliderML dataset")
    parser.add_argument("--output-dir", type=str, default="data",
                       help="Directory to save downloaded files")
    parser.add_argument("--workers", type=int, default=4,
                       help="Number of parallel downloads")
    parser.add_argument("--resume", action="store_true",
                       help="Resume interrupted downloads")
    parser.add_argument("--no-preserve-structure", action="store_true",
                       help="Don't preserve directory structure")
    args = parser.parse_args()
    
    # Initialize downloader
    downloader = DataDownloader()
    output_dir = Path(args.output_dir)
    
    # Get list of all files
    print("\nScanning for files...")
    start_time = time.time()
    all_files = get_all_files(downloader)
    scan_time = time.time() - start_time
    print(f"\nFound {len(all_files)} files in {scan_time:.2f} seconds")
    
    # Group files by type for reporting
    file_types = {}
    for f in all_files:
        ext = Path(f).suffix
        file_types[ext] = file_types.get(ext, 0) + 1
    print("\nFile types:")
    for ext, count in file_types.items():
        print(f"{ext}: {count} files")
    
    # Start downloads
    print(f"\nStarting downloads with {args.workers} workers...")
    if args.resume:
        print("Resume mode enabled - will attempt to continue partial downloads")
    
    start_time = time.time()
    results = downloader.download_files(
        remote_paths=all_files,
        local_dir=output_dir,
        max_workers=args.workers,
        resume=args.resume,
        preserve_structure=not args.no_preserve_structure
    )
    total_time = time.time() - start_time
    
    # Calculate statistics
    successful = [r for r in results.values() if r.success]
    failed = [r for r in results.values() if not r.success]
    total_size = sum(r.size or 0 for r in successful)  # Use size from DownloadResult
    avg_speed = total_size / total_time  # bytes per second
    
    # Print summary
    print("\nDownload Summary:")
    print(f"Total files: {len(all_files)}")
    print(f"Successful: {len(successful)}")
    print(f"Failed: {len(failed)}")
    print(f"Total size: {format_size(total_size)}")
    print(f"Total time: {total_time:.2f} seconds")
    print(f"Average speed: {format_size(int(avg_speed))}/s")
    
    if failed:
        print("\nFailed downloads:")
        for path, result in results.items():
            if not result.success:
                print(f"✗ {path}: {result.error}")
    
    # Save detailed results
    stats = {
        "total_files": len(all_files),
        "successful": len(successful),
        "failed": len(failed),
        "total_size_bytes": total_size,
        "total_time_seconds": total_time,
        "average_speed_bytes_per_second": avg_speed,
        "workers": args.workers,
        "file_types": file_types,
        "failed_files": [
            {
                "path": str(r.path),
                "error": r.error,
                "partial_size": r.size
            }
            for r in failed
        ]
    }
    
    stats_file = output_dir / "download_stats.json"
    print(f"\nSaving detailed statistics to {stats_file}")
    with open(stats_file, "w") as f:
        json.dump(stats, f, indent=2)

if __name__ == "__main__":
    main()