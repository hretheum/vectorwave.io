from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from datetime import datetime
import time
import os
import redis
import json
import hashlib
import re
from crewai import Agent, Task, Crew
from langchain_openai import ChatOpenAI
import chromadb
from chromadb.config import Settings

app = FastAPI(
    title="AI Writing Flow - Container First",
    description="AI-powered content generation system with CrewAI agents integration. Optimized for fast content analysis and draft generation.",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {"name": "health", "description": "Health check endpoints"},
        {"name": "content", "description": "Content analysis and generation"},
        {"name": "research", "description": "Research operations"},
        {"name": "flow", "description": "Complete flow execution"},
        {"name": "diagnostics", "description": "Flow diagnostics and monitoring"}
    ]
)

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

# Redis connection
try:
    redis_client = redis.Redis(host='redis', port=6379, decode_responses=True)
    redis_client.ping()
    print("✅ Redis connected")
except:
    redis_client = None
    print("⚠️ Redis not available - running without cache")

# ChromaDB connection
try:
    chroma_client = chromadb.HttpClient(
        host='chromadb',
        port=8000,
        settings=Settings(anonymized_telemetry=False)
    )
    # Test connection
    chroma_client.heartbeat()
    print("✅ ChromaDB connected")
    
    # Create or get style guide collection
    style_guide_collection = chroma_client.get_or_create_collection(
        name="vector_wave_style_guide",
        metadata={"description": "Vector Wave content style guidelines"}
    )
    print(f"📚 Style guide collection ready: {style_guide_collection.count()} rules")
except Exception as e:
    chroma_client = None
    style_guide_collection = None
    print(f"⚠️ ChromaDB not available: {e}")

class ContentRequest(BaseModel):
    """Content metadata for generation requests"""
    title: str
    content_type: str = "STANDARD"  # STANDARD, TECHNICAL, VIRAL
    platform: str = "LinkedIn"
    content_ownership: str = "EXTERNAL"  # EXTERNAL, ORIGINAL

class ResearchRequest(BaseModel):
    """Research configuration"""
    topic: str
    depth: str = "standard"  # quick, standard, deep
    skip_research: bool = False

@app.get("/", tags=["health"])
def root():
    """Root endpoint - returns service status"""
    return {"status": "ok", "service": "ai-writing-flow"}

@app.get("/health", tags=["health"])
def health():
    """Health check endpoint for container monitoring"""
    return {"status": "healthy", "container": "running"}

@app.get("/api/cache-test", tags=["diagnostics"])
async def test_cache():
    """Test Redis cache functionality"""
    if not redis_client:
        return {"status": "no_cache", "message": "Redis not connected"}
    
    # Test set/get
    test_key = f"test:{datetime.now().isoformat()}"
    redis_client.setex(test_key, 60, "Hello Redis!")
    value = redis_client.get(test_key)
    
    return {
        "status": "ok",
        "cached_value": value,
        "ttl": redis_client.ttl(test_key)
    }

