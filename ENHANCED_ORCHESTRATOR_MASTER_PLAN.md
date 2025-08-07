# 🎯 ENHANCED ORCHESTRATOR MASTER PLAN
## Multi-Channel Publisher z Image Processing, Presenton Integration i Platform-Specific Content

**Status**: COMPREHENSIVE IMPLEMENTATION PLAN  
**Version**: 1.0  
**Created**: 2025-08-07  
**Estimated Timeline**: 2-3 tygodnie (mikroprzyrostowe zadania atomowe)

---

## 📊 STAN OBECNY - ANALIZA SUBPROJECTS

### ✅ **Publisher (Multi-Channel) - PRODUCTION READY**
- **Status**: FAZA 4 UKOŃCZONA (100%) - Core Platform Complete
- **Komponenty gotowe**:
  - ✅ Orchestrator API (FastAPI, port 8085) - 31/32 testy passing
  - ✅ Redis Queue System (5 queues) - pełna implementacja
  - ✅ Worker Delegation - HTTP-based platform routing
  - ✅ Twitter Adapter - Typefully API, auto-publikacja potwierdzona
  - ✅ Ghost Adapter - Complete CMS integration, Task 4.5 image upload WORKING
  - ✅ Error Handling - 69 structured error codes
- **Gaps**: Brak image processing pipeline, brak Presenton integration

### ✅ **AI Writing Flow - PRODUCTION READY** 
- **Status**: Phase 4 Complete + Knowledge Base Integration
- **Komponenty gotowe**:
  - ✅ CrewAI Agents (Research, Writer, Style, Quality) - 227 tests passing
  - ✅ Linear Flow Pattern - zero infinite loops
  - ✅ Knowledge Base Integration - hybrid search 3705x speedup
  - ✅ Monitoring Stack - real-time KPIs, alerting
  - ✅ API Endpoints - FastAPI localhost:8003
- **Current Output**: Standard content format (text, HTML)
- **Gap**: Brak platform-specific content generation (LinkedIn prompt vs direct content)

### ⚠️ **Presenton - SKELETON ONLY**
- **Status**: Minimal implementation
- **Obecny stan**: 
  - ⚠️ Tylko README.md w folderze głównym
  - ✅ LinkedIn integration exists: `linkedin/services/presenton.py` (complete PPTX→PDF service)
- **Funkcjonalność**: Download PPTX URLs + konwersja do PDF
- **Gap**: Brak API service, brak prompt→presentation generation

### ✅ **LinkedIn Module - PRODUCTION READY**
- **Status**: Complete browser automation + Presenton integration
- **Komponenty gotowe**:
  - ✅ Browser automation (Stagehand + Browserbase) - production ready
  - ✅ Session management - 30+ dni persistence
  - ✅ Presenton service - PPTX download + PDF conversion working
  - ✅ CLI interface - `linkedin-cli.js publish`
- **Gap**: Brak wrapper adapter dla Orchestrator (planned port 8088)

---

## 🎯 MASTERPLAN OBJECTIVES

### **Primary Goal**: Enhanced Orchestrator z Complete Content Pipeline
1. **Image Processing Pipeline** - Pexels API + automatic image integration
2. **Presenton Integration** - Prompt generation + carousel content for LinkedIn  
3. **Platform-Specific Content** - LinkedIn prompts vs direct content
4. **Unified Content Flow** - AI Writing Flow → Enhanced Orchestrator → Platform Adapters

### **Content Flow Philosophy**:
```
AI Writing Flow → Enhanced Orchestrator → Platform Adapters → Publication
       ↓                    ↓                    ↓              ↓
[Content + Placeholders] [Process Images]  [Platform Adapt]  [Publish]
[LinkedIn: Prompts]      [Presenton]       [LinkedIn: PDF]   [Success]
[Others: Direct]         [Pexels Images]   [Others: Text]     [Tracking]
```

### **User Experience**:
- **Default**: LinkedIn content = prompt dla Presenton (carousel generation)
- **Checkbox**: "Treści bezpośrednie" = skip Presenton, publish text directly
- **All platforms**: Automatic image processing z Pexels placeholders

---

## 🏗️ IMPLEMENTATION STRATEGY

### **Phase 1: Enhanced Orchestrator Core (Week 1)**
Rozszerz istniejący Orchestrator o image processing i content differentiation

