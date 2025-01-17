from typing import Optional

from fastapi import HTTPException, status


class BaseHTTPException(HTTPException):
    """Base class for all http exceptions in this application"""


class BadRequestException(BaseHTTPException):
    def __init__(self, message: Optional[str] = None) -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bad request" if message is None else message,
        )


class ConflictRequestException(BaseHTTPException):
    def __init__(self, message: Optional[str] = None) -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail="Bad request" if message is None else message,
        )


class AlreadyRegisteredException(BaseHTTPException):
    def __init__(self, message: Optional[str] = None) -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already exist" if message is None else message,
        )


class NotFoundException(BaseHTTPException):
    def __init__(self, message: Optional[str] = None) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not found" if message is None else message,
        )


class UnauthorizedException(BaseHTTPException):
    def __init__(self, message: Optional[str] = None) -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized" if message is None else message,
        )


class AlreadyConfirmedException(BaseHTTPException):
    def __init__(self, message: Optional[str] = None) -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already confirmed" if message is None else message,
        )


class InvalidOrExpiredTokenException(BaseHTTPException):
    def __init__(self, message: Optional[str] = None) -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token" if message is None else message,
        )


class ServerErrorException(BaseHTTPException):
    def __init__(self, message: Optional[str] = None) -> None:
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "An error occurred while processing the request" if message is None else message
            ),
        )


class TokenExpiredException(BaseHTTPException):
    def __init__(self, message: Optional[str] = None) -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired" if message is None else message,
        )


class InvalidTokenException(BaseHTTPException):
    def __init__(self, message: Optional[str] = None) -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token" if message is None else message,
        )


class InvalidRoleException(BaseHTTPException):
    def __init__(self, message: Optional[str] = None) -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role" if message is None else message,
        )


class PermissionDeniedException(BaseHTTPException):
    def __init__(self, message: Optional[str] = None) -> None:
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied" if message is None else message,
        )
