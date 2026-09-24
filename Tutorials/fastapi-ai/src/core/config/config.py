import os
from pathlib import Path
from typing import Optional

from fastapi import Request


def _load_dotenv() -> None:
    """Load the project's .env (in the working directory) for plain uvicorn/local runs, if one exists."""
    env_path = Path.cwd() / ".env"
    if not env_path.exists():
        return

    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_dotenv()


def get_config(request: Request, key: str, default: Optional[str] = None) -> Optional[str]:
    """
    Read config from either the Worker env object or process environment.

    Cloudflare injects bindings/config into request.scope["env"], while plain
    uvicorn/Docker uses environment variables loaded from .env/docker-compose.
    """
    env = request.scope.get("env")
    if env is not None:
        try:
            value = getattr(env, key)
            if value is not None:
                return str(value)
        except AttributeError:
            pass

    return os.environ.get(key, default)
