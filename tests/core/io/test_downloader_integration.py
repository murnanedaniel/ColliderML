"""Integration tests for the DataDownloader class using real network calls."""

import pytest
import tempfile
from pathlib import Path
import shutil
import time
from colliderml.core.io.downloader import DataDownloader

# Mark all tests in this file as integration tests
pytestmark = pytest.mark.integration

@pytest.fixture
def temp_dir():
    """Create a temporary directory for downloads."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)

@pytest.fixture
def downloader():
    """Create a DataDownloader instance."""
    return DataDownloader()

def test_list_files_real(downloader):
    """Test listing files from the actual server."""
    files = downloader.list_files("pda_batch_parallel_testing/proc_1")
    assert len(files) > 0
    assert any(f.endswith('.root') for f in files)

def test_single_file_download(downloader, temp_dir):
    """Test downloading a single file from the server."""
    remote_path = "pda_batch_parallel_testing/proc_1/simhits.root"
    result = downloader._download_single_file(remote_path, temp_dir / "simhits.root")
    
    assert result.success
    assert result.path.exists()
    assert result.path.stat().st_size > 0
    assert result.checksum is not None

def test_parallel_downloads(downloader, temp_dir):
    """Test downloading multiple files in parallel."""
    remote_paths = [
        "pda_batch_parallel_testing/proc_1/calohits.root",
        "pda_batch_parallel_testing/proc_1/measurements.root"
    ]
    
    results = downloader.download_files(
        remote_paths=remote_paths,
        local_dir=temp_dir,
        max_workers=2
    )
    
    assert len(results) == len(remote_paths)
    assert all(result.success for result in results.values())
    assert all(result.path.exists() for result in results.values())
    assert all(result.checksum is not None for result in results.values())

def test_resume_download(downloader, temp_dir):
    """Test resuming an interrupted download."""
    remote_path = "pda_batch_parallel_testing/proc_1/edm4hep.root"
    local_path = temp_dir / "edm4hep.root"
    
    # Start initial download with forced interrupt
    result = downloader._download_single_file(
        remote_path,
        local_path,
        _test_interrupt=True  # Special flag for testing
    )
    
    assert not result.success
    assert "Test interruption" in result.error
    assert local_path.exists()
    initial_size = local_path.stat().st_size
    
    # Wait briefly to ensure we're not hitting rate limits
    time.sleep(1)
    
    # Resume download
    result = downloader._download_single_file(
        remote_path,
        local_path,
        resume=True
    )
    
    assert result.success
    assert result.path.exists()
    assert result.path.stat().st_size > initial_size
    assert result.checksum is not None

def test_error_handling_invalid_url(downloader, temp_dir):
    """Test handling of invalid URLs."""
    remote_path = "pda_batch_parallel_testing/nonexistent/file.root"
    result = downloader._download_single_file(
        remote_path,
        temp_dir / "nonexistent.root"
    )
    
    assert not result.success
    assert result.error is not None

def test_retry_mechanism(downloader, temp_dir):
    """Test the retry mechanism with an unstable connection."""
    remote_path = "pda_batch_parallel_testing/proc_1/simhits.root"
    
    # Configure downloader with aggressive retry settings
    downloader = DataDownloader(
        max_retries=5,
        retry_backoff=0.1  # Short backoff for testing
    )
    
    result = downloader._download_single_file(
        remote_path,
        temp_dir / "simhits.root"
    )
    
    assert result.success
    assert result.path.exists()
    assert result.checksum is not None 