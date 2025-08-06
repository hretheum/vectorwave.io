# Feature Design: Custom Ideas Analysis

## Overview
Umożliwienie użytkownikowi zaproponowania własnych pomysłów na posty w kontekście analizowanego folderu, gdy nie podobają mu się propozycje wygenerowane przez system.

## User Flow

1. **Analiza folderu**
   - User analizuje folder (np. "distributed-tracing")
   - System zwraca listę proponowanych tematów

2. **Reakcja użytkownika**
   - Pod listą tematów pojawia się przycisk: "Mam swoje propozycje do tego folderu"
   - Kliknięcie otwiera inline editor w czacie

3. **Wprowadzanie własnych pomysłów**
   - Editor zachowuje kontekst folderu
   - User może wprowadzić listę pomysłów (jeden per linia)
   - Option+Enter wstawia nową linię bez submitowania

4. **Analiza pomysłów**
   - System analizuje każdy pomysł w kontekście zawartości folderu
   - Ocenia: potencjał viralowy, zgodność z materiałem, ilość dostępnego contentu

## Technical Implementation

### Frontend Changes

#### 1. Przycisk "Mam swoje propozycje"
```typescript
// W komponencie wyświetlającym wyniki analizy
interface AnalysisResultProps {
  folder: string;
  topics: Topic[];
}

const AnalysisResult = ({ folder, topics }: AnalysisResultProps) => {
  const [showCustomIdeasEditor, setShowCustomIdeasEditor] = useState(false);
  
  return (
    <div>
      {/* Lista tematów */}
      <TopicsList topics={topics} />
      
      {/* Przycisk do własnych propozycji */}
      <button 
        onClick={() => setShowCustomIdeasEditor(true)}
        className="custom-ideas-button"
      >
        Mam swoje propozycje do tego folderu
      </button>
      
      {/* Inline editor */}
      {showCustomIdeasEditor && (
        <CustomIdeasEditor 
          folder={folder}
          onSubmit={(ideas) => analyzeCustomIdeas(folder, ideas)}
          onCancel={() => setShowCustomIdeasEditor(false)}
        />
      )}
    </div>
  );
};
```

#### 2. Inline Editor Component
```typescript
interface CustomIdeasEditorProps {
  folder: string;
  onSubmit: (ideas: string[]) => void;
  onCancel: () => void;
}

const CustomIdeasEditor = ({ folder, onSubmit, onCancel }: CustomIdeasEditorProps) => {
  const [content, setContent] = useState('');
  
  const handleKeyDown = (e: React.KeyboardEvent) => {
    // Option+Enter (Alt+Enter on Windows) dla nowej linii
    if (e.key === 'Enter' && e.altKey) {
      e.preventDefault();
      const textarea = e.target as HTMLTextAreaElement;
      const { selectionStart, selectionEnd } = textarea;
      const newContent = 
        content.substring(0, selectionStart) + 
        '\n' + 
        content.substring(selectionEnd);
      setContent(newContent);
      // Restore cursor position
      setTimeout(() => {
        textarea.selectionStart = textarea.selectionEnd = selectionStart + 1;
      }, 0);
      return;
    }
    
    // Enter bez modyfikatora submituje
    if (e.key === 'Enter' && !e.altKey && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };
  
  const handleSubmit = () => {
    const ideas = content
      .split('\n')
      .map(idea => idea.trim())
      .filter(idea => idea.length > 0);
    
    if (ideas.length > 0) {
      onSubmit(ideas);
    }
  };
  
  return (
    <div className="custom-ideas-editor">
      <div className="editor-header">
        <span>Twoje propozycje dla folderu: {folder}</span>
        <button onClick={onCancel}>×</button>
      </div>
      
      <textarea
        value={content}
        onChange={(e) => setContent(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Wpisz swoje pomysły (jeden per linia)&#10;Option+Enter dla nowej linii"
        rows={5}
        autoFocus
      />
      
      <div className="editor-actions">
        <button onClick={onCancel}>Anuluj</button>
        <button onClick={handleSubmit} disabled={!content.trim()}>
          Analizuj pomysły
        </button>
      </div>
    </div>
  );
};
```

### Backend Implementation