### **Phase 2: Presenton Service Implementation (Week 1-2)** 
Zbuduj dedykowany Presenton microservice z prompt→presentation API

### **Phase 3: AI Writing Flow Integration (Week 2)**
Extend AI Writing Flow o platform-specific content generation

### **Phase 4: End-to-End Integration (Week 3)**
Complete pipeline testing i production deployment

---

## 📋 ATOMIC TASKS BREAKDOWN

### **🔧 PHASE 1: ENHANCED ORCHESTRATOR CORE**

#### **Task 1.1: Image Processing Pipeline**
**Service**: Publisher Orchestrator  
**Estimated Time**: 2-3 dni  
**Priority**: HIGH

**Implementacja**:
```python
# publisher/src/orchestrator/image_processor.py
class ImageProcessor:
    def __init__(self):
        self.pexels_client = PexelsClient(api_key=os.getenv("PEXELS_API_KEY"))
        self.shared_storage = "/tmp/publisher_images"
        self.supported_formats = ["jpg", "jpeg", "png", "webp"]
    
    async def process_placeholders(self, content: str) -> Tuple[str, Dict[str, str]]:
        """
        Find placeholder:keyword patterns and download images
        Returns: (content_with_local_paths, image_mapping)
        """
        # 1. Extract placeholder:keyword patterns using regex
        # 2. Download images from Pexels API
        # 3. Store in shared storage with unique filenames
        # 4. Return mapping for platform-specific processing
        
    async def finalize_for_platform(self, content: str, platform: str, image_mapping: Dict) -> str:
        """Platform-specific image finalization"""
        if platform == "ghost":
            return await self.ghost_image_upload(content, image_mapping)
        elif platform == "twitter":
            return await self.twitter_media_attach(content, image_mapping)
        elif platform == "linkedin":
            return await self.linkedin_media_process(content, image_mapping)
        # etc.
```

**Deliverables**:
- [ ] `ImageProcessor` class z Pexels API integration
- [ ] Shared volume mount `/tmp/publisher_images` w docker-compose.yml
- [ ] Placeholder pattern extraction (regex `placeholder:keyword`)
- [ ] Platform-specific image finalization methods
- [ ] Environment variables: `PEXELS_API_KEY`

**Success Metrics**:
- [ ] Placeholder detection accuracy: >95%
- [ ] Pexels API success rate: >98%
- [ ] Image download speed: <5s per image
- [ ] Shared storage access: All adapters can read images

**Tests**:
```python
def test_placeholder_extraction():
    content = '<img src="placeholder:startup-office" alt="Office" />'
    placeholders = image_processor.extract_placeholders(content)
    assert "placeholder:startup-office" in placeholders

def test_pexels_image_download():
    image_path = await image_processor.download_from_pexels("startup office")
    assert Path(image_path).exists()
    assert Path(image_path).suffix in ['.jpg', '.jpeg', '.png']

def test_platform_specific_processing():
    # Test Ghost URL replacement
    # Test Twitter media attachment  
    # Test LinkedIn local file handling
```

---

#### **Task 1.2: Content Differentiation Logic**
**Service**: Publisher Orchestrator  
**Estimated Time**: 1-2 dni  
**Priority**: HIGH

**Implementacja**:
```python
# publisher/src/orchestrator/content_processor.py
class ContentProcessor:
    def __init__(self):
        self.image_processor = ImageProcessor()
        self.presenton_client = PresentonClient()
    
    async def process_content_request(self, request: PublicationRequest) -> Dict[str, Any]:
        """Main content processing pipeline"""
        
        processed_content = {}
        
        for platform, config in request.platforms.items():
            if not config.enabled:
                continue
                
            if platform == "linkedin":
                # LinkedIn-specific logic
                if config.get("direct_content", False):  # Checkbox checked
                    # Process as direct content
                    processed_content[platform] = await self.process_direct_content(
                        request.topic, platform
                    )
                else:
                    # Process as Presenton prompt
                    processed_content[platform] = await self.process_presenton_content(
                        request.topic, config
                    )
            else:
                # Other platforms - always direct content
                processed_content[platform] = await self.process_direct_content(
                    request.topic, platform
                )
        
        return processed_content
    
    async def process_presenton_content(self, topic: Topic, config: Dict) -> Dict:
        """Generate Presenton prompt and handle carousel creation"""
        # 1. Convert topic to Presenton prompt format
        # 2. Call Presenton API to generate presentation
        # 3. Download PPTX and convert to PDF
        # 4. Return PDF path for LinkedIn upload
        
    async def process_direct_content(self, topic: Topic, platform: str) -> Dict:
        """Process regular text content with image placeholders"""
        # 1. Process image placeholders
        # 2. Call platform-specific image finalization
        # 3. Return ready-to-publish content
```