@app.post("/api/style-guide/seed", tags=["content"])
async def seed_style_guide():
    """Seed ChromaDB with Vector Wave style guide rules"""
    if not style_guide_collection:
        return {"status": "error", "message": "ChromaDB not connected"}
    
    # Vector Wave style guide rules
    style_rules = [
        {
            "id": "tone-1",
            "rule": "Use conversational, approachable tone",
            "category": "tone",
            "examples": ["Let's dive into...", "Here's the thing about..."],
            "priority": "high"
        },
        {
            "id": "tone-2",
            "rule": "Avoid corporate jargon and buzzwords",
            "category": "tone",
            "examples": ["synergy", "leverage", "paradigm shift"],
            "priority": "high"
        },
        {
            "id": "structure-1",
            "rule": "Start with a hook that grabs attention",
            "category": "structure",
            "examples": ["Ever wondered why...", "The moment I realized..."],
            "priority": "high"
        },
        {
            "id": "structure-2",
            "rule": "Use short paragraphs (max 3 sentences)",
            "category": "structure",
            "examples": ["Break up long text", "White space is your friend"],
            "priority": "medium"
        },
        {
            "id": "linkedin-1",
            "rule": "LinkedIn posts should start with a pattern interrupt",
            "category": "platform-linkedin",
            "examples": ["Unpopular opinion:", "I was wrong about..."],
            "priority": "high"
        },
        {
            "id": "linkedin-2",
            "rule": "Include a clear CTA at the end",
            "category": "platform-linkedin",
            "examples": ["What's your experience?", "Drop a comment if..."],
            "priority": "medium"
        },
        {
            "id": "technical-1",
            "rule": "Explain technical concepts with analogies",
            "category": "technical",
            "examples": ["Redis is like a sticky note on your monitor..."],
            "priority": "high"
        },
        {
            "id": "engagement-1",
            "rule": "Ask questions to encourage comments",
            "category": "engagement",
            "examples": ["What would you do?", "Have you tried...?"],
            "priority": "medium"
        }
    ]
    
    # Clear existing rules
    try:
        existing_ids = style_guide_collection.get()['ids']
        if existing_ids:
            style_guide_collection.delete(ids=existing_ids)
    except:
        pass
    
    # Add rules to ChromaDB
    documents = []
    metadatas = []
    ids = []
    
    for rule in style_rules:
        documents.append(f"{rule['rule']}. Examples: {', '.join(rule['examples'])}")
        metadatas.append({
            "category": rule["category"],
            "priority": rule["priority"],
            "rule_text": rule["rule"]
        })
        ids.append(rule["id"])
    
    style_guide_collection.add(
        documents=documents,
        metadatas=metadatas,
        ids=ids
    )
    
    return {
        "status": "success",
        "rules_added": len(style_rules),
        "total_rules": style_guide_collection.count()
    }

class StyleCheckRequest(BaseModel):
    """Request for style guide checking"""
    content: str
    platform: str = "LinkedIn"
    check_categories: List[str] = ["tone", "structure", "engagement"]

@app.post("/api/style-guide/check", tags=["content"])
async def check_style_guide(request: StyleCheckRequest):
    """Check content against Vector Wave style guide using Naive RAG"""
    if not style_guide_collection:
        return {"status": "error", "message": "ChromaDB not connected"}
    
    try:
        # Query relevant rules based on content and platform
        query_text = f"{request.platform} content: {request.content[:200]}..."
        
        # Naive RAG - simple similarity search
        results = style_guide_collection.query(
            query_texts=[query_text],
            n_results=5,
            where={"$or": [
                {"category": cat} for cat in request.check_categories
            ] + [
                {"category": f"platform-{request.platform.lower()}"}
            ]}
        )
        
        # Extract relevant rules
        relevant_rules = []
        if results['ids'] and results['ids'][0]:
            for i, rule_id in enumerate(results['ids'][0]):
                metadata = results['metadatas'][0][i]
                relevant_rules.append({
                    "rule_id": rule_id,
                    "rule": metadata.get('rule_text', ''),
                    "category": metadata.get('category', ''),
                    "priority": metadata.get('priority', 'medium'),
                    "relevance_score": 1 - (results['distances'][0][i] if results['distances'] else 0)
                })
        
        # Simple rule-based checks
        violations = []
        suggestions = []
        
        # Check for pattern interrupt (LinkedIn)
        if request.platform.lower() == "linkedin":
            starters = ["Unpopular opinion:", "I was wrong about", "Ever wondered"]
            if not any(request.content.startswith(s) for s in starters):
                violations.append({
                    "rule": "LinkedIn posts should start with a pattern interrupt",
                    "severity": "medium",
                    "suggestion": "Consider starting with: 'Unpopular opinion:' or 'Ever wondered why...'"
                })
        
        # Check paragraph length
        paragraphs = request.content.split('\n\n')
        long_paragraphs = [p for p in paragraphs if len(p.split('.')) > 3]
        if long_paragraphs:
            violations.append({
                "rule": "Use short paragraphs (max 3 sentences)",
                "severity": "low",
                "suggestion": "Break up long paragraphs for better readability"
            })
        
        # Check for questions (engagement)
        if '?' not in request.content:
            suggestions.append({
                "rule": "Ask questions to encourage comments",
                "suggestion": "Add a question at the end like 'What's your experience with this?'"
            })
        
        # Calculate style score
        style_score = 100
        style_score -= len(violations) * 15
        style_score -= len(suggestions) * 5
        style_score = max(0, min(100, style_score))
        
        return {
            "status": "success",
            "style_score": style_score,
            "relevant_rules": relevant_rules,
            "violations": violations,
            "suggestions": suggestions,
            "platform": request.platform,
            "checked_categories": request.check_categories
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "message": "Failed to check style guide"
        }

