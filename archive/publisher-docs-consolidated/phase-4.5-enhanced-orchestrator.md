# Faza 4.5: Enhanced Orchestrator 🚧 **PLANNED**

## Cel fazy
Rozszerzenie istniejącego Orchestrator o Image Processing Pipeline, Presenton Integration i Platform-Specific Content Generation. Ta faza wprowadza zaawansowane przetwarzanie treści i automatyzację generowania obrazów oraz prezentacji.

**Prerequisite**: Fazy 1-4 muszą być ukończone przed rozpoczęciem Fazy 4.5.

---

## 🎯 **OVERVIEW & INNOVATIONS**

### **Enhanced Orchestrator Features**
- **Image Processing Pipeline**: Pexels API integration z automatic placeholder→image conversion
- **Presenton Integration**: LinkedIn prompt→presentation→PDF pipeline  
- **Content Differentiation**: LinkedIn carousel prompts vs direct content dla innych platform
- **Shared Storage**: Volume mounts dla image sharing między services
- **User Control**: Checkbox "treści bezpośrednie" dla manual override

### **Content Flow Architecture**
```
AI Writing Flow → Enhanced Orchestrator → Platform Adapters → Publication
       ↓                    ↓                    ↓              ↓
[Content + Placeholders] [Process Images]  [Platform Adapt]  [Publish]
[LinkedIn: Prompts]      [Presenton]       [LinkedIn: PDF]   [Success]  
[Others: Direct]         [Pexels Images]   [Others: Text]     [Tracking]
```

---

## 📋 **ATOMIC TASKS BREAKDOWN**

### **Phase 4.5.1: Image Processing Pipeline (Week 1)**

#### **Zadanie 4.5.1.1: ImageProcessor Implementation**
- **Wartość**: Automatic conversion `placeholder:keyword` → real images z Pexels API
- **Test**: Placeholder extraction accuracy >95%, Pexels API success rate >98%
- **Implementacja**:
  ```python
  class ImageProcessor:
      async def process_placeholders(self, content: str) -> Tuple[str, Dict[str, str]]
      async def finalize_for_platform(self, content: str, platform: str, image_mapping: Dict) -> str
  ```
- **Environment**: `PEXELS_API_KEY` required
- **Storage**: Shared volume `/tmp/publisher_images` z all adapters

#### **Zadanie 4.5.1.2: Shared Volume Integration**
- **Wartość**: All platform adapters can access processed images
- **Test**: Images stored w shared volume accessible by Ghost, Twitter, LinkedIn adapters
- **Docker**: Volume mount configuration w `docker-compose.yml`

#### **Zadanie 4.5.1.3: Platform-Specific Image Finalization**
- **Wartość**: Images processed according to platform requirements
- **Test**: Ghost gets Ghost URLs, Twitter gets media attachments, LinkedIn gets local files
- **Integration**: Enhanced każdy adapter z image processing capability

---

### **Phase 4.5.2: Presenton Service Implementation (Week 1-2)**

#### **Zadanie 4.5.2.1: Presenton Service Skeleton**
- **Wartość**: New FastAPI microservice dla presentation generation
- **Test**: `curl http://localhost:8089/health` returns healthy status
- **Port**: 8089 (new service allocation)
- **Docker**: New container w docker-compose.yml

#### **Zadanie 4.5.2.2: Presentation Generation Logic**
- **Wartość**: Prompt→PowerPoint generation z AI enhancement
- **Test**: Generation success rate >90%, generation time <60s per presentation
- **AI Integration**: OpenAI dla prompt enhancement i slide breakdown
- **Output**: PPTX URL dla download i conversion

#### **Zadanie 4.5.2.3: Orchestrator-Presenton Integration**
- **Wartość**: Orchestrator calls Presenton API dla LinkedIn carousel generation
- **Test**: End-to-end prompt→PDF pipeline <90s total time
- **Client**: `PresentonClient` class w Orchestrator
- **Error Handling**: Graceful fallbacks dla Presenton failures

---

### **Phase 4.5.3: Content Differentiation Logic (Week 2)**

#### **Zadanie 4.5.3.1: ContentProcessor Implementation**
- **Wartość**: Platform-specific content routing (LinkedIn prompts vs direct content)
- **Test**: Platform routing accuracy 100%, LinkedIn prompt quality >8/10
- **Logic**: 
  ```python
  class ContentProcessor:
      async def process_content_request(self, request: PublicationRequest) -> Dict[str, Any]
      async def process_presenton_content(self, topic: Topic, config: Dict) -> Dict
      async def process_direct_content(self, topic: Topic, platform: str) -> Dict
  ```

#### **Zadanie 4.5.3.2: Enhanced API Models**
- **Wartość**: Support dla `direct_content` checkbox i enhanced request/response models
- **Test**: Request validation 100%, proper error handling dla all invalid inputs
- **Models**: `EnhancedPublicationRequest`, `EnhancedPublicationResponse`
- **Backward Compatibility**: Existing API endpoints continue working

#### **Zadanie 4.5.3.3: Enhanced Publish Endpoint**
- **Wartość**: `/publish/enhanced` endpoint z complete image i content processing
- **Test**: API response time <1s, all platforms processed correctly
- **Features**: Image processing + content differentiation + platform routing

---

### **Phase 4.5.4: AI Writing Flow Integration (Week 2)**

