class SynDataXError(Exception):
    """Base application exception for SynDataX."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class ProjectNotFoundError(SynDataXError):
    """Raised when a requested Project is not found."""

    pass


class DatasetNotFoundError(SynDataXError):
    """Raised when a requested Dataset is not found."""

    pass


class UnsupportedFileTypeError(SynDataXError):
    """Raised when an uploaded file type is not supported."""

    pass


class DatasetParseError(SynDataXError):
    """Raised when a dataset file fails to parse."""

    pass


class DatasetTooLargeError(SynDataXError):
    """Raised when an uploaded file exceeds the configured size limit."""

    pass
