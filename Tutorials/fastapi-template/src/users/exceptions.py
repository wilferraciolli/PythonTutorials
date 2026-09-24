class SelfLockoutError(Exception):
    """
    Raised when an admin tries to remove their own ADMIN role or delete
    themselves — either could leave the system with no admin. The router
    turns it into a 400.
    """


class NotOwnerError(Exception):
    """
    Raised when a caller acts on a personal resource (e.g. another user's
    settings) that only its owner may use. The router turns it into a 403.
    """
