"""GUI-local project-file context for one MainWindow document.

The retained path is document/session state, not ProjectSchema data.  This
module deliberately performs no file access or path normalization.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class ProjectDocumentOrigin(str, Enum):
    """How the current in-memory document binding was established."""

    STARTUP = "startup"
    NEW = "new"
    OPENED = "opened"
    SAVED_AS = "saved_as"


@dataclass(frozen=True)
class ProjectDocumentContext:
    """Immutable, non-serialized file context for one MainWindow document."""

    project_file_path: str | None = None
    origin: ProjectDocumentOrigin = ProjectDocumentOrigin.STARTUP
    generation: int = 0

    def __post_init__(self) -> None:
        if self.project_file_path is not None and not isinstance(
            self.project_file_path, str
        ):
            raise TypeError("project_file_path must be a string or None")
        if self.project_file_path == "":
            raise ValueError("project_file_path must be non-empty when bound")
        if isinstance(self.generation, bool) or not isinstance(self.generation, int):
            raise TypeError("generation must be an integer")
        if self.generation < 0:
            raise ValueError("generation must be non-negative")
        object.__setattr__(self, "origin", ProjectDocumentOrigin(self.origin))

    @property
    def is_bound(self) -> bool:
        return self.project_file_path is not None

    @property
    def project_root(self) -> Path | None:
        if self.project_file_path is None:
            return None
        path = Path(self.project_file_path)
        return path.parent if path.is_absolute() else None
