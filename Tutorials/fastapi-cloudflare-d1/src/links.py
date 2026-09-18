from typing import List

from models import Link


def build_todo_links(todo_id: int) -> List[Link]:
    """Navigation links for a Todo: itself, plus tag actions related to it."""
    return [
        Link(name="self", href=f"/todos/{todo_id}", method="GET"),
        Link(name="update", href=f"/todos/{todo_id}", method="PUT"),
        Link(name="delete", href=f"/todos/{todo_id}", method="DELETE"),
        Link(name="addTag", href="/tags", method="POST"),
        Link(name="tags", href=f"/tags?resource_id={todo_id}", method="GET"),
    ]


def build_tag_links(tag_id: int) -> List[Link]:
    """Navigation links for a Tag: itself, and how to remove it."""
    return [
        Link(name="self", href=f"/tags/{tag_id}", method="GET"),
        Link(name="delete", href=f"/tags/{tag_id}", method="DELETE"),
    ]
