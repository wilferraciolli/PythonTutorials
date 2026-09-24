from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4



class UserSettingsService:
    """
    Application service for user settings.
    """

    def __init__(self, user_repository: UserRepository) -> None:
        self.user_repository = user_repository