from fastapi import APIRouter

router = APIRouter(prefix="/health")

# Health check
@router.get("/")
def health_check():
    return {"status": "API is running"}