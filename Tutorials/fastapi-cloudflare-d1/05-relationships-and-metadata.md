# 05 - Relationships and Metadata

This document explains how the API represents relationships between
resources (Todo ↔ Tag) and how it attaches navigation metadata (`links`) to
responses — a lightweight version of the **HATEOAS** ("Hypermedia as the
Engine of Application State") REST principle.

## 1. The relationship: Todo ↔ Tag

A `Tag` is a **generic** annotation that can point at *any* resource, not
just a Todo. It does this with a simple foreign-key-style column:

```sql
CREATE TABLE tags (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    resource_id   INTEGER NOT NULL,   -- points at ANY resource's id
    tag           TEXT NOT NULL,
    created_date  TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX idx_resource_tag ON tags(resource_id, tag);
```

- `resource_id` is **not** a strict SQL foreign key to `todos(id)` on
  purpose — this keeps `tags` reusable for other resource types later
  (comments, projects, etc.) without a schema change or a `resource_type`
  discriminator column (which we may add later if truly needed).
- The unique index on `(resource_id, tag)` enforces "no duplicate tag name
  per resource" at the database level — the cheapest, most reliable place to
  guarantee that invariant (better than only checking it in application
  code, which could race under concurrent requests).

### One-to-many, not many-to-many

This is a **one-to-many** relationship (one todo → many tags), not
many-to-many. There's no join table because a tag row *is* the join: it
directly stores which resource it belongs to. If we ever needed the same
tag *name* shared/reused as a distinct entity across resources (e.g. a
"Tag" table with its own metadata, joined via a `todo_tags` bridge table),
that would become many-to-many — but that's more complexity than this
feature currently needs.

### Auto-tagging (business rule → relationship side effect)

Tags aren't only created manually — `TodoService` automatically keeps a
couple of tags in sync with a todo's state, and cleans them up when the todo
is deleted:

| Trigger | Effect |
|---|---|
| Todo created/updated/patched, `complete_by` in the past | add `"overdue"`, remove `"not-started"` |
| Todo created/updated/patched, `complete_by` in the future and `state == NEW` | add `"not-started"`, remove `"overdue"` |
| Todo deleted | delete **all** tags where `resource_id == todo.id` |

This is implemented as **cascade-by-application-code**, not a SQL
`ON DELETE CASCADE` foreign key — because `resource_id` isn't a real FK (see
above). `TodoService.delete_todo()` explicitly calls
`TagService.delete_all_tags_for_resource(todo_id)` after a successful
delete, so orphaned tags never accumulate.

## 2. Metadata: the shared `links` field

Every response DTO (`Todo`, `Tag`, and any future resource) includes a
`links` array describing related actions the client can take next — without
the client needing to hardcode URL patterns.

### Example response

```json
{
  "id": 2,
  "title": "Link Test",
  "description": null,
  "complete_by": "2027-01-01T00:00:00",
  "state": "NEW",
  "created_date": "2026-09-18T15:30:48.831000Z",
  "links": [
    { "name": "self",   "href": "/todos/2",             "method": "GET" },
    { "name": "update", "href": "/todos/2",             "method": "PUT" },
    { "name": "delete", "href": "/todos/2",             "method": "DELETE" },
    { "name": "addTag", "href": "/tags",                "method": "POST" },
    { "name": "tags",   "href": "/tags?resource_id=2",  "method": "GET" }
  ]
}
```

### How it's built (shared, reusable)

**`models.py`** — one shared `Link` model, and a `LinkedResource` base class
that any DTO can inherit from to get a `links` field for free:

```python
class Link(BaseModel):
    name: str
    href: str
    method: str = "GET"

class LinkedResource(BaseModel):
    links: List[Link] = Field(default_factory=list)

class Todo(LinkedResource):
    id: int
    title: str
    # ...

class Tag(LinkedResource):
    id: int
    tag: str
    # ...
```

**`links.py`** — small, pure functions that build the right list of links
for a given resource id. No database access, no side effects — just a
lookup table of "what actions exist for this resource":

```python
def build_todo_links(todo_id: int) -> List[Link]:
    return [
        Link(name="self",   href=f"/todos/{todo_id}", method="GET"),
        Link(name="update", href=f"/todos/{todo_id}", method="PUT"),
        Link(name="delete", href=f"/todos/{todo_id}", method="DELETE"),
        Link(name="addTag", href="/tags",             method="POST"),
        Link(name="tags",   href=f"/tags?resource_id={todo_id}", method="GET"),
    ]

def build_tag_links(tag_id: int) -> List[Link]:
    return [
        Link(name="self",   href=f"/tags/{tag_id}", method="GET"),
        Link(name="delete", href=f"/tags/{tag_id}", method="DELETE"),
    ]
```

**Services** attach the links at the same point they convert a raw D1 row
into a Pydantic model (`_row_to_todo` / `_row_to_tag`), so every code path
that returns a `Todo` or `Tag` — create, get, update, list — automatically
includes correct links with zero extra effort per-endpoint.

### Why this approach?

- **Single source of truth**: link-building logic lives in one file
  (`links.py`), not scattered across every router.
- **Reusable across resources**: `LinkedResource` means adding `links` to a
  brand-new DTO later is a one-line inheritance change, not a
  copy-pasted field.
- **Discoverability for API clients**: a client can follow `links` instead
  of hardcoding URL patterns — if a route ever changes, only `links.py`
  needs updating.
- **Cheap to compute**: links are just string formatting (no DB calls), so
  attaching them costs virtually nothing per request.

### What's intentionally *not* done (yet)

- No `_links` HAL-style nesting (`{"_links": {"self": {"href": ...}}}`) —
  we used a flat `links: [...]` array instead, which is simpler to read and
  matches what was asked for.
- No pagination links (`next`/`prev`) — not needed yet since `GET /todos`
  and `GET /tags` return full lists, not paged ones.
- No `resource_type` column on `tags` — deferred until there's a second
  taggable resource that actually needs to disambiguate ids that might
  collide across resource types.
