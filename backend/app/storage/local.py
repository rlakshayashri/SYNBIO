import shutil
from pathlib import Path
from uuid import UUID

from app.core.config import settings


class LocalStorageService:
    """Local filesystem storage service for dataset files."""

    def __init__(self, base_dir: str | Path | None = None) -> None:
        self.base_dir = Path(base_dir or settings.DATASET_STORAGE_PATH).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save_file(self, dataset_id: UUID, file_name: str, content: bytes) -> str:
        """Saves file bytes under a dataset-specific subdirectory and returns the relative path string."""
        dataset_dir = self.base_dir / str(dataset_id)
        dataset_dir.mkdir(parents=True, exist_ok=True)
        file_path = dataset_dir / file_name

        with open(file_path, "wb") as f:
            f.write(content)

        return str(file_path.relative_to(self.base_dir.parent))

    def get_file_path(self, storage_path: str) -> Path:
        """Resolves a storage path string to an absolute Path object."""
        path = Path(storage_path)
        if path.is_absolute():
            return path
        return (self.base_dir.parent / path).resolve()

    def delete_dataset(self, dataset_id: UUID) -> None:
        """Deletes all stored files for a specific dataset."""
        dataset_dir = self.base_dir / str(dataset_id)
        if dataset_dir.exists() and dataset_dir.is_dir():
            shutil.rmtree(dataset_dir)
