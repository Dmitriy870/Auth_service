from fastapi import HTTPException, status


class AlreadyRegisteredHTTPException(HTTPException):
    def __init__(self, detail: str = "Already registered"):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)


class NotFoundHTTPException(HTTPException):
    def __init__(self, detail: str = "Not found"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class UnauthorizedHTTPException(HTTPException):
    def __init__(self, detail: str = "Unauthorized"):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


class ServerErrorHTTPException(HTTPException):
    def __init__(self, detail: str = "Internal server error"):
        super().__init__(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail)


class InvalidOrExpiredTokenHTTPException(HTTPException):
    def __init__(self, detail: str = "Invalid or expired token"):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


class PermissionDeniedHTTPException(HTTPException):
    def __init__(self, detail: str = "Permission denied"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class BadRequestHTTPException(HTTPException):
    def __init__(self, detail: str = "Bad request"):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class ErrorCallingFileServiceHTTPException(HTTPException):
    def __init__(self, detail: str = "Error Calling File Service"):
        super().__init__(status_code=status.HTTP_502_BAD_GATEWAY, detail=detail)


class AlreadyRegisteredException(Exception):
    pass


class NotFoundException(Exception):
    pass


class UnauthorizedException(Exception):
    pass


class ServerErrorException(Exception):
    pass


class TokenExpiredException(Exception):
    pass


class InvalidTokenException(Exception):
    pass


class AlreadyConfirmedException(Exception):
    pass


class BadRequestException(Exception):
    pass


class InvalidOrExpiredTokenException(Exception):
    pass


class PermissionDeniedException(Exception):
    pass


class InvalidRoleException(Exception):
    pass


class ErrorCallingFileService(Exception):
    pass
