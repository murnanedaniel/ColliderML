"""Dataset class for handling HEP data."""

from typing import Optional, List, Dict, Any
from pathlib import Path

class Dataset:
    """Base class for handling HEP datasets."""
    
    def __init__(self, name: str, files: List[str]):
        """Initialize a dataset.
        
        Args:
            name: Name of the dataset.
            files: List of file paths in the dataset.
        """
        self.name = name
        self.files = files
        self._metadata: Dict[str, Any] = {}
        
    def __len__(self) -> int:
        """Get the number of files in the dataset."""
        return len(self.files)
        
    def add_metadata(self, key: str, value: Any) -> None:
        """Add metadata to the dataset.
        
        Args:
            key: Metadata key.
            value: Metadata value.
        """
        self._metadata[key] = value
        
    def get_metadata(self, key: str) -> Any:
        """Get metadata from the dataset.
        
        Args:
            key: Metadata key.
            
        Returns:
            The metadata value.
            
        Raises:
            KeyError: If the key doesn't exist.
        """
        return self._metadata[key] 