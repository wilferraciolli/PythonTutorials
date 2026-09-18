from fastapi import APIRouter

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
def health_check():
    return {"status": "API is running", "runtime": "Cloudflare Python Workers + D1"}
