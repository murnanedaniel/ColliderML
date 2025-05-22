"""Downloader implementation for ColliderML."""

from typing import Optional, Union, List, Dict, Set, Tuple
from pathlib import Path
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import os
import hashlib
import time
from dataclasses import dataclass
import h5py
import numpy as np

from ..data.config import (
    DataType,
    PileupLevel,
    OBJECT_CONFIGS,
    VALID_PROCESSES,
    DEFAULT_URLS,
    get_object_path,
    EVENTS_PER_FILE
)

@dataclass
class DownloadResult:
    """Result of a file download operation."""
    success: bool
    path: Path
    error: Optional[str] = None
    checksum: Optional[str] = None
    size: Optional[int] = None
    metadata: Optional[Dict] = None

class DataDownloader:
    """A client for downloading ColliderML datasets."""
    
    def __init__(
        self,
        base_urls: List[str] = None,
        chunk_size: int = 8192
    ):
        """Initialize the downloader.
        
        Args:
            base_urls: List of base URLs to try for data download.
                      Will try each URL in order until successful.
            chunk_size: Size of chunks to download in bytes.
        """
        self.base_urls = base_urls or DEFAULT_URLS
        self.chunk_size = chunk_size
        self.session = requests.Session()
    
    def _compute_checksum(self, file_path: Path) -> str:
        """Compute SHA-256 checksum of a file.
        
        Args:
            file_path: Path to the file.
            
        Returns:
            Hexadecimal string of the checksum.
        """
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(self.chunk_size), b''):
                sha256.update(chunk)
        return sha256.hexdigest()
    
    def _validate_hdf5(self, file_path: Path) -> Dict:
        """Validate and get metadata from an HDF5 file.
        
        Args:
            file_path: Path to the HDF5 file.
            
        Returns:
            Dictionary of metadata
            
        Raises:
            ValueError: If file is invalid or doesn't match expected structure
        """
        try:
            with h5py.File(file_path, 'r') as f:
                # Check for required group structure
                if 'events' not in f:
                    raise ValueError("Missing required 'events' group")
                
                # Check event structure
                events = f['events']
                if len(events.keys()) == 0:
                    raise ValueError("No events found in file")
                
                # Get first event structure
                first_event = next(iter(events.values()))
                if not isinstance(first_event, h5py.Group):
                    raise ValueError("Events must be HDF5 groups")
                
                # Get metadata about the structure
                metadata = {
                    'n_events': len(events),
                    'datasets': {},
                    **dict(f.attrs)  # Include any file-level attributes
                }
                
                # Record shape and dtype of each dataset in first event
                for name, dataset in first_event.items():
                    if isinstance(dataset, h5py.Dataset):
                        metadata['datasets'][name] = {
                            'shape': dataset.shape,
                            'dtype': str(dataset.dtype)
                        }
                
                if not metadata['datasets']:
                    raise ValueError("No datasets found in events")
                
                return metadata
                
        except (OSError, KeyError) as e:
            raise ValueError(f"Invalid HDF5 file: {str(e)}")
        except Exception as e:
            raise ValueError(f"Error validating HDF5 file: {str(e)}")
    
    def _download_single_file(
        self,
        remote_path: str,
        local_path: Path,
        resume: bool = True,
    ) -> DownloadResult:
        """Download a single file.
        
        Args:
            remote_path: Path to the file on the server.
            local_path: Local path to save the file to.
            resume: Whether to attempt to resume a partial download.
            
        Returns:
            DownloadResult containing the download status and details.
        """
        # Create parent directories if they don't exist
        local_path.parent.mkdir(parents=True, exist_ok=True)
        
        last_error = None
        # Try each base URL
        for base_url in self.base_urls:
            url = f"{base_url.rstrip('/')}/{remote_path.lstrip('/')}"
            try:
                # Simple GET request, like wget
                response = self.session.get(url, stream=True)
                response.raise_for_status()
                
                # Download with progress bar
                with tqdm(
                    unit='B',
                    unit_scale=True,
                    desc=local_path.name
                ) as pbar:
                    with open(local_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=self.chunk_size):
                            if chunk:
                                f.write(chunk)
                                pbar.update(len(chunk))
                
                # Get final size
                final_size = local_path.stat().st_size
                
                try:
                    # Validate HDF5 and get metadata
                    metadata = self._validate_hdf5(local_path)
                    
                    # Compute checksum after successful download
                    checksum = self._compute_checksum(local_path)
                    
                    return DownloadResult(
                        True,
                        local_path,
                        checksum=checksum,
                        size=final_size,
                        metadata=metadata
                    )
                except ValueError as e:
                    # If HDF5 validation fails, consider it a failed download
                    if local_path.exists():
                        local_path.unlink()
                    return DownloadResult(
                        False,
                        local_path,
                        error=str(e)
                    )
                
            except Exception as e:
                last_error = e
                continue  # Try next URL
                
        # All URLs failed
        return DownloadResult(
            False,
            local_path,
            error=f"Failed to download from any URL: {str(last_error)}"
        )
    
    def download_object(
        self,
        pileup: Union[str, PileupLevel],
        process: str,
        object_name: str,
        local_dir: Union[str, Path],
        start_event: int = 0,
        end_event: int = 999,
        max_workers: int = 4,
        resume: bool = True,
    ) -> Dict[str, DownloadResult]:
        """Download data for a specific object type.
        
        Args:
            pileup: Pileup level (can be string or PileupLevel enum)
            process: Physics process
            object_name: Type of object to download
            local_dir: Directory to save files to
            start_event: First event number to download
            end_event: Last event number to download
            max_workers: Maximum number of parallel downloads
            resume: Whether to attempt to resume partial downloads
            
        Returns:
            Dictionary mapping remote paths to their download results
        """
        # Convert string pileup to enum if needed
        if isinstance(pileup, str):
            pileup = PileupLevel(pileup)
            
        # Get the remote path
        remote_path = get_object_path(
            pileup,
            process,
            object_name,
            start_event,
            end_event
        )
        
        local_dir = Path(local_dir)
        local_dir.mkdir(parents=True, exist_ok=True)
        
        # For now we're downloading single chunks, but this could be extended
        # to download multiple chunks in parallel
        result = self._download_single_file(
            remote_path,
            local_dir / os.path.basename(remote_path),
            resume
        )
        
        return {remote_path: result}
    
    def download_dataset(
        self,
        pileup: Union[str, PileupLevel],
        processes: Union[str, List[str]],
        object_types: Union[str, List[str]],
        local_dir: Union[str, Path],
        max_workers: int = 4,
        resume: bool = True,
        start_event: int = 0,
        end_event: int = 999,
    ) -> Dict[str, DownloadResult]:
        """Download multiple objects and processes.
        
        Args:
            pileup: Pileup level
            processes: Process(es) to download
            object_types: Object type(s) to download
            local_dir: Directory to save files to
            max_workers: Maximum number of parallel downloads
            resume: Whether to attempt to resume partial downloads
            start_event: First event number to download
            end_event: Last event number to download
            
        Returns:
            Dictionary mapping remote paths to their download results
        """
        if isinstance(processes, str):
            processes = [processes]
        if isinstance(object_types, str):
            object_types = [object_types]
            
        results = {}
        for process in processes:
            for object_type in object_types:
                chunk_results = self.download_object(
                    pileup,
                    process,
                    object_type,
                    local_dir,
                    start_event=start_event,
                    end_event=end_event,
                    max_workers=max_workers,
                    resume=resume
                )
                results.update(chunk_results)
                
        return results 

    def _check_file_exists(self, remote_path: str) -> Tuple[bool, Optional[str]]:
        """Check if a file exists on any of the base URLs.
        
        Args:
            remote_path: Path to the file on the server.
            
        Returns:
            Tuple of (exists, url) where exists is True if the file exists,
            and url is the working URL if it exists, None otherwise.
        """
        for base_url in self.base_urls:
            url = f"{base_url.rstrip('/')}/{remote_path.lstrip('/')}"
            try:
                response = self.session.head(url)
                if response.status_code == 200:
                    return True, url
            except:
                continue
        return False, None

    def find_last_available_event(
        self,
        pileup: Union[str, PileupLevel],
        process: str,
        object_name: str,
        start_event: int = 0,
        max_events: int = 100000  # Some reasonable upper limit
    ) -> int:
        """Find the last available event in a dataset by binary search.
        
        Args:
            pileup: Pileup level
            process: Physics process
            object_name: Type of object
            start_event: First event number to check from
            max_events: Maximum number of events to check
            
        Returns:
            The last available event number
        """
        if isinstance(pileup, str):
            pileup = PileupLevel(pileup)

        # First find the last available file by checking sequentially
        # This is more reliable than binary search for sparse files
        current_chunk = start_event
        last_found = -1

        while current_chunk <= max_events:
            remote_path = get_object_path(
                pileup,
                process,
                object_name,
                current_chunk,
                current_chunk + EVENTS_PER_FILE - 1
            )
            
            exists, _ = self._check_file_exists(remote_path)
            
            if exists:
                last_found = current_chunk
                current_chunk += EVENTS_PER_FILE
            else:
                break

        if last_found == -1:
            raise ValueError(f"No files found for {process} {object_name} with pileup {pileup.value}")

        # Now find the exact number of events in the last file
        last_chunk_start = last_found
        for end_event in range(last_chunk_start + EVENTS_PER_FILE - 1, last_chunk_start - 1, -1):
            remote_path = get_object_path(
                pileup,
                process,
                object_name,
                last_chunk_start,
                end_event
            )
            exists, _ = self._check_file_exists(remote_path)
            if exists:
                return end_event

        return last_chunk_start + EVENTS_PER_FILE - 1 