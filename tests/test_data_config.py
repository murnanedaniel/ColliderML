"""Tests for data configuration."""

import pytest
from colliderml.core.data.config import (
    DataType,
    PileupLevel,
    OBJECT_CONFIGS,
    VALID_PROCESSES,
    get_object_path
)

def test_pileup_levels():
    """Test pileup level values."""
    assert PileupLevel.SINGLE.value == "single-particle"
    assert PileupLevel.LOW.value == "pileup-10"
    assert PileupLevel.HIGH.value == "pileup-200"

def test_data_types():
    """Test data type values."""
    assert DataType.RECO.value == "reco"
    assert DataType.TRUTH.value == "truth"
    assert DataType.MEASUREMENTS.value == "measurements"

def test_object_configs():
    """Test object configurations."""
    # Test reconstruction objects
    assert "tracks" in OBJECT_CONFIGS
    assert OBJECT_CONFIGS["tracks"].data_type == DataType.RECO
    
    assert "particle_flow" in OBJECT_CONFIGS
    assert OBJECT_CONFIGS["particle_flow"].data_type == DataType.RECO
    
    # Test truth objects
    assert "particles" in OBJECT_CONFIGS
    assert OBJECT_CONFIGS["particles"].data_type == DataType.TRUTH
    
    # Test measurement objects
    assert "tracker_hits" in OBJECT_CONFIGS
    assert OBJECT_CONFIGS["tracker_hits"].data_type == DataType.MEASUREMENTS

def test_valid_processes():
    """Test valid physics processes."""
    expected = {"ttbar", "wjets", "zjets", "susy", "higgs", "qcd", "exotics"}
    assert VALID_PROCESSES == expected

def test_get_object_path():
    """Test path generation."""
    path = get_object_path(
        PileupLevel.LOW,
        "ttbar",
        "tracks",
        0,
        999
    )
    expected = "pileup-10/ttbar/v1/reco/tracks/pileup-10.ttbar.v1.reco.tracks.events0-999.h5"
    assert path == expected

def test_get_object_path_invalid_process():
    """Test path generation with invalid process."""
    with pytest.raises(ValueError, match="Invalid process"):
        get_object_path(
            PileupLevel.LOW,
            "invalid",
            "tracks",
            0,
            999
        )

def test_get_object_path_invalid_object():
    """Test path generation with invalid object."""
    with pytest.raises(ValueError, match="Invalid object type"):
        get_object_path(
            PileupLevel.LOW,
            "ttbar",
            "invalid",
            0,
            999
        ) 