"""Tests for downloader (manifest-agnostic)."""

import pytest
from pathlib import Path
import responses
import h5py
import numpy as np
from colliderml.core.io.downloader import DataDownloader

MOCK_BASE_URL = "https://mock.cern.ch/data"


@pytest.fixture
def mock_hdf5_file(tmp_path):
    file_path = tmp_path / "test.h5"
    with h5py.File(file_path, 'w') as f:
        f.attrs['test_attr'] = 'test_value'
        f.create_dataset('test_data', data=np.array([1, 2, 3]))
    return file_path


@responses.activate
def test_download_files(tmp_path, mock_hdf5_file):
    with open(mock_hdf5_file, 'rb') as f:
        content = f.read()

    remote_paths = [
        "campaign/dataset/objects/hits_0_2.h5",
        "campaign/dataset/objects/hits_3_5.h5",
    ]
    for rp in remote_paths:
        url = f"{MOCK_BASE_URL}/{rp}"
        responses.add(responses.HEAD, url, status=200, headers={'content-length': str(len(content))})
        responses.add(responses.GET, url, body=content, status=200, stream=True)

    dl = DataDownloader(base_urls=[MOCK_BASE_URL])
    results = dl.download_files(remote_paths=remote_paths, local_dir=tmp_path, max_workers=2)

    assert set(results.keys()) == set(remote_paths)
    for res in results.values():
        assert res.success
        assert res.error is None
        assert res.size == len(content)
        assert res.metadata == {'test_attr': 'test_value'}


@responses.activate
def test_download_failure(tmp_path):
    rp = "missing/file.h5"
    url = f"{MOCK_BASE_URL}/{rp}"
    responses.add(responses.HEAD, url, status=404)

    dl = DataDownloader(base_urls=[MOCK_BASE_URL])
    results = dl.download_files(remote_paths=[rp], local_dir=tmp_path)

    assert len(results) == 1
    res = results[rp]
    assert not res.success
    assert res.error is not None
    assert "Failed to access file" in res.error


def test_invalid_url():
    with pytest.raises(RuntimeError, match="Failed to connect to any data URLs"):
        DataDownloader(base_urls=["https://invalid.url"], request_timeout_seconds=1)