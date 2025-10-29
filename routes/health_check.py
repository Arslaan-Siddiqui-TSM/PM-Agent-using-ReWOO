from fastapi import APIRouter
import time

router = APIRouter()

# Health Check
@router.get("/")
async def health_check():
    """Check if the API is running"""
    return {
        "status": "healthy",
        "service": "ReWOO Agent API",
        "timestamp": time.time()
    }
