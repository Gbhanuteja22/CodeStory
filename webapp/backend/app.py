import sys
import os
import asyncio
from pathlib import Path
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import Response
from pydantic import BaseModel
import json
import base64

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
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
    output_dir: str = "./output"
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

class PDFRequest(BaseModel):
    content: str
    filename: str = "tutorial"
    title: str = "Tutorial"

generation_tasks: Dict[str, GenerationStatus] = {}

@app.get("/")
async def root():
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
        generation_tasks[task_id].message = "Starting documentation generation"
        generation_tasks[task_id].progress = 10
        
        class ProgressCallback:
            def __init__(self, task_id: str):
                self.task_id = task_id
                self.current_step = 0
                self.total_steps = 6
            
            def update(self, step_name: str, progress: int = None):
                if progress is None:
                    self.current_step += 1
                    progress = int((self.current_step / self.total_steps) * 80) + 10
                
                generation_tasks[self.task_id].progress = min(progress, 90)
                generation_tasks[self.task_id].message = f"Processing: {step_name}"
        
        callback = ProgressCallback(task_id)
        
        generator = DocumentationGenerator()
        workflow = DocumentationWorkflow()
        
        args_dict = {
            'repo': request.repo_url,
            'dir': request.local_path,
            'name': request.project_name,
            'output': request.output_dir,
            'language': request.language,
            'include': request.include_patterns,
            'exclude': request.exclude_patterns,
            'max_size': request.max_file_size,
            'max_abstractions': request.max_abstractions,
            'no_cache': not request.use_cache,
            'token': os.getenv('GITHUB_TOKEN')
        }
        
        generator.configure_workspace(args_dict)
        callback.update("Workspace configured")
        
        pipeline = workflow.create_processing_pipeline()
        callback.update("Processing pipeline created")
        
        result = await asyncio.get_event_loop().run_in_executor(
            None, pipeline.run, workspace
        )
        
        if result and hasattr(result, 'get') and result.get('output_directory'):
            output_path = result['output_directory']
            generation_tasks[task_id].output_path = str(output_path)
            generation_tasks[task_id].status = "completed"
            generation_tasks[task_id].progress = 100
            generation_tasks[task_id].message = "Documentation generated successfully"
        else:
            raise Exception("Generation completed but no output directory found")
            
    except Exception as e:
        generation_tasks[task_id].status = "failed"
        generation_tasks[task_id].error = str(e)
        generation_tasks[task_id].message = f"Generation failed: {str(e)}"

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

@app.post("/generate-pdf")
async def generate_pdf(request: PDFRequest):
    """Generate PDF-ready HTML from markdown content"""
    try:
        # Simple markdown to HTML conversion
        def simple_markdown_to_html(markdown_text):
            html = markdown_text
            
            # Convert headers
            html = re.sub(r'^### (.*$)', r'<h3>\1</h3>', html, flags=re.MULTILINE)
            html = re.sub(r'^## (.*$)', r'<h2>\1</h2>', html, flags=re.MULTILINE)
            html = re.sub(r'^# (.*$)', r'<h1>\1</h1>', html, flags=re.MULTILINE)
            
            # Convert code blocks
            html = re.sub(r'```[\w]*\n(.*?)\n```', r'<pre><code>\1</code></pre>', html, flags=re.DOTALL)
            
            # Convert inline code
            html = re.sub(r'`([^`]+)`', r'<code>\1</code>', html)
            
            # Convert bold and italic
            html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html)
            html = re.sub(r'\*(.*?)\*', r'<em>\1</em>', html)
            
            # Convert lists
            html = re.sub(r'^[\s]*- (.*$)', r'<li>\1</li>', html, flags=re.MULTILINE)
            html = re.sub(r'(<li>.*</li>)', r'<ul>\1</ul>', html, flags=re.DOTALL)
            
            # Convert paragraphs
            lines = html.split('\n')
            result_lines = []
            in_list = False
            
            for line in lines:
                line = line.strip()
                if not line:
                    if not in_list:
                        result_lines.append('')
                elif line.startswith('<h') or line.startswith('<pre') or line.startswith('<ul') or line.startswith('<li'):
                    if line.startswith('<ul') or line.startswith('<li'):
                        in_list = True
                    else:
                        in_list = False
                    result_lines.append(line)
                elif line.startswith('</ul'):
                    in_list = False
                    result_lines.append(line)
                else:
                    if not in_list and not line.startswith('<'):
                        result_lines.append(f'<p>{line}</p>')
                    else:
                        result_lines.append(line)
            
            return '\n'.join(result_lines)
        
        import re
        html_content = simple_markdown_to_html(request.content)
        
        # Create HTML template with styling optimized for PDF printing
        html_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>{request.title}</title>
            <style>
                @media print {{
                    @page {{
                        margin: 1in;
                        size: A4;
                    }}
                    body {{
                        margin: 0;
                        font-size: 12pt;
                        line-height: 1.4;
                    }}
                }}
                
                body {{
                    font-family: Arial, Helvetica, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                
                h1, h2, h3, h4, h5, h6 {{
                    color: #2c3e50;
                    margin-top: 25px;
                    margin-bottom: 15px;
                    page-break-after: avoid;
                }}
                
                h1 {{
                    font-size: 24pt;
                    border-bottom: 3px solid #3498db;
                    padding-bottom: 10px;
                }}
                
                h2 {{
                    font-size: 18pt;
                    border-bottom: 2px solid #e1e8ed;
                    padding-bottom: 8px;
                }}
                
                h3 {{
                    font-size: 14pt;
                }}
                
                p {{
                    margin-bottom: 12px;
                    text-align: justify;
                }}
                
                code {{
                    background-color: #f8f9fa;
                    padding: 2px 4px;
                    border-radius: 3px;
                    font-family: 'Courier New', monospace;
                    font-size: 0.9em;
                    border: 1px solid #e9ecef;
                }}
                
                pre {{
                    background-color: #2d3748;
                    color: #e2e8f0;
                    padding: 15px;
                    border-radius: 5px;
                    font-family: 'Courier New', monospace;
                    font-size: 11pt;
                    overflow-x: auto;
                    margin: 15px 0;
                    page-break-inside: avoid;
                }}
                
                pre code {{
                    background-color: transparent;
                    padding: 0;
                    color: inherit;
                    border: none;
                }}
                
                ul, ol {{
                    padding-left: 25px;
                    margin-bottom: 15px;
                }}
                
                li {{
                    margin-bottom: 5px;
                }}
                
                strong {{
                    font-weight: bold;
                    color: #2c3e50;
                }}
                
                em {{
                    font-style: italic;
                }}
                
                .no-print {{
                    display: none;
                }}
                
                @media screen {{
                    .print-button {{
                        position: fixed;
                        top: 20px;
                        right: 20px;
                        background: #3498db;
                        color: white;
                        border: none;
                        padding: 10px 20px;
                        border-radius: 5px;
                        cursor: pointer;
                        font-size: 14px;
                        z-index: 1000;
                    }}
                    
                    .print-button:hover {{
                        background: #2980b9;
                    }}
                }}
                
                @media print {{
                    .print-button {{
                        display: none;
                    }}
                }}
            </style>
            <script>
                function printPage() {{
                    window.print();
                }}
            </script>
        </head>
        <body>
            <button class="print-button" onclick="printPage()">Save as PDF</button>
            <div class="content">
                {html_content}
            </div>
        </body>
        </html>
        """
        
        # Return HTML content that browsers can save as PDF
        return Response(
            content=html_template,
            media_type="text/html",
            headers={
                "Content-Disposition": f"inline; filename={request.filename}.html"
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
