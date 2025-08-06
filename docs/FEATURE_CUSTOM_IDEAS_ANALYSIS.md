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

### ✅ 1. **Batch Analysis Progress** (COMPLETED - 2025-08-06)
   - Pokazuj progress bar podczas analizy wielu pomysłów
   - Streamuj wyniki jak są gotowe

   **Implementation Details:**
   - Added `/api/analyze-custom-ideas-stream` endpoint with SSE (Server-Sent Events)
   - Real-time progress tracking with percentage (0-100%)
   - Event types: start, progress, result, error, complete, cached_result
   - Frontend integration examples in `/docs/STREAMING_API_GUIDE.md`
   - Caching support for entire batch results (5 min TTL)
   - Individual error handling without stopping batch

   **Testing:**
   ```bash
   curl -N -X POST http://localhost:8003/api/analyze-custom-ideas-stream \
     -H "Content-Type: application/json" \
     -d '{
       "folder": "2025-08-05-hybrid-rag-crewai",
       "ideas": ["Idea 1", "Idea 2", "Idea 3"],
       "platform": "LinkedIn"
     }'
   ```

### 2. **Historical Tracking** (TODO)
   - Zapisuj własne pomysły użytkownika
   - Ucz się z jego preferencji
   - Suggested implementation:
     - Add user_id to requests
     - Store ideas in PostgreSQL with timestamps
     - Track which ideas were selected/used
     - Build preference model over time

### 3. **AI Suggestions** (TODO)
   - "Based on your ideas, consider also..."
   - Hybrid approach - mieszanka AI i user ideas
   - Suggested implementation:
     - Analyze patterns in user's ideas
     - Generate complementary suggestions
     - Use embeddings to find similar successful content
     - Provide "idea expansion" feature

## Phase 5: AI Assistant Integration for Draft Editing

### Overview
Integrate intelligent AI Assistant that can understand user's editing intentions, analyze impact of changes using agentic RAG, and provide contextual suggestions with actionable buttons.

### User Flow
1. User generates draft and opens it in editor
2. User types in chat: "Co sądzisz o dodatkowej sekcji o tym, że wykorzystujemy agentic RAG..."
3. AI Assistant:
   - Recognizes intent (draft modification suggestion)
   - Analyzes impact on metrics using agentic RAG
   - Provides analysis with scores
   - Offers "Regenerate draft" button if appropriate

### Technical Architecture
```
Frontend (ChatPanel) → /api/chat → OpenAI with Function Calling
                                    ↓
                        Tool Selection (dynamic)
                                    ↓
                    ┌───────────────┴───────────────┐
                    ↓               ↓               ↓
            analyze_impact   regenerate_draft   compare_versions
                    ↓               ↓               ↓
            Agentic RAG     AI Writing Flow    Style Guide Check
```

### Implementation Steps - Minimal Increments

#### Step 1: Basic Chat Endpoint (20 min)
Create `/api/chat` endpoint that echoes messages with mock AI response.

```python
@app.post("/api/chat")
async def chat_with_assistant(request: ChatRequest):
    return {
        "response": f"Otrzymałem: {request.message}",
        "intent": "unknown"
    }
```

**Test:**
```bash
curl -X POST http://localhost:8003/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Test message", "context": {}}'
```
- [ ] Endpoint returns response
- [ ] Frontend displays AI message
- [ ] No errors in console

#### Step 2: Add OpenAI Integration (30 min)
Connect to OpenAI API with basic conversation.

```python
async def chat_with_assistant(request: ChatRequest):
    response = await openai_client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": ASSISTANT_PROMPT},
            {"role": "user", "content": request.message}
        ]
    )
    return {"response": response.choices[0].message.content}
```

**Test:**
- [ ] Chat with "Cześć, kim jesteś?"
- [ ] Get intelligent response about being Vector Wave assistant
- [ ] Response time < 3 seconds

#### Step 3: Add Context Passing (25 min)
Frontend sends draft context, backend includes it in prompt.

```typescript
// Frontend
const response = await fetch('/api/chat', {
  method: 'POST',
  body: JSON.stringify({
    message: userMessage,
    context: {
      currentDraft: editorContent,
      topicTitle: currentTopic,
      platform: currentPlatform,
      metrics: currentMetrics
    }
  })
})
```

**Test:**
- [ ] Open draft in editor
- [ ] Ask "Co sądzisz o tym drafcie?"
- [ ] AI mentions specific content from draft
- [ ] AI knows platform (LinkedIn/Twitter/Blog)

#### Step 4: Intent Recognition (30 min)
Add intent classification to understand user requests.

```python
INTENTS = {
    "modify_draft": ["zmień", "dodaj", "usuń", "popraw", "edytuj", "zaktualizuj"],
    "analyze_impact": ["jak wpłynie", "co sądzisz", "czy to poprawi", "przeanalizuj"],
    "regenerate": ["wygeneruj ponownie", "stwórz nowy", "przepisz"]
}

def classify_intent(message: str) -> str:
    # Simple keyword matching, later can use embeddings
    for intent, keywords in INTENTS.items():
        if any(keyword in message.lower() for keyword in keywords):
            return intent
    return "general_question"
```

