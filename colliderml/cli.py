#!/usr/bin/env python3
"""ColliderML command line interface."""

import argparse
import sys
from pathlib import Path
from colliderml.core.io import DataDownloader
from colliderml.core.data.manifest import ManifestClient


def get(args):
    """Handle the get command (manifest-driven)."""
    downloader = DataDownloader()
    manifest = ManifestClient()

    # Determine campaign
    campaign = args.campaign if args.campaign and args.campaign != "default" else None

    # Parse lists
    datasets = args.datasets.split(',') if args.datasets else None
    objects = args.objects.split(',') if args.objects else None

    # Select files
    try:
        files = manifest.select_files(
            campaign=campaign,
            datasets=datasets,
            objects=objects,
            max_events=args.events,
            version=args.version,
        )
    except Exception as e:
        print(f"\nError reading manifest: {e}")
        sys.exit(1)

    if not files:
        print("No files matched the selection from the manifest.")
        sys.exit(0)

    print("\nGet Configuration:")
    print(f"Campaign: {args.campaign or 'default'}")
    print(f"Version: {args.version or 'dataset defaults'}")
    print(f"Datasets: {', '.join(datasets) if datasets else 'ALL'}")
    print(f"Objects: {', '.join(objects) if objects else 'ALL'}")
    print(f"Requested events: {args.events if args.events else 'ALL'}")
    print(f"Output directory: {args.output_dir}")

    # Download
    remote_paths = [f.path for f in files]
    results = downloader.download_files(
        remote_paths=remote_paths,
        local_dir=args.output_dir,
        max_workers=args.workers,
        resume=not args.no_resume,
    )

    successful = [r for r in results.values() if r.success]
    failed = [r for r in results.values() if not r.success]

    print("\nGet Summary:")
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

    # Get command (manifest-driven)
    get_parser = subparsers.add_parser('get', help='Get files using manifest selection')
    get_parser.add_argument('-c', '--campaign', type=str, default='default',
                            help='Campaign name (or "default" to use manifest default)')
    get_parser.add_argument('-d', '--datasets', type=str,
                            help='Comma-separated list of datasets (e.g. ttbar,qcd)')
    get_parser.add_argument('-o', '--objects', type=str,
                            help='Comma-separated list of objects (e.g. tracks,hits)')
    get_parser.add_argument('-e', '--events', type=int, default=None,
                            help='Max number of events to download (across selection)')
    get_parser.add_argument('-O', '--output-dir', '--output_dir', dest='output_dir', type=str, default='data',
                            help='Directory to save downloaded files')
    get_parser.add_argument('-w', '--workers', type=int, default=4,
                            help='Number of parallel downloads')
    get_parser.add_argument('--no-resume', '--no_resume', dest='no_resume', action='store_true',
                            help='Disable resuming partial downloads')
    get_parser.add_argument('-v', '--version', type=str, default=None,
                            help='Dataset version to use (overrides dataset default_version)')

    args = parser.parse_args()

    if args.command == 'get':
        get(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()


