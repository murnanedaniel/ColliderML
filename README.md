# ColliderML

A modern machine learning library for high-energy physics data analysis.

## Features

- XRootD integration for efficient data access
- Support for common HEP data formats
- Machine learning utilities for particle physics
- Visualization tools for physics data

## Installation

```bash
pip install colliderml
```

## Quick Start

```python
from colliderml.core.io import XRootDClient

# Initialize client
client = XRootDClient('root://eospublic.cern.ch/')

# List directory contents
files = client.list_directory('/eos/opendata/cms/Run2012B/DoubleMuParked/AOD')

# Download a file
client.download_file(
    remote_path='/eos/opendata/cms/Run2012B/DoubleMuParked/AOD/file.root',
    local_path='data/file.root'
)
```

## Development

1. Clone the repository
2. Install dependencies:
   ```bash
   poetry install
   ```
3. Run tests:
   ```bash
   poetry run pytest
   ```

## License

[MIT License](LICENSE) 