**Deliverables**:
- [ ] `ContentProcessor` class z platform differentiation
- [ ] LinkedIn prompt generation logic
- [ ] Direct content processing pipeline
- [ ] Integration z `PublicationRequest` model (add `direct_content` flag)

**Success Metrics**:
- [ ] Platform routing accuracy: 100%
- [ ] LinkedIn prompt quality: Manual review >8/10
- [ ] Processing speed: <10s per platform
- [ ] Error handling: All exceptions properly caught

**Tests**:
```python
def test_linkedin_prompt_generation():
    topic = Topic(title="AI trends", description="Latest AI developments")
    prompt = await content_processor.generate_presenton_prompt(topic)
    assert "slide" in prompt.lower()
    assert len(prompt) > 100  # Minimum prompt length

def test_platform_differentiation():
    request = PublicationRequest(
        platforms={
            "linkedin": {"enabled": True, "direct_content": False},
            "twitter": {"enabled": True}
        }
    )
    result = await content_processor.process_content_request(request)
    assert "presenton_prompt" in result["linkedin"]
    assert "text" in result["twitter"]
```

---

#### **Task 1.3: Enhanced API Endpoints**
**Service**: Publisher Orchestrator  
**Estimated Time**: 1 dzień  
**Priority**: MEDIUM

**Implementacja**:
```python
# publisher/src/orchestrator/main.py - Enhanced endpoints
@app.post("/publish/enhanced", response_model=EnhancedPublicationResponse)
async def publish_enhanced(request: EnhancedPublicationRequest):
    """Enhanced publish endpoint with image processing and content differentiation"""
    
    # 1. Process images and content
    content_processor = ContentProcessor()
    processed_content = await content_processor.process_content_request(request)
    
    # 2. Create platform-specific jobs
    jobs = []
    for platform, content in processed_content.items():
        job = PublicationJob(
            platform=platform,
            content=content,
            # ... other fields
        )
        jobs.append(job)
    
    # 3. Queue jobs (existing logic)
    # ... rest of existing implementation

@app.get("/images/gallery")
async def get_available_images():
    """List available images in shared storage"""
    # For debugging and manual image management

@app.post("/images/upload")
async def upload_custom_image(file: UploadFile):
    """Upload custom image to shared storage"""
    # For manual image uploads
```

**Deliverables**:
- [ ] Enhanced API models (`EnhancedPublicationRequest`, response models)
- [ ] Image gallery endpoint for debugging
- [ ] Custom image upload endpoint
- [ ] Updated OpenAPI documentation

**Success Metrics**:
- [ ] API response time: <1s for enhanced endpoint
- [ ] Request validation: 100% for all invalid inputs
- [ ] Documentation completeness: All endpoints documented

---

### **🏢 PHASE 2: PRESENTON SERVICE IMPLEMENTATION**

#### **Task 2.1: Presenton Service Skeleton**
**Service**: New microservice  
**Estimated Time**: 1 dzień  
**Priority**: HIGH

**Implementacja**:
```python
# presenton/src/main.py
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Presenton API", version="1.0.0")

class PresentationRequest(BaseModel):
    prompt: str
    slides_count: int = 5
    template: str = "business"
    style: str = "modern"

class PresentationResponse(BaseModel):
    presentation_id: str
    pptx_url: str
    status: str
    created_at: str

@app.post("/generate", response_model=PresentationResponse)
async def generate_presentation(request: PresentationRequest):
    """Generate presentation from prompt"""
    # Implementation will use actual Presenton logic
    
@app.get("/health")
async def health_check():
    """Service health check"""
    return {"status": "healthy", "service": "presenton"}
```

**Deliverables**:
- [ ] FastAPI skeleton w `presenton/` directory
- [ ] Docker setup z `Dockerfile` i service w `docker-compose.yml`
- [ ] Basic API models dla presentation generation
- [ ] Health check endpoint
- [ ] Port allocation: 8089

