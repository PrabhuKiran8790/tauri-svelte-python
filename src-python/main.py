"""
FastAPI Server for Tauri + SvelteKit
Supports both sidecar mode (with stdin handling) and standalone mode (with auto-reload)
"""

import os
import signal
import sys
import asyncio
import threading
import socket
import subprocess
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from uvicorn import Config, Server

from api.endpoints import router as api_router

PORT_API = 8009
server_instance = None

# Detect running mode
def is_standalone_mode():
    """Detect if running in standalone mode vs sidecar mode"""
    return (
        "--standalone" in sys.argv or 
        "--reload" in sys.argv or
        os.getenv("STANDALONE_MODE", "").lower() == "true" or
        os.getenv("UVICORN_RELOAD", "").lower() == "true"
    )

STANDALONE_MODE = is_standalone_mode()
mode_label = "standalone" if STANDALONE_MODE else "sidecar"

# Create FastAPI app
app = FastAPI(title="Test App API", version="1.0.0")

# Add CORS
cors_origins = [
    "http://localhost:5173",  # SvelteKit dev server
    "http://localhost:1420",  # Tauri dev server
    "http://127.0.0.1:5173",
    "http://127.0.0.1:1420",
    "tauri://localhost"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/v1")

@app.get("/")
async def root():
    return {
        "message": "Test App API", 
        "status": "running",
        "mode": mode_label,
        "port": PORT_API
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "mode": mode_label}

def is_port_available(port):
    """Check if a port is available"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('127.0.0.1', port))
            return True
        except OSError:
            return False

def find_available_port():
    """Find an available port starting from PORT_API"""
    port = PORT_API
    while port < PORT_API + 10:  # Try 10 ports
        if is_port_available(port):
            print(f"[{mode_label}] Using available port {port}", flush=True)
            return port
        port += 1
    
    # If no port is available, use the default
    print(f"[{mode_label}] No available ports found, using default {PORT_API}", flush=True)
    return PORT_API

def start_api_server(**kwargs):
    """Start the FastAPI server"""
    global server_instance
    port = kwargs.get("port", find_available_port())
    
    try:
        if server_instance is None:
            print(f"[{mode_label}] Starting API server on port {port}...", flush=True)
            print(f"[{mode_label}] Server will be available at http://127.0.0.1:{port}", flush=True)
            
            config = Config(app, host="127.0.0.1", port=port, log_level="info")
            server_instance = Server(config)
            asyncio.run(server_instance.serve())
        else:
            print(f"[{mode_label}] Server instance already running.", flush=True)
    except Exception as e:
        print(f"[{mode_label}] Error starting API server on port {port}: {e}", flush=True)

def stdin_loop():
    """Handle stdin commands in sidecar mode"""
    print(f"[{mode_label}] Waiting for commands...", flush=True)
    while True:
        try:
            user_input = sys.stdin.readline().strip()
            if user_input == "sidecar shutdown":
                print(f"[{mode_label}] Received 'sidecar shutdown' command.", flush=True)
                os.kill(os.getpid(), signal.SIGINT)
            else:
                print(f"[{mode_label}] Invalid command [{user_input}]. Try again.", flush=True)
        except EOFError:
            break
        except Exception as e:
            print(f"[{mode_label}] Error in stdin loop: {e}", flush=True)
            break

def start_input_thread():
    """Start stdin monitoring thread (only in sidecar mode)"""
    if not STANDALONE_MODE:
        try:
            input_thread = threading.Thread(target=stdin_loop, daemon=True)
            input_thread.start()
        except Exception as e:
            print(f"[{mode_label}] Failed to start input handler: {e}", flush=True)

def run_standalone():
    """Run in standalone mode with uvicorn auto-reload"""
    port = find_available_port()
    
    print(f"🚀 Starting standalone development mode")
    print(f"🔗 API server starting at http://127.0.0.1:{port}")
    print(f"📖 API docs will be at http://127.0.0.1:{port}/docs")
    print(f"🔄 Auto-reload enabled")
    print(f"💡 Press Ctrl+C to stop\n")
    
    try:
        uvicorn.run(
            "main:app", 
            host="127.0.0.1", 
            port=port, 
            reload=True,
            reload_dirs=["./"],
            reload_excludes=["*.pyc", "__pycache__", "*.log"],
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error starting API server: {e}")
        sys.exit(1)

def run_sidecar():
    """Run in sidecar mode with stdin handling"""
    start_input_thread()
    start_api_server()

if __name__ == "__main__":
    if STANDALONE_MODE:
        run_standalone()
    else:
        run_sidecar()