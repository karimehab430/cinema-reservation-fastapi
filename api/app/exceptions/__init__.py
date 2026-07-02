from __future__ import annotations


class DomainError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class NotFoundError(DomainError):
    def __init__(self, message: str):
        super().__init__(message, status_code=404)


class ConflictError(DomainError):
    def __init__(self, message: str):
        super().__init__(message, status_code=409)


class AuthenticationError(DomainError):
    def __init__(self, message: str = "Incorrect email or password"):
        super().__init__(message, status_code=401)


class AuthorizationError(DomainError):
    def __init__(self, message: str = "Forbidden"):
        super().__init__(message, status_code=403)


class ValidationError(DomainError):
    def __init__(self, message: str):
        super().__init__(message, status_code=400)


class InvalidTokenError(DomainError):
    def __init__(self, message: str = "Invalid token"):
        super().__init__(message, status_code=401)


class SeatAlreadyReservedError(ConflictError):
    pass