**Success Metrics**:
- [ ] Service startup time: <10s
- [ ] Health check response: <100ms
- [ ] Docker build success: 100%

**Tests**:
```python
def test_service_startup():
    response = requests.get("http://localhost:8089/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
```

---

#### **Task 2.2: Presentation Generation Logic**
**Service**: Presenton API  
**Estimated Time**: 3-4 dni  
**Priority**: HIGH

**Implementacja** (pseudo-code, actual implementation depends on Presenton technology):
```python
# presenton/src/generator.py
class PresentationGenerator:
    def __init__(self):
        # Initialize actual Presenton logic/API
        self.templates = self.load_templates()
        self.ai_client = OpenAI()  # For prompt enhancement
    
    async def generate_from_prompt(self, prompt: str, config: PresentationConfig) -> str:
        """
        Generate presentation from text prompt
        
        Args:
            prompt: User-provided prompt (from AI Writing Flow)
            config: Generation configuration (slides, template, style)
            
        Returns:
            URL to generated PPTX file
        """
        
        # 1. Enhance prompt using AI if needed
        enhanced_prompt = await self.enhance_prompt(prompt, config)
        
        # 2. Break down into slides
        slides_content = await self.extract_slides(enhanced_prompt, config.slides_count)
        
        # 3. Generate presentation (actual Presenton logic)
        presentation_id = await self.create_presentation(slides_content, config)
        
        # 4. Return PPTX URL
        return f"http://localhost:8089/presentations/{presentation_id}/download"
    
    async def enhance_prompt(self, prompt: str, config: PresentationConfig) -> str:
        """Use AI to enhance prompt for better slide generation"""
        system_prompt = f"""
        Convert this content into a {config.slides_count}-slide presentation prompt.
        Focus on: clear structure, engaging titles, bullet points, call-to-action.
        Template: {config.template}, Style: {config.style}
        """
        
        response = await self.ai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
        )
        
        return response.choices[0].message.content
```

**Deliverables**:
- [ ] `PresentationGenerator` class z AI enhancement
- [ ] Prompt→slides breakdown logic
- [ ] Integration z actual Presenton generation logic
- [ ] PPTX file storage i serving (`/presentations/{id}/download`)
- [ ] Error handling dla generation failures

**Success Metrics**:
- [ ] Generation success rate: >90%
- [ ] Generation time: <60s per presentation
- [ ] PPTX file quality: Manual review >7/10
- [ ] AI prompt enhancement effectiveness: A/B test improvement

**Tests**:
```python
def test_presentation_generation():
    prompt = "AI trends in 2025: machine learning, automation, future"
    config = PresentationConfig(slides_count=5, template="business")
    
    pptx_url = await generator.generate_from_prompt(prompt, config)
    
    assert pptx_url.startswith("http://localhost:8089/presentations/")
    
    # Verify PPTX is downloadable
    response = requests.get(pptx_url)
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith("application/")

def test_prompt_enhancement():
    basic_prompt = "AI is important"
    config = PresentationConfig(slides_count=3)
    
    enhanced = await generator.enhance_prompt(basic_prompt, config)
    
    assert len(enhanced) > len(basic_prompt)
    assert "slide" in enhanced.lower()
```

---

#### **Task 2.3: Orchestrator Integration**
**Service**: Publisher Orchestrator + Presenton API  
**Estimated Time**: 1 dzień  
**Priority**: HIGH

