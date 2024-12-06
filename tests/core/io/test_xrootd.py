"""Tests for the XRootD client implementation."""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from colliderml.core.io.xrootd import XRootDClient

@pytest.fixture
def mock_xrootd():
    """Create a mock XRootD client."""
    with patch('XRootD.client.FileSystem') as mock_fs:
        yield mock_fs

def test_init():
    """Test XRootDClient initialization."""
    client = XRootDClient('root://test.server/')
    assert client.server_url == 'root://test.server'
    
    client = XRootDClient('root://test.server')
    assert client.server_url == 'root://test.server'

def test_list_directory(mock_xrootd):
    """Test directory listing."""
    mock_status = MagicMock()
    mock_status.ok = True
    
    mock_item = MagicMock()
    mock_item.name = 'test_file.root'
    mock_item.statinfo.flags = 0  # Not a directory
    
    mock_xrootd.return_value.dirlist.return_value = (mock_status, [mock_item])
    
    client = XRootDClient('root://test.server')
    paths = client.list_directory('/test/path')
    
    assert paths == ['test_file.root']
    mock_xrootd.return_value.dirlist.assert_called_once_with(
        '/test/path', 
        flags=mock_xrootd.client.flags.DirListFlags.STAT
    )

def test_list_directory_error(mock_xrootd):
    """Test directory listing error handling."""
    mock_status = MagicMock()
    mock_status.ok = False
    mock_status.message = 'Test error'
    
    mock_xrootd.return_value.dirlist.return_value = (mock_status, None)
    
    client = XRootDClient('root://test.server')
    with pytest.raises(RuntimeError, match='Failed to list directory.*Test error'):
        client.list_directory('/test/path') 