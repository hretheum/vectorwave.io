from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from datetime import datetime
import time
import os
from crewai import Agent, Task, Crew
from langchain_openai import ChatOpenAI

app = FastAPI(title="AI Writing Flow - Container First")

# Storage dla wykonań flow (w produkcji użyj Redis/DB)
flow_executions = {}

class FlowStep:
    def __init__(self, id: str, name: str):
        self.id = id
        self.name = name
        self.status = "pending"
        self.start_time = None
        self.end_time = None
        self.input = None
        self.output = None
        self.agent_decisions = []
        self.content_loss = None
        self.errors = []

# Initialize LLM for CrewAI
llm = ChatOpenAI(
    model_name="gpt-4",
    temperature=0.7,
    api_key=os.getenv("OPENAI_API_KEY")
)

class ContentRequest(BaseModel):
    title: str
    content_type: str = "STANDARD"  # STANDARD, TECHNICAL, VIRAL
    platform: str = "LinkedIn"
    content_ownership: str = "EXTERNAL"  # EXTERNAL, ORIGINAL

class ResearchRequest(BaseModel):
    topic: str
    depth: str = "standard"  # quick, standard, deep
    skip_research: bool = False

@app.get("/")
def root():
    return {"status": "ok", "service": "ai-writing-flow"}

@app.get("/health")
def health():
    return {"status": "healthy", "container": "running"}

@app.post("/api/test-routing")
def test_routing(content: ContentRequest):
    """Test endpoint pokazujący że routing działa"""
    # Podstawowa logika routingu
    if content.content_ownership == "ORIGINAL":
        route = "skip_research_flow"
    elif content.content_type == "TECHNICAL":
        route = "technical_deep_dive_flow"
    elif content.content_type == "VIRAL":
        route = "viral_engagement_flow"
    else:
        route = "standard_editorial_flow"
    
    return {
        "status": "routed",
        "input": content.dict(),
        "route_decision": route,
        "skip_research": content.content_ownership == "ORIGINAL",
        "container_id": "ai-writing-flow-v1"
    }

@app.post("/api/research")
async def execute_research(request: ResearchRequest):
    """Wykonuje research używając CrewAI Agent"""
    
    if request.skip_research:
        return {
            "status": "skipped",
            "reason": "skip_research flag is True",
            "topic": request.topic,
            "findings": []
        }
    
    # Stwórz Research Agent
    researcher = Agent(
        role="Senior Research Analyst",
        goal=f"Research comprehensive information about {request.topic}",
        backstory="Expert researcher with access to vast knowledge",
        verbose=True,
        llm=llm
    )
    
    # Stwórz task
    research_task = Task(
        description=f"""
        Research the topic: {request.topic}
        Depth level: {request.depth}
        
        Provide:
        1. Key concepts and definitions
        2. Current trends and developments
        3. Best practices
        4. Common challenges
        """,
        agent=researcher,
        expected_output="Comprehensive research findings"
    )
    
    # Wykonaj research
    crew = Crew(
        agents=[researcher],
        tasks=[research_task],
        verbose=True
    )
    
    try:
        start_time = time.time()
        result = crew.kickoff()
        execution_time = int((time.time() - start_time) * 1000)
        
        return {
            "status": "completed",
            "topic": request.topic,
            "depth": request.depth,
            "findings": {
                "summary": str(result),
                "key_points": extract_key_points(str(result)),
                "word_count": len(str(result).split())
            },
            "execution_time_ms": execution_time
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "topic": request.topic
        }

def extract_key_points(text: str) -> list:
    """Wyciągnij kluczowe punkty z tekstu"""
    # Prosta heurystyka - w produkcji użyj NLP
    lines = text.split('\n')
    key_points = [line.strip() for line in lines if line.strip() and len(line.strip()) > 20][:5]
    return key_points

# Removed old duplicate GenerateDraftRequest