**Implementacja**:
```python
# publisher/src/orchestrator/presenton_client.py
class PresentonClient:
    def __init__(self):
        self.base_url = "http://presenton:8089"  # Docker network
        self.timeout = 120  # 2 minutes for generation
    
    async def generate_presentation(self, prompt: str, config: Dict) -> str:
        """
        Generate presentation and return PPTX URL
        
        Args:
            prompt: Generated prompt from AI Writing Flow
            config: LinkedIn platform configuration
            
        Returns:
            URL to generated PPTX file
        """
        
        request_data = {
            "prompt": prompt,
            "slides_count": config.get("slides_count", 5),
            "template": config.get("template", "business"),
            "style": config.get("style", "modern")
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/generate",
                json=request_data,
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            ) as response:
                
                if response.status != 200:
                    raise PresentonError(f"Generation failed: {response.status}")
                
                result = await response.json()
                return result["pptx_url"]
    
    async def health_check(self) -> bool:
        """Check if Presenton service is available"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/health") as response:
                    return response.status == 200
        except:
            return False

# Integration w ContentProcessor
async def process_presenton_content(self, topic: Topic, config: Dict) -> Dict:
    """Generate Presenton prompt and handle carousel creation"""
    
    # 1. Generate LinkedIn-specific prompt from topic
    prompt = await self.generate_linkedin_prompt(topic)
    
    # 2. Call Presenton API
    presenton_client = PresentonClient()
    pptx_url = await presenton_client.generate_presentation(prompt, config)
    
    # 3. Use existing LinkedIn Presenton service for PDF conversion
    linkedin_presenton = get_presenton_service()  # from linkedin module
    result = await linkedin_presenton.process_presenton_content(pptx_url)
    
    return {
        "type": "presenton_carousel",
        "prompt": prompt,
        "pptx_url": pptx_url,
        "pdf_path": result["pdf_path"],
        "ready_for_linkedin": True
    }
```

**Deliverables**:
- [ ] `PresentonClient` class w Orchestrator
- [ ] Integration z `ContentProcessor`
- [ ] Error handling i fallback logic
- [ ] Health checks dla Presenton service dependency

**Success Metrics**:
- [ ] Integration success rate: >95%
- [ ] End-to-end processing time: <90s (prompt→PDF)
- [ ] Error handling coverage: All Presenton failures handled gracefully

**Tests**:
```python
def test_orchestrator_presenton_integration():
    topic = Topic(title="AI Revolution", description="Impact of AI on business")
    config = {"slides_count": 4, "template": "business"}
    
    result = await content_processor.process_presenton_content(topic, config)
    
    assert result["type"] == "presenton_carousel"
    assert result["pdf_path"].endswith(".pdf")
    assert Path(result["pdf_path"]).exists()
    assert result["ready_for_linkedin"] is True
```

---

### **🤖 PHASE 3: AI WRITING FLOW INTEGRATION**

#### **Task 3.1: Platform-Specific Content Generation**
**Service**: AI Writing Flow  
**Estimated Time**: 2-3 dni  
**Priority**: HIGH

**Implementacja**:
```python
# kolegium/ai_writing_flow/src/ai_writing_flow/platform_optimizer.py
class PlatformOptimizer:
    """Generate platform-specific content variations"""
    
    def __init__(self):
        self.style_guide = self.load_style_guide()
        self.platform_configs = {
            "linkedin": {
                "prompt_mode": True,  # Default for LinkedIn
                "max_length": 3000,
                "focus": "professional, slide-friendly",
                "structure": "presentation_outline"
            },
            "twitter": {
                "prompt_mode": False,
                "max_length": 280,
                "focus": "viral, engaging",
                "structure": "thread_ready"
            },
            "ghost": {
                "prompt_mode": False,
                "max_length": 10000,
                "focus": "detailed, SEO-friendly",
                "structure": "blog_article"
            }
        }
    
    async def generate_for_platform(self, topic: Topic, platform: str, direct_content: bool = None) -> Dict:
        """
        Generate platform-specific content
        
        Args:
            topic: Base topic from user
            platform: Target platform
            direct_content: Override default behavior for LinkedIn
            
        Returns:
            Platform-optimized content
        """
        
        config = self.platform_configs[platform].copy()
        
        # Override LinkedIn behavior if direct_content specified
        if platform == "linkedin" and direct_content is not None:
            config["prompt_mode"] = not direct_content
        
        if config["prompt_mode"]:
            return await self.generate_presentation_prompt(topic, config)
        else:
            return await self.generate_direct_content(topic, config)
    
    async def generate_presentation_prompt(self, topic: Topic, config: Dict) -> Dict:
        """Generate Presenton-ready prompt for LinkedIn carousel"""
        
        system_prompt = f"""
        Create a presentation prompt for a {config.get('slides_count', 5)}-slide LinkedIn carousel.
        
        Topic: {topic.title}
        Description: {topic.description}
        
        Format as a detailed prompt that includes:
        1. Clear slide structure
        2. Engaging titles for each slide  
        3. Key points and bullet items
        4. Visual suggestions
        5. Call-to-action
        
        Focus: {config['focus']}
        Max length: {config['max_length']} characters
        
        The output will be used to generate a PowerPoint presentation.
        """
        
        # Use existing CrewAI agents with modified system prompt
        result = await self.writer_agent.execute_task(
            task_description=system_prompt,
            context={"topic": topic, "platform": "linkedin_carousel"}
        )
        
        return {
            "type": "presentation_prompt",
            "prompt": result.content,
            "slides_count": config.get("slides_count", 5),
            "platform": "linkedin",
            "ready_for_presenton": True
        }
    
    async def generate_direct_content(self, topic: Topic, config: Dict) -> Dict:
        """Generate direct text content for publication"""
        
        # Use existing AI Writing Flow logic with platform-specific optimization
        result = await self.writer_agent.execute_task(
            task_description=f"Create {config['focus']} content about {topic.title}",
            context={"topic": topic, "platform": config['structure']}
        )
        
        return {
            "type": "direct_content",
            "content": result.content,
            "html": result.html if hasattr(result, 'html') else None,
            "platform": config['structure'],
            "ready_for_publication": True
        }
```