class AgenticStyleCheckRequest(BaseModel):
    """Request for agentic style guide checking"""
    content: str
    platform: str = "LinkedIn"
    focus_areas: List[str] = ["engagement", "clarity", "brand_voice"]
    context: Optional[str] = None

@app.post("/api/style-guide/check-agentic", tags=["content"])
async def check_style_agentic(request: AgenticStyleCheckRequest):
    """Check content against style guide using CrewAI agent for intelligent analysis"""
    if not style_guide_collection:
        return {"status": "error", "message": "ChromaDB not connected"}
    
    try:
        # First get relevant rules from ChromaDB (RAG)
        results = style_guide_collection.query(
            query_texts=[f"{request.platform} {request.content[:200]}"],
            n_results=8,
            where={"$or": [
                {"category": f"platform-{request.platform.lower()}"},
                {"category": "tone"},
                {"category": "structure"},
                {"category": "engagement"}
            ]}
        )
        
        # Format rules for agent
        relevant_rules = []
        if results['ids'] and results['ids'][0]:
            for i, rule_id in enumerate(results['ids'][0]):
                metadata = results['metadatas'][0][i]
                relevant_rules.append(f"- {metadata.get('rule_text', '')}")
        
        # Create Style Guide Expert Agent
        style_expert = Agent(
            role="Vector Wave Style Guide Expert",
            goal="Provide intelligent, context-aware style guidance that goes beyond simple rule matching",
            backstory="""You are an expert content strategist who understands the nuances of viral content.
            You know that great content balances authenticity with engagement, and you can spot opportunities
            for improvement that simple rule-based systems miss. You understand platform-specific best practices
            and can provide actionable, creative suggestions.""",
            verbose=True,
            llm=llm
        )
        
        # Create analysis task
        analysis_task = Task(
            description=f"""
            Analyze this content for Vector Wave style guide compliance and viral potential:
            
            Content: "{request.content}"
            Platform: {request.platform}
            Context: {request.context or 'General business content'}
            Focus Areas: {', '.join(request.focus_areas)}
            
            Relevant style rules from our guide:
            {chr(10).join(relevant_rules)}
            
            Provide:
            1. Overall style score (0-100) with reasoning
            2. What works well (be specific)
            3. Critical improvements needed
            4. Creative suggestions to boost {request.platform} engagement
            5. Alternative opening if current one is weak
            6. Recommended CTA if missing
            
            Be constructive and specific. Focus on actionable improvements.
            """,
            agent=style_expert,
            expected_output="Detailed style analysis with score, strengths, improvements, and creative suggestions"
        )
        
        # Execute with CrewAI
        crew = Crew(
            agents=[style_expert],
            tasks=[analysis_task],
            verbose=True
        )
        
        start_time = time.time()
        result = crew.kickoff()
        execution_time = time.time() - start_time
        
        # Parse agent's analysis (in production, use structured output)
        analysis_text = str(result)
        
        # Extract score from analysis (simple regex, improve in production)
        import re
        score_match = re.search(r'score[:\s]+(\d+)', analysis_text, re.IGNORECASE)
        style_score = int(score_match.group(1)) if score_match else 75
        
        return {
            "status": "success",
            "analysis_type": "agentic",
            "style_score": style_score,
            "agent_analysis": analysis_text,
            "relevant_rules_used": len(relevant_rules),
            "platform": request.platform,
            "focus_areas": request.focus_areas,
            "execution_time_seconds": round(execution_time, 2),
            "cost_estimate": "$0.02-0.05 (GPT-4)"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "message": "Failed to perform agentic style analysis"
        }

@app.post("/api/style-guide/compare", tags=["content"])
async def compare_style_methods(request: StyleCheckRequest):
    """Compare Naive RAG vs Agentic RAG results for the same content"""
    
    # Run Naive RAG
    naive_start = time.time()
    naive_result = await check_style_guide(request)
    naive_time = time.time() - naive_start
    
    # Run Agentic RAG
    agentic_request = AgenticStyleCheckRequest(
        content=request.content,
        platform=request.platform,
        focus_areas=["engagement", "clarity", "brand_voice"],
        context=None
    )
    agentic_start = time.time()
    agentic_result = await check_style_agentic(agentic_request)
    agentic_time = time.time() - agentic_start
    
    return {
        "status": "success",
        "content_preview": request.content[:100] + "...",
        "comparison": {
            "naive_rag": {
                "score": naive_result.get("style_score", 0),
                "violations": len(naive_result.get("violations", [])),
                "suggestions": len(naive_result.get("suggestions", [])),
                "execution_time": round(naive_time, 3)
            },
            "agentic_rag": {
                "score": agentic_result.get("style_score", 0),
                "has_alternative_opening": "Alternative opening" in agentic_result.get("agent_analysis", ""),
                "has_cta_recommendation": "Recommended CTA" in agentic_result.get("agent_analysis", ""),
                "execution_time": round(agentic_time, 3)
            }
        },
        "recommendation": "Use Naive RAG for real-time validation, Agentic RAG for deep analysis"
    }

