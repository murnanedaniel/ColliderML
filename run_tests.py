#!/usr/bin/env python
"""Simple test runner that bypasses pytest to avoid ROS plugin conflicts."""

import sys
import time
from datasets import load_dataset, get_dataset_config_names
import numpy as np


def test_config_discovery():
    """Test discovering available configs."""
    print("\n" + "="*60)
    print("TEST: Config Discovery")
    print("="*60)

    configs = get_dataset_config_names("OpenDataDetector/ColliderML_ttbar_pu0")
    print(f"\n✓ Discovered {len(configs)} configs:")
    for config in configs:
        print(f"  - {config}")

    expected = {"particles", "tracker_hits", "calo_hits", "tracks"}
    found = set(configs)

    assert expected.issubset(found), f"Missing: {expected - found}"
    print(f"\n✓ All expected configs found")
    return True


def test_streaming_single_event():
    """Test loading single event in streaming mode."""
    print("\n" + "="*60)
    print("TEST: Streaming Single Event")
    print("="*60)

    start = time.time()
    dataset = load_dataset(
        "OpenDataDetector/ColliderML_ttbar_pu0",
        "particles",
        split="train",
        streaming=True
    )

    first_event = next(iter(dataset))
    elapsed = time.time() - start

    print(f"\n✓ Loaded 1 event in {elapsed:.2f}s")
    print(f"  Event keys: {list(first_event.keys())}")
    print(f"  Number of fields: {len(first_event.keys())}")

    assert first_event is not None
    assert len(first_event.keys()) > 0
    return True


def test_all_configs():
    """Test all available configs."""
    print("\n" + "="*60)
    print("TEST: All Configs")
    print("="*60)

    configs = get_dataset_config_names("OpenDataDetector/ColliderML_ttbar_pu0")

    for config in configs:
        print(f"\nTesting config: {config}")
        start = time.time()

        dataset = load_dataset(
            "OpenDataDetector/ColliderML_ttbar_pu0",
            config,
            split="train",
            streaming=True
        )

        first_event = next(iter(dataset))
        elapsed = time.time() - start

        print(f"  ✓ Loaded in {elapsed:.2f}s")
        print(f"  Fields ({len(first_event.keys())}): {list(first_event.keys())}")

        # Inspect data types
        for key, value in first_event.items():
            if hasattr(value, 'shape'):
                print(f"    - {key}: shape={value.shape}, dtype={value.dtype}")
            elif hasattr(value, '__len__'):
                print(f"    - {key}: length={len(value)}")

        assert first_event is not None
        assert len(first_event.keys()) > 0

    print(f"\n✓ All {len(configs)} configs verified")
    return True


def test_particle_data_inspection():
    """Test detailed particle data inspection."""
    print("\n" + "="*60)
    print("TEST: Particle Data Inspection")
    print("="*60)

    start = time.time()
    dataset = load_dataset(
        "OpenDataDetector/ColliderML_ttbar_pu0",
        "particles",
        split="train",
        streaming=True
    )

    event = next(iter(dataset))
    elapsed = time.time() - start

    print(f"\n✓ Loaded particle event in {elapsed:.2f}s")
    print("\nNumerical field statistics:")

    for key, value in event.items():
        if hasattr(value, 'dtype') and np.issubdtype(value.dtype, np.number):
            if value.size > 0:
                print(f"\n  {key}:")
                print(f"    Shape: {value.shape}, Dtype: {value.dtype}")
                print(f"    Range: [{np.min(value):.3f}, {np.max(value):.3f}]")
                print(f"    Mean: {np.mean(value):.3f}, Std: {np.std(value):.3f}")

    return True


def test_multiple_events():
    """Test iterating multiple events."""
    print("\n" + "="*60)
    print("TEST: Multiple Events Streaming")
    print("="*60)

    num_events = 3
    start = time.time()

    dataset = load_dataset(
        "OpenDataDetector/ColliderML_ttbar_pu0",
        "particles",
        split="train",
        streaming=True
    )

    events_processed = 0
    for i, event in enumerate(dataset):
        if i >= num_events:
            break
        assert event is not None
        events_processed += 1

    elapsed = time.time() - start

    print(f"\n✓ Streamed {events_processed} events in {elapsed:.2f}s")
    print(f"  Average: {elapsed/events_processed:.2f}s per event")

    assert events_processed == num_events
    return True


def main():
    """Run all tests."""
    print("\n" + "="*70)
    print(" ColliderML HuggingFace Loader Tests")
    print("="*70)

    tests = [
        ("Config Discovery", test_config_discovery),
        ("Streaming Single Event", test_streaming_single_event),
        ("All Configs", test_all_configs),
        ("Particle Data Inspection", test_particle_data_inspection),
        ("Multiple Events", test_multiple_events),
    ]

    passed = 0
    failed = 0
    start_time = time.time()

    for name, test_func in tests:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"\n✗ FAILED: {name}")
            print(f"  Error: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    total_time = time.time() - start_time

    print("\n" + "="*70)
    print(f" Test Summary")
    print("="*70)
    print(f"  Passed: {passed}/{len(tests)}")
    print(f"  Failed: {failed}/{len(tests)}")
    print(f"  Total time: {total_time:.2f}s")
    print("="*70)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