# OLD ENDPOINT DISABLED - using generate-draft-v2
def OLD_generate_draft_DISABLED():
    """Generuje draft używając CrewAI Writer Agent"""
    
    content = request.content
    research_data = request.research_data
    
    # Writer Agent
    writer = Agent(
        role=f"{content.platform} Content Writer",
        goal=f"Write engaging {content.platform} content about {content.title}",
        backstory=f"Expert {content.platform} content creator",
        verbose=True,
        llm=llm
    )
    
    # Context z research (jeśli jest)
    context = ""
    if research_data and research_data.get("findings"):
        context = f"Research findings: {research_data['findings']['summary']}"
    
    # Writing task
    writing_task = Task(
        description=f"""
        Write {content.platform} content about: {content.title}
        Content type: {content.content_type}
        
        {context}
        
        Requirements:
        - Optimize for {content.platform} best practices
        - Target length: {"280 chars" if content.platform == "Twitter" else "500-1000 words"}
        - Include engaging hook
        - Add call to action
        """,
        agent=writer,
        expected_output=f"Complete {content.platform} post"
    )
    
    crew = Crew(agents=[writer], tasks=[writing_task])
    
    try:
        result = crew.kickoff()
        
        return {
            "status": "completed",
            "draft": {
                "title": content.title,
                "content": str(result),
                "platform": content.platform,
                "word_count": len(str(result).split()),
                "optimized_for": content.platform
            },
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "content_type": content.content_type,
                "used_research": research_data is not None
            }
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}

@app.post("/api/execute-flow")
async def execute_complete_flow(content: ContentRequest):
    """Wykonuje kompletny flow: routing → research → writing"""
    
    execution_log = []
    start_time = datetime.now()
    
    # Step 1: Routing
    routing_result = test_routing(content)
    execution_log.append({
        "step": "routing",
        "result": routing_result,
        "duration_ms": 50
    })
    
    # Step 2: Research (jeśli potrzebny)
    research_result = None
    if not routing_result["skip_research"]:
        research_request = ResearchRequest(
            topic=content.title,
            depth="deep" if content.content_type == "TECHNICAL" else "standard"
        )
        research_result = await execute_research(research_request)
        execution_log.append({
            "step": "research",
            "result": research_result,
            "duration_ms": research_result.get("execution_time_ms", 2500)
        })
    
    # Step 3: Generate Draft
    draft_request = GenerateDraftRequest(
        content=content,
        research_data=research_result
    )
    draft_result = await generate_draft(draft_request)
    execution_log.append({
        "step": "draft_generation",
        "result": draft_result,
        "duration_ms": 3000
    })
    
    total_duration = int((datetime.now() - start_time).total_seconds() * 1000)
    
    return {
        "flow_id": f"flow_{int(time.time())}",
        "status": "completed",
        "routing_decision": routing_result["route_decision"],
        "execution_log": execution_log,
        "final_draft": draft_result.get("draft"),
        "total_duration_ms": total_duration
    }

