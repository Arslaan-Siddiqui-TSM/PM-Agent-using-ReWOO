from fastapi import APIRouter
import time

router = APIRouter()

# Health Check
@router.get("/")
async def health_check():
    """Check if the API is running"""
    return {
        "status": "healthy",
        "service": "Reflection Agent API",
        "version": "2.0.0",
        "pattern": "draft→critique→revise",
        "timestamp": time.time()
    }
