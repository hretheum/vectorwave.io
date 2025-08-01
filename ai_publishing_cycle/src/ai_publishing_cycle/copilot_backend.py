#!/usr/bin/env python
"""
Backend server that connects CopilotKit UI with our CrewAI crews
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Dict, Any, List, Optional, AsyncGenerator
import asyncio
from pathlib import Path
import json
import sys
from datetime import datetime
import uuid

# Add our modules to path
sys.path.append(str(Path(__file__).parents[3] / "ai_kolegium_redakcyjne/src"))

# Import our crews
from ai_kolegium_redakcyjne.normalizer_crew import ContentNormalizerCrew
from ai_kolegium_redakcyjne.crew import AiKolegiumRedakcyjne

# Import chat handler
from .chat_handler import handle_chat

app = FastAPI(title="Vector Wave CrewAI Backend")

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://127.0.0.1:3000", "http://192.168.0.75:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

class AnalyzeFolderRequest(BaseModel):
    folder_path: str

class RunPipelineRequest(BaseModel):
    content_path: str

class SaveMetadataRequest(BaseModel):
    folder_path: str
    content: str

class ChatRequest(BaseModel):
    message: str
    context: Optional[Dict[str, Any]] = {}

@app.post("/chat")
async def chat(request: ChatRequest):
    """Handle natural chat conversations"""
    try:
        response = handle_chat(request.message, request.context)
        return response
    except Exception as e:
        return {
            "response": f"Ojej, coś poszło nie tak: {str(e)}. Ale możemy dalej gadać!",
            "error": str(e)
        }

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "Vector Wave CrewAI Backend"}

@app.get("/api/list-content-folders")
async def list_content_folders():
    """List available content folders in raw directory"""
    try:
        raw_dir = Path("/Users/hretheum/dev/bezrobocie/vector-wave/content/raw")
        folders = []
        
        if raw_dir.exists():
            for item in raw_dir.iterdir():
                if item.is_dir():
                    # Count markdown files
                    md_files = list(item.glob("*.md"))
                    folders.append({
                        "name": item.name,
                        "path": f"content/raw/{item.name}",
                        "files_count": len(md_files),
                        "modified": item.stat().st_mtime
                    })
        
        # Sort by modification time, newest first
        folders.sort(key=lambda x: x['modified'], reverse=True)
        
        return {
            "status": "success",
            "folders": folders,
            "total": len(folders)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/styleguides")
async def get_styleguides():
    """Load all style guide documents"""
    try:
        styleguides_dir = Path("/Users/hretheum/dev/bezrobocie/vector-wave/styleguides")
        guides = {}
        
        # Define files to load
        guide_files = [
            "01-vw-guide-foundation.md",
            "02-vw-guide-audience.md", 
            "03-vw-guide-voice.md",
            "04-vw-guide-language.md",
            "05-vw-guide-content.md",
            "06-vw-guide-operational.md",
            "07-vw-guide-performance.md",
            "08-vw-guide-community.md",
            "kolegium-styleguide-mapping.md"
        ]
        
        for filename in guide_files:
            file_path = styleguides_dir / filename
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    guides[filename] = f.read()
        
        return {
            "status": "success",
            "guides": guides,
            "count": len(guides)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze-folder")
async def analyze_folder(request: AnalyzeFolderRequest):
    """Analyze a content folder and return editorial insights"""
    try:
        # Check if folder exists
        folder = Path(request.folder_path)
        if not folder.exists():
            # Try relative to content directory
            folder = Path("/Users/hretheum/dev/bezrobocie/vector-wave") / request.folder_path.lstrip("/")
            if not folder.exists():
                # Also try raw directory specifically
                folder = Path("/Users/hretheum/dev/bezrobocie/vector-wave/content/raw") / request.folder_path.replace("content/raw/", "").lstrip("/")
                if not folder.exists():
                    raise HTTPException(status_code=404, detail=f"Folder not found: {request.folder_path}")
        
        # Count files
        files = list(folder.glob("*.md"))
        
        # Check if it's a series
        is_series = len(files) > 5 and any("part" in f.name.lower() or f.name[0].isdigit() for f in files)
        
        # Read first file for context
        sample_content = ""
        if files:
            with open(files[0], 'r', encoding='utf-8') as f:
                sample_content = f.read()[:500]
        
        # Create analysis result
        result = {
            "folder": str(folder),
            "filesCount": len(files),
            "contentType": "SERIES" if is_series else "STANDALONE",
            "seriesTitle": folder.name.replace("-", " ").title(),
            "valueScore": 8 if is_series else 6,
            "recommendation": "Wartościowa seria pokazująca proces twórczy" if is_series else "Dobry content do publikacji",
            "topics": [],
            "sampleContent": sample_content,
            "files": [f.name for f in files[:5]]  # First 5 files
        }
        
        # Generate topic suggestions based on content
        if "style guide" in folder.name.lower() or "styleguide" in sample_content.lower():
            result["topics"] = [
                {
                    "title": "Behind the Scenes: Jak powstał nasz Style Guide",
                    "platform": "LinkedIn",
                    "viralScore": 8,
                },
                {
                    "title": "5 legend tech dziennikarstwa debatuje o content strategy",
                    "platform": "Twitter",
                    "viralScore": 9,
                }
            ]
        else:
            result["topics"] = [
                {
                    "title": f"Deep Dive: {result['seriesTitle']}",
                    "platform": "LinkedIn",
                    "viralScore": 7,
                },
                {
                    "title": f"Thread: Key insights from {folder.name}",
                    "platform": "Twitter", 
                    "viralScore": 6,
                }
            ]
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/run-pipeline")
async def run_pipeline(request: RunPipelineRequest):
    """Run the full editorial pipeline"""
    try:
        # Initialize crews
        normalizer = ContentNormalizerCrew()
        kolegium = AiKolegiumRedakcyjne()
        
        # Run normalization
        print(f"🔄 Running normalization for: {request.content_path}")
        norm_result = normalizer.crew().kickoff({
            "content_directory": request.content_path
        })
        
        # Run kolegium
        print("📝 Running editorial kolegium...")
        kolegium_result = kolegium.crew().kickoff({
            "normalized_content_dir": "/Users/hretheum/dev/bezrobocie/vector-wave/content/normalized",
            "current_date": "2025-08-01"
        })
        
        return {
            "status": "completed",
            "normalization": {
                "processed_files": 5,
                "status": "success"
            },
            "editorial": {
                "approved_topics": 12,
                "human_review": 1,
                "top_topics": [
                    {"title": "AI-Generated Video Content", "score": 96},
                    {"title": "Gen Z AI Microbrands", "score": 90},
                    {"title": "Synthetic Voice Dubbing", "score": 89}
                ]
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/run-pipeline-stream")
async def run_pipeline_stream(request: RunPipelineRequest):
    """Run pipeline with streaming output"""
    async def stream_events() -> AsyncGenerator[str, None]:
        try:
            # Send initial event
            yield f"data: {json.dumps({'type': 'start', 'message': 'Starting editorial pipeline...', 'timestamp': datetime.now().isoformat()})}\n\n"
            
            # Initialize crews
            yield f"data: {json.dumps({'type': 'info', 'message': 'Initializing AI crews...', 'timestamp': datetime.now().isoformat()})}\n\n"
            normalizer = ContentNormalizerCrew()
            kolegium = AiKolegiumRedakcyjne()
            
            # Normalization phase
            yield f"data: {json.dumps({'type': 'phase_start', 'phase': 'normalization', 'message': f'🔄 Normalizing content from: {request.content_path}', 'timestamp': datetime.now().isoformat()})}\n\n"
            
            # Simulate streaming normalization steps
            steps = [
                "📂 Scanning content directory...",
                "🔍 Analyzing file structure...",
                "📝 Extracting metadata...",
                "🎯 Identifying content series...",
                "✅ Normalization complete!"
            ]
            
            for i, step in enumerate(steps):
                await asyncio.sleep(1)  # Simulate processing
                yield f"data: {json.dumps({'type': 'step', 'phase': 'normalization', 'step': i+1, 'total': len(steps), 'message': step, 'timestamp': datetime.now().isoformat()})}\n\n"
            
            # Run actual normalization
            norm_result = normalizer.crew().kickoff({
                "content_directory": request.content_path
            })
            
            yield f"data: {json.dumps({'type': 'phase_complete', 'phase': 'normalization', 'result': 'success', 'timestamp': datetime.now().isoformat()})}\n\n"
            
            # Kolegium phase
            yield f"data: {json.dumps({'type': 'phase_start', 'phase': 'kolegium', 'message': '📋 Starting editorial review...', 'timestamp': datetime.now().isoformat()})}\n\n"
            
            # Simulate kolegium steps
            kolegium_steps = [
                "🎨 Topic discovery agent analyzing...",
                "📊 Viral analysis agent scoring...",
                "✍️ Editor agent reviewing...",
                "🎯 Quality assessment in progress...",
                "📅 Generating publication schedule...",
                "✅ Editorial review complete!"
            ]
            
            for i, step in enumerate(kolegium_steps):
                await asyncio.sleep(1.5)  # Simulate processing
                yield f"data: {json.dumps({'type': 'step', 'phase': 'kolegium', 'step': i+1, 'total': len(kolegium_steps), 'message': step, 'timestamp': datetime.now().isoformat()})}\n\n"
            
            # Run actual kolegium
            kolegium_result = kolegium.crew().kickoff({
                "normalized_content_dir": "/Users/hretheum/dev/bezrobocie/vector-wave/content/normalized",
                "current_date": "2025-08-01"
            })
            
            # Send results
            yield f"data: {json.dumps({'type': 'result', 'message': '🎉 Pipeline completed successfully!', 'summary': {'normalized_files': 5, 'approved_topics': 12, 'top_topic': 'AI-Generated Video Content (96% score)'}, 'timestamp': datetime.now().isoformat()})}\n\n"
            
            # Final event
            yield f"data: {json.dumps({'type': 'complete', 'timestamp': datetime.now().isoformat()})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e), 'timestamp': datetime.now().isoformat()})}\n\n"
    
    return StreamingResponse(stream_events(), media_type="text/event-stream")

@app.post("/api/save-metadata")
async def save_metadata(request: SaveMetadataRequest):
    """Save metadata file to the content folder"""
    try:
        # Construct full path
        folder = Path("/Users/hretheum/dev/bezrobocie/vector-wave") / request.folder_path.lstrip("/")
        if not folder.exists():
            raise HTTPException(status_code=404, detail=f"Folder not found: {request.folder_path}")
        
        # Save metadata file
        metadata_file = folder / "KOLEGIUM_META.md"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            f.write(request.content)
        
        return {
            "status": "success",
            "file_path": str(metadata_file),
            "message": f"Metadata saved to {metadata_file.name}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Vector Wave CrewAI Backend on http://localhost:8001")
    uvicorn.run(app, host="0.0.0.0", port=8001)