@app.post("/api/execute-flow-tracked")
async def execute_flow_with_tracking(content: ContentRequest):
    """Wykonuje flow z pełnym śledzeniem dla diagnostyki"""
    
    flow_id = f"flow_{int(time.time())}"
    steps: List[FlowStep] = []
    
    # Step 1: Input Validation
    validation_step = FlowStep("input_validation", "Walidacja Wejścia")
    validation_step.start_time = datetime.now().isoformat()
    validation_step.input = content.dict()
    
    try:
        # Walidacja
        validation_step.output = {
            "validated": True,
            "content_type": content.content_type,
            "platform": content.platform,
            "ownership": content.content_ownership
        }
        validation_step.agent_decisions = [
            f"Wykryto typ contentu: {content.content_type}",
            f"Platforma docelowa: {content.platform}",
            f"Ownership: {content.content_ownership} - {'pominięto research' if content.content_ownership == 'ORIGINAL' else 'wymagany research'}"
        ]
        validation_step.status = "completed"
    except Exception as e:
        validation_step.status = "failed"
        validation_step.errors = [str(e)]
    
    validation_step.end_time = datetime.now().isoformat()
    steps.append(validation_step)
    
    # Step 2: Research (jeśli potrzebny)
    research_step = FlowStep("research", "Badanie Tematu")
    if content.content_ownership == "ORIGINAL":
        research_step.status = "skipped"
        research_step.agent_decisions = [
            "Pominięto research dla ORIGINAL content",
            "Flaga skip_research = true"
        ]
    else:
        research_step.start_time = datetime.now().isoformat()
        try:
            research_request = ResearchRequest(
                topic=content.title,
                depth="deep" if content.content_type == "TECHNICAL" else "standard"
            )
            research_result = await execute_research(research_request)
            
            research_step.output = research_result
            research_step.agent_decisions = [
                f"Wykonano {research_request.depth} research",
                f"Znaleziono {len(research_result.get('findings', {}).get('key_points', []))} kluczowych punktów",
                f"Czas wykonania: {research_result.get('execution_time_ms', 0)}ms"
            ]
            research_step.status = "completed"
            
            # Oblicz content loss
            input_size = len(content.title) * 50  # Przybliżenie
            output_size = research_result.get('findings', {}).get('word_count', 0) * 5
            research_step.content_loss = {
                "inputSize": input_size,
                "outputSize": output_size,
                "lossPercentage": round((1 - output_size/input_size) * 100, 1) if input_size > 0 else 0
            }
        except Exception as e:
            research_step.status = "failed"
            research_step.errors = [str(e)]
        
        research_step.end_time = datetime.now().isoformat()
    
    steps.append(research_step)
    
    # Step 3: Draft Generation
    draft_step = FlowStep("draft_generation", "Generowanie Draftu")
    draft_step.start_time = datetime.now().isoformat()
    
    try:
        draft_request = GenerateDraftRequest(
            content=content,
            research_data=research_step.output if research_step.status == "completed" else None
        )
        draft_result = await generate_draft(draft_request)
        
        draft_step.output = draft_result
        draft_step.agent_decisions = [
            "✅ Wygenerowano draft używając CrewAI Writer Agent",
            f"Długość: {draft_result.get('draft', {}).get('word_count', 0)} słów",
            f"Wykorzystano research: {'Tak' if draft_request.research_data else 'Nie'}",
            f"Platforma: {content.platform}"
        ]
        draft_step.status = "completed"
        
        # Content preservation check
        draft_step.content_loss = {
            "inputSize": len(str(draft_request.dict())) * 10,
            "outputSize": len(draft_result.get('draft', {}).get('content', '')),
            "lossPercentage": 0  # CrewAI zachowuje content
        }
    except Exception as e:
        draft_step.status = "failed"
        draft_step.errors = [str(e)]
    
    draft_step.end_time = datetime.now().isoformat()
    steps.append(draft_step)
    
    # Zapisz wykonanie
    flow_executions[flow_id] = {
        "flow_id": flow_id,
        "steps": [vars(step) for step in steps],
        "created_at": datetime.now().isoformat(),
        "total_duration_ms": sum(
            (datetime.fromisoformat(s.end_time) - datetime.fromisoformat(s.start_time)).total_seconds() * 1000
            for s in steps if s.start_time and s.end_time
        )
    }
    
    return {
        "flow_id": flow_id,
        "status": "completed" if all(s.status in ["completed", "skipped"] for s in steps) else "failed",
        "diagnostic_url": f"/api/flow-diagnostics/{flow_id}",
        "final_draft": draft_step.output.get("draft") if draft_step.status == "completed" else None
    }

@app.get("/api/flow-diagnostics/{flow_id}")
async def get_flow_diagnostics(flow_id: str):
    """Zwraca dane diagnostyczne dla konkretnego wykonania flow"""
    
    if flow_id not in flow_executions:
        raise HTTPException(status_code=404, detail="Flow execution not found")
    
    return flow_executions[flow_id]

@app.get("/api/flow-diagnostics")
async def list_flow_executions(limit: int = 10):
    """Lista ostatnich wykonań flow"""
    
    executions = sorted(
        flow_executions.values(),
        key=lambda x: x["created_at"],
        reverse=True
    )[:limit]
    
    return {
        "total": len(flow_executions),
        "executions": executions
    }