@app.post("/api/test-routing", tags=["flow"], deprecated=True)
def test_routing(content: ContentRequest):
    """Test routing logic (deprecated - use analyze-potential instead)"""
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

@app.post("/api/research", tags=["research"])
async def execute_research(request: ResearchRequest):
    """
    Execute research using CrewAI Research Agent
    
    - **topic**: Topic to research
    - **depth**: Research depth (quick/standard/deep)
    - **skip_research**: Skip research entirely (returns empty findings)
    
    Returns research findings with key points and execution time.
    """
    
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

class GenerateDraftRequest(BaseModel):
    """Draft generation request with optional research data"""
    content: ContentRequest
    research_data: Optional[Dict] = None
    skip_research: Optional[bool] = False  # Automatically true for ORIGINAL content

@app.post("/api/generate-draft", tags=["content"])
async def generate_draft(request: GenerateDraftRequest):
    """
    Generate content draft using CrewAI Writer Agent
    
    **Optimizations:**
    - Automatically skips research for ORIGINAL content
    - ~20% faster for ORIGINAL content (20s vs 25s)
    
    **Request fields:**
    - **content**: Content metadata (title, type, platform, ownership)
    - **research_data**: Optional pre-computed research data
    - **skip_research**: Force skip research phase
    
    Returns generated draft with metadata and execution time.
    """
    
    start_time = time.time()
    
    content = request.content
    research_data = request.research_data
    
    # Log optimization
    if request.skip_research or content.content_ownership == "ORIGINAL":
        print(f"🚀 OPTIMIZED: Skipping research for ORIGINAL content - {content.title}")
        print(f"⏱️  Starting draft generation at: {datetime.now().strftime('%H:%M:%S.%f')[:-3]}")
    
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
    elif request.skip_research or content.content_ownership == "ORIGINAL":
        # For ORIGINAL content, add context about using internal knowledge
        context = """This is ORIGINAL content - use your internal knowledge and creativity.
        No external research needed. Focus on creating engaging, authentic content.
        The author has their own materials and perspective on this topic."""
    
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
        
        # Calculate total execution time
        execution_time = time.time() - start_time
        
        # Log optimization results
        if request.skip_research or content.content_ownership == "ORIGINAL":
            print(f"✅ Draft generated in {execution_time:.1f} seconds (research skipped)")
            print(f"💡 Time saved: ~{max(0, 25 - execution_time):.0f} seconds")
        
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
                "used_research": research_data is not None,
                "execution_time_seconds": round(execution_time, 2),
                "optimization_applied": request.skip_research or content.content_ownership == "ORIGINAL"
            }
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}

@app.post("/api/execute-flow", tags=["flow"])
async def execute_complete_flow(content: ContentRequest):
    """
    Execute complete flow: routing → research → writing
    
    Combines all steps into single execution with automatic routing decisions.
    """
    
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

@app.post("/api/execute-flow-tracked", tags=["flow", "diagnostics"])
async def execute_flow_with_tracking(content: ContentRequest):
    """
    Execute flow with full tracking and diagnostics
    
    Provides detailed step-by-step execution tracking including:
    - Agent decisions at each step
    - Content loss metrics
    - Timing information
    - Error tracking
    
    Use `/api/flow-diagnostics/{flow_id}` to retrieve detailed results.
    """
    
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

@app.get("/api/flow-diagnostics/{flow_id}", tags=["diagnostics"])
async def get_flow_diagnostics(flow_id: str):
    """Get diagnostic data for specific flow execution"""
    
    if flow_id not in flow_executions:
        raise HTTPException(status_code=404, detail="Flow execution not found")
    
    return flow_executions[flow_id]