**Test:**
- [ ] "Dodaj sekcję o..." → intent: modify_draft
- [ ] "Jak wpłynie to na score?" → intent: analyze_impact
- [ ] "Wygeneruj ponownie z..." → intent: regenerate
- [ ] "Cześć" → intent: general_question

#### Step 5: Function Calling Setup (40 min)
Define tools/functions for OpenAI to call when needed.

**IMPORTANT**: AI should primarily be a conversational assistant. Tools are optional - only used when the user's request specifically requires them. Most conversations should be natural dialogue without tool calls.

```python
# System prompt emphasizing conversational nature
ASSISTANT_PROMPT = """
Jesteś AI Assistantem Vector Wave - inteligentnym partnerem do rozmowy o content marketingu.

NAJWAŻNIEJSZE: Jesteś przede wszystkim konwersacyjnym assistentem. Możesz:
- Rozmawiać na dowolne tematy związane z marketingiem, pisaniem, AI bądź czymkolwiek innym
- Żartować, filozofować, doradzać
- Odpowiadać na pytania niezwiązane z draftem
- Po prostu gawędzić z użytkownikiem

Masz OPCJONALNY dostęp do narzędzi, ale używaj ich TYLKO gdy użytkownik wyraźnie:
- Prosi o analizę wpływu zmian na metryki
- Chce regenerować draft z konkretnymi sugestiami
- Pyta o konkretne score'y lub compliance

NIE używaj narzędzi gdy użytkownik:
- Pyta ogólne pytania ("Co sądzisz o AI?")
- Chce pogadać ("Nudzi mi się")
- Prosi o opinię niezwiązaną z konkretnymi metrykami
- Żartuje lub bawi się konwersacją

Bądź naturalny, pomocny i przyjacielski. To rozmowa, nie tylko wykonywanie poleceń.
"""

tools = [
    {
        "type": "function",
        "function": {
            "name": "analyze_draft_impact",
            "description": "Use ONLY when user explicitly asks about impact on scores/metrics",
            "parameters": {
                "type": "object",
                "properties": {
                    "original_draft": {"type": "string"},
                    "suggested_changes": {"type": "string"},
                    "platform": {"type": "string"}
                }
            }
        }
    },
    {
        "type": "function", 
        "function": {
            "name": "regenerate_draft_with_suggestions",
            "description": "Use ONLY when user explicitly asks to regenerate with specific changes",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic_title": {"type": "string"},
                    "suggestions": {"type": "string"},
                    "platform": {"type": "string"}
                }
            }
        }
    }
]

# Configure OpenAI to prefer conversation over tools
response = await openai_client.chat.completions.create(
    model="gpt-4",
    messages=messages,
    tools=tools,
    tool_choice="auto",  # Let AI decide, don't force tools
    temperature=0.8      # Higher for more natural conversation
)
```

**Test:**
- [ ] "Cześć, nudzi mi się" → Natural conversation, NO tool call
- [ ] "Co sądzisz o przyszłości AI?" → Opinion response, NO tool call  
- [ ] "Opowiedz żart o marketingu" → Tells joke, NO tool call
- [ ] "Jak wpłynie dodanie X na score?" → Uses analyze_draft_impact tool
- [ ] "Czy warto pisać o blockchain?" → General advice, NO tool call
- [ ] "Wygeneruj draft z moimi sugestiami" → Uses regenerate tool

#### Step 6: Implement analyze_draft_impact (35 min)
Connect to agentic RAG for impact analysis.

```python
async def analyze_draft_impact(
    original_draft: str,
    suggested_changes: str,
    platform: str
) -> Dict:
    # Use existing agentic RAG endpoint
    analysis = await check_style_agentic({
        "content": f"{original_draft}\n\nSugerowane zmiany: {suggested_changes}",
        "platform": platform,
        "check_mode": "impact_analysis"
    })
    
    return {
        "current_score": analysis.get("quality_score", 0),
        "predicted_score": analysis.get("predicted_score", 0),
        "impact": analysis.get("impact_analysis", ""),
        "recommendation": analysis.get("recommendation", "")
    }
```

**Test:**
- [ ] Ask "Jak wpłynie dodanie sekcji o X na ocenę?"
- [ ] Get specific scores (before/after)
- [ ] Get recommendation (positive/negative impact)
- [ ] Response includes style guide compliance

#### Step 7: Response Formatting with Actions (30 min)
Format AI responses with context actions (buttons).

```python
if function_name == "analyze_draft_impact":
    result = await analyze_draft_impact(**function_args)
    
    response = {
        "message": f"""
Analiza wpływu sugerowanych zmian:

**Obecny score:** {result['current_score']}/10
**Przewidywany score:** {result['predicted_score']}/10

{result['impact']}

**Rekomendacja:** {result['recommendation']}
        """,
        "context_actions": []
    }
    
    if result['predicted_score'] > result['current_score']:
        response["context_actions"].append({
            "label": "✍️ Wygeneruj draft z sugestiami",
            "action": "regenerate_with_suggestions",
            "params": {
                "suggestions": suggested_changes
            }
        })
```

