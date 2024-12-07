"""Tests for the DataDownloader class."""

import pytest
from pathlib import Path
import requests
from unittest.mock import Mock, patch, PropertyMock
from colliderml.core.io.downloader import DataDownloader, DownloadResult

@pytest.fixture
def mock_session():
    """Create a mock session object."""
    with patch('requests.Session') as mock:
        mock.return_value.head.return_value.status_code = 200
        mock.return_value.head.return_value.raise_for_status.return_value = None
        return mock.return_value

@pytest.fixture
def downloader(mock_session):
    """Create a DataDownloader instance with a mock session."""
    with patch('requests.Session', return_value=mock_session):
        return DataDownloader()

def test_init_success(mock_session):
    """Test successful initialization."""
    with patch('requests.Session', return_value=mock_session):
        downloader = DataDownloader()
        assert downloader.base_url == "https://portal.nersc.gov/cfs/m3443/dtmurnane/ColliderML"
        assert downloader.chunk_size == 8192

def test_init_failure():
    """Test initialization with connection failure."""
    with patch('requests.Session') as mock:
        mock.return_value.head.side_effect = requests.RequestException("Connection failed")
        with pytest.raises(RuntimeError):
            DataDownloader()

def test_list_files(downloader, mock_session):
    """Test listing files."""
    mock_session.get.return_value.text = "file1.root\nfile2.root"
    files = downloader.list_files("test/path")
    assert files == ["file1.root", "file2.root"]

def test_compute_checksum(downloader, tmp_path):
    """Test checksum computation."""
    test_file = tmp_path / "test.txt"
    test_content = b"test content"
    test_file.write_bytes(test_content)
    
    checksum = downloader._compute_checksum(test_file)
    assert isinstance(checksum, str)
    assert len(checksum) == 64  # SHA-256 produces 64 character hex string

def test_download_single_file_success(downloader, tmp_path, mock_session):
    """Test successful single file download."""
    mock_content = b"test content"
    mock_response = Mock()
    mock_response.headers = {'content-length': str(len(mock_content))}
    mock_response.iter_content.return_value = [mock_content]
    mock_session.get.return_value = mock_response
    
    result = downloader._download_single_file("test.root", tmp_path / "test.root")
    assert result.success
    assert result.path.exists()
    assert result.error is None
    assert isinstance(result.checksum, str)

def test_download_single_file_resume(downloader, tmp_path, mock_session):
    """Test resuming a partial download."""
    # Create partial file
    partial_content = b"partial"
    test_file = tmp_path / "test.root"
    test_file.write_bytes(partial_content)
    
    # Mock response for remaining content
    remaining_content = b"_content"
    mock_response = Mock()
    mock_response.headers = {'content-length': str(len(remaining_content))}
    mock_response.iter_content.return_value = [remaining_content]
    mock_session.get.return_value = mock_response
    
    result = downloader._download_single_file("test.root", test_file, resume=True)
    assert result.success
    assert result.path.read_bytes() == b"partial_content"

def test_download_single_file_error(downloader, tmp_path, mock_session):
    """Test error handling in single file download."""
    mock_session.get.side_effect = requests.RequestException("Download failed")
    
    result = downloader._download_single_file("test.root", tmp_path / "test.root")
    assert not result.success
    assert "Download failed" in result.error

def test_download_files_multiple(downloader, tmp_path, mock_session):
    """Test downloading multiple files in parallel."""
    mock_content = b"test content"
    mock_response = Mock()
    mock_response.headers = {'content-length': str(len(mock_content))}
    mock_response.iter_content.return_value = [mock_content]
    mock_session.get.return_value = mock_response
    
    files = ["test1.root", "test2.root"]
    results = downloader.download_files(files, tmp_path, max_workers=2)
    
    assert len(results) == 2
    assert all(result.success for result in results.values())
    assert all((tmp_path / f).exists() for f in files)

def test_download_files_partial_failure(downloader, tmp_path, mock_session):
    """Test handling of partial failures in multiple downloads."""
    def mock_get(url, **kwargs):
        if "test1.root" in url:
            return Mock(
                headers={'content-length': '12'},
                iter_content=lambda chunk_size: [b"test content"]
            )
        else:
            raise requests.RequestException("Failed")
    
    mock_session.get.side_effect = mock_get
    
    files = ["test1.root", "test2.root"]
    results = downloader.download_files(files, tmp_path)
    
    assert results["test1.root"].success
    assert not results["test2.root"].success
    assert "Failed" in results["test2.root"].error

def test_session_retry_configuration(mock_session):
    """Test that the session is configured with retries."""
    with patch('requests.Session', return_value=mock_session) as mock_session_class:
        downloader = DataDownloader(max_retries=5, retry_backoff=0.5)
        assert mock_session.mount.call_count == 2  # Called for both http and https