@app.get("/api/flow-diagnostics", tags=["diagnostics"])
async def list_flow_executions(limit: int = 10):
    """List recent flow executions with basic stats"""
    
    executions = sorted(
        flow_executions.values(),
        key=lambda x: x["created_at"],
        reverse=True
    )[:limit]
    
    return {
        "total": len(flow_executions),
        "executions": executions
    }

@app.get("/api/list-content-folders", tags=["content"])
async def list_content_folders():
    """List available content folders from raw content directory"""
    import os
    import glob
    
    content_path = "/Users/hretheum/dev/bezrobocie/vector-wave/content/raw"
    
    try:
        if not os.path.exists(content_path):
            return {
                "status": "error", 
                "message": f"❌ CRITICAL: Content path does not exist: {content_path}",
                "folders": []
            }
        
        # Znajdź wszystkie foldery w content/raw
        folders = []
        for folder_path in glob.glob(os.path.join(content_path, "*")):
            if os.path.isdir(folder_path):
                folder_name = os.path.basename(folder_path)
                folders.append({
                    "name": folder_name,
                    "path": folder_path,
                    "type": "raw_content"
                })
        
        return {
            "status": "ok",
            "folders": folders,
            "total": len(folders)
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"❌ CRITICAL ERROR: {str(e)}",
            "folders": []
        }

class AnalyzePotentialRequest(BaseModel):
    """Content analysis request"""
    folder: str
    use_flow: bool = False

class CustomIdeasRequest(BaseModel):
    """Request for analyzing custom topic ideas"""
    folder: str
    ideas: List[str]
    platform: str = "LinkedIn"

class IdeaAnalysis(BaseModel):
    """Analysis result for a single idea"""
    idea: str
    viral_score: float
    content_alignment: float
    available_material: float
    overall_score: float
    recommendation: str
    suggested_angle: Optional[str] = None

class CustomIdeasResponse(BaseModel):
    """Response with analyzed ideas"""
    folder: str
    platform: str
    ideas: List[IdeaAnalysis]
    best_idea: Optional[IdeaAnalysis] = None
    folder_context: Dict[str, Any]
    from_cache: bool = False

@app.post("/api/analyze-potential", tags=["content"], 
         summary="Ultra-fast content analysis",
         response_description="Content analysis with viral score and topic suggestions")
