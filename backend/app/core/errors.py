"""Domain errors mapped to HTTP status codes in one place."""

from fastapi import HTTPException, status


class DomainError(Exception):
    status_code = status.HTTP_400_BAD_REQUEST

    def __init__(self, message: str, *, detail: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.detail = detail or {}

    def as_http(self) -> HTTPException:
        return HTTPException(
            status_code=self.status_code,
            detail={"message": self.message, **self.detail},
        )


class NotFound(DomainError):
    status_code = status.HTTP_404_NOT_FOUND


class PermissionDenied(DomainError):
    status_code = status.HTTP_403_FORBIDDEN


class ConflictError(DomainError):
    status_code = status.HTTP_409_CONFLICT


class FilingBlocked(ConflictError):
    """Raised when a transmission is attempted while a gate is unsatisfied.

    There is no override flag. Every path to the IRS runs through these gates.
    """
