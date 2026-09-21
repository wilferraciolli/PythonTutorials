# 06 - Standard API Response Payload

This document defines the response payload pattern used by this API and
intended to be reused in future Python/FastAPI projects.

The goal is to return data in a predictable shape while also giving the client
enough information to render forms, buttons, links, and valid dropdown values
without hardcoding those rules in the UI.

## 1. Standard response shape

Most successful API responses return this envelope:

```json
{
  "_data": {},
  "_metadata": {},
  "_metaLinks": {}
}
```

Optional:

```json
{
  "_messages": []
}
```

`_messages` is only returned when the service has a useful message to show.
Do **not** return an empty `_messages: []` on every response.

Delete endpoints are the main exception:

```text
DELETE /todos/{id} -> 204 No Content
DELETE /tags/{id}  -> 204 No Content
```

Deletes should not return the envelope, because `204 No Content` means there
is intentionally no response body.

## 2. `_data`

`_data` contains the real business payload.

For a single resource:

```json
{
  "_data": {
    "todo": {
      "id": 123,
      "title": "Learn FastAPI"
    }
  }
}
```

For a list:

```json
{
  "_data": {
    "todos": [
      {
        "id": 123,
        "title": "Learn FastAPI"
      }
    ]
  }
}
```

The key inside `_data` should describe the resource:

| Scenario | `_data` key |
|---|---|
| Single todo | `todo` |
| Todo list | `todos` |
| Todo template | `todo` |
| Single tag | `tag` |
| Tag list | `tags` |
| Tag template | `tag` |

## 3. Resource-level `links`

Each resource DTO may include a `links` object.

Example:

```json
{
  "id": 123,
  "title": "Learn FastAPI",
  "links": {
    "self": {
      "href": "/todos/123",
      "method": "GET"
    },
    "update": {
      "href": "/todos/123",
      "method": "PUT"
    },
    "delete": {
      "href": "/todos/123",
      "method": "DELETE"
    },
    "addTag": {
      "href": "/tags",
      "method": "POST"
    },
    "tags": {
      "href": "/tags?resource_id=123",
      "method": "GET"
    }
  }
}
```

These links should be built in the application service layer on every request.
They are not static, because the available actions can depend on:

- current user permissions
- current resource state
- tenant rules
- business workflow rules

Example:

If the current user cannot delete a todo, the service should simply omit the
`delete` link from that todo response.

## 4. `_metadata`

`_metadata` describes how the client should treat fields.

It is **not** a duplicate schema for every field. Optional fields do not need
metadata unless there is something meaningful to tell the client.

Use metadata for things like:

- field is mandatory
- field is read-only
- field should be hidden
- field has available values
- field is disabled because of business rules

Example:

```json
{
  "_metadata": {
    "id": {
      "readOnly": true,
      "hidden": true
    },
    "title": {
      "mandatory": true
    },
    "complete_by": {
      "mandatory": true
    },
    "state": {
      "mandatory": true,
      "values": [
        {
          "id": "NEW",
          "value": "New"
        },
        {
          "id": "ACTIVE",
          "value": "Active"
        },
        {
          "id": "CLOSED",
          "value": "Closed"
        }
      ]
    },
    "created_date": {
      "readOnly": true
    }
  }
}
```

Important: metadata must be calculated by the application service layer per
request.

Example business rule:

- If a todo is `NEW`, state values may include `NEW`, `ACTIVE`, `CLOSED`.
- If a todo is already `ACTIVE`, state values should not include `NEW`.

So this:

```json
"state": {
  "mandatory": true,
  "values": [
    { "id": "ACTIVE", "value": "Active" },
    { "id": "CLOSED", "value": "Closed" }
  ]
}
```

is valid for an already-started todo.

## 5. `_metaLinks`

`_metaLinks` describes collection-level or page-level actions.

Example:

```json
{
  "_metaLinks": {
    "createTodo": {
      "href": "/todos",
      "method": "POST"
    }
  }
}
```

Use `_metaLinks` for links that are not tied to a single resource instance.

Examples:

| Link | Meaning |
|---|---|
| `createTodo` | Create a todo |
| `createTag` | Create a tag |
| `todoTemplate` | Get a blank todo template |
| `tagTemplate` | Get a blank tag template |

