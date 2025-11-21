# ColliderML HuggingFace Integration - Test Results

## Summary

All tests pass successfully! ColliderML datasets are now fully accessible via HuggingFace Hub.

## Available Datasets

**Repository**: `OpenDataDetector/ColliderML_ttbar_pu0`

**Configurations** (4 total):
- `particles` - Truth-level particle information (15 fields)
- `tracker_hits` - Detector measurements in tracking system (14 fields)
- `calo_hits` - Calorimeter hit measurements (9 fields)
- `tracks` - Reconstructed particle tracks (9 fields)

## Test Results

### Config Discovery
✅ All 4 expected configs discovered via HuggingFace API

### Streaming Access
✅ All configs accessible in streaming mode
- `particles`: 52.89s for first event
- `tracker_hits`: 57.54s
- `calo_hits`: 85.37s
- `tracks`: 46.32s

### Data Fields

#### Particles (15 fields)
- `event_id`, `particle_id`, `pdg_id`, `mass`, `energy`, `charge`
- `vx`, `vy`, `vz`, `time`
- `px`, `py`, `pz`
- `vertex_primary`, `parent_id`

#### Tracker Hits (14 fields)
- `event_id`, `x`, `y`, `z`
- `true_x`, `true_y`, `true_z`, `time`
- `particle_id`, `cell_id`, `detector`
- `volume_id`, `layer_id`, `surface_id`

#### Calo Hits (9 fields)
- `event_id`, `detector`, `total_energy`
- `x`, `y`, `z`
- `contrib_particle_ids`, `contrib_energies`, `contrib_times`

#### Tracks (9 fields)
- `event_id`, `d0`, `z0`, `phi`, `theta`, `qop`
- `majority_particle_id`, `hit_ids`, `track_id`

## Download Behavior

**Important Finding**: HuggingFace's "streaming" mode still downloads complete parquet files (~1000 events per file) before providing access to individual events.

### Timing Analysis
- **First event**: ~45-85 seconds (downloads full parquet file)
- **Subsequent events from same file**: <1 second (cached)
- **File sizes vary by config**: calo_hits largest (~85s), tracks smallest (~46s)

### Implications
- "Streaming" is efficient for processing many events from the same file
- Not ideal for accessing single random events
- Caching happens automatically after first file download
- For CI/CD, expect ~1-2 minutes per test accessing different configs

## Running Tests

### With Make (recommended)
```bash
make test-fast     # Fast tests only (streaming mode)
make test-slow     # Slow tests (actual downloads)
make test-all      # All tests
make test-cov      # With coverage report
```

### With pytest directly
```bash
# If you have ROS packages installed:
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -v

# Otherwise:
pytest -v
```

### Test Categories
- **Fast tests** (`not slow`): Use streaming mode, complete in ~5-10 minutes
- **Slow tests** (`slow`): Download full splits, may take 30+ minutes

## CI/CD Integration

GitHub Actions workflow updated to:
1. Install ColliderML with HuggingFace `datasets` library
2. Run tests with `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` (avoids ROS conflicts)
3. Generate coverage reports
4. Tests run on Python 3.10 and 3.11

## Example Usage

```python
from datasets import load_dataset

# Load particles in streaming mode
dataset = load_dataset(
    "OpenDataDetector/ColliderML_ttbar_pu0",
    "particles",
    split="train",
    streaming=True
)

# Get first event (~50s first time, cached after)
first_event = next(iter(dataset))

# Iterate through multiple events efficiently
for i, event in enumerate(dataset):
    if i >= 10:
        break
    # Process event...
```

## Next Steps

1. ✅ Tests implemented and passing
2. ✅ Documentation created (quickstart, installation)
3. ✅ All 4 configs verified accessible
4. 🔲 Add helper functions for common operations
5. 🔲 Create Dataset wrapper class
6. 🔲 Add CLI for data exploration
7. 🔲 Expand documentation with examples
8. 🔲 Add visualization utilities

## Notes for Developers

- Use `make test-fast` during development (avoids long downloads)
- Full parquet files are cached in `~/.cache/huggingface/datasets/`
- Clear cache if you need to re-download: `rm -rf ~/.cache/huggingface/`
- Tests discover configs dynamically via HuggingFace API
- Add new processes by updating parametrize decorators in tests
