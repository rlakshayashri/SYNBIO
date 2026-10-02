import math
import uuid
from collections.abc import Sequence
from uuid import UUID

import numpy as np
import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import (
    DatasetNotFoundError,
    DatasetTooLargeError,
    ProjectNotFoundError,
)
from app.models.dataset import Dataset
from app.models.project import Project
from app.schemas.dataset import (
    ColumnMetadata,
    DatasetCreate,
    DatasetPreviewResponse,
    DatasetUpdate,
)
from app.scientific.preprocessing.data_loader import load_dataset_to_dataframe
from app.storage.local import LocalStorageService


class DatasetService:
    """Service encapsulating ingestion, preview, and storage logic for Datasets."""

    def __init__(self, db: Session, storage: LocalStorageService | None = None) -> None:
        self.db = db
        self.storage = storage or LocalStorageService()

    def get_by_id(self, dataset_id: UUID) -> Dataset | None:
        """Retrieves a single dataset by ID."""
        return self.db.scalar(select(Dataset).where(Dataset.id == dataset_id))

    def list_by_project(
        self, project_id: UUID, skip: int = 0, limit: int = 100
    ) -> Sequence[Dataset]:
        """Lists datasets belonging to a specific project."""
        stmt = (
            select(Dataset)
            .where(Dataset.project_id == project_id)
            .offset(skip)
            .limit(limit)
            .order_by(Dataset.created_at.desc())
        )
        return self.db.scalars(stmt).all()

    def upload_dataset(
        self,
        project_id: UUID,
        file_name: str,
        file_type: str,
        file_bytes: bytes,
        name: str | None = None,
    ) -> Dataset:
        """Handles full upload flow: project check, file validation, storage,
        pandas parsing, and DB record persistence."""
        # 1. Verify Project exists
        project = self.db.scalar(select(Project).where(Project.id == project_id))
        if not project:
            raise ProjectNotFoundError(f"Project with ID '{project_id}' does not exist.")

        # 2. Check File Size
        file_size = len(file_bytes)
        max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        if file_size > max_bytes:
            mb_size = file_size / (1024 * 1024)
            raise DatasetTooLargeError(
                f"File size ({mb_size:.2f} MB) exceeds maximum limit of {settings.MAX_UPLOAD_SIZE_MB} MB."
            )

        # 3. Save File to Storage
        dataset_id = uuid.uuid4()
        storage_path = self.storage.save_file(dataset_id, file_name, file_bytes)

        # 4. Parse DataFrame to extract row/column metadata
        try:
            abs_path = self.storage.get_file_path(storage_path)
            df = load_dataset_to_dataframe(abs_path, file_type)
            row_count, column_count = len(df), len(df.columns)
        except Exception:
            # Clean up orphaned storage file if parsing fails
            self.storage.delete_dataset(dataset_id)
            raise

        # 5. Persist Dataset ORM model in PostgreSQL
        display_name = name or file_name
        dataset = Dataset(
            id=dataset_id,
            project_id=project_id,
            name=display_name,
            file_name=file_name,
            file_type=file_type,
            file_size=file_size,
            row_count=row_count,
            column_count=column_count,
            storage_path=storage_path,
        )
        self.db.add(dataset)
        self.db.commit()
        self.db.refresh(dataset)

        return dataset

    def get_preview(self, dataset_id: UUID, limit: int = 10) -> DatasetPreviewResponse:
        """Generates a dataset preview containing head rows and column null/dtype metrics."""
        dataset = self.get_by_id(dataset_id)
        if not dataset:
            raise DatasetNotFoundError(f"Dataset with ID '{dataset_id}' not found.")

        abs_path = self.storage.get_file_path(dataset.storage_path)
        df = load_dataset_to_dataframe(abs_path, dataset.file_type)

        total_rows = len(df)
        total_cols = len(df.columns)

        columns_meta: list[ColumnMetadata] = []
        for col in df.columns:
            null_count = int(df[col].isna().sum())
            pct = round((null_count / total_rows) * 100.0, 2) if total_rows > 0 else 0.0
            columns_meta.append(
                ColumnMetadata(
                    name=str(col),
                    dtype=str(df[col].dtype),
                    null_count=null_count,
                    null_percentage=pct,
                )
            )

        # Extract head preview rows and format for JSON serialization
        preview_df = df.head(limit)
        cleaned_data: list[dict[str, float | str | int | None]] = []
        for row in preview_df.to_dict(orient="records"):
            clean_row: dict[str, float | str | int | None] = {}
            for k, v in row.items():
                if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
                    clean_row[str(k)] = None
                elif pd.isna(v):
                    clean_row[str(k)] = None
                elif isinstance(v, (np.integer, np.int64)):
                    clean_row[str(k)] = int(v)
                elif isinstance(v, (np.floating, np.float64)):
                    clean_row[str(k)] = float(v)
                else:
                    clean_row[str(k)] = str(v) if not isinstance(v, (str, int, float, bool)) else v
            cleaned_data.append(clean_row)

        return DatasetPreviewResponse(
            dataset_id=dataset.id,
            row_count=dataset.row_count or total_rows,
            column_count=dataset.column_count or total_cols,
            preview_rows=len(cleaned_data),
            columns=columns_meta,
            data=cleaned_data,
        )

    def create(self, schema: DatasetCreate) -> Dataset:
        """Creates a new Dataset record."""
        dataset = Dataset(
            project_id=schema.project_id,
            name=schema.name,
            file_name=schema.file_name,
            file_type=schema.file_type,
            file_size=schema.file_size,
            row_count=schema.row_count,
            column_count=schema.column_count,
            storage_path=schema.storage_path,
        )
        self.db.add(dataset)
        self.db.commit()
        self.db.refresh(dataset)
        return dataset

    def update(self, dataset_id: UUID, schema: DatasetUpdate) -> Dataset | None:
        """Updates dataset metadata."""
        dataset = self.get_by_id(dataset_id)
        if not dataset:
            return None

        update_data = schema.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(dataset, key, value)

        self.db.commit()
        self.db.refresh(dataset)
        return dataset

    def delete(self, dataset_id: UUID) -> bool:
        """Deletes a dataset by ID and cleans up stored files."""
        dataset = self.get_by_id(dataset_id)
        if not dataset:
            return False

        self.storage.delete_dataset(dataset_id)
        self.db.delete(dataset)
        self.db.commit()
        return True