#### New Endpoint: /api/analyze-custom-ideas
```python
class CustomIdeasRequest(BaseModel):
    """Request for analyzing custom topic ideas"""
    folder: str
    ideas: List[str]
    platform: str = "LinkedIn"

class IdeaAnalysis(BaseModel):
    """Analysis result for a single idea"""
    idea: str
    viral_score: float
    content_alignment: float  # Jak dobrze idea pasuje do contentu w folderze
    available_material: float  # Ile materiału mamy do tego tematu
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

@app.post("/api/analyze-custom-ideas", tags=["content"])
async def analyze_custom_ideas(request: CustomIdeasRequest):
    """
    Analyze user's custom topic ideas in context of folder content
    """
    # Generate cache key
    cache_key = f"custom_ideas:{request.folder}:{hashlib.md5(':'.join(request.ideas).encode()).hexdigest()}"
    
    # Check cache
    if redis_client:
        cached = redis_client.get(cache_key)
        if cached:
            result = json.loads(cached)
            result["from_cache"] = True
            return result
    
    # Get folder context
    folder_context = await analyze_folder_content(request.folder)
    
    # Analyze each idea
    analyzed_ideas = []
    for idea in request.ideas:
        analysis = await analyze_single_idea(
            idea=idea,
            folder_context=folder_context,
            platform=request.platform
        )
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
            "content_type": folder_context.get("content_type", "unknown")
        }
    )
    
    # Cache result
    if redis_client:
        redis_client.setex(
            cache_key,
            300,  # 5 minutes
            json.dumps(response.dict())
        )
    
    return response

async def analyze_single_idea(idea: str, folder_context: Dict, platform: str) -> IdeaAnalysis:
    """Analyze single idea in context of folder"""
    
    # Use AI to evaluate idea
    prompt = f"""
    Analyze this content idea in context of available material:
    
    Idea: {idea}
    Platform: {platform}
    
    Folder contains:
    - Files: {folder_context.get('file_summary', '')}
    - Main topics: {', '.join(folder_context.get('main_topics', []))}
    - Technical depth: {folder_context.get('technical_depth', 'medium')}
    
    Evaluate:
    1. Viral potential (0-1)
    2. Content alignment - how well idea matches available material (0-1)
    3. Available material - how much content we have for this topic (0-1)
    4. Suggested angle if idea needs refinement
    
    Be critical but constructive.
    """
    
    # AI analysis here...
    
    return IdeaAnalysis(
        idea=idea,
        viral_score=0.75,
        content_alignment=0.8,
        available_material=0.6,
        overall_score=0.7,
        recommendation="Strong potential with good material coverage",
        suggested_angle="Focus on practical implementation challenges"
    )
```

## UI/UX Considerations

1. **Visual Feedback**
   - Przycisk "Mam swoje propozycje" powinien być subtelny ale widoczny
   - Editor pojawia się płynnie (fade in) bez przesuwania contentu
   - Clear visual connection między edytorem a folderem

2. **Keyboard Shortcuts**
   - Option+Enter (Alt+Enter) - nowa linia
   - Enter - submit
   - Escape - cancel

3. **Results Display**
   - Wyniki analizy pokazują się inline w czacie
   - Każdy pomysł ma score i rekomendację
   - Najlepszy pomysł jest wyróżniony

## Implementation Steps - Minimal Increments

### Phase 1: Backend Foundation (Container-First)

#### Step 1: Basic Endpoint (15 min)
```bash
# Test: curl -X POST http://localhost:8000/api/analyze-custom-ideas \
#   -H "Content-Type: application/json" \
#   -d '{"folder": "test", "ideas": ["idea 1"]}'
```
- [ ] Add endpoint that returns mock data
- [ ] Test in container with curl
- [ ] Verify response structure

#### Step 2: Folder Context (20 min)
```python
# Najpierw mock, potem real implementation
async def analyze_folder_content(folder: str) -> Dict:
    return {
        "files": ["file1.md", "file2.md"],
        "main_topics": ["distributed", "tracing"],
        "technical_depth": "high"
    }
```
- [ ] Add analyze_folder_content with mock data
- [ ] Test endpoint returns folder context
- [ ] Verify in container

#### Step 3: Single Idea Analysis (30 min)
- [ ] Implement analyze_single_idea with static scores
- [ ] Test single idea analysis works
- [ ] Add proper response model

#### Step 4: Redis Cache Integration (20 min)
- [ ] Add cache check/set logic
- [ ] Test with redis-cli in container
- [ ] Verify cache hit on second request

#### Step 5: AI Integration (30 min)
- [ ] Replace mock scores with AI call
- [ ] Use existing LLM client from app
- [ ] Test with real content analysis

### Phase 2: Frontend - Minimal UI (Container-First)

#### Step 1: Mock Button (10 min)
```typescript
// Najpierw hardcoded button
<button onClick={() => console.log('Custom ideas clicked')}>
  Mam swoje propozycje
</button>
```
- [ ] Add button to existing results component
- [ ] Test click logs to console
- [ ] Deploy to container, verify

