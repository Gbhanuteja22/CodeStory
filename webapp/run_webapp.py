import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from webapp.backend.app import app
from webapp.backend.frontend_server import serve_frontend

app = serve_frontend(app)

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Documentation Generator Webapp...")
    print("📖 Web interface: http://localhost:8000")
    print("🔧 API docs: http://localhost:8000/docs")
    print("⚡ Your existing CLI remains untouched at codestory.py")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
