from core.common.errors import AppError


class SelfLockoutError(AppError):
    """
    Raised when an admin tries to remove their own ADMIN role or delete
    themselves — either could leave the system with no admin. Answered with
    a 400 (core.common.errors).
    """
