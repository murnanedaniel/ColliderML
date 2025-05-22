"""Tests for data downloader."""

import pytest
from pathlib import Path
import responses
import h5py
import numpy as np
from colliderml.core.io.downloader import DataDownloader, DownloadResult
from colliderml.core.data.config import PileupLevel

# Mock data for testing
MOCK_BASE_URL = "https://mock.cern.ch/data"
MOCK_FILE_CONTENT = b"Mock HDF5 content"

@pytest.fixture
def mock_hdf5_file(tmp_path):
    """Create a mock HDF5 file."""
    file_path = tmp_path / "test.h5"
    with h5py.File(file_path, 'w') as f:
        f.attrs['test_attr'] = 'test_value'
        f.create_dataset('test_data', data=np.array([1, 2, 3]))
    return file_path

@pytest.fixture
def downloader():
    """Create a downloader instance with mock URL."""
    return DataDownloader(base_urls=[MOCK_BASE_URL])

@responses.activate
def test_download_object(downloader, tmp_path, mock_hdf5_file):
    """Test downloading a single object."""
    # Setup mock response
    with open(mock_hdf5_file, 'rb') as f:
        mock_content = f.read()
    
    remote_path = "pileup-10/ttbar/v1/reco/tracks/pileup-10.ttbar.v1.reco.tracks.events0-999.h5"
    url = f"{MOCK_BASE_URL}/{remote_path}"
    
    # Mock HEAD request
    responses.add(
        responses.HEAD,
        url,
        status=200,
        headers={'content-length': str(len(mock_content))}
    )
    
    # Mock GET request
    responses.add(
        responses.GET,
        url,
        body=mock_content,
        status=200,
        stream=True
    )
    
    # Perform download
    results = downloader.download_object(
        PileupLevel.LOW,
        "ttbar",
        "tracks",
        tmp_path,
        0,
        999
    )
    
    assert len(results) == 1
    result = next(iter(results.values()))
    assert result.success
    assert result.error is None
    assert result.size == len(mock_content)
    assert result.metadata == {'test_attr': 'test_value'}

@responses.activate
def test_download_dataset(downloader, tmp_path, mock_hdf5_file):
    """Test downloading multiple objects."""
    # Setup mock response
    with open(mock_hdf5_file, 'rb') as f:
        mock_content = f.read()
    
    # Mock responses for two files
    for process in ["ttbar", "qcd"]:
        remote_path = f"pileup-10/{process}/v1/reco/tracks/pileup-10.{process}.v1.reco.tracks.events0-999.h5"
        url = f"{MOCK_BASE_URL}/{remote_path}"
        
        responses.add(
            responses.HEAD,
            url,
            status=200,
            headers={'content-length': str(len(mock_content))}
        )
        
        responses.add(
            responses.GET,
            url,
            body=mock_content,
            status=200,
            stream=True
        )
    
    # Perform download
    results = downloader.download_dataset(
        PileupLevel.LOW,
        ["ttbar", "qcd"],
        "tracks",
        tmp_path
    )
    
    assert len(results) == 2
    for result in results.values():
        assert result.success
        assert result.error is None
        assert result.size == len(mock_content)
        assert result.metadata == {'test_attr': 'test_value'}

@responses.activate
def test_download_failure(downloader, tmp_path):
    """Test handling of download failures."""
    url = f"{MOCK_BASE_URL}/nonexistent"
    responses.add(
        responses.HEAD,
        url,
        status=404
    )
    
    results = downloader.download_object(
        PileupLevel.LOW,
        "ttbar",
        "tracks",
        tmp_path,
        0,
        999
    )
    
    assert len(results) == 1
    result = next(iter(results.values()))
    assert not result.success
    assert result.error is not None
    assert "Failed to access file" in result.error

def test_invalid_url():
    """Test initialization with invalid URL."""
    with pytest.raises(RuntimeError, match="Failed to connect to any data URLs"):
        DataDownloader(base_urls=["https://invalid.url"]) 