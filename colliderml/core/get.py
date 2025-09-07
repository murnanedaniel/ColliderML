from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

from .data.manifest import ManifestClient
from .io.downloader import DataDownloader, DownloadResult


def get(
    campaign: Optional[str] = None,
    datasets: Optional[List[str]] = None,
    objects: Optional[List[str]] = None,
    events: Optional[int] = None,
    output_dir: Path | str = "data",
    workers: int = 4,
    resume: bool = True,
) -> Dict[str, DownloadResult]:
    """Manifest-driven download helper.

    Returns a mapping from remote path to DownloadResult.
    """
    manifest = ManifestClient()
    files = manifest.select_files(
        campaign=campaign,
        datasets=datasets,
        objects=objects,
        max_events=events,
    )
    if not files:
        return {}
    downloader = DataDownloader()
    return downloader.download_files(
        remote_paths=[f.path for f in files],
        local_dir=output_dir,
        max_workers=workers,
        resume=resume,
    )


__all__ = ["get"]