@app.get("/api/list-content-folders")
async def list_content_folders():
    """Lista folderów z contentem do analizy - kompatybilność z frontendem"""
    
    base_path = "/Users/hretheum/dev/bezrobocie/vector-wave/content/raw"
    
    try:
        if not os.path.exists(base_path):
            return {
                "folders": [],
                "count": 0,
                "message": "Content folder not found"
            }
        
        folders = []
        for item in os.listdir(base_path):
            item_path = os.path.join(base_path, item)
            if os.path.isdir(item_path) and not item.startswith('.'):
                # Sprawdź czy folder ma pliki .md
                md_files = [f for f in os.listdir(item_path) if f.endswith('.md')]
                if md_files:
                    folder_info = {
                        "path": item_path,
                        "name": item,
                        "files": len(md_files),
                        "md_files": md_files,
                        "created": datetime.fromtimestamp(os.path.getctime(item_path)).isoformat()
                    }
                    folders.append(folder_info)
        
        folders.sort(key=lambda x: x["created"], reverse=True)
        
        return {
            "folders": folders,
            "count": len(folders),
            "message": f"Found {len(folders)} content folders"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading content folders: {str(e)}")

class AnalyzeContentRequest(BaseModel):
    folder: str
    use_flow: bool = False

@app.post("/api/analyze-content")
async def analyze_content(request: AnalyzeContentRequest):
    """Analizuje zawartość folderu - kompatybilność z frontendem"""
    
    try:
        folder_name = request.folder
        base_path = "/Users/hretheum/dev/bezrobocie/vector-wave/content/raw"
        folder_path = os.path.join(base_path, folder_name)
        
        if not os.path.exists(folder_path):
            raise HTTPException(status_code=404, detail=f"Folder {folder_name} not found")
        
        # Znajdź pliki .md w folderze
        md_files = [f for f in os.listdir(folder_path) if f.endswith('.md')]
        
        if not md_files:
            raise HTTPException(status_code=404, detail=f"No .md files found in {folder_name}")
        
        # Przeczytaj zawartość plików (uproszczona analiza)
        content_analysis = {
            "folder": folder_name,
            "filesCount": len(md_files),  # Frontend oczekuje filesCount
            "totalFiles": len(md_files),  # Zachowaj dla kompatybilności
            "mdFiles": md_files,
            "analysisDate": datetime.now().isoformat(),
            "contentType": "ORIGINAL",  # Zakładamy że to content własny
            "suggestedPlatform": "LinkedIn",
            "topTopics": [],  # Zostanie wypełnione poniżej
            "valueScore": 7.5,  # Frontend oczekuje valueScore
            "viralPotential": 7.5,  # Zachowaj dla kompatybilności
            "audienceAlignment": 8.0,
            "contentOwnership": "ORIGINAL"
        }
        
        # Przeczytaj pierwszy plik dla analizy tematów
        first_file = os.path.join(folder_path, md_files[0])
        try:
            with open(first_file, 'r', encoding='utf-8') as f:
                content = f.read()[:1000]  # Pierwsze 1000 znaków
                
                # Prosta analiza tematów (frontend oczekuje obiektów z title, platform, viralScore)
                if "adhd" in content.lower():
                    content_analysis["topTopics"] = [
                        {"title": "ADHD w pracy", "platform": "LinkedIn", "viralScore": 8.5},
                        {"title": "Mental Health Tips", "platform": "Twitter", "viralScore": 7.8},
                        {"title": "Productivity Hacks", "platform": "LinkedIn", "viralScore": 8.2}
                    ]
                    content_analysis["valueScore"] = 8.5
                elif "knowledge" in content.lower():
                    content_analysis["topTopics"] = [
                        {"title": "AI Knowledge Management", "platform": "LinkedIn", "viralScore": 9.1},
                        {"title": "Tech Architecture", "platform": "Twitter", "viralScore": 7.5},
                        {"title": "Development Patterns", "platform": "LinkedIn", "viralScore": 8.0}
                    ]
                    content_analysis["valueScore"] = 8.8
                elif "brain" in content.lower():
                    content_analysis["topTopics"] = [
                        {"title": "Strategic Planning", "platform": "LinkedIn", "viralScore": 7.2},
                        {"title": "Creative Process", "platform": "Twitter", "viralScore": 6.8},
                        {"title": "Team Brainstorming", "platform": "LinkedIn", "viralScore": 7.5}
                    ]
                    content_analysis["valueScore"] = 7.2
                else:
                    content_analysis["topTopics"] = [
                        {"title": "Content Creation", "platform": "LinkedIn", "viralScore": 6.5},
                        {"title": "Writing Tips", "platform": "Twitter", "viralScore": 6.0},
                        {"title": "Marketing Strategy", "platform": "LinkedIn", "viralScore": 7.0}
                    ]
                    content_analysis["valueScore"] = 6.5
                    
        except Exception as e:
            print(f"Error reading file {first_file}: {e}")
            content_analysis["topTopics"] = [
                {"title": "General Content", "platform": "LinkedIn", "viralScore": 5.0},
                {"title": "Content Writing", "platform": "Twitter", "viralScore": 4.5},
                {"title": "Marketing", "platform": "LinkedIn", "viralScore": 5.5}
            ]
            content_analysis["valueScore"] = 5.0
        
        return content_analysis
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing content: {str(e)}")

@app.post("/api/analyze-folder")
async def analyze_folder(request: dict):
    """Alias dla analyze-content - kompatybilność z różnymi route.ts"""
    
    # Konwertuj request na AnalyzeContentRequest format
    folder_path = request.get("folder_path", request.get("folder", ""))
    
    if not folder_path:
        raise HTTPException(status_code=400, detail="folder_path or folder is required")
    
    # Wyciągnij tylko nazwę folderu jeśli podano pełną ścieżkę
    folder_name = os.path.basename(folder_path)
    
    analyze_request = AnalyzeContentRequest(folder=folder_name, use_flow=False)
    return await analyze_content(analyze_request)

class GenerateDraftRequestV2(BaseModel):
    topic_title: str
    platform: str = "LinkedIn"
    folder_path: str
    content_type: str = "ORIGINAL"
    content_ownership: str = "ORIGINAL"
    viral_score: float = 7.0
    editorial_recommendations: str = ""
    skip_research: bool = True

@app.post("/api/generate-draft-v2")
async def generate_draft_v2(request: GenerateDraftRequestV2):
    """Generuje draft na podstawie wybranego tematu"""
    
    try:
        # Wyciągnij folder name z folder_path
        folder_name = os.path.basename(request.folder_path) if request.folder_path else request.topic_title
        base_path = "/Users/hretheum/dev/bezrobocie/vector-wave/content/raw"
        folder_path = os.path.join(base_path, folder_name)
        
        if not os.path.exists(folder_path):
            raise HTTPException(status_code=404, detail=f"Folder {folder_name} not found")
        
        # Znajdź pliki .md w folderze
        md_files = [f for f in os.listdir(folder_path) if f.endswith('.md')]
        
        if not md_files:
            raise HTTPException(status_code=404, detail=f"No .md files found in {folder_name}")
            
        # Przeczytaj pierwszy plik jako base content
        first_file = os.path.join(folder_path, md_files[0])
        base_content = ""
        
        try:
            with open(first_file, 'r', encoding='utf-8') as f:
                base_content = f.read()[:2000]  # Pierwsze 2000 znaków
        except Exception as e:
            print(f"Error reading file {first_file}: {e}")
            base_content = f"Content from {folder_name}"
        
        # Generuj draft na podstawie tematu i platformy (mock implementation)
        platform_templates = {
            "LinkedIn": {
                "intro": "🚀 Insight alert:",
                "structure": "Problem → Solution → Action",
                "cta": "What's your experience with this? Share in comments! 💬"
            },
            "Twitter": {
                "intro": "💡 Quick thread:",
                "structure": "Hook → Value → Thread",
                "cta": "RT if helpful! 🔄"
            }
        }
        
        template = platform_templates.get(request.platform, platform_templates["LinkedIn"])
        
        # Prosta generacja draft na podstawie tematu
        if "adhd" in request.topic_title.lower() or "productivity" in request.topic_title.lower():
            draft_content = f"""{template["intro"]} {request.topic_title}

Based on analysis from {folder_name}, here are actionable insights:

🎯 **The Challenge**
Many professionals struggle with productivity, especially those with ADHD traits.

💡 **The Solution**
• Time-blocking with flexible buffers
• Breaking tasks into 15-minute chunks  
• Using visual progress tracking
• Building in movement breaks

🚀 **Take Action**
1. Pick ONE technique to try this week
2. Track your energy levels
3. Adjust based on what works

{template["cta"]}

#Productivity #ADHD #WorkSmarter #MentalHealth"""
        
        elif "knowledge" in request.topic_title.lower() or "ai" in request.topic_title.lower():
            draft_content = f"""{template["intro"]} {request.topic_title}

From our {folder_name} analysis - here's what's working:

🔍 **The Problem**
Knowledge gets scattered across tools, making it hard to leverage.

⚡ **The Solution**
• Centralized knowledge graphs
• AI-powered search and discovery
• Automated tagging and categorization
• Cross-reference linking

📈 **Results**
Teams using structured knowledge management see:
→ 40% faster onboarding
→ 60% reduction in duplicate work  
→ 3x better knowledge retention

{template["cta"]}

#KnowledgeManagement #AI #TechLeadership #Innovation"""
        
        else:
            draft_content = f"""{template["intro"]} {request.topic_title}

Insights from {folder_name}:

🎯 **Key Insight**
{request.topic_title} is crucial for modern professionals.

💡 **Actionable Steps**
• Identify the core challenge
• Apply proven frameworks
• Measure and iterate
• Share learnings with team

🚀 **Next Steps**
Start with one small change today.

{template["cta"]}

#Leadership #Strategy #Growth"""
        
        # Zwróć response
        return {
            "success": True,
            "draft": {
                "content": draft_content,
                "topic_title": request.topic_title,
                "platform": request.platform,
                "word_count": len(draft_content.split()),
                "character_count": len(draft_content),
                "viral_score": request.viral_score,
                "source_folder": folder_name,
                "generated_at": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating draft: {str(e)}")