#### **Zadanie 4.5.4.1: Platform-Specific Content Generation**
- **Wartość**: AI Writing Flow generates platform-optimized content
- **Test**: Content quality >8/10 dla każdy platform, prompt effectiveness >7/10
- **Implementation**:
  ```python
  class PlatformOptimizer:
      async def generate_for_platform(self, topic: Topic, platform: str, direct_content: bool) -> Dict
      async def generate_presentation_prompt(self, topic: Topic, config: Dict) -> Dict
      async def generate_direct_content(self, topic: Topic, config: Dict) -> Dict
  ```

#### **Zadanie 4.5.4.2: Multi-Platform API Endpoints**
- **Wartość**: Enhanced AI Writing Flow endpoints dla Orchestrator integration
- **Test**: Multi-platform generation <45s, concurrent processing works
- **Endpoints**: `/generate/multi-platform`, `/generate/linkedin-prompt`
- **Integration**: CrewAI agents z platform-specific optimization

---

### **Phase 4.5.5: End-to-End Integration (Week 3)**

#### **Zadanie 4.5.5.1: Complete Pipeline Testing**
- **Wartość**: Full LinkedIn carousel pipeline (AI→Orchestrator→Presenton→LinkedIn)
- **Test**: End-to-end success rate >95%, total pipeline time <150s
- **Scenarios**: LinkedIn carousel, multi-platform z images, error handling
- **Performance**: 5 concurrent requests handled successfully

#### **Zadanie 4.5.5.2: Production Deployment Configuration**
- **Wartość**: Production-ready docker-compose z all enhanced services  
- **Test**: All services start <60s, health checks pass 100%
- **Environment**: Complete environment variables documentation
- **Monitoring**: Enhanced health checks dla all new components

---

## 📊 **SUCCESS METRICS & VALIDATION**

### **Business Metrics**
- [ ] **Content Quality**: Manual review scores >8/10 dla każdy content type
- [ ] **Processing Speed**: <150s dla complete LinkedIn carousel pipeline  
- [ ] **Platform Coverage**: Support dla 4+ platforms z specialized handling
- [ ] **User Experience**: Single API call creates multi-platform content

### **Technical Metrics**
- [ ] **Service Reliability**: >99% uptime dla każdy microservice
- [ ] **Integration Success**: >95% end-to-end pipeline success rate
- [ ] **Error Handling**: 100% failure scenarios handled gracefully
- [ ] **Performance**: Support dla 10+ concurrent content generation requests

### **Feature Completeness**
- [ ] **Image Processing**: Pexels placeholder→real images w all platforms
- [ ] **Presenton Integration**: LinkedIn prompt→carousel→PDF pipeline working
- [ ] **Platform Differentiation**: LinkedIn prompts vs direct content working
- [ ] **User Control**: Checkbox dla "treści bezpośrednie" functional
- [ ] **Backward Compatibility**: Existing Publisher functionality preserved

---

## 🔧 **DEPENDENCIES & REQUIREMENTS**

### **Prerequisites (Must be Completed)**
- ✅ **Faza 1**: Substack Adapter (completed)
- ✅ **Faza 2**: Twitter Adapter (completed)  
- ✅ **Faza 3**: Ghost Adapter (completed)
- ✅ **Faza 4**: Orchestrator API (completed)

### **External Requirements**
- **Pexels API Key**: Free tier available, required dla image processing
- **Presenton Technology**: Implementation approach needs clarification
- **AI Writing Flow**: Platform-specific content generation capability
- **Docker Resources**: Additional container dla Presenton service

### **Environment Variables**
```bash
# New variables for Enhanced Orchestrator
PEXELS_API_KEY=your_pexels_api_key_here
PRESENTON_URL=http://presenton:8089
PRESENTON_TEMPLATES_PATH=/app/templates

# AI Writing Flow integration
AI_WRITING_FLOW_URL=http://localhost:8003
OPENAI_API_KEY=your_openai_key_here  # For Presenton AI enhancement
```

---

## 🚀 **IMPLEMENTATION ROADMAP**

### **Week 1: Foundation**
- **Days 1-2**: Task 4.5.1.1 - ImageProcessor implementation
- **Days 3-4**: Task 4.5.2.1 - Presenton service skeleton  
- **Day 5**: Task 4.5.1.2 - Shared volume integration

### **Week 2: Core Features**
- **Days 1-2**: Task 4.5.2.2 - Presentation generation logic
- **Days 3-4**: Task 4.5.3.1 - Content differentiation
- **Day 5**: Task 4.5.4.1 - AI Writing Flow integration

### **Week 3: Integration & Testing**
- **Days 1-2**: Task 4.5.5.1 - Complete pipeline testing
- **Days 3-4**: Task 4.5.5.2 - Production deployment
- **Day 5**: Documentation i final validation

---

## 📁 **DELIVERABLES**

### **New Services**
- `presenton/` - Complete Presenton microservice
- Enhanced `src/orchestrator/` - Image processing i content differentiation
- Enhanced AI Writing Flow endpoints

### **Updated Services**  
- All platform adapters - shared volume integration
- Docker compose - new services i volumes
- Environment configuration - new variables

### **Documentation**
- Complete API documentation dla enhanced endpoints
- Deployment guide dla production setup
- Integration examples dla każdy use case
- Testing procedures i validation checklists

---

**Status**: 🚧 **PLANNED FOR IMPLEMENTATION**  
**Prerequisite**: Fazy 1-4 COMPLETED ✅  
**Ready to Start**: Task 4.5.1.1 can begin immediately after Fazy 1-4 completion  
**Timeline**: 2-3 weeks z 1 developer full-time

---

*Created: 2025-08-07*  
*Version: 1.0*  
*Dependencies: Phases 1-4 must be completed first*
