from core.common.errors import AppError, ForbiddenError


class SelfLockoutError(AppError):
    """
    Raised when an admin tries to remove their own ADMIN role or delete
    themselves — either could leave the system with no admin. Answered with
    a 400 (core.common.errors).
    """


class NotOwnerError(ForbiddenError):
    """
    Raised when a caller acts on a personal resource (e.g. another user's
    settings) that only its owner may use. Answered with a 403.
    """
