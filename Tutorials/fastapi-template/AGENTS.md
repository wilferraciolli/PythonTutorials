# AI agent instructions

Before creating or changing this Python FastAPI app, read the central Python
conventions:

- `../PYTHON_APP_CONVENTIONS.md`

Follow those conventions for:

- local-first FastAPI development with `uvicorn`, `uv`, SQLite, and Docker;
- optional Cloudflare Workers + D1 support;
- router -> service -> repository -> database adapter layering;
- UUID identifiers;
- UTC date formatting;
- response envelopes using `_data`, `_metadata`, `_metaLinks`, and optional `_messages`;
- dynamic metadata and links built in the application service layer;
- `204 No Content` delete responses.

Only deviate from these conventions when the user explicitly asks for a
different approach.
