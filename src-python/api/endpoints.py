"""
Simple API endpoints
"""

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import asyncio
import json
import time

router = APIRouter()

class FibonacciRequest(BaseModel):
    number: int

@router.get("/connect")
async def connect():
    """Simple connect endpoint"""
    return {
        "success": True,
        "message": "Connected to Python sidecar",
        "host": "127.0.0.1:8008"
    }

@router.post("/fibonacci")
async def calculate_fibonacci(request: FibonacciRequest):
    """Calculate fibonacci number"""
    def fib(n):
        if n <= 1:
            return n
        return fib(n - 1) + fib(n - 2)
    
    start_time = time.time()
    result = fib(request.number)
    end_time = time.time()
    
    return {
        "success": True,
        "input": request.number,
        "result": result,
        "calculation_time": f"{end_time - start_time:.4f}s"
    }

@router.get("/stream")
async def stream_data():
    """Stream numbers 1-10 with delay"""
    async def generate():
        for i in range(1, 11):
            data = json.dumps({"count": i, "message": f"Streaming item {i}"}) + "\n"
            yield data
            await asyncio.sleep(0.5)
    
    return StreamingResponse(generate(), media_type="text/plain") 