**Deliverables**:
- [ ] `PlatformOptimizer` class w AI Writing Flow
- [ ] LinkedIn prompt generation logic
- [ ] Platform-specific content optimization
- [ ] Integration z existing CrewAI agents
- [ ] Updated API endpoints w AI Writing Flow

**Success Metrics**:
- [ ] Content quality (manual review): >8/10 for each platform
- [ ] Prompt effectiveness: LinkedIn carousels rate >7/10
- [ ] Generation time: <30s per platform
- [ ] Platform optimization accuracy: Content fits platform constraints 100%

**Tests**:
```python
def test_linkedin_prompt_generation():
    topic = Topic(title="Remote Work Trends", description="Future of remote work")
    
    result = await platform_optimizer.generate_for_platform(topic, "linkedin", direct_content=False)
    
    assert result["type"] == "presentation_prompt"
    assert result["ready_for_presenton"] is True
    assert "slide" in result["prompt"].lower()
    assert len(result["prompt"]) > 200

def test_platform_content_variations():
    topic = Topic(title="AI Ethics", description="Ethical considerations in AI")
    
    # Test all platforms
    linkedin_result = await platform_optimizer.generate_for_platform(topic, "linkedin", direct_content=True)
    twitter_result = await platform_optimizer.generate_for_platform(topic, "twitter")
    ghost_result = await platform_optimizer.generate_for_platform(topic, "ghost")
    
    # Verify platform-specific characteristics
    assert len(twitter_result["content"]) <= 280  # Twitter limit
    assert len(ghost_result["content"]) > len(linkedin_result["content"])  # Blog vs social
    assert linkedin_result["type"] == "direct_content"  # direct_content=True
```

---

#### **Task 3.2: Enhanced API Integration**
**Service**: AI Writing Flow  
**Estimated Time**: 1 dzień  
**Priority**: MEDIUM

**Implementacja**:
```python
# kolegium/ai_writing_flow/src/ai_writing_flow/main.py - Enhanced endpoints
@app.post("/generate/multi-platform", response_model=MultiPlatformResponse)
async def generate_multi_platform_content(request: MultiPlatformRequest):
    """
    Generate content for multiple platforms simultaneously
    
    Enhanced endpoint for Publisher Orchestrator integration
    """
    
    platform_optimizer = PlatformOptimizer()
    results = {}
    
    for platform, config in request.platforms.items():
        if config.enabled:
            result = await platform_optimizer.generate_for_platform(
                topic=request.topic,
                platform=platform,
                direct_content=config.get("direct_content")
            )
            results[platform] = result
    
    return MultiPlatformResponse(
        request_id=request.request_id,
        topic=request.topic,
        platform_content=results,
        generation_time=time.time() - request.start_time,
        quality_score=await self.calculate_quality_score(results)
    )

@app.post("/generate/linkedin-prompt", response_model=LinkedInPromptResponse)
async def generate_linkedin_prompt(request: LinkedInPromptRequest):
    """
    Specialized endpoint for LinkedIn carousel prompt generation
    """
    
    platform_optimizer = PlatformOptimizer()
    result = await platform_optimizer.generate_presentation_prompt(
        topic=request.topic,
        config={
            "slides_count": request.slides_count,
            "focus": request.focus or "professional, slide-friendly",
            "template": request.template or "business"
        }
    )
    
    return LinkedInPromptResponse(
        prompt=result["prompt"],
        slides_count=result["slides_count"],
        estimated_generation_time=60,  # seconds for Presenton
        ready_for_presenton=True
    )
```

