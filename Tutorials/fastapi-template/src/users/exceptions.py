class SelfLockoutError(Exception):
    """
    Raised when an admin tries to remove their own ADMIN role or delete
    themselves — either could leave the system with no admin. The router
    turns it into a 400.
    """