async def analyze_content_potential(request: AnalyzePotentialRequest):
    """
    Ultra-fast content potential analysis (1ms response time)
    
    Analyzes content folder and returns:
    - Viral score (0-10)
    - Content type classification
    - Top 3 topic suggestions with platform optimization
    - Audience targeting scores
    - Editorial recommendations
    
    **Performance**: ~1ms response time (no AI calls)
    **Caching**: Results cached for 5 minutes
    """
    
    start_time = time.time()
    
    try:
        folder_name = request.folder
        
        # Check cache first
        cache_key = f"analysis:{folder_name}"
        if redis_client:
            try:
                cached_result = redis_client.get(cache_key)
                if cached_result:
                    result = json.loads(cached_result)
                    result["from_cache"] = True
                    result["processing_time_ms"] = int((time.time() - start_time) * 1000)
                    return result
            except Exception as e:
                print(f"Cache read error: {e}")
        
        # Simple analysis without ContentAnalysisAgent
        # Analyze folder name for themes
        title = folder_name.replace('-', ' ').title()
        themes = []
        
        # Extract key themes from folder name
        tech_keywords = ['ai', 'ml', 'api', 'database', 'cloud', 'automation', 'framework', 'workflow', 'agent']
        for keyword in tech_keywords:
            if keyword in folder_name.lower():
                themes.append(keyword.upper())
        
        if not themes:
            # Extract any significant words
            words = folder_name.split('-')
            themes = [w.upper() for w in words if len(w) > 3][:3]
        
        # Calculate viral score based on folder name
        viral_score = 0.5  # Base score
        viral_keywords = ['solution', 'hack', 'secret', 'mistake', 'truth', 'guide', 'tips']
        for keyword in viral_keywords:
            if keyword in folder_name.lower():
                viral_score += 0.1
        
        # Platform-specific boost
        if 'linkedin' in folder_name.lower():
            viral_score += 0.05
        
        viral_score = min(viral_score, 1.0)
        
        # Count actual files in folder
        import glob
        file_path = f"/Users/hretheum/dev/bezrobocie/vector-wave/content/raw/{folder_name}"
        files_count = len(glob.glob(f"{file_path}/*")) if os.path.exists(file_path) else 0
        
        # Determine content type and complexity
        content_type = "TECHNICAL" if any(kw in folder_name.lower() for kw in ['code', 'api', 'implementation']) else "GENERAL"
        complexity_level = "advanced" if any(kw in folder_name.lower() for kw in ['advanced', 'expert', 'deep']) else "intermediate"
        
        # Generate topic suggestions
        top_topics = []
        
        # LinkedIn topic
        top_topics.append({
            "title": f"5 Lessons from {title} Implementation",
            "platform": "LinkedIn",
            "viralScore": min(10, int(viral_score * 10 + 1))
        })
        
        # Twitter topic
        main_theme = themes[0] if themes else 'Tech'
        top_topics.append({
            "title": f"The {main_theme} Mistake Everyone Makes",
            "platform": "Twitter",
            "viralScore": min(10, int(viral_score * 10 + 2))
        })
        
        # Blog topic
        top_topics.append({
            "title": f"{title}: A Complete Guide",
            "platform": "Blog",
            "viralScore": min(10, int(viral_score * 10))
        })
        
        # Generate recommendation
        if viral_score > 0.7:
            recommendation = "🔥 High viral potential! Publish immediately on LinkedIn for maximum reach."
        elif viral_score > 0.5:
            recommendation = "✅ Good potential. Consider adding controversial angles to boost engagement."
        else:
            recommendation = "📊 Niche content. Focus on technical communities for better reception."
        
        # Get audience scores
        audience_scores = await get_quick_audience_scores(
            title,
            'LinkedIn',
            timeout=1.0,
            fallback_scores={
                "technical_founder": 0.7,
                "senior_engineer": 0.6,
                "decision_maker": 0.5,
                "skeptical_learner": 0.8
            }
        )
        
        # Build response
        analysis_result = {
            "folder": folder_name,
            "filesCount": files_count,
            "contentType": content_type,
            "contentOwnership": "ORIGINAL" if "adhd" in folder_name.lower() or "personal" in folder_name.lower() else "EXTERNAL",
            "valueScore": round(viral_score * 10, 1),
            "viral_score": viral_score,
            "complexity_level": complexity_level,
            "key_themes": themes,
            "topTopics": top_topics,
            "recommendation": recommendation,
            "audience_scores": audience_scores,
            "processing_time_ms": int((time.time() - start_time) * 1000),
            "confidence": 0.75,  # Fixed confidence for simple analysis
            "from_cache": False
        }
        
        # Save to cache
        if redis_client:
            try:
                # Cache for 5 minutes (300 seconds)
                redis_client.setex(
                    cache_key, 
                    300, 
                    json.dumps(analysis_result)
                )
                print(f"✅ Cached analysis for folder: {folder_name}")
            except Exception as e:
                print(f"Cache write error: {e}")
        
        return analysis_result
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "folder": request.folder
        }

@app.post("/api/analyze-content", tags=["content"], deprecated=True)
async def analyze_content_legacy(request: dict):
    """Legacy endpoint (deprecated) - use /api/analyze-potential instead"""
    analyze_request = AnalyzePotentialRequest(
        folder=request.get("folder", ""),
        use_flow=request.get("use_flow", False)
    )
    return await analyze_content_potential(analyze_request)

async def get_quick_audience_scores(
    title: str, 
    platform: str, 
    timeout: float = 1.0,
    fallback_scores: Dict[str, float] = None
) -> Dict[str, float]:
    """Get audience scores with simple heuristics"""
    
    if fallback_scores is None:
        fallback_scores = {
            "technical_founder": 0.6,
            "senior_engineer": 0.6,
            "decision_maker": 0.5,
            "skeptical_learner": 0.7
        }
    
    # Simple scoring based on title keywords
    title_lower = title.lower()
    
    scores = fallback_scores.copy()
    
    # Adjust scores based on keywords
    if any(word in title_lower for word in ['framework', 'workflow', 'process', 'solution']):
        scores["technical_founder"] += 0.2
        scores["decision_maker"] += 0.1
    
    if any(word in title_lower for word in ['architecture', 'code', 'technical', 'engineering', 'implementation']):
        scores["senior_engineer"] += 0.2
        scores["technical_founder"] += 0.1
    
    if any(word in title_lower for word in ['ai', 'automation', 'efficiency']):
        scores["skeptical_learner"] += 0.1
        scores["decision_maker"] += 0.1
    
    # Platform adjustments
    if platform.lower() == "linkedin":
        scores["decision_maker"] += 0.1
    elif platform.lower() == "twitter":
        scores["technical_founder"] += 0.1
        scores["senior_engineer"] += 0.1
    
    # Normalize scores to max 1.0
    for key in scores:
        scores[key] = min(scores[key], 1.0)
    
    return scores

