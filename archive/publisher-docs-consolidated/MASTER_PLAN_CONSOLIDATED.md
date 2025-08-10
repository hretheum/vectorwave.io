# Multi-Channel Publisher – MASTER PLAN (Complete & Consolidated)

## 🚀 **STATUS OVERVIEW**

### ✅ **COMPLETED PHASES (Production Ready)**
- **Faza 1**: Substack Adapter ✅ **COMPLETED** - Full browserbase/stagehand integration
- **Faza 2**: Twitter/X Adapter ✅ **COMPLETED** - Typefully API integration  
- **Faza 3**: Ghost Adapter ✅ **COMPLETED** - Complete CMS with image upload
- **Faza 4**: Orchestrator API ✅ **COMPLETED** - Multi-platform publication system

### 🚧 **CURRENT PRIORITY: Enhanced Orchestrator (Faza 4.5)**
**Image Processing + Presenton Integration + AI Writing Flow Extensions**

### ⏳ **PLANNED PHASES**
- **Faza 5**: Monitoring & Alerting
- **Faza 6**: Enhanced E2E Integration  
- **Faza 7**: LinkedIn Module Integration
- **Faza 8+**: Advanced Features

---

## 🎯 **FAZA 4.5: ENHANCED ORCHESTRATOR - COMPLETE IMPLEMENTATION PLAN**

### **OVERVIEW & ARCHITECTURE**

**Enhanced Content Pipeline**:
```
AI Writing Flow → Enhanced Orchestrator → Platform Adapters → Publication
       ↓                    ↓                    ↓              ↓
[Content + Placeholders] [Process Images]  [Platform Adapt]  [Publish]
[LinkedIn: Prompts]      [Presenton]       [LinkedIn: PDF]   [Success]
[Others: Direct]         [Pexels Images]   [Others: Text]     [Tracking]
```

**Key Innovations**:
- **Image Processing Pipeline**: Pexels API + automatic placeholder→image conversion
- **Presenton Integration**: LinkedIn prompt→presentation→PDF pipeline
- **Content Differentiation**: LinkedIn carousel prompts vs direct content
- **User Control**: Checkbox "treści bezpośrednie" dla manual override

---

## 📋 **ATOMIC TASKS BREAKDOWN - ENHANCED ORCHESTRATOR**

### **PHASE 4.5.1: IMAGE PROCESSING PIPELINE (Week 1)**