#### Step 2: Basic Text Input (15 min)
```typescript
// Simple textarea, no fancy editor yet
const [showInput, setShowInput] = useState(false);
const [text, setText] = useState('');

{showInput && (
  <textarea 
    value={text} 
    onChange={e => setText(e.target.value)}
    onKeyDown={e => {
      if (e.key === 'Enter' && !e.altKey) {
        e.preventDefault();
        console.log('Submit:', text);
      }
    }}
  />
)}
```
- [ ] Add basic textarea toggle
- [ ] Test Enter submits
- [ ] Verify in container

#### Step 3: API Integration (20 min)
- [ ] Call real endpoint from frontend
- [ ] Display response in console
- [ ] Test with mock ideas

#### Step 4: Option+Enter Support (15 min)
- [ ] Add Alt+Enter handling for newline
- [ ] Test keyboard shortcuts
- [ ] Verify cross-platform (Mac/Windows)

#### Step 5: Results Display (20 min)
- [ ] Show analysis results in UI
- [ ] Highlight best idea
- [ ] Test with multiple ideas

### Phase 3: Polish & Edge Cases

#### Step 1: Error Handling (15 min)
- [ ] Handle empty ideas list
- [ ] Handle API errors gracefully
- [ ] Show loading state

#### Step 2: UI Polish (15 min)
- [ ] Add transitions/animations
- [ ] Improve button/editor styling
- [ ] Mobile responsive check

#### Step 3: Integration Tests (20 min)
- [ ] Full flow test: button → input → API → results
- [ ] Cache behavior verification
- [ ] Edge cases (long lists, special chars)

### Phase 4: Step 6 - AI-Powered Dashboard Analysis with Preload

#### Step 6a: Update analyze-potential endpoint (20 min)
```python
# Zastąp mock topics prawdziwą analizą AI
async def generate_topics_with_ai(folder: str, folder_content: List[str]) -> List[Dict]:
    """Generate topics using AI instead of mocks"""
    # Use CrewAI Content Strategy Expert
    # Return list of topics with scores
```
- [ ] Replace mock topic generation with AI
- [ ] Use same CrewAI agent as custom ideas
- [ ] Test with curl

#### Step 6b: Create preload mechanism (25 min)
```python
# W app startup event
@app.on_event("startup")
async def preload_popular_folders():
    """Preload analysis for common folders on startup"""
    common_folders = ["distributed-tracing", "ai-agents", "crewai-flow"]
    for folder in common_folders:
        asyncio.create_task(preload_folder_analysis(folder))
```
- [ ] Add startup event handler
- [ ] Define list of folders to preload
- [ ] Create async preload function
- [ ] Store results in Redis with longer TTL (30 min)

#### Step 6c: Modify analyze-potential to check preload (15 min)
```python
@app.post("/api/analyze-potential")
async def analyze_content_potential(request):
    # First check if we have preloaded results
    preload_key = f"preload:analyze:{request.folder}"
    if redis_client:
        preloaded = redis_client.get(preload_key)
        if preloaded:
            return json.loads(preloaded)
    
    # If not, generate on demand
    return await generate_analysis_with_ai(request)
```
- [ ] Check for preloaded results first
- [ ] Fall back to on-demand generation
- [ ] Test preload hit vs generation

#### Step 6d: Add monitoring for preload status (15 min)
```python
@app.get("/api/preload-status")
async def get_preload_status():
    """Check which folders are preloaded"""
    return {
        "preloaded_folders": [...],
        "cache_ttl": {...},
        "next_refresh": "..."
    }
```
- [ ] Add endpoint to check preload status
- [ ] Show which folders are ready
- [ ] Display remaining TTL

#### Step 6e: Auto-refresh mechanism (20 min)
```python
# Background task to refresh preloaded data
async def refresh_preloaded_data():
    """Refresh preloaded data before it expires"""
    while True:
        await asyncio.sleep(1200)  # 20 minutes
        await preload_popular_folders()
```
- [ ] Create background refresh task
- [ ] Run every 20 minutes (before 30min TTL)
- [ ] Log refresh operations
- [ ] Handle errors gracefully

## Future Enhancements

1. **Batch Analysis Progress**
   - Pokazuj progress bar podczas analizy wielu pomysłów
   - Streamuj wyniki jak są gotowe

2. **Historical Tracking**
   - Zapisuj własne pomysły użytkownika
   - Ucz się z jego preferencji

3. **Collaborative Mode**
   - Możliwość udostępnienia pomysłów zespołowi
   - Voting na najlepsze pomysły

4. **AI Suggestions**
   - "Based on your ideas, consider also..."
   - Hybrid approach - mieszanka AI i user ideas