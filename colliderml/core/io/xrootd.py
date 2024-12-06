"""XRootD client implementation for ColliderML."""

from typing import Optional, Union, List
from pathlib import Path
import XRootD.client

class XRootDClient:
    """A client for interacting with XRootD servers."""
    
    def __init__(self, server_url: str):
        """Initialize the XRootD client.
        
        Args:
            server_url: The URL of the XRootD server (e.g., 'root://eospublic.cern.ch/').
        """
        self.server_url = server_url.rstrip('/')
        self._client = XRootD.client.FileSystem(self.server_url)
    
    def list_directory(
        self, 
        path: str, 
        recursive: bool = False
    ) -> List[str]:
        """List contents of a directory.
        
        Args:
            path: Path to list contents of.
            recursive: Whether to list contents recursively.
            
        Returns:
            List of paths found in the directory.
        """
        status, listing = self._client.dirlist(path, flags=XRootD.client.flags.DirListFlags.STAT)
        if not status.ok:
            raise RuntimeError(f"Failed to list directory {path}: {status.message}")
            
        paths = [item.name for item in listing]
        
        if recursive:
            for item in listing:
                if item.statinfo.flags & XRootD.client.flags.StatInfoFlags.IS_DIR:
                    subpaths = self.list_directory(f"{path}/{item.name}", recursive=True)
                    paths.extend(subpaths)
                    
        return paths
    
    def download_file(
        self, 
        remote_path: str, 
        local_path: Union[str, Path],
        chunk_size: int = 8 * 1024 * 1024  # 8MB chunks
    ) -> None:
        """Download a file from the XRootD server.
        
        Args:
            remote_path: Path to the file on the server.
            local_path: Local path to save the file to.
            chunk_size: Size of chunks to download in bytes.
        """
        local_path = Path(local_path)
        local_path.parent.mkdir(parents=True, exist_ok=True)
        
        with XRootD.client.File() as f:
            status = f.open(f"{self.server_url}/{remote_path.lstrip('/')}")
            if not status.ok:
                raise RuntimeError(f"Failed to open file {remote_path}: {status.message}")
                
            with open(local_path, 'wb') as local_f:
                offset = 0
                while True:
                    status, data = f.read(offset=offset, size=chunk_size)
                    if not status.ok:
                        raise RuntimeError(f"Failed to read file {remote_path}: {status.message}")
                    
                    if not data:  # EOF
                        break
                        
                    local_f.write(data)
                    offset += len(data) 