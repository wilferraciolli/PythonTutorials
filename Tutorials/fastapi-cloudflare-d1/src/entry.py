from fastapi import FastAPI
from workers import asgi

from routers import health, tags, todos

app = FastAPI(title="TODO API", version="1.0.0", description="Runs on Cloudflare Python Workers + D1")

app.include_router(health.router)
app.include_router(tags.router)
app.include_router(todos.router)

# Cloudflare Workers entrypoint: wraps the FastAPI (ASGI) app so the
# Workers runtime can route incoming requests into it.
Default = asgi.entrypoint(app)
