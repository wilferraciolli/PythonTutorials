from workers import asgi

from main import app

# Cloudflare Workers entrypoint: wraps the FastAPI (ASGI) app so the
# Workers runtime can route incoming requests into it.
Default = asgi.entrypoint(app)