#### **Zadanie 4.5.1.1: ImageProcessor Implementation** ⏳ **READY TO START**
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
        Returns: (updated_content, {placeholder: local_path})
        """
        import re
        
        # Find all placeholder:keyword patterns
        placeholder_pattern = r'placeholder:(\w+)'
        placeholders = re.findall(placeholder_pattern, content)
        
        image_mapping = {}
        updated_content = content
        
        for keyword in placeholders:
            # Download image from Pexels
            image_path = await self.download_pexels_image(keyword)
            placeholder_tag = f"placeholder:{keyword}"
            
            # Replace with local path marker
            updated_content = updated_content.replace(
                placeholder_tag, 
                f"LOCAL_IMAGE:{image_path}"
            )
            image_mapping[keyword] = image_path
        
        return updated_content, image_mapping
    
    async def download_pexels_image(self, keyword: str) -> str:
        """Download image from Pexels API"""
        try:
            # Search Pexels API
            response = await self.pexels_client.search(keyword, per_page=1)
            
            if response['photos']:
                photo = response['photos'][0]
                image_url = photo['src']['medium']
                
                # Download and save to shared storage
                image_filename = f"{keyword}_{int(time.time())}.jpg"
                image_path = os.path.join(self.shared_storage, image_filename)
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(image_url) as resp:
                        with open(image_path, 'wb') as f:
                            f.write(await resp.read())
                
                return image_path
            else:
                raise Exception(f"No images found for keyword: {keyword}")
                
        except Exception as e:
            logger.error(f"Pexels download failed for {keyword}: {e}")
            # Fallback to placeholder
            return self.create_placeholder_image(keyword)
    
    async def finalize_for_platform(self, content: str, platform: str, image_mapping: Dict) -> str:
        """Platform-specific image URL replacement"""
        
        if platform == "ghost":
            # Upload to Ghost and replace with Ghost URLs
            return await self.process_ghost_images(content, image_mapping)
        
        elif platform == "twitter":
            # Keep local paths for Twitter media attachment
            return content.replace("LOCAL_IMAGE:", "")
        
        elif platform == "linkedin":
            # Keep local paths for Presenton processing  
            return content.replace("LOCAL_IMAGE:", "")
        
        else:
            # Default: return local paths
            return content.replace("LOCAL_IMAGE:", "")
    
    async def process_ghost_images(self, content: str, image_mapping: Dict) -> str:
        """Upload images to Ghost and replace URLs"""
        
        # Use existing Ghost client logic
        from src.adapters.ghost.ghost_client import GhostClient
        
        ghost_client = GhostClient()
        updated_content = content
        
        for keyword, local_path in image_mapping.items():
            try:
                # Upload to Ghost
                upload_result = await ghost_client.upload_image(local_path)
                ghost_url = upload_result['images'][0]['url']
                
                # Replace local path with Ghost URL
                updated_content = updated_content.replace(
                    f"LOCAL_IMAGE:{local_path}",
                    f'<img src="{ghost_url}" alt="{keyword}">'
                )
                
            except Exception as e:
                logger.error(f"Ghost upload failed for {keyword}: {e}")
                # Keep local path as fallback
                pass
        
        return updated_content
```

**Success Metrics**:
- [ ] Placeholder extraction accuracy: >95%
- [ ] Pexels API success rate: >98%  
- [ ] Image processing time: <10s per image
- [ ] Shared storage accessibility: All adapters can access images

**Environment Variables**:
```bash
PEXELS_API_KEY=your_pexels_api_key_here
SHARED_IMAGES_PATH=/tmp/publisher_images
```

**Tests**:
```python
def test_placeholder_processing():
    content = "Check this placeholder:business-meeting image!"
    processor = ImageProcessor()
    
    updated_content, mapping = await processor.process_placeholders(content)
    
    assert "placeholder:business-meeting" not in updated_content
    assert len(mapping) == 1
    assert Path(mapping['business-meeting']).exists()

def test_ghost_image_finalization():
    content = "LOCAL_IMAGE:/tmp/publisher_images/business_123.jpg"
    processor = ImageProcessor()
    
    final_content = await processor.finalize_for_platform(content, "ghost", {})
    
    assert "LOCAL_IMAGE:" not in final_content
    assert "<img src=" in final_content
```

---

#### **Zadanie 4.5.1.2: Shared Volume Integration**
**Estimated Time**: 1 dzień  

**Docker Configuration**:
```yaml
# docker-compose.yml updates
volumes:
  publisher_images:
    driver: local

services:
  orchestrator:
    volumes:
      - publisher_images:/tmp/publisher_images
  
  ghost-adapter:
    volumes:
      - publisher_images:/tmp/publisher_images
      
  twitter-adapter:
    volumes:
      - publisher_images:/tmp/publisher_images
```

**Tests**:
```bash
# Test shared volume accessibility
docker exec orchestrator ls -la /tmp/publisher_images
docker exec ghost-adapter ls -la /tmp/publisher_images
```

---

### **PHASE 4.5.2: PRESENTON SERVICE IMPLEMENTATION (Week 1-2)**

#### **Zadanie 4.5.2.1: Presenton Service Skeleton**
**Estimated Time**: 1 dzień  

**New Microservice Structure**:
```
presenton/
├── src/
│   ├── main.py              # FastAPI application
│   ├── models.py            # Pydantic models
│   ├── presentation_generator.py  # Core logic
│   └── templates/           # PowerPoint templates
├── Dockerfile
├── requirements.txt
└── README.md
```

**Core Implementation**:
```python
# presenton/src/main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uuid
import time

class PresentationRequest(BaseModel):
    prompt: str
    slides_count: int = 5
    template: str = "business"
    topic_title: str

class PresentationResponse(BaseModel):
    presentation_id: str
    pptx_url: str
    pdf_path: str
    slide_count: int
    generation_time: float

app = FastAPI(title="Presenton Service", version="1.0.0")

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "presenton"}

@app.post("/generate", response_model=PresentationResponse)
async def generate_presentation(request: PresentationRequest):
    """Generate PowerPoint from prompt and convert to PDF"""
    
    start_time = time.time()
    presentation_id = str(uuid.uuid4())
    
    try:
        from presentation_generator import PresentationGenerator
        
        generator = PresentationGenerator()
        
        # 1. AI-enhanced prompt processing
        slide_structure = await generator.enhance_prompt(request.prompt, {
            "slides_count": request.slides_count,
            "template": request.template,
            "topic_title": request.topic_title
        })
        
        # 2. Generate PowerPoint
        pptx_path = await generator.generate_pptx(slide_structure)
        
        # 3. Convert to PDF
        pdf_path = await generator.convert_to_pdf(pptx_path)
        
        generation_time = time.time() - start_time
        
        return PresentationResponse(
            presentation_id=presentation_id,
            pptx_url=f"/download/{presentation_id}.pptx",
            pdf_path=pdf_path,
            slide_count=len(slide_structure.get("slides", [])),
            generation_time=generation_time
        )
        
    except Exception as e:
        logger.error(f"Presentation generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/download/{filename}")
async def download_file(filename: str):
    """Download generated presentation files"""
    # File download logic
    pass
```

**Docker Integration**:
```yaml
# docker-compose.yml addition
presenton:
  build: ./presenton
  ports:
    - "8089:8089"
  environment:
    - OPENAI_API_KEY=${OPENAI_API_KEY}
    - PRESENTON_TEMPLATES_PATH=/app/templates
  volumes:
    - publisher_images:/tmp/publisher_images
    - ./presenton/templates:/app/templates
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8089/health"]
    interval: 30s
    timeout: 10s
    retries: 3
```

---

#### **Zadanie 4.5.2.2: AI-Enhanced Presentation Generation**
**Estimated Time**: 2-3 dni  

**Implementation**:
```python
# presenton/src/presentation_generator.py
from openai import AsyncOpenAI
import json
import os
from python_pptx import Presentation
from python_pptx.util import Inches

class PresentationGenerator:
    def __init__(self):
        self.openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.templates_path = os.getenv("PRESENTON_TEMPLATES_PATH", "/app/templates")
    
    async def enhance_prompt(self, prompt: str, config: Dict) -> Dict:
        """Use AI to break down prompt into slide structure"""
        
        system_prompt = f"""
        Break down this presentation prompt into {config['slides_count']} slides.
        
        Return a JSON structure with:
        {{
            "title": "Presentation Title",
            "slides": [
                {{
                    "slide_number": 1,
                    "title": "Slide Title",
                    "bullet_points": ["Point 1", "Point 2", "Point 3"],
                    "speaker_notes": "Additional context and speaking notes",
                    "visual_suggestion": "Suggested image or graphic"
                }}
            ]
        }}
        
        Template style: {config['template']}
        Topic: {config['topic_title']}
        
        Make each slide concise, engaging, and professional.
        """
        
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
            
            content = response.choices[0].message.content
            
            # Parse JSON response
            slide_structure = json.loads(content)
            
            # Validate structure
            if "slides" not in slide_structure:
                raise ValueError("Invalid slide structure returned by AI")
            
            return slide_structure
            
        except json.JSONDecodeError as e:
            logger.error(f"AI returned invalid JSON: {e}")
            # Fallback to basic structure
            return self.create_fallback_structure(prompt, config)
        
        except Exception as e:
            logger.error(f"AI prompt enhancement failed: {e}")
            return self.create_fallback_structure(prompt, config)
    
    async def generate_pptx(self, slide_structure: Dict) -> str:
        """Generate PowerPoint file from slide structure"""
        
        # Load template
        template_path = os.path.join(self.templates_path, f"{slide_structure.get('template', 'business')}.pptx")
        
        if os.path.exists(template_path):
            prs = Presentation(template_path)
        else:
            prs = Presentation()  # Use default template
        
        # Clear existing slides (keep master)
        slide_count = len(prs.slides)
        for i in range(slide_count - 1, -1, -1):
            rId = prs.slides._sldIdLst[i].rId
            prs.part.drop_rel(rId)
            del prs.slides._sldIdLst[i]
        
        # Add title slide
        title_layout = prs.slide_layouts[0]
        title_slide = prs.slides.add_slide(title_layout)
        title_slide.shapes.title.text = slide_structure.get("title", "Presentation")
        
        # Add content slides
        for slide_data in slide_structure.get("slides", []):
            content_layout = prs.slide_layouts[1]  # Bullet point layout
            slide = prs.slides.add_slide(content_layout)
            
            # Set title
            slide.shapes.title.text = slide_data.get("title", "")
            
            # Add bullet points
            if "bullet_points" in slide_data:
                content_placeholder = slide.shapes.placeholders[1]
                tf = content_placeholder.text_frame
                
                for i, point in enumerate(slide_data["bullet_points"]):
                    if i == 0:
                        tf.text = point
                    else:
                        p = tf.add_paragraph()
                        p.text = point
            
            # Add speaker notes
            if "speaker_notes" in slide_data:
                notes_slide = slide.notes_slide
                notes_slide.notes_text_frame.text = slide_data["speaker_notes"]
        
        # Save presentation
        timestamp = int(time.time())
        pptx_filename = f"presentation_{timestamp}.pptx"
        pptx_path = os.path.join("/tmp/publisher_images", pptx_filename)
        
        prs.save(pptx_path)
        
        return pptx_path
    
    async def convert_to_pdf(self, pptx_path: str) -> str:
        """Convert PPTX to PDF using existing presenton logic"""
        
        # Integration with existing linkedin/services/presenton.py
        # This should reuse the proven PPTX→PDF conversion logic
        
        try:
            # Import existing Presenton service logic
            import sys
            sys.path.append('/app/linkedin/services')
            from presenton import convert_pptx_to_pdf
            
            pdf_path = pptx_path.replace('.pptx', '.pdf')
            await convert_pptx_to_pdf(pptx_path, pdf_path)
            
            return pdf_path
            
        except ImportError:
            # Fallback: use LibreOffice headless conversion
            return await self.convert_with_libreoffice(pptx_path)
    
    async def convert_with_libreoffice(self, pptx_path: str) -> str:
        """Fallback PDF conversion using LibreOffice"""
        
        import subprocess
        
        output_dir = os.path.dirname(pptx_path)
        
        cmd = [
            "libreoffice",
            "--headless",
            "--convert-to", "pdf",
            "--outdir", output_dir,
            pptx_path
        ]
        
        try:
            subprocess.run(cmd, check=True, timeout=60)
            pdf_path = pptx_path.replace('.pptx', '.pdf')
            
            if os.path.exists(pdf_path):
                return pdf_path
            else:
                raise Exception("PDF conversion failed - file not created")
                
        except subprocess.CalledProcessError as e:
            raise Exception(f"LibreOffice conversion failed: {e}")
        except subprocess.TimeoutExpired:
            raise Exception("PDF conversion timed out")
    
    def create_fallback_structure(self, prompt: str, config: Dict) -> Dict:
        """Create basic slide structure when AI fails"""
        
        slides_count = config.get('slides_count', 5)
        
        return {
            "title": config.get('topic_title', 'Presentation'),
            "slides": [
                {
                    "slide_number": i + 1,
                    "title": f"Slide {i + 1}",
                    "bullet_points": [
                        "Key point from the content",
                        "Supporting information",
                        "Call to action"
                    ],
                    "speaker_notes": "Generated from: " + prompt[:100] + "...",
                    "visual_suggestion": "Professional image"
                }
                for i in range(slides_count)
            ]
        }
```

**Dependencies**:
```txt
# presenton/requirements.txt
fastapi==0.104.1
uvicorn==0.24.0
python-pptx==0.6.23
openai==1.3.0
aiofiles==23.2.0
```

**Success Metrics**:
- [ ] AI prompt enhancement success rate: >90%
- [ ] PPTX generation time: <30s
- [ ] PDF conversion success rate: >95%
- [ ] Total pipeline time: <60s

---

### **PHASE 4.5.3: AI WRITING FLOW INTEGRATION (Week 2)**

#### **Zadanie 4.5.3.1: PlatformOptimizer Implementation**
**Service**: AI Writing Flow  
**Location**: `kolegium/ai_writing_flow/src/ai_writing_flow/platform_optimizer.py`  
**Estimated Time**: 2-3 dni  

**Core Implementation**:
```python
# kolegium/ai_writing_flow/src/ai_writing_flow/platform_optimizer.py
from typing import Dict, Any
import time

class PlatformOptimizer:
    """Generate platform-specific content variations"""
    
    def __init__(self):
        self.platform_configs = {
            "linkedin": {
                "prompt_mode": True,  # Default for LinkedIn = carousel prompts
                "max_length": 3000,
                "focus": "professional, slide-friendly",
                "structure": "presentation_outline",
                "slides_count": 5
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
            },
            "substack": {
                "prompt_mode": False,
                "max_length": 8000,
                "focus": "newsletter, personal",
                "structure": "newsletter_format"
            }
        }
        
        # Import existing CrewAI agents
        from ai_writing_flow.agents import WriterAgent, EditorAgent
        self.writer_agent = WriterAgent()
        self.editor_agent = EditorAgent()
    
    async def generate_for_platform(self, topic: "Topic", platform: str, direct_content: bool = None) -> Dict:
        """
        Generate platform-specific content
        
        Args:
            topic: Topic object with title and description
            platform: Target platform (linkedin, twitter, ghost, substack)
            direct_content: User override for LinkedIn (True = skip carousel, False = carousel)
        
        Returns:
            Dict with content type, content, and platform metadata
        """
        
        if platform not in self.platform_configs:
            raise ValueError(f"Unsupported platform: {platform}")
        
        config = self.platform_configs[platform].copy()
        
        # Handle user override for LinkedIn
        if platform == "linkedin" and direct_content is not None:
            config["prompt_mode"] = not direct_content
        
        if config["prompt_mode"] and platform == "linkedin":
            return await self.generate_presentation_prompt(topic, config)
        else:
            return await self.generate_direct_content(topic, config)
    
    async def generate_presentation_prompt(self, topic: "Topic", config: Dict) -> Dict:
        """Generate LinkedIn carousel prompt for Presenton"""
        
        system_prompt = f"""
        Create a detailed prompt for generating a {config.get('slides_count', 5)}-slide 
        LinkedIn carousel presentation about: {topic.title}
        
        Topic description: {topic.description}
        
        The prompt should specify:
        - Clear slide titles and content structure
        - Professional, business-focused tone
        - Engaging visual suggestions
        - Call-to-action for the final slide
        - Specific talking points for each slide
        
        Format the prompt as detailed instructions that will be used to generate 
        a PowerPoint presentation. Be specific about what each slide should contain.
        
        The output will be used by an AI presentation generator.
        """
        
        try:
            # Use existing CrewAI agents with modified context
            result = await self.writer_agent.execute_task(
                task_description=system_prompt,
                context={
                    "topic": topic,
                    "platform": "linkedin_carousel",
                    "output_type": "presentation_prompt",
                    "slides_count": config.get('slides_count', 5)
                }
            )
            
            return {
                "type": "presentation_prompt",
                "prompt": result.content,
                "slides_count": config.get("slides_count", 5),
                "platform": "linkedin",
                "ready_for_presenton": True,
                "generation_time": result.execution_time if hasattr(result, 'execution_time') else None
            }
            
        except Exception as e:
            logger.error(f"Presentation prompt generation failed: {e}")
            # Fallback to basic prompt
            return {
                "type": "presentation_prompt",
                "prompt": f"Create a {config.get('slides_count', 5)}-slide presentation about {topic.title}. {topic.description}",
                "slides_count": config.get("slides_count", 5),
                "platform": "linkedin",
                "ready_for_presenton": True,
                "error": str(e)
            }
    
    async def generate_direct_content(self, topic: "Topic", config: Dict) -> Dict:
        """Generate direct text content for publication"""
        
        # Platform-specific content optimization
        task_description = self.build_platform_task(topic, config)
        
        try:
            # Use existing AI Writing Flow logic with platform-specific optimization
            result = await self.writer_agent.execute_task(
                task_description=task_description,
                context={
                    "topic": topic,
                    "platform": config['structure'],
                    "max_length": config['max_length'],
                    "focus": config['focus']
                }
            )
            
            # Post-process content for platform
            processed_content = await self.post_process_content(result.content, config)
            
            return {
                "type": "direct_content",
                "content": processed_content,
                "html": result.html if hasattr(result, 'html') else None,
                "platform": config['structure'],
                "ready_for_publication": True,
                "word_count": len(processed_content.split()),
                "generation_time": result.execution_time if hasattr(result, 'execution_time') else None
            }
            
        except Exception as e:
            logger.error(f"Direct content generation failed for {config['structure']}: {e}")
            raise
    
    def build_platform_task(self, topic: "Topic", config: Dict) -> str:
        """Build platform-specific task description"""
        
        platform_instructions = {
            "thread_ready": f"""
                Create engaging Twitter content about {topic.title}.
                Maximum {config['max_length']} characters.
                Style: {config['focus']}
                
                If content is longer, structure as a thread with numbered tweets.
                Use relevant hashtags and mentions.
                Include a strong hook in the first tweet.
            """,
            
            "blog_article": f"""
                Write a comprehensive blog article about {topic.title}.
                Target length: {config['max_length']} words.
                Style: {config['focus']}
                
                Include:
                - SEO-friendly title and meta description
                - Clear headings and subheadings
                - Introduction, body, and conclusion
                - Call-to-action at the end
                - Image placeholders where appropriate (use placeholder:keyword format)
            """,
            
            "newsletter_format": f"""
                Create newsletter content about {topic.title}.
                Target length: {config['max_length']} words.
                Style: {config['focus']}
                
                Format:
                - Personal greeting
                - Main content with stories and insights
                - Key takeaways section
                - Community engagement call
                - Footer with next newsletter preview
            """,
            
            "presentation_outline": f"""
                Create professional LinkedIn post about {topic.title}.
                Maximum {config['max_length']} characters.
                Style: {config['focus']}
                
                Format:
                - Attention-grabbing hook
                - 3-5 key insights with clear structure
                - Professional tone with personal touch
                - Relevant hashtags
                - Call for engagement (questions, comments)
            """
        }
        
        return platform_instructions.get(
            config['structure'],
            f"Create {config['focus']} content about {topic.title}. {topic.description}"
        )
    
    async def post_process_content(self, content: str, config: Dict) -> str:
        """Platform-specific content post-processing"""
        
        if config['structure'] == 'thread_ready':
            # Ensure Twitter content fits character limits
            return self.format_twitter_thread(content, config['max_length'])
        
        elif config['structure'] == 'blog_article':
            # Add image placeholders if missing
            return self.enhance_blog_content(content)
        
        elif config['structure'] == 'newsletter_format':
            # Format for newsletter structure
            return self.format_newsletter(content)
        
        else:
            return content
    
    def format_twitter_thread(self, content: str, max_length: int) -> str:
        """Format content as Twitter thread if needed"""
        
        if len(content) <= max_length:
            return content
        
        # Split into thread tweets
        sentences = content.split('. ')
        tweets = []
        current_tweet = ""
        
        for sentence in sentences:
            if len(current_tweet + sentence + '. ') <= max_length - 10:  # Reserve space for numbering
                current_tweet += sentence + '. '
            else:
                if current_tweet:
                    tweets.append(current_tweet.strip())
                current_tweet = sentence + '. '
        
        if current_tweet:
            tweets.append(current_tweet.strip())
        
        # Number the tweets
        numbered_tweets = []
        for i, tweet in enumerate(tweets, 1):
            numbered_tweets.append(f"{i}/{len(tweets)} {tweet}")
        
        return '\n\n---THREAD---\n\n'.join(numbered_tweets)
    
    def enhance_blog_content(self, content: str) -> str:
        """Add image placeholders to blog content if missing"""
        
        # Check if content already has image placeholders
        if 'placeholder:' in content:
            return content
        
        # Add image placeholder after introduction
        paragraphs = content.split('\n\n')
        if len(paragraphs) > 1:
            # Insert image after first paragraph
            paragraphs.insert(1, 'placeholder:main-concept')
        
        return '\n\n'.join(paragraphs)
    
    def format_newsletter(self, content: str) -> str:
        """Format content for newsletter structure"""
        
        # Basic newsletter formatting
        if not content.startswith('Hello'):
            content = f"Hello,\n\n{content}"
        
        if not content.endswith('newsletter'):
            content += f"\n\nThat's all for today! See you in the next newsletter."
        
        return content
```

**Enhanced Models**:
```python
# kolegium/ai_writing_flow/src/ai_writing_flow/models.py
from pydantic import BaseModel
from typing import Dict, Any, Optional

class Topic(BaseModel):
    title: str
    description: str
    keywords: Optional[List[str]] = []
    target_audience: Optional[str] = None

class PlatformConfig(BaseModel):
    enabled: bool = True
    direct_content: Optional[bool] = None  # LinkedIn override
    slides_count: Optional[int] = 5
    template: Optional[str] = "business"
    focus: Optional[str] = None

class MultiPlatformRequest(BaseModel):
    request_id: str
    topic: Topic
    platforms: Dict[str, PlatformConfig]
    start_time: float = time.time()

class MultiPlatformResponse(BaseModel):
    request_id: str
    topic: Topic
    platform_content: Dict[str, Any]
    generation_time: float
    quality_score: Optional[float] = None

class LinkedInPromptRequest(BaseModel):
    topic: Topic
    slides_count: int = 5
    focus: Optional[str] = None
    template: Optional[str] = "business"

class LinkedInPromptResponse(BaseModel):
    prompt: str
    slides_count: int
    estimated_generation_time: int
    ready_for_presenton: bool
```

**Success Metrics**:
- [ ] Content quality (manual review): >8/10 for each platform
- [ ] Prompt effectiveness: LinkedIn carousels rate >7/10
- [ ] Generation time: <30s per platform
- [ ] Platform optimization accuracy: Content fits platform constraints 100%

**Tests**:
```python
# tests/test_platform_optimizer.py
import pytest
from ai_writing_flow.platform_optimizer import PlatformOptimizer
from ai_writing_flow.models import Topic

@pytest.fixture
def platform_optimizer():
    return PlatformOptimizer()

@pytest.fixture
def sample_topic():
    return Topic(
        title="Remote Work Trends",
        description="Future of remote work in 2025 and its impact on business"
    )

async def test_linkedin_prompt_generation(platform_optimizer, sample_topic):
    """Test LinkedIn carousel prompt generation"""
    
    result = await platform_optimizer.generate_for_platform(
        topic=sample_topic,
        platform="linkedin",
        direct_content=False  # Use carousel
    )
    
    assert result["type"] == "presentation_prompt"
    assert result["ready_for_presenton"] is True
    assert result["slides_count"] == 5
    assert "slide" in result["prompt"].lower()
    assert len(result["prompt"]) > 200

async def test_linkedin_direct_content(platform_optimizer, sample_topic):
    """Test LinkedIn direct content generation"""
    
    result = await platform_optimizer.generate_for_platform(
        topic=sample_topic,
        platform="linkedin",
        direct_content=True  # Skip carousel
    )
    
    assert result["type"] == "direct_content"
    assert result["ready_for_publication"] is True
    assert len(result["content"]) <= 3000  # LinkedIn limit

async def test_twitter_content_generation(platform_optimizer, sample_topic):
    """Test Twitter content generation"""
    
    result = await platform_optimizer.generate_for_platform(
        topic=sample_topic,
        platform="twitter"
    )
    
    assert result["type"] == "direct_content"
    assert result["platform"] == "thread_ready"
    
    # Check if content fits Twitter constraints
    if "---THREAD---" in result["content"]:
        tweets = result["content"].split("---THREAD---")
        for tweet in tweets:
            assert len(tweet.strip()) <= 280

async def test_ghost_blog_generation(platform_optimizer, sample_topic):
    """Test Ghost blog content generation"""
    
    result = await platform_optimizer.generate_for_platform(
        topic=sample_topic,
        platform="ghost"
    )
    
    assert result["type"] == "direct_content"
    assert result["platform"] == "blog_article"
    assert len(result["content"]) > 500  # Substantial blog content
    assert "placeholder:" in result["content"]  # Image placeholders added

async def test_platform_content_variations(platform_optimizer, sample_topic):
    """Test that different platforms generate different content"""
    
    linkedin_result = await platform_optimizer.generate_for_platform(sample_topic, "linkedin", direct_content=True)
    twitter_result = await platform_optimizer.generate_for_platform(sample_topic, "twitter")
    ghost_result = await platform_optimizer.generate_for_platform(sample_topic, "ghost")
    
    # Verify platform-specific characteristics
    assert len(twitter_result["content"]) <= 280 or "---THREAD---" in twitter_result["content"]
    assert len(ghost_result["content"]) > len(linkedin_result["content"])  # Blog vs social
    assert linkedin_result["type"] == "direct_content"  # direct_content=True
    
    # Verify content is actually different
    assert linkedin_result["content"] != twitter_result["content"]
    assert twitter_result["content"] != ghost_result["content"]
```

---

#### **Zadanie 4.5.3.2: Enhanced API Endpoints**
**Estimated Time**: 1 dzień  

**Implementation**:
```python
# kolegium/ai_writing_flow/src/ai_writing_flow/main.py - Enhanced endpoints
from fastapi import FastAPI, HTTPException
from .platform_optimizer import PlatformOptimizer
from .models import MultiPlatformRequest, MultiPlatformResponse, LinkedInPromptRequest, LinkedInPromptResponse
import time

app = FastAPI(title="AI Writing Flow", version="2.0.0")

@app.post("/generate/multi-platform", response_model=MultiPlatformResponse)
async def generate_multi_platform_content(request: MultiPlatformRequest):
    """
    Generate content for multiple platforms simultaneously
    
    Enhanced endpoint for Publisher Orchestrator integration
    """
    
    try:
        platform_optimizer = PlatformOptimizer()
        results = {}
        errors = {}
        
        # Process platforms concurrently
        import asyncio
        
        async def process_platform(platform: str, config: Dict):
            try:
                if config.enabled:
                    result = await platform_optimizer.generate_for_platform(
                        topic=request.topic,
                        platform=platform,
                        direct_content=config.get("direct_content")
                    )
                    return platform, result
                return platform, None
            except Exception as e:
                logger.error(f"Platform {platform} generation failed: {e}")
                return platform, {"error": str(e)}
        
        # Execute all platforms in parallel
        tasks = [
            process_platform(platform, config)
            for platform, config in request.platforms.items()
        ]
        
        platform_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        for platform, result in platform_results:
            if isinstance(result, Exception):
                errors[platform] = str(result)
            elif result:
                results[platform] = result
        
        generation_time = time.time() - request.start_time
        
        # Calculate quality score
        quality_score = await calculate_quality_score(results) if results else 0.0
        
        response = MultiPlatformResponse(
            request_id=request.request_id,
            topic=request.topic,
            platform_content=results,
            generation_time=generation_time,
            quality_score=quality_score
        )
        
        # Add errors to response if any
        if errors:
            response.errors = errors
        
        return response
        
    except Exception as e:
        logger.error(f"Multi-platform generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate/linkedin-prompt", response_model=LinkedInPromptResponse)
async def generate_linkedin_prompt(request: LinkedInPromptRequest):
    """
    Specialized endpoint for LinkedIn carousel prompt generation
    """
    
    try:
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
            ready_for_presenton=True,
            generation_time=result.get("generation_time", 0)
        )
        
    except Exception as e:
        logger.error(f"LinkedIn prompt generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def calculate_quality_score(results: Dict[str, Any]) -> float:
    """Calculate overall quality score for generated content"""
    
    scores = []
    
    for platform, content in results.items():
        if "error" in content:
            scores.append(0.0)
            continue
            
        # Basic quality metrics
        score = 5.0  # Base score
        
        # Content length appropriateness
        if content.get("word_count"):
            word_count = content["word_count"]
            if platform == "twitter" and word_count <= 50:
                score += 2.0
            elif platform == "linkedin" and 100 <= word_count <= 500:
                score += 2.0
            elif platform == "ghost" and word_count >= 500:
                score += 2.0
        
        # Generation time bonus
        if content.get("generation_time") and content["generation_time"] < 30:
            score += 1.0
        
        scores.append(min(score, 10.0))
    
    return sum(scores) / len(scores) if scores else 0.0

# Backward compatibility endpoints
@app.post("/generate")
async def generate_content_legacy(request: Dict):
    """Legacy endpoint for backward compatibility"""
    
    # Convert legacy format to new format and delegate
    topic = Topic(title=request.get("title", ""), description=request.get("description", ""))
    
    platform_optimizer = PlatformOptimizer()
    result = await platform_optimizer.generate_for_platform(
        topic=topic,
        platform=request.get("platform", "linkedin"),
        direct_content=request.get("direct_content")
    )
    
    return result
```

**API Integration Tests**:
```python
# tests/test_enhanced_api.py
import pytest
from fastapi.testclient import TestClient
from ai_writing_flow.main import app

client = TestClient(app)

def test_multi_platform_endpoint():
    """Test multi-platform generation endpoint"""
    
    request_data = {
        "request_id": "test-123",
        "topic": {
            "title": "AI Innovation",
            "description": "Latest developments in artificial intelligence"
        },
        "platforms": {
            "linkedin": {"enabled": True, "direct_content": False},
            "twitter": {"enabled": True},
            "ghost": {"enabled": True}
        }
    }
    
    response = client.post("/generate/multi-platform", json=request_data)
    
    assert response.status_code == 200
    result = response.json()
    
    assert result["request_id"] == "test-123"
    assert "platform_content" in result
    assert len(result["platform_content"]) <= 3  # Max requested platforms
    assert result["generation_time"] > 0

def test_linkedin_prompt_endpoint():
    """Test LinkedIn prompt generation endpoint"""
    
    request_data = {
        "topic": {
            "title": "Remote Work Future",
            "description": "Evolution of remote work practices"
        },
        "slides_count": 5,
        "template": "business"
    }
    
    response = client.post("/generate/linkedin-prompt", json=request_data)
    
    assert response.status_code == 200
    result = response.json()
    
    assert "prompt" in result
    assert result["slides_count"] == 5
    assert result["ready_for_presenton"] is True
    assert len(result["prompt"]) > 100

def test_backward_compatibility():
    """Test legacy endpoint still works"""
    
    request_data = {
        "title": "Test Topic",
        "description": "Test description",
        "platform": "twitter"
    }
    
    response = client.post("/generate", json=request_data)
    
    assert response.status_code == 200
    result = response.json()
    
    assert "type" in result
    assert result["platform"] == "thread_ready"
```

**Success Metrics**:
- [ ] API response time: <45s for multi-platform generation
- [ ] Concurrent platform processing: All platforms generated in parallel
- [ ] Error handling: Partial failures don't break entire request
- [ ] Backward compatibility: Legacy endpoints continue working

---

### **PHASE 4.5.4: ENHANCED ORCHESTRATOR INTEGRATION (Week 2)**

#### **Zadanie 4.5.4.1: ContentProcessor Implementation**
**Service**: Publisher Orchestrator  
**Estimated Time**: 2 dni  

**Core Logic**:
```python
# publisher/src/orchestrator/content_processor.py
import uuid
import time
import asyncio
from typing import Dict, Any, Tuple
from .image_processor import ImageProcessor
from .clients.presenton_client import PresentonClient
from .clients.ai_writing_flow_client import AIWritingFlowClient

class ContentProcessor:
    """Main content processing pipeline for Enhanced Orchestrator"""
    
    def __init__(self):
        self.image_processor = ImageProcessor()
        self.presenton_client = PresentonClient()
        self.ai_writing_flow_client = AIWritingFlowClient()
    
    async def process_content_request(self, request: "EnhancedPublicationRequest") -> Dict[str, Any]:
        """Main content processing pipeline"""
        
        start_time = time.time()
        publication_id = str(uuid.uuid4())
        
        try:
            # 1. Generate platform-specific content from AI Writing Flow
            logger.info(f"[ContentProcessor] Starting content generation for {publication_id}")
            
            content_results = await self.ai_writing_flow_client.generate_multi_platform(
                topic=request.topic,
                platforms=request.platforms
            )
            
            # 2. Process each platform's content
            processed_platforms = {}
            processing_tasks = []
            
            for platform, content_data in content_results.get("platform_content", {}).items():
                if "error" in content_data:
                    logger.error(f"[ContentProcessor] Platform {platform} generation failed: {content_data['error']}")
                    processed_platforms[platform] = {
                        "type": "error",
                        "error": content_data["error"],
                        "ready_for_publication": False
                    }
                    continue
                
                platform_config = request.platforms[platform]
                
                # Create processing task based on content type
                if platform == "linkedin" and content_data.get("type") == "presentation_prompt":
                    task = self.process_presenton_content(content_data, platform_config, platform)
                else:
                    task = self.process_direct_content(content_data, platform_config, platform)
                
                processing_tasks.append((platform, task))
            
            # 3. Execute all processing tasks concurrently
            if processing_tasks:
                platform_results = await asyncio.gather(
                    *[task for _, task in processing_tasks],
                    return_exceptions=True
                )
                
                # Map results back to platforms
                for i, (platform, _) in enumerate(processing_tasks):
                    result = platform_results[i]
                    if isinstance(result, Exception):
                        logger.error(f"[ContentProcessor] Platform {platform} processing failed: {result}")
                        processed_platforms[platform] = {
                            "type": "error",
                            "error": str(result),
                            "ready_for_publication": False
                        }
                    else:
                        processed_platforms[platform] = result
            
            processing_time = time.time() - start_time
            
            return {
                "publication_id": publication_id,
                "platforms": processed_platforms,
                "processing_time": processing_time,
                "ready_for_publication": len([p for p in processed_platforms.values() if p.get("ready_for_publication")]) > 0,
                "enhanced_features": {
                    "image_processing": any("images" in p for p in processed_platforms.values()),
                    "presenton_integration": any(p.get("type") == "presenton_carousel" for p in processed_platforms.values()),
                    "platform_optimization": True
                }
            }
            
        except Exception as e:
            logger.error(f"[ContentProcessor] Content processing failed: {e}")
            raise
    
    async def process_presenton_content(self, content_data: Dict, config: Dict, platform: str) -> Dict:
        """Process LinkedIn carousel through Presenton"""
        
        try:
            logger.info(f"[ContentProcessor] Processing Presenton content for {platform}")
            
            # 1. Generate presentation using Presenton service
            presenton_result = await self.presenton_client.generate_presentation(
                prompt=content_data["prompt"],
                slides_count=content_data.get("slides_count", 5),
                template=config.get("template", "business"),
                topic_title=content_data.get("topic_title", "Presentation")
            )
            
            # 2. Verify files exist
            if not os.path.exists(presenton_result["pdf_path"]):
                raise Exception("Generated PDF file not found")
            
            logger.info(f"[ContentProcessor] Presenton generation successful: {presenton_result['presentation_id']}")
            
            return {
                "type": "presenton_carousel",
                "presentation_id": presenton_result["presentation_id"],
                "prompt": content_data["prompt"],
                "pptx_url": presenton_result["pptx_url"],
                "pdf_path": presenton_result["pdf_path"],
                "slides_count": presenton_result["slide_count"],
                "generation_time": presenton_result["generation_time"],
                "ready_for_linkedin": True,
                "ready_for_publication": True
            }
            
        except Exception as e:
            logger.error(f"[ContentProcessor] Presenton processing failed: {e}")
            # Fallback to direct content
            return await self.fallback_to_direct_content(content_data, config, platform)
    
    async def process_direct_content(self, content_data: Dict, config: Dict, platform: str) -> Dict:
        """Process direct content with image processing"""
        
        try:
            logger.info(f"[ContentProcessor] Processing direct content for {platform}")
            
            content = content_data.get("content", "")
            html_content = content_data.get("html")
            
            # 1. Process image placeholders
            updated_content, image_mapping = await self.image_processor.process_placeholders(content)
            
            # Also process HTML content if available
            updated_html = None
            if html_content:
                updated_html, _ = await self.image_processor.process_placeholders(html_content)
            
            # 2. Platform-specific image finalization
            final_content = await self.image_processor.finalize_for_platform(
                updated_content, platform, image_mapping
            )
            
            final_html = None
            if updated_html:
                final_html = await self.image_processor.finalize_for_platform(
                    updated_html, platform, image_mapping
                )
            
            logger.info(f"[ContentProcessor] Direct content processing complete for {platform}")
            
            return {
                "type": "direct_content",
                "content": final_content,
                "html": final_html,
                "original_content": content,
                "images": image_mapping,
                "image_count": len(image_mapping),
                "platform": platform,
                "word_count": len(final_content.split()),
                "ready_for_publication": True
            }
            
        except Exception as e:
            logger.error(f"[ContentProcessor] Direct content processing failed for {platform}: {e}")
            # Return original content as fallback
            return {
                "type": "direct_content",
                "content": content_data.get("content", ""),
                "html": content_data.get("html"),
                "platform": platform,
                "ready_for_publication": True,
                "error": str(e)
            }
    
    async def fallback_to_direct_content(self, content_data: Dict, config: Dict, platform: str) -> Dict:
        """Fallback when Presenton fails - convert prompt to direct content"""
        
        try:
            # Extract key points from presentation prompt
            prompt = content_data.get("prompt", "")
            
            # Simple conversion: use prompt as base content
            fallback_content = f"Key insights about {content_data.get('topic_title', 'this topic')}:\n\n{prompt}"
            
            # Process as direct content
            fallback_data = {
                "content": fallback_content,
                "html": None
            }
            
            result = await self.process_direct_content(fallback_data, config, platform)
            result["fallback_reason"] = "presenton_failed"
            result["original_prompt"] = prompt
            
            return result
            
        except Exception as e:
            logger.error(f"[ContentProcessor] Fallback processing failed: {e}")
            return {
                "type": "error",
                "error": f"Both Presenton and fallback failed: {str(e)}",
                "ready_for_publication": False
            }
```

**Client Implementations**:
```python
# publisher/src/orchestrator/clients/presenton_client.py
import aiohttp
import os
from typing import Dict, Any

class PresentonClient:
    """Client for Presenton microservice"""
    
    def __init__(self):
        self.base_url = os.getenv("PRESENTON_URL", "http://presenton:8089")
        self.timeout = 120  # 2 minutes for presentation generation
    
    async def generate_presentation(self, prompt: str, slides_count: int = 5, 
                                  template: str = "business", topic_title: str = "Presentation") -> Dict[str, Any]:
        """Generate presentation via Presenton service"""
        
        request_data = {
            "prompt": prompt,
            "slides_count": slides_count,
            "template": template,
            "topic_title": topic_title
        }
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.post(
                    f"{self.base_url}/generate",
                    json=request_data
                ) as response:
                    
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"Presenton API error {response.status}: {error_text}")
                    
                    result = await response.json()
                    return result
                    
        except aiohttp.ClientTimeout:
            raise Exception("Presenton generation timed out")
        except aiohttp.ClientError as e:
            raise Exception(f"Presenton client error: {e}")
    
    async def health_check(self) -> bool:
        """Check if Presenton service is healthy"""
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.get(f"{self.base_url}/health") as response:
                    return response.status == 200
        except:
            return False

# publisher/src/orchestrator/clients/ai_writing_flow_client.py
import aiohttp
import os
from typing import Dict, Any

class AIWritingFlowClient:
    """Client for AI Writing Flow service"""
    
    def __init__(self):
        self.base_url = os.getenv("AI_WRITING_FLOW_URL", "http://localhost:8003")
        self.timeout = 60
    
    async def generate_multi_platform(self, topic: Dict, platforms: Dict) -> Dict[str, Any]:
        """Generate content for multiple platforms"""
        
        request_data = {
            "request_id": f"orchestrator_{int(time.time())}",
            "topic": topic,
            "platforms": platforms
        }
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.post(
                    f"{self.base_url}/generate/multi-platform",
                    json=request_data
                ) as response:
                    
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"AI Writing Flow API error {response.status}: {error_text}")
                    
                    result = await response.json()
                    return result
                    
        except aiohttp.ClientTimeout:
            raise Exception("AI Writing Flow generation timed out")
        except aiohttp.ClientError as e:
            raise Exception(f"AI Writing Flow client error: {e}")
    
    async def health_check(self) -> bool:
        """Check if AI Writing Flow service is healthy"""
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.get(f"{self.base_url}/health") as response:
                    return response.status == 200
        except:
            return False
```

---

#### **Zadanie 4.5.4.2: Enhanced Publish Endpoint**
**Estimated Time**: 1 dzień  

**Enhanced API Models**:
```python
# publisher/src/orchestrator/models.py
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import time

class Topic(BaseModel):
    title: str
    description: str
    keywords: Optional[List[str]] = []

class PlatformConfig(BaseModel):
    enabled: bool = True
    direct_content: Optional[bool] = None  # LinkedIn override
    slides_count: Optional[int] = 5
    template: Optional[str] = "business"

class EnhancedPublicationRequest(BaseModel):
    topic: Topic
    platforms: Dict[str, PlatformConfig]
    scheduled_time: Optional[str] = None
    priority: str = "normal"

class EnhancedPublicationResponse(BaseModel):
    publication_id: str
    platform_jobs: Dict[str, str]
    processing_time: float
    status: str
    enhanced_features: Dict[str, bool]
    errors: Optional[Dict[str, str]] = None
```

**Enhanced API Implementation**:
```python
# publisher/src/orchestrator/main.py - Enhanced endpoint
@app.post("/publish/enhanced", response_model=EnhancedPublicationResponse)
async def publish_enhanced_content(request: EnhancedPublicationRequest):
    """Enhanced publish endpoint with image processing and content differentiation"""
    
    start_time = time.time()
    
    try:
        logger.info(f"[Enhanced Orchestrator] Starting enhanced publication: {request.topic.title}")
        
        # 1. Process content through enhanced pipeline
        content_processor = ContentProcessor()
        processed_content = await content_processor.process_content_request(request)
        
        if not processed_content["ready_for_publication"]:
            raise HTTPException(
                status_code=422, 
                detail="Content processing failed - no platforms ready for publication"
            )
        
        # 2. Queue jobs for each platform
        publication_jobs = {}
        errors = {}
        
        for platform, content_data in processed_content["platforms"].items():
            if not content_data.get("ready_for_publication"):
                errors[platform] = content_data.get("error", "Processing failed")
                continue
            
            try:
                # Queue publication job with enhanced content
                job_id = await queue_manager.queue_publication_job(
                    platform=platform,
                    content=content_data,
                    publication_id=processed_content["publication_id"],
                    scheduled_time=request.scheduled_time,
                    priority=request.priority,
                    enhanced_mode=True
                )
                
                publication_jobs[platform] = job_id
                
                logger.info(f"[Enhanced Orchestrator] Queued {platform} job: {job_id}")
                
            except Exception as e:
                logger.error(f"[Enhanced Orchestrator] Failed to queue {platform}: {e}")
                errors[platform] = str(e)
        
        if not publication_jobs:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to queue any platforms. Errors: {errors}"
            )
        
        # 3. Update metrics
        await metrics_collector.record_enhanced_publication(
            platforms=list(publication_jobs.keys()),
            processing_time=processed_content["processing_time"],
            features=processed_content["enhanced_features"]
        )
        
        total_time = time.time() - start_time
        
        response = EnhancedPublicationResponse(
            publication_id=processed_content["publication_id"],
            platform_jobs=publication_jobs,
            processing_time=total_time,
            status="queued",
            enhanced_features=processed_content["enhanced_features"]
        )
        
        if errors:
            response.errors = errors
        
        logger.info(f"[Enhanced Orchestrator] Enhanced publication completed: {response.publication_id}")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Enhanced Orchestrator] Enhanced publication failed: {e}")
        raise HTTPException(status_code=500, detail=f"Enhanced publication failed: {str(e)}")

@app.get("/status/enhanced/{publication_id}")
async def get_enhanced_publication_status(publication_id: str):
    """Get detailed status for enhanced publication"""
    
    try:
        # Get status from all platform jobs
        publication_status = await status_tracker.get_publication_status(publication_id)
        
        # Enhanced status includes additional metadata
        enhanced_status = {
            "publication_id": publication_id,
            "overall_status": publication_status["status"],
            "platforms": publication_status["platforms"],
            "enhanced_features": publication_status.get("enhanced_features", {}),
            "processing_metrics": {
                "total_time": publication_status.get("processing_time"),
                "image_processing_time": publication_status.get("image_processing_time"),
                "presenton_time": publication_status.get("presenton_time")
            },
            "created_at": publication_status["created_at"],
            "updated_at": publication_status["updated_at"]
        }
        
        return enhanced_status
        
    except Exception as e:
        logger.error(f"[Enhanced Orchestrator] Status check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

**Queue Manager Enhancement**:
```python
# publisher/src/orchestrator/queue_manager.py - Enhanced job queueing
async def queue_publication_job(self, platform: str, content: Dict, publication_id: str, 
                               scheduled_time: str = None, priority: str = "normal", 
                               enhanced_mode: bool = False) -> str:
    """Queue publication job with enhanced content support"""
    
    job_id = str(uuid.uuid4())
    
    job_data = {
        "job_id": job_id,
        "publication_id": publication_id,
        "platform": platform,
        "content": content,
        "priority": priority,
        "enhanced_mode": enhanced_mode,
        "created_at": datetime.utcnow().isoformat(),
        "attempts": 0,
        "max_attempts": 3
    }
    
    if scheduled_time:
        # Queue for scheduled execution
        job_data["scheduled_time"] = scheduled_time
        await self.redis_client.zadd(
            f"queue:scheduled:{platform}",
            {json.dumps(job_data): self.parse_scheduled_time(scheduled_time)}
        )
    else:
        # Queue for immediate execution
        await self.redis_client.lpush(
            f"queue:immediate:{platform}",
            json.dumps(job_data)
        )
    
    # Track job in publication registry
    await self.redis_client.hset(
        f"publication:{publication_id}",
        platform,
        json.dumps({
            "job_id": job_id,
            "status": "queued",
            "enhanced_mode": enhanced_mode
        })
    )
    
    logger.info(f"[Queue Manager] Queued {'enhanced' if enhanced_mode else 'standard'} job {job_id} for {platform}")
    
    return job_id
```

---

### **PHASE 4.5.5: END-TO-END INTEGRATION (Week 3)**

#### **Zadanie 4.5.5.1: Complete Pipeline Testing**
**Estimated Time**: 2 dni  

**Test Scenarios**:
```python
# tests/integration/test_enhanced_pipeline.py
import pytest
import asyncio
import time
from fastapi.testclient import TestClient
from publisher.src.orchestrator.main import app

client = TestClient(app)

class TestEnhancedPipeline:
    
    async def test_linkedin_carousel_pipeline(self):
        """
        Test complete LinkedIn carousel pipeline:
        AI Writing Flow → Orchestrator → Presenton → LinkedIn
        """
        
        request_data = {
            "topic": {
                "title": "Future of Remote Work",
                "description": "Trends and predictions for remote work in 2025"
            },
            "platforms": {
                "linkedin": {
                    "enabled": True,
                    "direct_content": False,  # Use Presenton
                    "slides_count": 5,
                    "template": "business"
                }
            }
        }
        
        # 1. Submit enhanced publication request
        response = client.post("/publish/enhanced", json=request_data)
        
        assert response.status_code == 200
        result = response.json()
        
        # Verify response structure
        assert "publication_id" in result
        assert result["status"] == "queued"
        assert result["enhanced_features"]["presenton_integration"] is True
        assert "linkedin" in result["platform_jobs"]
        
        publication_id = result["publication_id"]
        
        # 2. Wait for processing and check status
        max_wait = 150  # 2.5 minutes max
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            status_response = client.get(f"/status/enhanced/{publication_id}")
            status = status_response.json()
            
            if status["platforms"]["linkedin"]["status"] in ["published", "failed"]:
                break
                
            await asyncio.sleep(10)
        
        # 3. Verify final status
        final_status = client.get(f"/status/enhanced/{publication_id}").json()
        
        assert final_status["platforms"]["linkedin"]["status"] == "published"
        assert "pdf_path" in final_status["platforms"]["linkedin"]["content"]
        assert final_status["processing_metrics"]["presenton_time"] > 0
        
        # 4. Verify files exist
        pdf_path = final_status["platforms"]["linkedin"]["content"]["pdf_path"]
        assert os.path.exists(pdf_path)
        assert os.path.getsize(pdf_path) > 1000  # Non-empty PDF
    
    async def test_multi_platform_with_images(self):
        """Test multi-platform with image processing"""
        
        request_data = {
            "topic": {
                "title": "AI Innovation Trends",
                "description": "Latest developments in artificial intelligence with placeholder:ai-technology breakthrough!"
            },
            "platforms": {
                "twitter": {"enabled": True, "direct_content": True},
                "ghost": {"enabled": True, "direct_content": True},
                "linkedin": {"enabled": True, "direct_content": True}  # Direct, not carousel
            }
        }
        
        # 1. Submit request
        response = client.post("/publish/enhanced", json=request_data)
        result = response.json()
        
        # Verify image processing enabled
        assert result["enhanced_features"]["image_processing"] is True
        assert result["enhanced_features"]["presenton_integration"] is False  # Direct content
        
        # 2. Check all platforms were queued
        assert len(result["platform_jobs"]) == 3
        assert "twitter" in result["platform_jobs"]
        assert "ghost" in result["platform_jobs"]
        assert "linkedin" in result["platform_jobs"]
        
        # 3. Wait for processing
        publication_id = result["publication_id"]
        await self.wait_for_completion(publication_id, timeout=90)
        
        # 4. Verify image processing results
        final_status = client.get(f"/status/enhanced/{publication_id}").json()
        
        for platform in ["twitter", "ghost", "linkedin"]:
            platform_status = final_status["platforms"][platform]
            assert platform_status["status"] == "published"
            
            # Check that image placeholders were processed
            content = platform_status["content"]
            assert "placeholder:ai-technology" not in content["content"]
            
            if platform == "ghost":
                # Ghost should have uploaded images with URLs
                assert "<img src=" in content["content"]
            else:
                # Other platforms should have local image references
                assert "images" in content
                assert len(content["images"]) > 0
    
    async def test_error_handling_and_fallbacks(self):
        """Test error scenarios and fallback mechanisms"""
        
        # 1. Test Presenton failure fallback
        request_data = {
            "topic": {
                "title": "Test Topic",
                "description": "Test description with invalid prompt format {}[]()"
            },
            "platforms": {
                "linkedin": {
                    "enabled": True,
                    "direct_content": False,  # Force Presenton
                    "slides_count": 50,  # Invalid slides count to trigger error
                    "template": "invalid_template"
                }
            }
        }
        
        response = client.post("/publish/enhanced", json=request_data)
        result = response.json()
        
        # Should still succeed with fallback
        assert response.status_code == 200
        
        # Wait for processing
        await self.wait_for_completion(result["publication_id"], timeout=60)
        
        # Check fallback was used
        final_status = client.get(f"/status/enhanced/{result['publication_id']}").json()
        linkedin_content = final_status["platforms"]["linkedin"]["content"]
        
        # Should have fallback content
        assert "fallback_reason" in linkedin_content
        assert linkedin_content["type"] == "direct_content"
    
    async def test_partial_platform_failures(self):
        """Test handling when some platforms fail"""
        
        request_data = {
            "topic": {
                "title": "Test Topic",
                "description": "Test with mixed success/failure"
            },
            "platforms": {
                "twitter": {"enabled": True},  # Should succeed
                "invalid_platform": {"enabled": True},  # Should fail
                "ghost": {"enabled": True}  # Should succeed
            }
        }
        
        response = client.post("/publish/enhanced", json=request_data)
        
        # Should partially succeed
        assert response.status_code == 200
        result = response.json()
        
        # Should have errors for invalid platform
        assert "errors" in result
        assert "invalid_platform" in result["errors"]
        
        # Should have successful jobs for valid platforms
        assert len(result["platform_jobs"]) >= 2
        assert "twitter" in result["platform_jobs"]
        assert "ghost" in result["platform_jobs"]
    
    async def test_performance_benchmarks(self):
        """Test performance meets requirements"""
        
        request_data = {
            "topic": {
                "title": "Performance Test",
                "description": "Testing performance with multiple platforms"
            },
            "platforms": {
                "twitter": {"enabled": True},
                "ghost": {"enabled": True},
                "linkedin": {"enabled": True, "direct_content": True}
            }
        }
        
        start_time = time.time()
        
        # Submit request
        response = client.post("/publish/enhanced", json=request_data)
        result = response.json()
        
        # API response should be fast
        api_time = time.time() - start_time
        assert api_time < 5.0  # API response under 5 seconds
        
        # Wait for full processing
        publication_id = result["publication_id"]
        processing_start = time.time()
        
        await self.wait_for_completion(publication_id, timeout=120)
        
        total_processing_time = time.time() - processing_start
        
        # Total processing should meet performance requirements
        assert total_processing_time < 120  # Under 2 minutes for direct content
        
        # Check processing metrics
        final_status = client.get(f"/status/enhanced/{publication_id}").json()
        metrics = final_status["processing_metrics"]
        
        assert metrics["total_time"] < 120
        if metrics.get("image_processing_time"):
            assert metrics["image_processing_time"] < 30
    
    async def wait_for_completion(self, publication_id: str, timeout: int = 120):
        """Helper to wait for publication completion"""
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            status_response = client.get(f"/status/enhanced/{publication_id}")
            status = status_response.json()
            
            # Check if all platforms are done (published or failed)
            all_done = True
            for platform_status in status["platforms"].values():
                if platform_status["status"] not in ["published", "failed"]:
                    all_done = False
                    break
            
            if all_done:
                return status
                
            await asyncio.sleep(5)
        
        raise TimeoutError(f"Publication {publication_id} did not complete within {timeout} seconds")

# Load testing
@pytest.mark.load_test
class TestEnhancedPipelineLoad:
    
    async def test_concurrent_requests(self):
        """Test handling multiple concurrent enhanced publication requests"""
        
        async def submit_request(i: int):
            request_data = {
                "topic": {
                    "title": f"Concurrent Test {i}",
                    "description": f"Load test request number {i}"
                },
                "platforms": {
                    "twitter": {"enabled": True},
                    "linkedin": {"enabled": True, "direct_content": True}
                }
            }
            
            response = client.post("/publish/enhanced", json=request_data)
            return response.json()
        
        # Submit 10 concurrent requests
        tasks = [submit_request(i) for i in range(10)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # All requests should succeed
        successful_requests = [r for r in results if not isinstance(r, Exception)]
        assert len(successful_requests) >= 8  # At least 80% success rate
        
        # Wait for all to complete
        for result in successful_requests:
            if "publication_id" in result:
                await self.wait_for_completion(result["publication_id"], timeout=180)
        
        # Verify no system degradation
        health_response = client.get("/health")
        assert health_response.status_code == 200
```

---

#### **Zadanie 4.5.5.2: Production Deployment Configuration**
**Estimated Time**: 1 dzień  

**Complete Docker Compose**:
```yaml
# docker-compose.yml - Complete Enhanced Orchestrator setup
version: '3.8'

volumes:
  publisher_images:
    driver: local
  redis_data:
    driver: local
  prometheus_data:
    driver: local
  grafana_data:
    driver: local

networks:
  publisher_network:
    driver: bridge

services:
  # Core Infrastructure
  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    networks:
      - publisher_network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Enhanced Orchestrator
  orchestrator:
    build: ./src/orchestrator
    ports:
      - "8085:8080"
    environment:
      - REDIS_URL=redis://redis:6379
      - PEXELS_API_KEY=${PEXELS_API_KEY}
      - SHARED_IMAGES_PATH=/tmp/publisher_images
      - PRESENTON_URL=http://presenton:8089
      - AI_WRITING_FLOW_URL=${AI_WRITING_FLOW_URL:-http://localhost:8003}
      - GHOST_API_KEY=${GHOST_API_KEY}
      - GHOST_API_URL=${GHOST_API_URL}
      - TYPEFULLY_API_KEY=${TYPEFULLY_API_KEY}
    volumes:
      - publisher_images:/tmp/publisher_images
    depends_on:
      - redis
      - presenton
    networks:
      - publisher_network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # New Presenton Service
  presenton:
    build: ./presenton
    ports:
      - "8089:8089"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - PRESENTON_TEMPLATES_PATH=/app/templates
    volumes:
      - publisher_images:/tmp/publisher_images
      - ./presenton/templates:/app/templates
    networks:
      - publisher_network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8089/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Platform Adapters
  ghost-adapter:
    build: ./src/adapters/ghost
    ports:
      - "8086:8082"
    environment:
      - GHOST_API_KEY=${GHOST_API_KEY}
      - GHOST_API_URL=${GHOST_API_URL}
      - REDIS_URL=redis://redis:6379
    volumes:
      - publisher_images:/tmp/publisher_images
    depends_on:
      - redis
    networks:
      - publisher_network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8082/health"]

  twitter-adapter:
    build: ./src/adapters/twitter
    ports:
      - "8087:8083"
    environment:
      - TYPEFULLY_API_KEY=${TYPEFULLY_API_KEY}
      - REDIS_URL=redis://redis:6379
    volumes:
      - publisher_images:/tmp/publisher_images
    depends_on:
      - redis
    networks:
      - publisher_network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8083/health"]

  substack-adapter:
    build: ./src/adapters/substack
    ports:
      - "8088:8084"
    environment:
      - BROWSERBASE_API_KEY=${BROWSERBASE_API_KEY}
      - BROWSERBASE_PROJECT_ID=${BROWSERBASE_PROJECT_ID}
      - REDIS_URL=redis://redis:6379
    volumes:
      - publisher_images:/tmp/publisher_images
    depends_on:
      - redis
    networks:
      - publisher_network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8084/health"]

  # Monitoring
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--web.enable-lifecycle'
    networks:
      - publisher_network

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD:-admin}
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana:/etc/grafana/provisioning
    depends_on:
      - prometheus
    networks:
      - publisher_network

  # Nginx Load Balancer
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
    depends_on:
      - orchestrator
    networks:
      - publisher_network
```

**Environment Configuration**:
```bash
# .env.example - Complete environment template
# Core Services
REDIS_URL=redis://redis:6379

# Enhanced Orchestrator
PEXELS_API_KEY=your_pexels_api_key_here
SHARED_IMAGES_PATH=/tmp/publisher_images
PRESENTON_URL=http://presenton:8089

# AI Writing Flow Integration
AI_WRITING_FLOW_URL=http://localhost:8003
OPENAI_API_KEY=your_openai_key_here

# Platform APIs
GHOST_API_KEY=your_ghost_admin_api_key
GHOST_API_URL=https://your-ghost-site.com
TYPEFULLY_API_KEY=your_typefully_key
BROWSERBASE_API_KEY=your_browserbase_key
BROWSERBASE_PROJECT_ID=your_project_id

# Monitoring
GRAFANA_PASSWORD=your_secure_password

# Optional: Enhanced Features
ENABLE_IMAGE_PROCESSING=true
ENABLE_PRESENTON_INTEGRATION=true
ENABLE_CONTENT_OPTIMIZATION=true

# Performance Tuning
MAX_CONCURRENT_PUBLICATIONS=10
IMAGE_PROCESSING_TIMEOUT=30
PRESENTON_GENERATION_TIMEOUT=120
REDIS_MAX_CONNECTIONS=20
```

**Production Startup Script**:
```bash
#!/bin/bash
# scripts/start-enhanced-production.sh

set -e

echo "🚀 Starting Enhanced Multi-Channel Publisher..."

# Verify environment
if [ ! -f .env ]; then
    echo "❌ .env file not found. Copy .env.example and configure."
    exit 1
fi

# Load environment
source .env

# Verify required variables
required_vars=(
    "PEXELS_API_KEY"
    "OPENAI_API_KEY"
    "GHOST_API_KEY"
    "GHOST_API_URL"
    "TYPEFULLY_API_KEY"
)

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "❌ Required environment variable $var is not set"
        exit 1
    fi
done

# Create shared directories
mkdir -p ./presenton/templates
mkdir -p ./monitoring/grafana
mkdir -p ./nginx/ssl

# Build and start services
echo "🔨 Building services..."
docker-compose build

echo "🏃 Starting infrastructure..."
docker-compose up -d redis prometheus grafana

echo "⏳ Waiting for infrastructure..."
sleep 10

echo "🎯 Starting Presenton service..."
docker-compose up -d presenton

echo "⏳ Waiting for Presenton..."
sleep 15

echo "🎼 Starting Enhanced Orchestrator..."
docker-compose up -d orchestrator

echo "⏳ Waiting for Orchestrator..."
sleep 10

echo "📱 Starting platform adapters..."
docker-compose up -d ghost-adapter twitter-adapter substack-adapter

echo "🌐 Starting Nginx..."
docker-compose up -d nginx

echo "⏳ Final system check..."
sleep 15

# Health checks
echo "🔍 Running health checks..."
services=("orchestrator:8085" "presenton:8089" "ghost-adapter:8086" "twitter-adapter:8087")

for service in "${services[@]}"; do
    name=$(echo $service | cut -d: -f1)
    port=$(echo $service | cut -d: -f2)
    
    if curl -f -s "http://localhost:$port/health" > /dev/null; then
        echo "✅ $name is healthy"
    else
        echo "❌ $name health check failed"
        docker-compose logs $name
    fi
done

echo ""
echo "🎉 Enhanced Multi-Channel Publisher is running!"
echo ""
echo "📊 Services:"
echo "   Enhanced Orchestrator: http://localhost:8085"
echo "   Presenton Service:     http://localhost:8089"
echo "   Ghost Adapter:         http://localhost:8086"
echo "   Twitter Adapter:       http://localhost:8087"
echo "   Substack Adapter:      http://localhost:8088"
echo ""
echo "📈 Monitoring:"
echo "   Prometheus:            http://localhost:9090"
echo "   Grafana:              http://localhost:3000"
echo ""
echo "📝 API Documentation:"
echo "   Enhanced API:         http://localhost:8085/docs"
echo "   Presenton API:        http://localhost:8089/docs"
echo ""
echo "🧪 Test enhanced publication:"
echo '   curl -X POST http://localhost:8085/publish/enhanced \'
echo '   -H "Content-Type: application/json" \'
echo '   -d "{\"topic\":{\"title\":\"Test\",\"description\":\"Test enhanced pipeline\"},\"platforms\":{\"linkedin\":{\"enabled\":true,\"direct_content\":false}}}"'
```

---

## 📊 **SUCCESS METRICS & VALIDATION**

### **Business Metrics**:
- [ ] **Content Quality**: Manual review scores >8/10 dla każdy content type
- [ ] **Processing Speed**: <150s dla complete LinkedIn carousel pipeline
- [ ] **Platform Coverage**: Support dla 4+ platforms z specialized handling
- [ ] **User Experience**: Single API call creates multi-platform content

### **Technical Metrics**:
- [ ] **Service Reliability**: >99% uptime dla każdy microservice
- [ ] **Integration Success**: >95% end-to-end pipeline success rate
- [ ] **Error Handling**: 100% failure scenarios handled gracefully
- [ ] **Performance**: Support dla 10+ concurrent content generation requests

### **Feature Completeness**:
- [ ] **Image Processing**: Pexels placeholder→real images w all platforms
- [ ] **Presenton Integration**: LinkedIn prompt→carousel→PDF pipeline working
- [ ] **Platform Differentiation**: LinkedIn prompts vs direct content working
- [ ] **User Control**: Checkbox dla "treści bezpośrednie" functional
- [ ] **Backward Compatibility**: Existing Publisher functionality preserved

---

## 🚀 **IMPLEMENTATION TIMELINE**

### **Week 1: Foundation**
- **Days 1-2**: Task 4.5.1.1 - ImageProcessor implementation
- **Days 3-4**: Task 4.5.2.1 - Presenton service skeleton
- **Day 5**: Task 4.5.1.2 - Shared volume integration

### **Week 2: Core Features**
- **Days 1-2**: Task 4.5.2.2 - Presentation generation logic
- **Days 3-4**: Task 4.5.3.1 - AI Writing Flow PlatformOptimizer
- **Day 5**: Task 4.5.4.1 - Enhanced Orchestrator integration

### **Week 3: Integration & Testing**
- **Days 1-2**: Task 4.5.5.1 - Complete pipeline testing
- **Days 3-4**: Task 4.5.5.2 - Production deployment
- **Day 5**: Documentation i final validation

---

**STATUS**: 🚧 **READY FOR IMPLEMENTATION**  
**Prerequisites**: Fazy 1-4 COMPLETED ✅  
**Next Step**: Start Task 4.5.1.1 (ImageProcessor Implementation)

---

*Last Updated: 2025-08-07*  
*Status: Complete Consolidated Master Plan*  
*Ready For: Enhanced Orchestrator Implementation*
