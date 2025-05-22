#!/usr/bin/env python3
"""Script to download the ColliderML dataset."""

import argparse
from pathlib import Path
import json
from typing import List, Dict, Any
from colliderml.core.io import DataDownloader
from colliderml.core.data.config import (
    PileupLevel,
    OBJECT_CONFIGS,
    VALID_PROCESSES
)

def format_size(size_bytes: int) -> str:
    """Format size in bytes to human readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.2f} TB"

def main():
    parser = argparse.ArgumentParser(description="Download the ColliderML dataset")
    parser.add_argument("--output-dir", type=str, default="data",
                       help="Directory to save downloaded files")
    parser.add_argument("--workers", type=int, default=4,
                       help="Number of parallel downloads")
    parser.add_argument("--resume", action="store_true",
                       help="Resume interrupted downloads")
    parser.add_argument("--pileup", type=str, choices=['single-particle', 'pileup-10', 'pileup-200'],
                       default='pileup-10', help="Pileup level to download")
    parser.add_argument("--processes", type=str, nargs="+", choices=list(VALID_PROCESSES),
                       default=['ttbar'], help="Physics processes to download")
    parser.add_argument("--objects", type=str, nargs="+", choices=list(OBJECT_CONFIGS.keys()),
                       default=['tracks'], help="Object types to download")
    parser.add_argument("--start-event", type=int, default=0,
                       help="First event number to download")
    parser.add_argument("--end-event", type=int, default=999,
                       help="Last event number to download")
    args = parser.parse_args()
    
    # Initialize downloader
    downloader = DataDownloader()
    output_dir = Path(args.output_dir)
    
    # Print download plan
    print("\nDownload Configuration:")
    print(f"Pileup: {args.pileup}")
    print(f"Processes: {', '.join(args.processes)}")
    print(f"Objects: {', '.join(args.objects)}")
    print(f"Event range: {args.start_event}-{args.end_event}")
    print(f"Output directory: {output_dir}")
    print(f"Workers: {args.workers}")
    if args.resume:
        print("Resume mode enabled - will attempt to continue partial downloads")
    
    # Start downloads
    results = downloader.download_dataset(
        pileup=args.pileup,
        processes=args.processes,
        object_types=args.objects,
        local_dir=output_dir,
        max_workers=args.workers,
        resume=args.resume
    )
    
    # Calculate statistics
    successful = [r for r in results.values() if r.success]
    failed = [r for r in results.values() if not r.success]
    total_size = sum(r.size or 0 for r in successful)
    
    # Print summary
    print("\nDownload Summary:")
    print(f"Total files: {len(results)}")
    print(f"Successful: {len(successful)}")
    print(f"Failed: {len(failed)}")
    print(f"Total size: {format_size(total_size)}")
    
    if failed:
        print("\nFailed downloads:")
        for path, result in results.items():
            if not result.success:
                print(f"✗ {path}: {result.error}")
    
    # Save detailed results
    stats = {
        "total_files": len(results),
        "successful": len(successful),
        "failed": len(failed),
        "total_size_bytes": total_size,
        "configuration": {
            "pileup": args.pileup,
            "processes": args.processes,
            "objects": args.objects,
            "event_range": f"{args.start_event}-{args.end_event}",
            "workers": args.workers,
            "resume": args.resume
        },
        "failed_files": [
            {
                "path": str(path),
                "error": result.error,
                "partial_size": result.size
            }
            for path, result in results.items()
            if not result.success
        ]
    }
    
    stats_file = output_dir / "download_stats.json"
    print(f"\nSaving detailed statistics to {stats_file}")
    with open(stats_file, "w") as f:
        json.dump(stats, f, indent=2)

if __name__ == "__main__":
    main()