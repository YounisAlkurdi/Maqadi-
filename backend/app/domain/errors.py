"""Domain errors mapped to HTTP responses in the interfaces layer."""


class DomainError(Exception):
    """Base class for all domain-level errors."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)


class NotFoundError(DomainError):
    """Requested resource does not exist or is not accessible."""

    def __init__(self, message: str = "Resource not found", code: str = "not_found") -> None:
        super().__init__(code=code, message=message)


class InvalidTransitionError(DomainError):
    """Illegal item status transition."""

    def __init__(
        self,
        message: str = "Invalid status transition",
        code: str = "invalid_transition",
    ) -> None:
        super().__init__(code=code, message=message)


class DuplicateItemError(DomainError):
    """An open item with the same normalized name already exists in the household."""

    def __init__(
        self,
        message: str = "Item already exists in the open list",
        existing_item_id: str | None = None,
        code: str = "duplicate_item",
    ) -> None:
        self.existing_item_id = existing_item_id
        super().__init__(code=code, message=message)


class ForbiddenError(DomainError):
    """Action is not permitted for the current actor."""

    def __init__(self, message: str = "Forbidden", code: str = "forbidden") -> None:
        super().__init__(code=code, message=message)


class UnauthorizedError(DomainError):
    """Authentication is missing or invalid."""

    def __init__(self, message: str = "Unauthorized", code: str = "unauthorized") -> None:
        super().__init__(code=code, message=message)


class RateLimitedError(DomainError):
    """Too many attempts; caller must wait."""

    def __init__(
        self,
        message: str = "Too many attempts, please try again later",
        code: str = "rate_limited",
    ) -> None:
        super().__init__(code=code, message=message)


class ValidationError(DomainError):
    """Domain validation failure."""

    def __init__(self, message: str, code: str = "validation_error") -> None:
        super().__init__(code=code, message=message)