**Deliverables**:
- [ ] Multi-platform generation endpoint
- [ ] Specialized LinkedIn prompt endpoint  
- [ ] Enhanced API models (`MultiPlatformRequest`, response models)
- [ ] Integration hooks dla Publisher Orchestrator

**Success Metrics**:
- [ ] API response time: <45s for multi-platform generation
- [ ] Concurrent platform processing: All platforms generated in parallel
- [ ] Error handling: Partial failures don't break entire request

---

### **🔗 PHASE 4: END-TO-END INTEGRATION**

#### **Task 4.1: Complete Pipeline Testing**
**Service**: All services  
**Estimated Time**: 2 dni  
**Priority**: HIGH

**Test Scenarios**:
```python
# tests/integration/test_complete_pipeline.py
class TestCompletePipeline:
    
    async def test_linkedin_carousel_pipeline(self):
        """
        Test complete LinkedIn carousel pipeline:
        AI Writing Flow → Orchestrator → Presenton → LinkedIn
        """
        
        # 1. Create publication request
        request = EnhancedPublicationRequest(
            topic=Topic(
                title="Future of Remote Work",
                description="Trends and predictions for remote work in 2025"
            ),
            platforms={
                "linkedin": {
                    "enabled": True,
                    "direct_content": False,  # Use Presenton
                    "slides_count": 5,
                    "template": "business"
                }
            }
        )
        
        # 2. Call Enhanced Orchestrator
        response = await orchestrator_client.post("/publish/enhanced", json=request.dict())
        assert response.status_code == 200
        
        publication_id = response.json()["publication_id"]
        
        # 3. Wait for processing and verify completion
        await self.wait_for_completion(publication_id, timeout=120)
        
        # 4. Verify LinkedIn post was created with PDF
        status = await orchestrator_client.get(f"/publication/{publication_id}")
        linkedin_job = next(job for job in status.json()["platform_jobs"] if job["platform"] == "linkedin")
        
        assert linkedin_job["status"] == "completed"
        assert "pdf_path" in linkedin_job["result"]
        assert Path(linkedin_job["result"]["pdf_path"]).exists()
    
    async def test_multi_platform_with_images(self):
        """
        Test multi-platform pipeline with image processing:
        Content with placeholders → Image download → Platform adaptation
        """
        
        request = EnhancedPublicationRequest(
            topic=Topic(
                title="AI Startup Office Trends",
                description="Modern workspace design with AI integration",
                content_template='<h1>Office Trends</h1><img src="placeholder:modern-office" alt="Office" /><p>AI integration in workspaces...</p>'
            ),
            platforms={
                "twitter": {"enabled": True},
                "ghost": {"enabled": True},
                "linkedin": {"enabled": True, "direct_content": True}  # Direct content, no Presenton
            }
        )
        
        response = await orchestrator_client.post("/publish/enhanced", json=request.dict())
        publication_id = response.json()["publication_id"]
        
        await self.wait_for_completion(publication_id, timeout=90)
        
        # Verify all platforms completed with processed images
        status = await orchestrator_client.get(f"/publication/{publication_id}")
        
        for job in status.json()["platform_jobs"]:
            assert job["status"] == "completed"
            
            if job["platform"] == "ghost":
                # Ghost should have Ghost URLs
                assert "ghost.io" in job["result"]["content"]
            elif job["platform"] == "twitter":
                # Twitter should have media attachments
                assert "media_urls" in job["result"]
            elif job["platform"] == "linkedin":
                # LinkedIn should have processed text content
                assert job["result"]["type"] == "direct_content"
```

**Deliverables**:
- [ ] Complete integration test suite
- [ ] Performance benchmarks dla całego pipeline
- [ ] Error handling tests dla każdego failure scenario
- [ ] Documentation z example requests/responses

