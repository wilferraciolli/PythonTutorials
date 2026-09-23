from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from api_response import API_PREFIX, envelope
from models import Link, User, UserCreate, UserRole, UserUpdate
from repositories.user_repository import UserRepository


class UserService:
    """
    Application service for users.

    Owns business logic, UUID generation, response envelope creation,
    metadata, links, and templates.
    """

    def __init__(self, user_repository: UserRepository) -> None:
        self.user_repository = user_repository

    async def create_user(self, user: UserCreate) -> User:
        role_ids = self.normalise_role_ids(user.roleIds)
        created = await self.user_repository.create(
            user_id=str(uuid4()),
            name=user.name,
            email=user.email,
            role_ids=role_ids,
            created_date=datetime.now(timezone.utc).isoformat(),
        )

        return self.to_user(created)

    async def get_user(self, user_id: str) -> Optional[User]:
        row = await self.user_repository.get_by_id(user_id)

        if not row:
            return None

        return self.to_user(row)

    async def get_users(self) -> List[User]:
        rows = await self.user_repository.get_all()
        return [self.to_user(row) for row in rows]

    async def update_user(self, user_id: str, user: UserUpdate) -> Optional[User]:
        existing = await self.user_repository.get_by_id(user_id)

        if not existing:
            return None

        role_ids = (
            self.normalise_role_ids(user.roleIds)
            if "roleIds" in user.model_fields_set
            else None
        )

        updated = await self.user_repository.update(
            user_id,
            name=user.name,
            email=user.email,
            roleIds=role_ids,
        )

        return self.to_user(updated)

    def normalise_role_ids(
        self,
        role_ids: Optional[list[UserRole]],
    ) -> list[UserRole]:
        if not role_ids:
            return [UserRole.STANDARD]

        return list(dict.fromkeys(role_ids))

    async def delete_user(self, user_id: str) -> bool:
        return await self.user_repository.delete(user_id)

    def to_user(self, row: Dict[str, Any]) -> User:
        return User(
            id=row["id"],
            external_user_id=row.get("external_user_id"),
            name=row["name"],
            email=row["email"],
            roleIds=row["roleIds"],
            created_date=row["created_date"],
            links=self.build_user_links(row["id"]),
        )

    def build_user_links(self, user_id: str) -> dict[str, Link]:
        return {
            "self": Link(href=f"{API_PREFIX}/users/{user_id}", method="GET"),
            "updateUser": Link(href=f"{API_PREFIX}/users/{user_id}", method="PUT"),
            "deleteUser": Link(href=f"{API_PREFIX}/users/{user_id}", method="DELETE"),
        }

    def build_metadata(self) -> dict[str, Any]:
        return {
            "id": {
                "readOnly": True,
                "hidden": True,
            },
            "external_user_id": {
                "readOnly": True,
                "hidden": True,
            },
            "name": {
                "mandatory": True,
            },
            "email": {
                "mandatory": True,
            },
            "roleIds": {
                "mandatory": True,
                "values": [
                    {
                        "id": UserRole.STANDARD.value,
                        "value": "Standard user",
                    },
                    {
                        "id": UserRole.ADMIN.value,
                        "value": "System Administrator",
                    },
                ],
            },
            "created_date": {
                "readOnly": True,
            },
        }

    def build_meta_links(self) -> dict[str, Link]:
        return {
            "createUser": Link(href=f"{API_PREFIX}/users", method="POST"),
            "userTemplate": Link(href=f"{API_PREFIX}/users/template", method="GET"),
        }

    def build_response(
        self,
        data_key: str,
        data: User | list[User] | dict[str, Any],
        messages: Optional[list[dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        return envelope(
            data_name=data_key,
            data=data,
            metadata=self.build_metadata(),
            meta_links=self.build_meta_links(),
            messages=messages,
        )

    def build_template_response(self) -> Dict[str, Any]:
        return envelope(
            data_name="user",
            data={
                "name": "",
                "email": "",
                "roleIds": [UserRole.STANDARD.value],
            },
            metadata={
                "name": {
                    "mandatory": True,
                },
                "email": {
                    "mandatory": True,
                },
                "roleIds": {
                    "mandatory": True,
                    "values": [
                        {
                            "id": UserRole.STANDARD.value,
                            "value": "Standard user",
                        },
                        {
                            "id": UserRole.ADMIN.value,
                            "value": "System Administrator",
                        },
                    ],
                },
            },
            meta_links={
                "createUser": Link(href=f"{API_PREFIX}/users", method="POST"),
            },
        )