from typing import Any

from api_response import envelope
from auth import AuthenticatedUser
from models import Link, Me


class MeService:
    def build_response(self, current_user: AuthenticatedUser) -> dict[str, Any]:
        me = Me(
            id=current_user.id,
            name=current_user.name,
            email=current_user.email,
            roleIds=current_user.role_ids,
            links={
                "self": Link(href="/me", method="GET"),
            },
        )

        return envelope(
            data_name="me",
            data=me,
            metadata={
                "id": {
                    "readOnly": True,
                    "hidden": True,
                },
                "name": {
                    "readOnly": True,
                },
                "email": {
                    "readOnly": True,
                },
                "roleIds": {
                    "readOnly": True,
                },
            },
            meta_links={},
        )