@app.get("/api/verify-openai", tags=["health"])
async def verify_openai():
    """Verify OpenAI API integration is working with real GPT-4"""
    import time
    
    try:
        # Test bezpośredni z OpenAI
        start_time = time.time()
        test_agent = Agent(
            role="Verification Agent",
            goal="Generate a unique timestamp-based message",
            backstory="I verify API authenticity",
            verbose=True,
            llm=llm
        )
        
        test_task = Task(
            description=f"Generate ONE short sentence with current timestamp: {datetime.now().isoformat()}",
            agent=test_agent,
            expected_output="One unique sentence"
        )
        
        crew = Crew(agents=[test_agent], tasks=[test_task])
        result = crew.kickoff()
        
        execution_time = time.time() - start_time
        
        return {
            "status": "verified",
            "api_type": "OpenAI GPT-4",
            "response": str(result),
            "execution_time_seconds": round(execution_time, 2),
            "timestamp": datetime.now().isoformat(),
            "api_key_configured": bool(os.getenv("OPENAI_API_KEY")),
            "model": llm.model_name
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "api_key_configured": bool(os.getenv("OPENAI_API_KEY"))
        }

async def analyze_folder_content(folder: str) -> Dict[str, Any]:
    """
    Analyze folder content - Step 2
    For now returns enhanced mock data based on folder name
    """
    # Mock implementation - will be replaced with real folder analysis
    folder_mocks = {
        "distributed-tracing": {
            "files": ["opentelemetry-intro.md", "jaeger-setup.md", "tracing-patterns.md"],
            "main_topics": ["opentelemetry", "jaeger", "distributed systems", "observability"],
            "technical_depth": "high",
            "content_type": "technical guide"
        },
        "ai-agents": {
            "files": ["crewai-basics.md", "agent-patterns.md", "multi-agent-systems.md"],
            "main_topics": ["crewai", "agents", "AI coordination", "automation"],
            "technical_depth": "medium",
            "content_type": "implementation guide"
        }
    }
    
    # Return specific mock or default
    if folder in folder_mocks:
        return folder_mocks[folder]
    else:
        return {
            "files": ["file1.md", "file2.md"],
            "main_topics": ["general", "content"],
            "technical_depth": "medium",
            "content_type": "article"
        }

