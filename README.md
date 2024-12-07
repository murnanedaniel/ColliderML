# ColliderML

A modern machine learning library for high-energy physics data analysis.

## Features

- Efficient parallel data downloading with resume capability
- Support for common HEP data formats
- Machine learning utilities for particle physics
- Visualization tools for physics data

## Installation

### For Users
```bash
# Create and activate environment
conda create -n collider-env python=3.11  # 3.10 or 3.11 recommended
conda activate collider-env

# Install package
pip install colliderml
```

### For Developers
```bash
# Create and activate environment
conda create -n collider-dev python=3.11  # 3.10 or 3.11 recommended
conda activate collider-dev

# Clone repository
git clone https://github.com/yourusername/colliderml.git
cd colliderml

# Install in development mode with extra dependencies
pip install -e ".[dev]"
```

## Quick Start

```python
from colliderml.core.io import DataDownloader

# Initialize downloader with custom settings
downloader = DataDownloader(
    max_retries=3,        # Maximum retry attempts for failed downloads
    retry_backoff=0.3,    # Exponential backoff factor between retries
    chunk_size=8192       # Download chunk size in bytes
)

# List available files
files = downloader.list_files("pda_batch_parallel_testing/proc_1")

# Download files in parallel with progress tracking and resume capability
results = downloader.download_files(
    remote_paths=[
        "pda_batch_parallel_testing/proc_1/edm4hep.root",
        "pda_batch_parallel_testing/proc_1/simhits.root"
    ],
    local_dir="data",
    max_workers=4,  # Number of parallel downloads
    resume=True     # Automatically resume interrupted downloads
)

# Check download results
for path, result in results.items():
    if result.success:
        print(f"✓ Successfully downloaded {path}")
        print(f"  SHA-256: {result.checksum}")
    else:
        print(f"✗ Failed to download {path}: {result.error}")
```

### Features

- **Parallel Downloads**: Download multiple files concurrently for better performance
- **Resume Capability**: Automatically resume interrupted downloads
- **Checksum Verification**: SHA-256 checksums for file integrity
- **Progress Tracking**: Real-time progress bars for each download
- **Error Handling**: Automatic retries with exponential backoff
- **Detailed Results**: Comprehensive download status and error reporting

## Development

1. Activate your environment:
   ```bash
   conda activate collider-dev
   ```

2. Run tests:
   ```bash
   pytest --cov=colliderml
   ```

3. Build documentation:
   ```bash
   mkdocs build
   mkdocs serve  # View at http://127.0.0.1:8000
   ```

## License

[MIT License](LICENSE) 