**Test:**
- [ ] Suggest improvement → see scores comparison
- [ ] If improvement → see "Wygeneruj draft" button
- [ ] If degradation → no regenerate button
- [ ] Button params contain suggestions

#### Step 8: Handle Button Actions in Frontend (25 min)
Process context actions from AI responses.

```typescript
// In ChatPanel
if (data.context_actions) {
  setMessages(prev => [...prev, {
    id: Date.now(),
    role: 'assistant',
    content: data.message,
    contextActions: data.context_actions.map(action => ({
      label: action.label,
      action: async () => {
        if (action.action === 'regenerate_with_suggestions') {
          await regenerateDraftWithSuggestions(action.params)
        }
      }
    }))
  }])
}
```

**Test:**
- [ ] Click "Wygeneruj draft z sugestiami"
- [ ] See loading state
- [ ] New draft generated with suggestions
- [ ] Editor updates with new content

#### Step 9: Implement Regenerate with Suggestions (35 min)
Connect to existing draft generation with modifications.

```python
async def regenerate_draft_with_suggestions(
    topic_title: str,
    suggestions: str,
    platform: str,
    context: Dict
) -> Dict:
    # Enhance prompt with user suggestions
    enhanced_prompt = f"""
    Original topic: {topic_title}
    Platform: {platform}
    
    User suggestions to incorporate:
    {suggestions}
    
    Current metrics: {context.get('metrics', {})}
    """
    
    # Call existing generate-draft with enhanced context
    result = await generate_draft({
        "topic_title": topic_title,
        "platform": platform,
        "editorial_recommendations": enhanced_prompt,
        "skip_research": False  # Do research to incorporate suggestions
    })
    
    return result
```

**Test:**
- [ ] Suggest specific addition
- [ ] Click regenerate button
- [ ] New draft includes suggestion
- [ ] Original style maintained
- [ ] Metrics improved

#### Step 10: Add Streaming Support (30 min)
Stream long AI responses for better UX.

```python
async def chat_with_assistant_stream(request: ChatRequest):
    # SSE streaming for long analyses
    async def generate():
        yield f"data: {json.dumps({'type': 'start'})}\n\n"
        
        # Stream OpenAI response
        stream = await openai_client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            tools=tools,
            stream=True
        )
        
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield f"data: {json.dumps({
                    'type': 'content',
                    'content': chunk.choices[0].delta.content
                })}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")
```

**Test:**
- [ ] Ask complex question
- [ ] See text appearing progressively
- [ ] No UI freezing
- [ ] Complete message displayed correctly

#### Step 11: Add Conversation Memory (25 min)
Maintain context across messages.

```python
# Store conversation in Redis with session ID
async def get_conversation_history(session_id: str) -> List[Dict]:
    if redis_client:
        history = redis_client.get(f"chat:history:{session_id}")
        return json.loads(history) if history else []
    return []

async def save_message(session_id: str, role: str, content: str):
    history = await get_conversation_history(session_id)
    history.append({"role": role, "content": content})
    
    # Keep last 20 messages
    if len(history) > 20:
        history = history[-20:]
    
    if redis_client:
        redis_client.setex(
            f"chat:history:{session_id}",
            3600,  # 1 hour TTL
            json.dumps(history)
        )
```

**Test:**
- [ ] Ask about draft
- [ ] Make suggestion
- [ ] Reference "jak mówiłem wcześniej"
- [ ] AI remembers previous context
- [ ] Clear chat → context reset

#### Step 12: Error Handling & Fallbacks (20 min)
Handle API failures gracefully.

```python
try:
    response = await openai_client.chat.completions.create(...)
except Exception as e:
    logger.error(f"OpenAI API error: {e}")
    
    # Fallback to simple responses
    if "limit" in str(e):
        return {
            "response": "Przepraszam, przekroczono limit API. Spróbuj za chwilę.",
            "error": "rate_limit"
        }
    else:
        return {
            "response": "Wystąpił błąd. Sprawdź czy backend jest dostępny.",
            "error": "api_error"
        }
```

**Test:**
- [ ] Disable OpenAI API key → get fallback message (KRYTYCZNE: ŻADNYCH MOCKÓW, to ma być dla użytkownika jasne, że jest konkretny problem do rozwiązania)
- [ ] Overload with requests → get rate limit message
- [ ] Backend down → get connection error
- [ ] User sees friendly error messages

### Configuration & Environment (klucz już jest w .env!!!)

```env
# Add to .env
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4
ASSISTANT_MAX_TOKENS=1000
ASSISTANT_TEMPERATURE=0.7
```

### Success Metrics
- Response time < 3s for simple queries
- Function calling accuracy > 90%
- Correct intent recognition > 85%
- User can modify draft through natural language
- Context maintained across conversation