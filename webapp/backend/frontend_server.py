from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

def serve_frontend(app: FastAPI):
    frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
    
    if os.path.exists(frontend_dir):
        app.mount("/static", StaticFiles(directory=frontend_dir), name="static")
        
        @app.get("/")
        async def read_index():
            return FileResponse(os.path.join(frontend_dir, "index.html"))
    
    return app
