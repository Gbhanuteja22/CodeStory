import sys
import os
import asyncio
from pathlib import Path
from typing import Optional, List, Dict, Any

try:
    from fastapi import FastAPI, HTTPException, BackgroundTasks
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import FileResponse
    from pydantic import BaseModel
    import uvicorn
except ImportError as e:
    print(f"Missing dependencies. Please run: python -m pip install fastapi uvicorn[standard] pydantic python-multipart")
    print(f"Error: {e}")
    sys.exit(1)

import json

from tutorial_builder import DocumentationGenerator
from pipeline_orchestrator import DocumentationWorkflow

app = FastAPI(title="Documentation Generator API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class GenerationRequest(BaseModel):
    repo_url: Optional[str] = None
    local_path: Optional[str] = None
    project_name: Optional[str] = None
    language: str = "english"
    include_patterns: List[str] = []
    exclude_patterns: List[str] = []
    max_file_size: int = 150000
    max_abstractions: int = 10
    use_cache: bool = True

class GenerationStatus(BaseModel):
    task_id: str
    status: str
    progress: int
    message: str
    output_path: Optional[str] = None
    error: Optional[str] = None

generation_tasks: Dict[str, GenerationStatus] = {}

frontend_dir = os.path.join(os.path.dirname(__file__), "webapp", "frontend")
if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

@app.get("/")
async def read_index():
    frontend_file = os.path.join(os.path.dirname(__file__), "webapp", "frontend", "index.html")
    if os.path.exists(frontend_file):
        return FileResponse(frontend_file)
    return {"message": "Documentation Generator API", "status": "running", "frontend": "not available"}

@app.get("/health")
async def health_check():
    return {"message": "Documentation Generator API", "status": "running"}

@app.post("/generate")
async def generate_documentation(request: GenerationRequest, background_tasks: BackgroundTasks):
    import uuid
    task_id = str(uuid.uuid4())
    
    if not request.repo_url and not request.local_path:
        raise HTTPException(status_code=400, detail="Either repo_url or local_path must be provided")
    
    generation_tasks[task_id] = GenerationStatus(
        task_id=task_id,
        status="queued",
        progress=0,
        message="Task queued for processing"
    )
    
    background_tasks.add_task(run_generation, task_id, request)
    
    return {"task_id": task_id, "status": "queued"}

async def run_generation(task_id: str, request: GenerationRequest):
    try:
        generation_tasks[task_id].status = "running"
        generation_tasks[task_id].message = "Initializing documentation generation"
        generation_tasks[task_id].progress = 5
        
        # Create output directory with timestamp to avoid conflicts
        import time
        timestamp = int(time.time())
        output_dir = f"./output/webapp_generation_{timestamp}"
        
        generation_tasks[task_id].message = "Setting up workspace configuration"
        generation_tasks[task_id].progress = 10
        
        # Setup workspace configuration like in tutorial_builder.py
        workspace_config = {
            "source_repository": request.repo_url,
            "local_filesystem_path": request.local_path,
            "project_identifier": request.project_name,
            "github_api_token": os.getenv('GITHUB_TOKEN'),
            "documentation_output_path": output_dir,
            "included_file_patterns": set(request.include_patterns) if request.include_patterns else {
                "*.py", "*.js", "*.jsx", "*.ts", "*.tsx", "*.go", "*.java", "*.pyi", "*.pyx",
                "*.c", "*.cc", "*.cpp", "*.h", "*.md", "*.rst", "*Dockerfile",
                "*Makefile", "*.yaml", "*.yml"
            },
            "excluded_file_patterns": set(request.exclude_patterns) if request.exclude_patterns else {
                "assets/*", "data/*", "images/*", "public/*", "static/*", "temp/*",
                "*docs/*", "*venv/*", "*.venv/*", "*test*", "*tests/*", "*examples/*",
                "v1/*", "*dist/*", "*build/*", "*experimental/*", "*deprecated/*",
                "*misc/*", "*legacy/*", ".git/*", ".github/*", ".next/*", ".vscode/*",
                "*obj/*", "*bin/*", "*node_modules/*", "*.log"
            },
            "maximum_file_size_bytes": request.max_file_size,
            "target_language": request.language,
            "enable_ai_caching": request.use_cache,
            "maximum_concept_count": request.max_abstractions,
            "discovered_files": [],
            "identified_concepts": [],
            "concept_relationships": {},
            "chapter_sequence": [],
            "generated_chapters": [],
            "final_documentation_path": None
        }
        
        generation_tasks[task_id].message = "Creating documentation generator"
        generation_tasks[task_id].progress = 15
        
        generator = DocumentationGenerator()
        
        generation_tasks[task_id].message = "Configuring workspace"
        generation_tasks[task_id].progress = 20
        
        generator.configure_workspace(workspace_config)
        
        generation_tasks[task_id].message = "Starting documentation generation pipeline"
        generation_tasks[task_id].progress = 30
        
        # Run the documentation generation in a thread
        def run_generation_sync():
            try:
                return generator.build_documentation()
            except Exception as e:
                print(f"Generation error: {e}")
                raise e
        
        # Update progress during generation
        generation_tasks[task_id].message = "Scanning codebase and identifying concepts"
        generation_tasks[task_id].progress = 40
        
        # Run the generation
        output_location = await asyncio.get_event_loop().run_in_executor(
            None, run_generation_sync
        )
        
        generation_tasks[task_id].message = "Finalizing documentation"
        generation_tasks[task_id].progress = 90
        
        # Check if generation was successful
        # The output might be in a subdirectory with the project name
        output_path = Path(output_dir)
        generated_files = list(output_path.rglob("*.md"))  # Search recursively for any .md files
        
        if generated_files:
            # Find the actual directory containing the files (might be a subdirectory)
            actual_output_dir = generated_files[0].parent
            generation_tasks[task_id].output_path = str(actual_output_dir)
            generation_tasks[task_id].status = "completed"
            generation_tasks[task_id].progress = 100
            generation_tasks[task_id].message = f"Documentation generated successfully! Created {len(generated_files)} files."
        else:
            raise Exception("Generation completed but no documentation files were created")
            
    except Exception as e:
        import traceback
        error_msg = str(e)
        traceback_str = traceback.format_exc()
        print(f"Generation error for task {task_id}: {error_msg}")
        print(f"Traceback: {traceback_str}")
        
        generation_tasks[task_id].status = "failed"
        generation_tasks[task_id].error = error_msg
        generation_tasks[task_id].message = f"Generation failed: {error_msg}"

@app.get("/status/{task_id}")
async def get_generation_status(task_id: str):
    if task_id not in generation_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    return generation_tasks[task_id]

@app.get("/tasks")
async def list_tasks():
    return list(generation_tasks.values())

@app.delete("/tasks/{task_id}")
async def delete_task(task_id: str):
    if task_id not in generation_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    del generation_tasks[task_id]
    return {"message": "Task deleted"}

@app.get("/output/{task_id}")
async def get_output_files(task_id: str):
    if task_id not in generation_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = generation_tasks[task_id]
    if task.status != "completed" or not task.output_path:
        raise HTTPException(status_code=400, detail="Task not completed or no output available")
    
    output_path = Path(task.output_path)
    if not output_path.exists():
        raise HTTPException(status_code=404, detail="Output directory not found")
    
    files = []
    for file_path in output_path.rglob("*.md"):
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        files.append({
            "filename": file_path.name,
            "path": str(file_path.relative_to(output_path)),
            "content": content
        })
    
    return {"files": files, "output_directory": str(output_path)}

if __name__ == "__main__":
    print("🚀 Starting Documentation Generator Webapp...")
    print("📖 Web interface: http://localhost:8000")
    print("🔧 API docs: http://localhost:8000/docs")
    print("⚡ Your existing CLI remains untouched at codestory.py")
    print()
    print("Press Ctrl+C to stop the server")
    print("=" * 50)
    
    try:
        uvicorn.run(app, host="127.0.0.1", port=8000, reload=False, log_level="info")
    except KeyboardInterrupt:
        print("\n👋 Server stopped")
    except Exception as e:
        print(f"Error starting server: {e}")
        print("Make sure you have installed the dependencies:")
        print("python -m pip install fastapi uvicorn[standard] pydantic python-multipart")
