"""Downloader implementation for ColliderML."""

from typing import Optional, Union, List, Dict
from pathlib import Path
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import os
import hashlib
import time
from dataclasses import dataclass
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import re

@dataclass
class DownloadResult:
    """Result of a file download operation."""
    success: bool
    path: Path
    error: Optional[str] = None
    checksum: Optional[str] = None
    size: Optional[int] = None

class DataDownloader:
    """A client for downloading ColliderML datasets."""
    
    def __init__(
        self,
        base_url: str = "https://portal.nersc.gov/cfs/m3443/dtmurnane/ColliderML",
        max_retries: int = 3,
        retry_backoff: float = 0.3,
        chunk_size: int = 8192
    ):
        """Initialize the downloader.
        
        Args:
            base_url: Base URL for the data repository.
            max_retries: Maximum number of retry attempts for failed requests.
            retry_backoff: Exponential backoff factor between retries.
            chunk_size: Size of chunks to download in bytes.
        """
        self.base_url = base_url.rstrip('/')
        self.chunk_size = chunk_size
        
        # Configure session with retries
        self.session = requests.Session()
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=retry_backoff,
            status_forcelist=[500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Test connection
        try:
            response = self.session.head(self.base_url)
            response.raise_for_status()
        except requests.RequestException as e:
            raise RuntimeError(f"Failed to connect to {base_url}: {str(e)}")
    
    def list_files(self, path: str = "") -> List[str]:
        """List available files at the given path.
        
        Args:
            path: Relative path to list files from.
            
        Returns:
            List of available file paths.
        """
        url = f"{self.base_url}/{path.lstrip('/')}"
        response = self.session.get(url)
        response.raise_for_status()
        
        # Parse HTML to extract file links
        # Look for <a href="filename"> patterns
        files = []
        for match in re.finditer(r'<a href="([^"]+)">', response.text):
            filename = match.group(1)
            # Skip parent directory and full URLs
            if filename.startswith('/') or filename == '../' or '://' in filename:
                continue
            # Remove trailing slash from directory names
            filename = filename.rstrip('/')
            if filename:
                files.append(filename)
        
        return files
    
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
    
    def _download_single_file(
        self,
        remote_path: str,
        local_path: Path,
        resume: bool = True,
        _test_interrupt: bool = False  # For testing only
    ) -> DownloadResult:
        """Download a single file.
        
        Args:
            remote_path: Path to the file on the server.
            local_path: Local path to save the file to.
            resume: Whether to attempt to resume a partial download.
            _test_interrupt: If True, raises an exception mid-download (for testing only).
            
        Returns:
            DownloadResult containing the download status and details.
        """
        url = f"{self.base_url}/{remote_path.lstrip('/')}"
        headers = {}
        mode = 'wb'
        initial_size = 0
        
        # Create parent directories if they don't exist
        local_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Check if we can resume a partial download
        if resume and local_path.exists():
            initial_size = local_path.stat().st_size
            headers['Range'] = f'bytes={initial_size}-'
            mode = 'ab'
        
        try:
            response = self.session.get(url, stream=True, headers=headers)
            response.raise_for_status()
            
            # Get the total file size
            total_size = int(response.headers.get('content-length', 0))
            if initial_size > 0:
                total_size += initial_size
            
            downloaded = initial_size
            interrupt_size = total_size // 3 if _test_interrupt else total_size
            
            with tqdm(
                total=total_size,
                initial=initial_size,
                unit='B',
                unit_scale=True,
                desc=local_path.name
            ) as pbar:
                with open(local_path, mode) as f:
                    for chunk in response.iter_content(chunk_size=self.chunk_size):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            pbar.update(len(chunk))
                            
                            # Simulate interruption for testing
                            if _test_interrupt and downloaded >= interrupt_size:
                                raise Exception("Test interruption")
            
            # Verify the download is complete
            final_size = local_path.stat().st_size
            if final_size != total_size:
                raise Exception(f"Download incomplete: got {final_size} bytes, expected {total_size}")
            
            # Compute checksum after successful download
            checksum = self._compute_checksum(local_path)
            return DownloadResult(True, local_path, checksum=checksum, size=final_size)
            
        except Exception as e:
            return DownloadResult(False, local_path, error=str(e), size=local_path.stat().st_size if local_path.exists() else None)
    
    def download_files(
        self,
        remote_paths: Union[str, List[str]],
        local_dir: Union[str, Path],
        max_workers: int = 4,
        resume: bool = True,
        preserve_structure: bool = True
    ) -> Dict[str, DownloadResult]:
        """Download one or more files in parallel.
        
        Args:
            remote_paths: Single path or list of paths to download.
            local_dir: Directory to save files to.
            max_workers: Maximum number of parallel downloads.
            resume: Whether to attempt to resume partial downloads.
            preserve_structure: Whether to preserve directory structure.
            
        Returns:
            Dictionary mapping remote paths to their download results.
        """
        if isinstance(remote_paths, str):
            remote_paths = [remote_paths]
            
        local_dir = Path(local_dir)
        local_dir.mkdir(parents=True, exist_ok=True)
        
        results = {}
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_path = {}
            for remote_path in remote_paths:
                if preserve_structure:
                    # Keep directory structure
                    local_path = local_dir / remote_path
                else:
                    # Just use filename
                    local_path = local_dir / os.path.basename(remote_path)
                
                future = executor.submit(
                    self._download_single_file,
                    remote_path,
                    local_path,
                    resume
                )
                future_to_path[future] = remote_path
            
            # Process results as they complete
            for future in as_completed(future_to_path):
                remote_path = future_to_path[future]
                try:
                    results[remote_path] = future.result()
                except Exception as e:
                    if preserve_structure:
                        local_path = local_dir / remote_path
                    else:
                        local_path = local_dir / os.path.basename(remote_path)
                    results[remote_path] = DownloadResult(
                        False,
                        local_path,
                        error=str(e)
                    )
        
        return results 