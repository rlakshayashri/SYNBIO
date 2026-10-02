from pathlib import Path

import pandas as pd

from app.core.exceptions import DatasetParseError, UnsupportedFileTypeError


def load_dataset_to_dataframe(file_path: str | Path, file_type: str | None = None) -> pd.DataFrame:
    """Parses a CSV or Excel file into a pandas DataFrame.

    Independent of FastAPI, HTTP, and database logic.
    """
    path = Path(file_path)
    if not path.exists():
        raise DatasetParseError(f"Dataset file does not exist at path: {path}")

    ext = path.suffix.lower().lstrip(".")
    if not ext and file_type:
        ext = file_type.lower().lstrip(".")

    try:
        if ext == "csv":
            df = pd.read_csv(path)
        elif ext in ("xlsx", "xls"):
            df = pd.read_excel(path)
        else:
            raise UnsupportedFileTypeError(
                f"Unsupported file extension '.{ext}'. Only CSV (.csv) and Excel (.xlsx, .xls) files are supported."
            )
    except UnsupportedFileTypeError:
        raise
    except Exception as e:
        raise DatasetParseError(f"Failed to parse scientific dataset file: {str(e)}") from e

    if df.empty:
        raise DatasetParseError("Uploaded dataset file is empty.")

    return df