Like resource-level `links`, `_metaLinks` should be calculated by the
application service layer per request. If the user cannot create a resource,
omit the create link.

## 6. Templates

Each API should expose a template endpoint for create screens.

Examples:

```text
GET /todos/template
GET /tags/template
```

Templates return the same response envelope as normal GET endpoints, but with
default/empty values in `_data`.

Example todo template:

```json
{
  "_data": {
    "todo": {
      "id": 0,
      "title": "",
      "description": "",
      "complete_by": "2026-09-21T12:00:00Z",
      "state": "NEW",
      "created_date": "2026-09-21T12:00:00Z",
      "links": {}
    }
  },
  "_metadata": {
    "id": {
      "readOnly": true,
      "hidden": true
    },
    "title": {
      "mandatory": true
    },
    "complete_by": {
      "mandatory": true
    },
    "state": {
      "mandatory": true,
      "values": [
        { "id": "NEW", "value": "New" },
        { "id": "ACTIVE", "value": "Active" },
        { "id": "CLOSED", "value": "Closed" }
      ]
    },
    "created_date": {
      "readOnly": true
    }
  },
  "_metaLinks": {
    "createTodo": {
      "href": "/todos",
      "method": "POST"
    }
  }
}
```

The Tags API should also have a template because creating a tag requires the
client to know:

- `resource_id` is mandatory
- `tag` is mandatory
- `id` is read-only/hidden
- `created_date` is read-only

Example tag template:

```json
{
  "_data": {
    "tag": {
      "id": 0,
      "resource_id": 0,
      "tag": "",
      "created_date": "2026-09-21T12:00:00Z",
      "links": {}
    }
  },
  "_metadata": {
    "id": {
      "readOnly": true,
      "hidden": true
    },
    "resource_id": {
      "mandatory": true
    },
    "tag": {
      "mandatory": true
    },
    "created_date": {
      "readOnly": true
    }
  },
  "_metaLinks": {
    "createTag": {
      "href": "/tags",
      "method": "POST"
    }
  }
}
```

## 7. Where the logic belongs

Keep responsibilities separate:

| Layer | Responsibility |
|---|---|
| Router | HTTP routing, path/query/body params, HTTP status codes, 404 handling |
| Application service | Business logic, DTO construction, metadata, links, messages |
| Repository | Database reads/writes only |
| `api_response.py` | Dumb envelope helper only |

The router should not decide if a field is mandatory, hidden, disabled, or
which links are allowed. That belongs in the application service because it is
business logic.

Good router shape:

```python
@router.get("/{todo_id}")
async def get_todo(todo_id: int, service: TodoService = Depends(get_todo_service)):
    todo = await service.get_todo(todo_id)
    if not todo:
        raise HTTPException(status_code=404, detail=f"TODO {todo_id} not found")
    return service.build_response("todo", todo)
```

Good service shape:

```python
def build_response(self, data_name: str, data: Any, messages: Optional[list] = None):
    return envelope(
        data_name,
        data,
        self._metadata(data if isinstance(data, Todo) else None),
        self._meta_links(),
        messages,
    )
```

## 8. Rules to reuse in future projects

1. Use `_data` for the business payload.
2. Use `_metadata` only for fields with client-relevant rules.
3. Optional fields do not need metadata unless there is a rule to communicate.
4. Use `values` to tell the client which values are available now.
5. Use resource-level `links` for actions on a specific resource.
6. Use `_metaLinks` for collection/page actions.
7. Build metadata and links in the application service layer per request.
8. Omit `_messages` unless there are real messages.
9. Use `204 No Content` for successful deletes.
10. Add a `/template` endpoint for every createable API resource.

## 9. Date format

All dates returned by the API must be:

- UTC
- seconds precision only
- formatted as `YYYY-MM-DDTHH:MM:SSZ`

Example:

```json
{
  "complete_by": "2027-01-01T12:34:56Z",
  "created_date": "2026-09-21T12:25:40Z"
}
```

Do not return:

```json
{
  "created_date": "2026-09-21T12:25:40.123456+00:00"
}
```

In this project the rule is implemented in `models.py` with a shared
`format_utc_datetime(...)` helper and Pydantic field serializers on the
response DTOs (`Todo`, `Tag`).