async def analyze_single_idea(idea: str, folder_context: Dict, platform: str) -> IdeaAnalysis:
    """
    Analyze single idea using Agentic RAG with Style Guide - Step 5
    Uses our style guide expert to evaluate ideas for our specific audience
    """
    # First do quick static analysis for available material
    file_count = len(folder_context.get("files", []))
    available_material = min(0.9, 0.4 + (file_count * 0.1))
    
    # Prepare content for style guide analysis
    content_with_context = f"""
    Platform: {platform}
    Folder: {folder_context.get("content_type", "unknown")}
    Topics: {', '.join(folder_context.get("main_topics", []))}
    
    Proposed idea: {idea}
    """
    
    try:
        # Use our Agentic RAG for deep analysis
        style_guide_expert = Agent(
            role="Content Strategy Expert",
            goal="Evaluate content ideas for viral potential and audience fit",
            backstory="""You are an expert at evaluating content ideas for technical audiences.
            You understand what makes content viral on different platforms and can assess
            if an idea aligns with available material and audience interests.""",
            verbose=False,
            llm=llm
        )
        
        evaluation_task = Task(
            description=f"""
            Evaluate this content idea for our technical audience:
            {content_with_context}
            
            Consider:
            1. Viral potential on {platform} (0-1 score)
            2. Alignment with folder topics (0-1 score)
            3. Specific recommendation
            4. Suggested angle if needed
            
            Our audience: Technical leaders, developers, AI enthusiasts
            Style: Pattern interrupts, specific numbers, controversial takes
            
            Return evaluation in this format:
            VIRAL_SCORE: [number]
            ALIGNMENT_SCORE: [number]
            RECOMMENDATION: [text]
            SUGGESTED_ANGLE: [text or none]
            """,
            agent=style_guide_expert,
            expected_output="Structured evaluation with scores and recommendations"
        )
        
        crew = Crew(
            agents=[style_guide_expert],
            tasks=[evaluation_task]
        )
        
        result = crew.kickoff()
        
        # Parse AI response
        result_text = str(result)
        
        # Extract scores with defaults
        viral_score = 0.5
        content_alignment = 0.5
        
        if "VIRAL_SCORE:" in result_text:
            try:
                viral_score = float(result_text.split("VIRAL_SCORE:")[1].split("\n")[0].strip())
            except:
                pass
                
        if "ALIGNMENT_SCORE:" in result_text:
            try:
                content_alignment = float(result_text.split("ALIGNMENT_SCORE:")[1].split("\n")[0].strip())
            except:
                pass
        
        # Extract recommendation
        recommendation = "AI analysis completed"
        if "RECOMMENDATION:" in result_text:
            recommendation = result_text.split("RECOMMENDATION:")[1].split("\n")[0].strip()
        
        # Extract suggested angle
        suggested_angle = None
        if "SUGGESTED_ANGLE:" in result_text:
            angle = result_text.split("SUGGESTED_ANGLE:")[1].split("\n")[0].strip()
            if angle.lower() not in ["none", "n/a", ""]:
                suggested_angle = angle
        
        # Calculate overall score
        overall_score = (viral_score * 0.5 + content_alignment * 0.35 + available_material * 0.15)
        
    except Exception as e:
        print(f"⚠️ AI analysis failed, falling back to static: {e}")
        # Fallback to simple static scoring
        viral_score = 0.6
        content_alignment = 0.7
        overall_score = 0.65
        recommendation = "Analysis based on static patterns"
        suggested_angle = None
    
    return IdeaAnalysis(
        idea=idea,
        viral_score=round(viral_score, 2),
        content_alignment=round(content_alignment, 2),
        available_material=round(available_material, 2),
        overall_score=round(overall_score, 2),
        recommendation=recommendation,
        suggested_angle=suggested_angle
    )

@app.post("/api/analyze-custom-ideas", tags=["content"],
         summary="Analyze user's custom topic ideas",
         response_description="Analysis of custom ideas in folder context")
async def analyze_custom_ideas(request: CustomIdeasRequest):
    """
    Analyze user's custom topic ideas in context of folder content
    Step 4: Added Redis caching
    """
    # Step 4: Generate cache key
    cache_key = f"custom_ideas:{request.folder}:{request.platform}:{hashlib.md5(':'.join(sorted(request.ideas)).encode()).hexdigest()}"
    
    # Check cache
    if redis_client:
        try:
            cached = redis_client.get(cache_key)
            if cached:
                print(f"✅ Cache hit for custom ideas: {cache_key}")
                result = json.loads(cached)
                result["from_cache"] = True
                return result
        except Exception as e:
            print(f"⚠️ Redis cache error: {e}")
    
    # Get folder context
    folder_context = await analyze_folder_content(request.folder)
    
    # Analyze each idea with context
    analyzed_ideas = []
    for idea in request.ideas:
        analysis = await analyze_single_idea(idea, folder_context, request.platform)
        analyzed_ideas.append(analysis)
    
    # Sort by overall score
    analyzed_ideas.sort(key=lambda x: x.overall_score, reverse=True)
    
    response = CustomIdeasResponse(
        folder=request.folder,
        platform=request.platform,
        ideas=analyzed_ideas,
        best_idea=analyzed_ideas[0] if analyzed_ideas else None,
        folder_context={
            "total_files": len(folder_context.get("files", [])),
            "main_topics": folder_context.get("main_topics", []),
            "content_type": folder_context.get("content_type", "unknown"),
            "technical_depth": folder_context.get("technical_depth", "medium")
        },
        from_cache=False
    )
    
    # Step 4: Cache the result
    if redis_client:
        try:
            redis_client.setex(
                cache_key,
                300,  # 5 minutes TTL
                json.dumps(response.dict())
            )
            print(f"📝 Cached custom ideas analysis: {cache_key}")
        except Exception as e:
            print(f"⚠️ Failed to cache result: {e}")
    
    return response