**Success Metrics**:
- [ ] End-to-end success rate: >95%
- [ ] Total pipeline time: <150s for complete carousel generation
- [ ] Error recovery: All partial failures handled gracefully
- [ ] Performance under load: 5 concurrent requests handled successfully

---

#### **Task 4.2: Production Deployment**
**Service**: All services  
**Estimated Time**: 1 dzień  
**Priority**: MEDIUM

**Implementacja**:
```yaml
# Enhanced docker-compose.yml
version: '3.8'

services:
  # Existing services...
  
  presenton:
    build: ./presenton
    ports:
      - "8089:8089"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - PRESENTON_TEMPLATES_PATH=/app/templates
    volumes:
      - presenton_data:/app/data
      - shared_images:/tmp/publisher_images
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8089/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    depends_on:
      - redis
  
  orchestrator:
    # Enhanced with new environment variables
    environment:
      - PEXELS_API_KEY=${PEXELS_API_KEY}
      - PRESENTON_URL=http://presenton:8089
    volumes:
      - shared_images:/tmp/publisher_images
    depends_on:
      - presenton
      - redis
  
  # Enhanced adapters with shared volume
  ghost-adapter:
    volumes:
      - shared_images:/tmp/publisher_images
  
  twitter-adapter:
    volumes:
      - shared_images:/tmp/publisher_images

volumes:
  presenton_data:
  shared_images:
```

**Deliverables**:
- [ ] Production docker-compose configuration
- [ ] Environment variables documentation
- [ ] Health check configuration dla wszystkich services
- [ ] Volume mounts dla shared image storage
- [ ] Production-ready logging configuration

**Success Metrics**:
- [ ] All services start successfully: <60s total startup time
- [ ] Health checks pass: 100% for all services
- [ ] Volume sharing works: All adapters can access shared images
- [ ] Production environment compatibility: Works w staging environment

---

## 📊 FINAL SUCCESS METRICS & VALIDATION

### **Business Metrics**
- [ ] **Content Quality**: Manual review scores >8/10 dla każdego typu contentu
- [ ] **Processing Speed**: <150s dla complete LinkedIn carousel pipeline
- [ ] **Platform Coverage**: Support for 4+ platforms z specialized handling
- [ ] **User Experience**: Single API call creates multi-platform content

### **Technical Metrics** 
- [ ] **Service Reliability**: >99% uptime dla każdego microservice
- [ ] **Integration Success**: >95% end-to-end pipeline success rate
- [ ] **Error Handling**: 100% failure scenarios handled gracefully
- [ ] **Performance**: Support for 10+ concurrent content generation requests

### **Feature Completeness**
- [ ] ✅ **Image Processing**: Pexels placeholder→real images w all platforms
- [ ] ✅ **Presenton Integration**: LinkedIn prompt→carousel→PDF pipeline working  
- [ ] ✅ **Platform Differentiation**: LinkedIn prompts vs direct content dla innych platform
- [ ] ✅ **User Control**: Checkbox dla "treści bezpośrednie" working
- [ ] ✅ **Backward Compatibility**: Existing Publisher functionality preserved

### **Documentation & Testing**
- [ ] **Complete Test Coverage**: >90% code coverage dla new components
- [ ] **API Documentation**: All new endpoints documented w OpenAPI
- [ ] **Integration Examples**: Working examples dla każdego use case
- [ ] **Deployment Guide**: Step-by-step production deployment instructions

---

## 🚀 IMMEDIATE NEXT STEPS

### **Week 1 Priorities**
1. **Start Task 1.1**: Image Processing Pipeline (highest impact)
2. **Parallel Task 2.1**: Presenton Service Skeleton (enables LinkedIn carousel)
3. **Document architecture**: Update wszystkich README files

### **Dependencies & Blockers**
- **Pexels API Key**: Required dla image processing
- **Presenton Technology**: Need to clarify actual Presenton implementation approach
- **Testing Environment**: Stage environment dla integration testing

### **Resource Requirements**
- **Development Time**: 2-3 tygodnie z 1 developer working full-time
- **Infrastructure**: Docker resources dla nowego Presenton service
- **API Keys**: Pexels API access (free tier available)

---

**Status**: COMPREHENSIVE PLAN COMPLETE ✅  
**Ready for Implementation**: Task 1.1 może rozpocząć się natychmiast  
**Next Action**: Rozpocznij Task 1.1 Image Processing Pipeline implementation
