#!/usr/bin/env python3
"""ColliderML command line interface."""

import argparse
import sys
from pathlib import Path
import colliderml
from colliderml import core
from colliderml.core.io import DataDownloader
from colliderml.core.data.config import PileupLevel, EVENTS_PER_FILE, DATASET_SIZES

def download(args):
    """Handle the download command."""
    # Convert comma-separated lists to lists
    channels = args.channels.split(',') if args.channels else []
    objects = args.objects.split(',') if args.objects else []
    pileup_levels = args.pileup.split(',') if args.pileup else []
    
    # Initialize downloader
    downloader = DataDownloader()
    
    # Print download plan
    print("\nDownload Configuration:")
    print(f"Channels: {', '.join(channels)}")
    print(f"Pileup: {', '.join(pileup_levels)}")
    print(f"Objects: {', '.join(objects)}")
    print(f"Requested events: {args.events}")
    print(f"Output directory: {args.output_dir}")
    
    # Download for each combination
    results = {}
    for pileup in pileup_levels:
        for process in channels:
            for object_type in objects:
                try:
                    # Get the total available events for this process
                    if process not in DATASET_SIZES:
                        print(f"\nWarning: No dataset size information for {process}, skipping")
                        continue
                        
                    total_events = DATASET_SIZES[process]
                    events_to_download = min(args.events, total_events)
                    num_files = (events_to_download + EVENTS_PER_FILE - 1) // EVENTS_PER_FILE
                    
                    print(f"\nDownloading {process} {object_type} with pileup {pileup}:")
                    print(f"Available events: {total_events}")
                    print(f"Will download: {events_to_download} events ({num_files} files)")
                    
                    # Download each chunk
                    for chunk in range(num_files):
                        start_event = chunk * EVENTS_PER_FILE
                        end_event = min(
                            (chunk + 1) * EVENTS_PER_FILE - 1,
                            events_to_download - 1
                        )
                        
                        chunk_results = downloader.download_dataset(
                            pileup=pileup,
                            processes=[process],
                            object_types=[object_type],
                            local_dir=args.output_dir,
                            max_workers=args.workers,
                            resume=not args.no_resume,
                            start_event=start_event,
                            end_event=end_event
                        )
                        results.update(chunk_results)
                
                except Exception as e:
                    print(f"\nWarning: {str(e)}")
                    continue
    
    # Print summary
    successful = [r for r in results.values() if r.success]
    failed = [r for r in results.values() if not r.success]
    
    print("\nDownload Summary:")
    print(f"Total files: {len(results)}")
    print(f"Successful: {len(successful)}")
    print(f"Failed: {len(failed)}")
    
    if failed:
        print("\nFailed downloads:")
        for path, result in results.items():
            if not result.success:
                print(f"✗ {path}: {result.error}")
        sys.exit(1)

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="ColliderML command line interface")
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Download command
    download_parser = subparsers.add_parser('download', help='Download datasets')
    download_parser.add_argument('--channels', type=str,
                               help='Comma-separated list of physics channels (e.g. ttbar,qcd)')
    download_parser.add_argument('--pileup', type=str,
                               help='Comma-separated list of pileup levels (single_particle,pileup-10,pileup-200)')
    download_parser.add_argument('--objects', type=str,
                               help='Comma-separated list of objects (e.g. tracks,calo_clusters)')
    download_parser.add_argument('--events', type=int, default=1000,
                               help='Number of events to download')
    download_parser.add_argument('--output-dir', type=str, default='data',
                               help='Directory to save downloaded files')
    download_parser.add_argument('--workers', type=int, default=4,
                               help='Number of parallel downloads')
    download_parser.add_argument('--no-resume', action='store_true',
                               help='Disable resuming partial downloads')
    
    args = parser.parse_args()
    
    if args.command == 'download':
        download(args)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == '__main__':
    main()