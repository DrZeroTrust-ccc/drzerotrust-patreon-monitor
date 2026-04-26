"""Google Drive archive stub.

V1 does NOT upload anything. This module exists so the module
boundary is in place; the future implementation will push generated
markdown drafts to a Drive folder using a service-account credential.
"""

from __future__ import annotations

from pathlib import Path


class GoogleDriveArchive:
    """No-op archive in V1. Records intent only."""

    def __init__(self, credentials_path: str | None = None,
                 folder_id: str | None = None) -> None:
        self.credentials_path = credentials_path
        self.folder_id = folder_id

    def is_configured(self) -> bool:
        return bool(self.credentials_path and self.folder_id)

    def archive(self, file_path: Path) -> dict:
        """Pretend to archive a file. Returns a result descriptor.

        V1 intentionally does nothing on the network. The caller may
        log the descriptor so it's clear that archival was a no-op.
        """
        return {
            "uploaded": False,
            "reason": "V1 is mock-only; Google Drive archival is disabled.",
            "local_path": str(file_path),
            "configured": self.is_configured(),
        }
