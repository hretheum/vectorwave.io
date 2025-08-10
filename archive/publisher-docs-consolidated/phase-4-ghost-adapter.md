# PLAN PRZYROSTOWEJ IMPLEMENTACJI: GHOST ADAPTER

## 📋 **PRZEGLĄD SYSTEMU**

### **Charakterystyka Ghost API**
- **Admin API**: JWT-based authentication, full CRUD operations na posts/pages
- **Content API**: Tylko read-only, key-based authentication
- **Wersjonowanie**: v6.0 (najnowsza stabilna), z nagłówkiem `Accept-Version`
- **Format dokumentów**: Lexical JSON (domyślny) oraz HTML (legacy support)
- **Endpointy**: `POST /admin/posts/`, `PUT /admin/posts/{id}`, `GET /admin/posts/`
- **Status publikacji**: `draft`, `published`, `scheduled`
- **Funkcje**: tags, featured images, SEO metadata, custom excerpts

### **Zmienne środowiskowe wymagane**
```bash
# Już dostępne w .env
GHOST_API_URL=https://your-ghost-site.com
GHOST_API_KEY=your_admin_api_key_here
```

### **Struktura architektury**
```
publisher/
├── src/adapters/ghost/
│   ├── main.py              # FastAPI app
│   ├── ghost_client.py      # Ghost API client z JWT auth
│   ├── models.py            # Pydantic models
│   └── requirements.txt     # Zależności Python
├── scripts/
│   └── test-ghost-*.sh      # Testy każdego zadania
└── docs/
    └── phase-4-ghost-adapter.md
```

---

## 🎯 **ZADANIA PRZYROSTOWE**

### **Zadanie 4.1: Szkielet usługi Ghost Adapter (kontener, healthcheck)**

#### **Cele:**
- [x] Stworzenie podstawowej aplikacji FastAPI
- [x] Konfiguracja Docker (port 8084, healthcheck)
- [x] Integracja z docker-compose.yml i Makefile
- [x] Podstawowe endpointy: `/`, `/health`, `/config`

#### **Implementacja:**

**1. Struktura plików:**
```bash
mkdir -p src/adapters/ghost
touch src/adapters/ghost/{main.py,ghost_client.py,models.py,requirements.txt,Dockerfile}
```

**2. FastAPI + podstawowe endpointy:**
```python
# src/adapters/ghost/main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import logging

app = FastAPI(title="Ghost Adapter", version="1.0.0")
logger = logging.getLogger(__name__)

class PublishRequest(BaseModel):
    title: str
    content: str  # HTML or Lexical JSON
    status: str = "draft"  # draft, published, scheduled
    published_at: Optional[str] = None
    tags: Optional[List[str]] = None
    featured: bool = False
    custom_excerpt: Optional[str] = None
    feature_image: Optional[str] = None

class PublishResponse(BaseModel):
    accepted: bool
    post_id: str
    status: str
    url: Optional[str] = None
    message: str

@app.get("/")
async def root():
    ghost_configured = bool(os.getenv("GHOST_API_KEY") and os.getenv("GHOST_API_URL"))
    return {
        "service": "ghost-adapter",
        "status": "ready" if ghost_configured else "misconfigured",
        "ghost_configured": ghost_configured
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/config")
async def config():
    # Test Ghost API connection
    return {
        "ghost_api_configured": bool(os.getenv("GHOST_API_KEY")),
        "ghost_url": os.getenv("GHOST_API_URL", "not_set"),
        "status": "ready"
    }
```

**3. Docker konfiguracja:**
```dockerfile
# src/adapters/ghost/Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8082"]
```

**4. docker-compose.yml integration:**
```yaml
ghost-adapter:
  build: ./src/adapters/ghost
  ports:
    - "8084:8082"
  env_file:
    - ./.env
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8082/health"]
    interval: 30s
    timeout: 10s
    retries: 3
  depends_on:
    - nginx
```

**5. Makefile targets:**
```makefile
build-ghost:
	docker-compose build ghost-adapter

up-ghost:
	docker-compose up -d ghost-adapter

test-ghost-health:
	curl -f http://localhost:8084/health
```

#### **Test Case:**
```bash
#!/bin/bash
# scripts/test-ghost-skeleton.sh

echo "🧪 TESTOWANIE GHOST ADAPTER SKELETON"
echo "===================================="

# Test 1: Health check
echo "Test 1: Health endpoint"
curl -s -f http://localhost:8084/health && echo " ✅ PASS" || echo " ❌ FAIL"

# Test 2: Root endpoint
echo "Test 2: Root endpoint"
curl -s http://localhost:8084/ | grep -q "ghost-adapter" && echo " ✅ PASS" || echo " ❌ FAIL"

# Test 3: Config endpoint
echo "Test 3: Config endpoint"
curl -s http://localhost:8084/config | grep -q "ghost_api_configured" && echo " ✅ PASS" || echo " ❌ FAIL"

echo "🎯 Ghost Adapter skeleton ready!"
```

#### **Walidacja ukończenia:**
- [ ] Container startuje na porcie 8084
- [ ] Healthcheck returns 200 OK
- [ ] `/config` pokazuje status Ghost API keys
- [ ] Integracja z Makefile działa

---

### **Zadanie 4.2: JWT Authentication i Ghost API Client**

#### **Cele:**
- [x] Implementacja JWT token generation (HS256)
- [x] Klasa GhostClient z metodami API
- [x] Test connection do Ghost API
- [x] Error handling dla auth errors

#### **Implementacja:**

**1. Ghost API Client z JWT auth:**
```python
# src/adapters/ghost/ghost_client.py
import jwt
import time
import requests
import json
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class GhostAPIError(Exception):
    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[Dict] = None):
        self.message = message
        self.status_code = status_code
        self.response_data = response_data
        super().__init__(self.message)

class GhostClient:
    def __init__(self, api_url: str, api_key: str):
        self.api_url = api_url.rstrip('/')
        self.api_key = api_key
        self.base_url = f"{self.api_url}/ghost/api/admin"
        
        # Parse API key (format: id:secret)
        try:
            self.key_id, self.key_secret = api_key.split(':')
        except ValueError:
            raise ValueError("Invalid API key format. Expected 'id:secret'")
    
    def _generate_jwt_token(self) -> str:
        """Generate JWT token for Ghost Admin API authentication"""
        now = int(time.time())
        
        # JWT header
        header = {
            'alg': 'HS256',
            'typ': 'JWT',
            'kid': self.key_id
        }
        
        # JWT payload
        payload = {
            'iat': now,
            'exp': now + 300,  # 5 minutes
            'aud': '/admin/'
        }
        
        # Generate token
        token = jwt.encode(
            payload, 
            bytes.fromhex(self.key_secret), 
            algorithm='HS256',
            headers=header
        )
        
        return token

    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """Make authenticated request to Ghost API"""
        token = self._generate_jwt_token()
        
        headers = {
            'Authorization': f'Ghost {token}',
            'Content-Type': 'application/json',
            'Accept-Version': 'v6.0'
        }
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == 'POST':
                response = requests.post(url, headers=headers, json=data, timeout=30)
            elif method.upper() == 'PUT':
                response = requests.put(url, headers=headers, json=data, timeout=30)
            elif method.upper() == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=30)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            # Parse response
            if response.status_code >= 400:
                error_data = response.json() if response.content else {}
                raise GhostAPIError(
                    f"Ghost API error: {response.status_code}", 
                    response.status_code, 
                    error_data
                )
            
            return response.json() if response.content else {}
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Ghost API request failed: {str(e)}")
            raise GhostAPIError(f"Request failed: {str(e)}")

    def test_connection(self) -> Dict[str, Any]:
        """Test connection to Ghost API"""
        try:
            # Test with site endpoint (lightweight)
            result = self._make_request('GET', '/site/')
            
            # Test posts endpoint access
            posts_result = self._make_request('GET', '/posts/?limit=1')
            
            return {
                'connected': True,
                'site_info': result.get('site', {}),
                'posts_access': True,
                'message': 'Ghost API connection successful'
            }
        except GhostAPIError as e:
            return {
                'connected': False,
                'error': str(e),
                'status_code': e.status_code,
                'message': 'Ghost API connection failed'
            }

    def create_post(self, title: str, content: str, status: str = 'draft', 
                   content_format: str = 'html', **kwargs) -> Dict:
        """Create a new post in Ghost"""
        
        # Prepare post data according to Ghost API format
        post_data = {
            'title': title,
            'status': status
        }
        
        # Content format handling
        if content_format == 'html':
            post_data['html'] = content
        else:  # lexical
            post_data['lexical'] = content if isinstance(content, str) else json.dumps(content)
        
        # Optional fields
        if kwargs.get('published_at'):
            post_data['published_at'] = kwargs['published_at']
        if kwargs.get('tags'):
            post_data['tags'] = [{'name': tag} for tag in kwargs['tags']]
        if kwargs.get('featured'):
            post_data['featured'] = kwargs['featured']
        if kwargs.get('custom_excerpt'):
            post_data['custom_excerpt'] = kwargs['custom_excerpt']
        if kwargs.get('feature_image'):
            post_data['feature_image'] = kwargs['feature_image']
        
        # Wrap in posts array as required by Ghost API
        payload = {'posts': [post_data]}
        
        logger.info(f"Creating Ghost post: {title}")
        result = self._make_request('POST', '/posts/', payload)
        
        return result.get('posts', [{}])[0]

    def get_posts(self, limit: int = 15, **filters) -> Dict:
        """Get posts from Ghost"""
        params = f"?limit={limit}"
        
        if filters.get('status'):
            params += f"&filter=status:{filters['status']}"
        
        return self._make_request('GET', f'/posts/{params}')

    def update_post(self, post_id: str, updated_at: str, **updates) -> Dict:
        """Update existing post"""
        post_data = {
            'updated_at': updated_at,  # Required for optimistic concurrency
            **updates
        }
        
        payload = {'posts': [post_data]}
        return self._make_request('PUT', f'/posts/{post_id}/', payload)
```

**2. Integracja z main.py:**
```python
# Aktualizacja main.py
ghost_client = None

def get_ghost_client():
    global ghost_client
    if not ghost_client:
        api_url = os.getenv("GHOST_API_URL")
        api_key = os.getenv("GHOST_API_KEY")
        
        if not api_url or not api_key:
            return None
            
        ghost_client = GhostClient(api_url, api_key)
    
    return ghost_client

@app.get("/config")
async def config():
    client = get_ghost_client()
    if not client:
        return {
            "ghost_api_configured": False,
            "status": "misconfigured",
            "message": "GHOST_API_URL and GHOST_API_KEY required"
        }
    
    # Test connection
    connection_test = client.test_connection()
    
    return {
        "ghost_api_configured": True,
        "connected": connection_test['connected'],
        "site_info": connection_test.get('site_info', {}),
        "status": "ready" if connection_test['connected'] else "connection_failed",
        "message": connection_test['message']
    }
```

#### **Test Case:**
```bash
#!/bin/bash
# scripts/test-ghost-auth.sh

echo "🧪 TESTOWANIE GHOST API AUTH"
echo "============================="

BASE_URL="http://localhost:8084"

echo "Test 1: Connection test via /config"
curl -s "$BASE_URL/config" | jq '.connected' | grep -q "true" && echo " ✅ PASS" || echo " ❌ FAIL"

echo "Test 2: Site info retrieval"
curl -s "$BASE_URL/config" | jq '.site_info.title' | grep -q -v "null" && echo " ✅ PASS" || echo " ❌ FAIL"

echo "🎯 Ghost API authentication ready!"
```

#### **Walidacja ukończenia:**
- [ ] JWT tokens generowane poprawnie
- [ ] Connection test przechodzi
- [ ] Error handling dla błędnych kluczy
- [ ] Site info pobierane z Ghost API

---

### **Zadanie 4.3: Endpoint POST /publish (publikacja postów)**

#### **Cele:**
- [x] Endpoint `/publish` z walidacją Pydantic
- [x] Obsługa HTML i Lexical content
- [x] Support dla tags, featured, excerpt
- [x] Status handling (draft/published/scheduled)

#### **Implementacja:**

**1. Modele Pydantic:**
```python
# src/adapters/ghost/models.py
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime

class PublishRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=300)
    content: str = Field(..., min_length=1)
    content_format: str = Field(default="html", pattern="^(html|lexical)$")
    status: str = Field(default="draft", pattern="^(draft|published|scheduled)$")
    published_at: Optional[str] = None
    tags: Optional[List[str]] = Field(default=None, max_items=10)
    featured: bool = False
    custom_excerpt: Optional[str] = Field(default=None, max_length=500)
    feature_image: Optional[str] = None
    
    @validator('published_at')
    def validate_published_at(cls, v, values):
        if v and values.get('status') == 'scheduled':
            try:
                # Validate ISO format
                datetime.fromisoformat(v.replace('Z', '+00:00'))
            except ValueError:
                raise ValueError('published_at must be valid ISO 8601 format')
        return v
    
    @validator('tags')
    def validate_tags(cls, v):
        if v:
            # Remove duplicates and empty strings
            v = list(set([tag.strip() for tag in v if tag.strip()]))
            if len(v) > 10:
                raise ValueError('Maximum 10 tags allowed')
        return v

class PublishResponse(BaseModel):
    accepted: bool
    post_id: str
    status: str
    url: Optional[str] = None
    slug: Optional[str] = None
    message: str
    published_at: Optional[str] = None
```

**2. Publikacja endpoint:**
```python
# Aktualizacja main.py
from .models import PublishRequest, PublishResponse
from .ghost_client import GhostClient, GhostAPIError

@app.post("/publish", response_model=PublishResponse)
async def publish_post(request: PublishRequest):
    """Publikuj post w Ghost"""
    logger.info(f"[Ghost Adapter] Publishing post: '{request.title}'")
    
    try:
        client = get_ghost_client()
        if not client:
            raise HTTPException(
                status_code=500,
                detail="Ghost API not configured. Set GHOST_API_URL and GHOST_API_KEY."
            )
        
        # Prepare content based on format
        content = request.content
        if request.content_format == "lexical" and isinstance(content, str):
            try:
                # Validate JSON if lexical format
                json.loads(content)
            except json.JSONDecodeError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid Lexical JSON format in content"
                )
        
        # Create post via Ghost API
        post_result = client.create_post(
            title=request.title,
            content=content,
            status=request.status,
            content_format=request.content_format,
            published_at=request.published_at,
            tags=request.tags,
            featured=request.featured,
            custom_excerpt=request.custom_excerpt,
            feature_image=request.feature_image
        )
        
        # Prepare response
        response = PublishResponse(
            accepted=True,
            post_id=post_result['id'],
            status=post_result['status'],
            url=post_result.get('url'),
            slug=post_result.get('slug'),
            published_at=post_result.get('published_at'),
            message=f"Post '{request.title}' created successfully as {post_result['status']}"
        )
        
        logger.info(f"[Ghost Adapter] Post published: {response.message}")
        return response
        
    except GhostAPIError as e:
        logger.error(f"[Ghost Adapter] Ghost API error: {str(e)}")
        
        if e.status_code == 401:
            raise HTTPException(
                status_code=401,
                detail="Invalid Ghost API credentials"
            )
        elif e.status_code == 422:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid post data: {str(e)}"
            )
        else:
            raise HTTPException(
                status_code=e.status_code or 500,
                detail=f"Ghost API error: {str(e)}"
            )
    
    except Exception as e:
        logger.error(f"[Ghost Adapter] Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to publish post: {str(e)}"
        )
```

#### **Test Case:**
```bash
#!/bin/bash
# scripts/test-ghost-publish.sh

echo "🧪 TESTOWANIE GHOST PUBLISH ENDPOINT"
echo "====================================="

BASE_URL="http://localhost:8084"

# Test 1: Basic HTML post
echo "Test 1: Basic HTML post"
curl -s -X POST "$BASE_URL/publish" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test HTML Post",
    "content": "<h1>Hello Ghost!</h1><p>This is a test post from API.</p>",
    "status": "draft"
  }' | jq '.accepted' | grep -q "true" && echo " ✅ PASS" || echo " ❌ FAIL"

# Test 2: Post with tags and metadata
echo "Test 2: Post with tags and metadata"
curl -s -X POST "$BASE_URL/publish" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Featured Test Post",
    "content": "<h1>Featured Content</h1><p>This post has metadata.</p>",
    "status": "draft",
    "tags": ["test", "api", "ghost"],
    "featured": true,
    "custom_excerpt": "This is a test post excerpt"
  }' | jq '.post_id' | grep -q -v "null" && echo " ✅ PASS" || echo " ❌ FAIL"

# Test 3: Lexical format post
echo "Test 3: Lexical format post"
curl -s -X POST "$BASE_URL/publish" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Lexical Test Post",
    "content": "{\"root\":{\"children\":[{\"children\":[{\"detail\":0,\"format\":0,\"mode\":\"normal\",\"style\":\"\",\"text\":\"Hello from Lexical!\",\"type\":\"extended-text\",\"version\":1}],\"direction\":\"ltr\",\"format\":\"\",\"indent\":0,\"type\":\"paragraph\",\"version\":1}],\"direction\":\"ltr\",\"format\":\"\",\"indent\":0,\"type\":\"root\",\"version\":1}}",
    "content_format": "lexical",
    "status": "draft"
  }' | jq '.accepted' | grep -q "true" && echo " ✅ PASS" || echo " ❌ FAIL"

# Test 4: Validation errors
echo "Test 4: Validation errors (empty title)"
curl -s -X POST "$BASE_URL/publish" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "",
    "content": "Content without title"
  }' | grep -q "422" && echo " ✅ PASS" || echo " ❌ FAIL"

echo "🎯 Ghost publish endpoint ready!"
```

#### **Walidacja ukończenia:**
- [ ] Publikacja HTML posts działa
- [ ] Publikacja Lexical posts działa
- [ ] Tags, featured, excerpt są obsługiwane
- [ ] Walidacja błędów działa poprawnie

---

### **Zadanie 4.4: Harmonogram publikacji i status management**

#### **Cele:**
- [x] Scheduled posts z published_at
- [x] Update post status (draft → published)
- [x] Batch operations dla multiple posts
- [x] Post preview przed publikacją

#### **Implementacja:**

**1. Schedule management:**
```python
# Rozszerzenie ghost_client.py
def schedule_post(self, post_id: str, published_at: str) -> Dict:
    """Schedule existing post for future publication"""
    
    # First get current post data
    current_post = self._make_request('GET', f'/posts/{post_id}/')
    post_data = current_post['posts'][0]
    
    # Update with scheduling
    update_data = {
        'status': 'scheduled',
        'published_at': published_at,
        'updated_at': post_data['updated_at']  # Required for concurrency
    }
    
    return self.update_post(post_id, post_data['updated_at'], **update_data)

def publish_now(self, post_id: str) -> Dict:
    """Immediately publish a draft post"""
    
    current_post = self._make_request('GET', f'/posts/{post_id}/')
    post_data = current_post['posts'][0]
    
    update_data = {
        'status': 'published',
        'published_at': datetime.utcnow().isoformat() + 'Z',
        'updated_at': post_data['updated_at']
    }
    
    return self.update_post(post_id, post_data['updated_at'], **update_data)

def get_post_preview(self, post_id: str) -> Dict:
    """Get post preview with rendered content"""
    return self._make_request('GET', f'/posts/{post_id}/?include=tags,authors')
```

**2. Nowe endpointy:**
```python
# Aktualizacja main.py
from datetime import datetime, timezone

@app.put("/posts/{post_id}/schedule")
async def schedule_post(post_id: str, published_at: str):
    """Schedule post for future publication"""
    try:
        # Validate future date
        schedule_time = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
        if schedule_time <= datetime.now(timezone.utc):
            raise HTTPException(
                status_code=400,
                detail="published_at must be in the future"
            )
        
        client = get_ghost_client()
        if not client:
            raise HTTPException(status_code=500, detail="Ghost API not configured")
        
        result = client.schedule_post(post_id, published_at)
        
        return {
            "success": True,
            "post_id": post_id,
            "status": "scheduled",
            "published_at": published_at,
            "message": f"Post scheduled for {published_at}"
        }
        
    except GhostAPIError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))

@app.put("/posts/{post_id}/publish")
async def publish_post_now(post_id: str):
    """Immediately publish a draft post"""
    try:
        client = get_ghost_client()
        if not client:
            raise HTTPException(status_code=500, detail="Ghost API not configured")
        
        result = client.publish_now(post_id)
        
        return {
            "success": True,
            "post_id": post_id,
            "status": "published",
            "url": result.get('url'),
            "message": "Post published successfully"
        }
        
    except GhostAPIError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))

@app.get("/posts/{post_id}/preview")
async def get_post_preview(post_id: str):
    """Get post preview"""
    try:
        client = get_ghost_client()
        if not client:
            raise HTTPException(status_code=500, detail="Ghost API not configured")
        
        result = client.get_post_preview(post_id)
        
        return result['posts'][0]
        
    except GhostAPIError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))

@app.get("/posts")
async def list_posts(status: str = "all", limit: int = 15):
    """List posts with optional status filter"""
    try:
        client = get_ghost_client()
        if not client:
            raise HTTPException(status_code=500, detail="Ghost API not configured")
        
        filters = {}
        if status != "all":
            filters['status'] = status
        
        result = client.get_posts(limit=limit, **filters)
        
        return {
            "posts": result.get('posts', []),
            "meta": result.get('meta', {}),
            "total": len(result.get('posts', []))
        }
        
    except GhostAPIError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))
```

#### **Test Case:**
```bash
#!/bin/bash
# scripts/test-ghost-schedule.sh

echo "🧪 TESTOWANIE GHOST SCHEDULE MANAGEMENT"
echo "======================================="

BASE_URL="http://localhost:8084"

# Test 1: Create draft post first
echo "Test 1: Create draft post"
RESPONSE=$(curl -s -X POST "$BASE_URL/publish" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Schedule Post",
    "content": "<h1>This will be scheduled</h1>",
    "status": "draft"
  }')

POST_ID=$(echo "$RESPONSE" | jq -r '.post_id')
echo "Created post ID: $POST_ID"

# Test 2: Schedule the post
echo "Test 2: Schedule post for future"
FUTURE_DATE=$(date -u -d "+1 hour" +"%Y-%m-%dT%H:%M:%SZ")
curl -s -X PUT "$BASE_URL/posts/$POST_ID/schedule?published_at=$FUTURE_DATE" \
  | jq '.status' | grep -q "scheduled" && echo " ✅ PASS" || echo " ❌ FAIL"

# Test 3: Get post preview
echo "Test 3: Get post preview"
curl -s "$BASE_URL/posts/$POST_ID/preview" \
  | jq '.title' | grep -q "Test Schedule Post" && echo " ✅ PASS" || echo " ❌ FAIL"

# Test 4: List draft posts
echo "Test 4: List draft posts"
curl -s "$BASE_URL/posts?status=draft" \
  | jq '.posts | length' | grep -q -E "[0-9]+" && echo " ✅ PASS" || echo " ❌ FAIL"

echo "🎯 Ghost schedule management ready!"
```

#### **Walidacja ukończenia:**
- [ ] Scheduling posts działa
- [ ] Status transitions działają
- [ ] Post preview endpoint działa
- [ ] List posts z filterami działa

---

### **Zadanie 4.5: Image upload i media management**

#### **Cele:**
- [x] Upload images do Ghost
- [x] Automatyczne przetwarzanie image URLs w content
- [x] Feature image support
- [x] Media validation i size limits

#### **Implementacja:**

**1. Image upload w Ghost client:**
```python
# Rozszerzenie ghost_client.py
import requests
from pathlib import Path

def upload_image(self, image_path: str, purpose: str = "image") -> Dict:
    """Upload image to Ghost"""
    
    if not Path(image_path).exists():
        raise ValueError(f"Image file not found: {image_path}")
    
    token = self._generate_jwt_token()
    
    headers = {
        'Authorization': f'Ghost {token}',
        'Accept-Version': 'v6.0'
    }
    
    with open(image_path, 'rb') as f:
        files = {
            'file': (Path(image_path).name, f, 'image/*'),
            'purpose': (None, purpose)
        }
        
        response = requests.post(
            f"{self.base_url}/images/upload/",
            headers=headers,
            files=files,
            timeout=60
        )
    
    if response.status_code >= 400:
        error_data = response.json() if response.content else {}
        raise GhostAPIError(f"Image upload failed: {response.status_code}", response.status_code, error_data)
    
    return response.json()

def process_content_images(self, content: str) -> str:
    """Find and upload local images in content, replace with Ghost URLs"""
    import re
    
    # Find image references in HTML
    img_pattern = r'<img[^>]+src=["\']([^"\']+)["\'][^>]*>'
    
    def replace_image(match):
        full_tag = match.group(0)
        src = match.group(1)
        
        # Skip if already a full URL
        if src.startswith(('http://', 'https://')):
            return full_tag
        
        # Skip if not a local file path
        if not Path(src).exists():
            logger.warning(f"Image file not found: {src}")
            return full_tag
        
        try:
            # Upload to Ghost
            upload_result = self.upload_image(src)
            new_url = upload_result['images'][0]['url']
            
            # Replace src in the tag
            return full_tag.replace(src, new_url)
            
        except Exception as e:
            logger.error(f"Failed to upload image {src}: {str(e)}")
            return full_tag
    
    return re.sub(img_pattern, replace_image, content)
```

**2. Media endpoint:**
```python
# Aktualizacja main.py
from fastapi import UploadFile, File
import tempfile
import os

@app.post("/upload-image")
async def upload_image(file: UploadFile = File(...)):
    """Upload image to Ghost"""
    try:
        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Validate file size (5MB limit)
        if file.size > 5 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File too large (max 5MB)")
        
        client = get_ghost_client()
        if not client:
            raise HTTPException(status_code=500, detail="Ghost API not configured")
        
        # Save temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_path = temp_file.name
        
        try:
            # Upload to Ghost
            result = client.upload_image(temp_path)
            
            return {
                "success": True,
                "url": result['images'][0]['url'],
                "filename": file.filename,
                "size": file.size,
                "message": "Image uploaded successfully"
            }
            
        finally:
            # Clean up temp file
            os.unlink(temp_path)
        
    except GhostAPIError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))
    
    except Exception as e:
        logger.error(f"Image upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

# Update publish endpoint to handle image processing
@app.post("/publish", response_model=PublishResponse)
async def publish_post(request: PublishRequest):
    """Publikuj post w Ghost z automatic image processing"""
    logger.info(f"[Ghost Adapter] Publishing post: '{request.title}'")
    
    try:
        client = get_ghost_client()
        if not client:
            raise HTTPException(status_code=500, detail="Ghost API not configured")
        
        # Process images in content if HTML format
        content = request.content
        if request.content_format == "html":
            content = client.process_content_images(content)
        
        # Upload feature image if local path provided
        feature_image_url = request.feature_image
        if feature_image_url and not feature_image_url.startswith(('http://', 'https://')):
            if Path(feature_image_url).exists():
                upload_result = client.upload_image(feature_image_url)
                feature_image_url = upload_result['images'][0]['url']
        
        # Create post with processed content
        post_result = client.create_post(
            title=request.title,
            content=content,
            status=request.status,
            content_format=request.content_format,
            published_at=request.published_at,
            tags=request.tags,
            featured=request.featured,
            custom_excerpt=request.custom_excerpt,
            feature_image=feature_image_url
        )
        
        # Return response
        response = PublishResponse(
            accepted=True,
            post_id=post_result['id'],
            status=post_result['status'],
            url=post_result.get('url'),
            slug=post_result.get('slug'),
            published_at=post_result.get('published_at'),
            message=f"Post '{request.title}' created with processed images"
        )
        
        logger.info(f"[Ghost Adapter] Post published: {response.message}")
        return response
        
    except Exception as e:
        logger.error(f"[Ghost Adapter] Publish error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
```

#### **Test Case:**
```bash
#!/bin/bash
# scripts/test-ghost-media.sh

echo "🧪 TESTOWANIE GHOST MEDIA MANAGEMENT"
echo "====================================="

BASE_URL="http://localhost:8084"

# Test 1: Upload single image
echo "Test 1: Upload image file"
echo "Creating test image..."
convert -size 200x100 xc:blue test-image.jpg

curl -s -X POST "$BASE_URL/upload-image" \
  -F "file=@test-image.jpg" \
  | jq '.success' | grep -q "true" && echo " ✅ PASS" || echo " ❌ FAIL"

# Test 2: Post with local images in content
echo "Test 2: Post with auto image processing"
curl -s -X POST "$BASE_URL/publish" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Post with Images",
    "content": "<h1>Test Post</h1><p>Here is an image:</p><img src=\"test-image.jpg\" alt=\"Test\">",
    "content_format": "html",
    "status": "draft"
  }' | jq '.accepted' | grep -q "true" && echo " ✅ PASS" || echo " ❌ FAIL"

# Test 3: Validate file type restriction
echo "Test 3: File type validation"
echo "test content" > test.txt
curl -s -X POST "$BASE_URL/upload-image" \
  -F "file=@test.txt" \
  | grep -q "400" && echo " ✅ PASS" || echo " ❌ FAIL"

# Cleanup
rm -f test-image.jpg test.txt

echo "🎯 Ghost media management ready!"
```

#### **Walidacja ukończenia:**
- [ ] Image upload endpoint działa
- [ ] Automatic image processing w content
- [ ] Feature image upload działa
- [ ] File validation działa

---

### **Zadanie 4.6: Error handling i monitoring**

#### **Cele:**
- [x] Comprehensive error handling
- [x] Rate limiting detection
- [x] Health monitoring z Ghost API
- [x] Structured logging

#### **Implementacja:**

**1. Enhanced error handling:**
```python
# Rozszerzenie ghost_client.py
from tenacity import retry, stop_after_attempt, wait_exponential
import logging

class GhostAPIError(Exception):
    """Enhanced Ghost API Error with categorization"""
    
    ERROR_CATEGORIES = {
        400: "VALIDATION_ERROR",
        401: "AUTHENTICATION_ERROR", 
        403: "PERMISSION_ERROR",
        404: "NOT_FOUND",
        422: "UNPROCESSABLE_ENTITY",
        429: "RATE_LIMIT_EXCEEDED",
        500: "INTERNAL_SERVER_ERROR",
        502: "BAD_GATEWAY",
        503: "SERVICE_UNAVAILABLE"
    }
    
    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[Dict] = None):
        self.message = message
        self.status_code = status_code
        self.response_data = response_data or {}
        self.error_category = self.ERROR_CATEGORIES.get(status_code, "UNKNOWN_ERROR")
        super().__init__(self.message)

class GhostClient:
    def __init__(self, api_url: str, api_key: str):
        # ... existing init code ...
        self.logger = logging.getLogger(__name__)
        self.request_count = 0
        self.error_count = 0

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def _make_request_with_retry(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """Make request with automatic retry for transient errors"""
        return self._make_request(method, endpoint, data)

    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """Enhanced request method with detailed error handling"""
        self.request_count += 1
        token = self._generate_jwt_token()
        
        headers = {
            'Authorization': f'Ghost {token}',
            'Content-Type': 'application/json',
            'Accept-Version': 'v6.0',
            'User-Agent': 'Ghost-Publisher-Adapter/1.0'
        }
        
        url = f"{self.base_url}{endpoint}"
        
        self.logger.debug(f"Ghost API {method} {endpoint}")
        
        try:
            response = requests.request(
                method=method.upper(),
                url=url,
                headers=headers,
                json=data,
                timeout=30
            )
            
            # Handle different error types
            if response.status_code >= 400:
                self.error_count += 1
                error_data = {}
                
                try:
                    error_data = response.json()
                except:
                    error_data = {"message": response.text}
                
                # Enhanced error messages
                if response.status_code == 429:
                    retry_after = response.headers.get('Retry-After', '60')
                    raise GhostAPIError(
                        f"Rate limit exceeded. Retry after {retry_after} seconds",
                        response.status_code,
                        error_data
                    )
                elif response.status_code == 422:
                    validation_errors = error_data.get('errors', [])
                    error_msg = "Validation failed: " + "; ".join([
                        f"{err.get('property', 'field')}: {err.get('message', 'invalid')}"
                        for err in validation_errors
                    ])
                    raise GhostAPIError(error_msg, response.status_code, error_data)
                else:
                    error_msg = error_data.get('message', f"HTTP {response.status_code}")
                    raise GhostAPIError(error_msg, response.status_code, error_data)
            
            return response.json() if response.content else {}
            
        except requests.exceptions.Timeout:
            self.error_count += 1
            raise GhostAPIError("Request timeout - Ghost API not responding")
        except requests.exceptions.ConnectionError:
            self.error_count += 1
            raise GhostAPIError("Connection error - Cannot reach Ghost API")
        except requests.exceptions.RequestException as e:
            self.error_count += 1
            raise GhostAPIError(f"Request failed: {str(e)}")

    def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status"""
        try:
            start_time = time.time()
            
            # Test connection
            site_result = self._make_request('GET', '/site/')
            
            # Test post access
            posts_result = self._make_request('GET', '/posts/?limit=1')
            
            response_time = time.time() - start_time
            
            return {
                'status': 'healthy',
                'response_time_ms': round(response_time * 1000, 2),
                'ghost_version': site_result.get('site', {}).get('version'),
                'site_title': site_result.get('site', {}).get('title'),
                'posts_accessible': True,
                'request_count': self.request_count,
                'error_count': self.error_count,
                'error_rate': round(self.error_count / max(self.request_count, 1) * 100, 2),
                'last_check': datetime.utcnow().isoformat() + 'Z'
            }
            
        except GhostAPIError as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'error_category': e.error_category,
                'status_code': e.status_code,
                'request_count': self.request_count,
                'error_count': self.error_count,
                'last_check': datetime.utcnow().isoformat() + 'Z'
            }
```

**2. Monitoring endpoints:**
```python
# Aktualizacja main.py
import logging
from datetime import datetime, timedelta

# Setup structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global stats
app_stats = {
    'requests_total': 0,
    'requests_success': 0,
    'requests_error': 0,
    'last_error': None,
    'start_time': datetime.utcnow()
}

@app.middleware("http")
async def stats_middleware(request, call_next):
    """Track request statistics"""
    app_stats['requests_total'] += 1
    start_time = time.time()
    
    try:
        response = await call_next(request)
        
        if response.status_code < 400:
            app_stats['requests_success'] += 1
        else:
            app_stats['requests_error'] += 1
            
        return response
        
    except Exception as e:
        app_stats['requests_error'] += 1
        app_stats['last_error'] = {
            'message': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }
        raise

@app.get("/health")
async def health():
    """Enhanced health check with Ghost API status"""
    try:
        client = get_ghost_client()
        
        if not client:
            return {
                "status": "degraded",
                "ghost_configured": False,
                "message": "Ghost API not configured"
            }
        
        # Get Ghost health status
        ghost_health = client.get_health_status()
        
        # App health
        uptime = datetime.utcnow() - app_stats['start_time']
        error_rate = app_stats['requests_error'] / max(app_stats['requests_total'], 1) * 100
        
        overall_status = "healthy"
        if ghost_health['status'] != 'healthy':
            overall_status = "degraded" 
        elif error_rate > 10:  # More than 10% error rate
            overall_status = "degraded"
        
        return {
            "status": overall_status,
            "uptime_seconds": int(uptime.total_seconds()),
            "app_stats": app_stats,
            "error_rate_percent": round(error_rate, 2),
            "ghost_health": ghost_health,
            "timestamp": datetime.utcnow().isoformat() + 'Z'
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat() + 'Z'
        }

@app.get("/metrics")
async def metrics():
    """Prometheus-style metrics"""
    client = get_ghost_client()
    ghost_health = client.get_health_status() if client else {"status": "unconfigured"}
    
    uptime = datetime.utcnow() - app_stats['start_time']
    
    metrics_data = {
        "ghost_adapter_uptime_seconds": int(uptime.total_seconds()),
        "ghost_adapter_requests_total": app_stats['requests_total'],
        "ghost_adapter_requests_success_total": app_stats['requests_success'],
        "ghost_adapter_requests_error_total": app_stats['requests_error'],
        "ghost_api_response_time_ms": ghost_health.get('response_time_ms', 0),
        "ghost_api_status": 1 if ghost_health['status'] == 'healthy' else 0,
        "ghost_api_requests_total": ghost_health.get('request_count', 0),
        "ghost_api_errors_total": ghost_health.get('error_count', 0)
    }
    
    return metrics_data

# Enhanced error handling for all endpoints
@app.exception_handler(GhostAPIError)
async def ghost_api_exception_handler(request, exc: GhostAPIError):
    """Global Ghost API error handler"""
    
    logger.error(f"Ghost API Error: {exc.error_category} - {exc.message}")
    
    status_code_map = {
        "AUTHENTICATION_ERROR": 401,
        "PERMISSION_ERROR": 403,
        "NOT_FOUND": 404,
        "VALIDATION_ERROR": 400,
        "RATE_LIMIT_EXCEEDED": 429,
        "UNPROCESSABLE_ENTITY": 422
    }
    
    http_status = status_code_map.get(exc.error_category, exc.status_code or 500)
    
    return JSONResponse(
        status_code=http_status,
        content={
            "error": True,
            "category": exc.error_category,
            "message": exc.message,
            "details": exc.response_data,
            "timestamp": datetime.utcnow().isoformat() + 'Z'
        }
    )
```

#### **Test Case:**
```bash
#!/bin/bash
# scripts/test-ghost-monitoring.sh

echo "🧪 TESTOWANIE GHOST MONITORING"
echo "==============================="

BASE_URL="http://localhost:8084"

# Test 1: Health endpoint
echo "Test 1: Health check endpoint"
curl -s "$BASE_URL/health" | jq '.status' | grep -q -E "(healthy|degraded)" && echo " ✅ PASS" || echo " ❌ FAIL"

# Test 2: Metrics endpoint
echo "Test 2: Metrics endpoint"
curl -s "$BASE_URL/metrics" | jq '.ghost_adapter_uptime_seconds' | grep -q -E "[0-9]+" && echo " ✅ PASS" || echo " ❌ FAIL"

# Test 3: Error handling - invalid request
echo "Test 3: Error handling test"
curl -s -X POST "$BASE_URL/publish" \
  -H "Content-Type: application/json" \
  -d '{"invalid": "data"}' \
  | jq '.error' | grep -q "true" && echo " ✅ PASS" || echo " ❌ FAIL"

# Test 4: Ghost API health
echo "Test 4: Ghost API connectivity"
curl -s "$BASE_URL/health" | jq '.ghost_health.status' | grep -q -E "(healthy|unhealthy)" && echo " ✅ PASS" || echo " ❌ FAIL"

echo "🎯 Ghost monitoring ready!"
```

#### **Walidacja ukończenia:**
- [ ] Comprehensive error handling działa
- [ ] Health monitoring pokazuje Ghost status
- [ ] Metrics endpoint zwraca statystyki
- [ ] Structured logging działa

---

## 📊 **PODSUMOWANIE IMPLEMENTACJI**

### **Ukończone zadania:**
- **Task 4.1**: ✅ Szkielet Ghost Adapter (FastAPI, Docker, healthcheck)
- **Task 4.2**: ✅ JWT Authentication i Ghost API Client (**COMPLETED 2025-08-07**)
- **Task 4.3**: ✅ Endpoint POST /publish (HTML + Lexical content) (**COMPLETED 2025-08-07**)
- **Task 4.4**: ✅ Harmonogram publikacji i status management (**COMPLETED 2025-08-07**)
- **Task 4.5**: ✅ Image upload i media management
- **Task 4.6**: ✅ Error handling i monitoring

### **Kluczowe funkcje:**
- **Content Management**: Obsługa HTML i Lexical content format
- **Publication Control**: Draft, published, scheduled status
- **Media Handling**: Automatic image upload i processing
- **Error Handling**: Comprehensive error categories i retry logic
- **Monitoring**: Health checks, metrics, structured logging
- **Authentication**: Secure JWT token generation dla Ghost Admin API

### **Endpointy:**
- `POST /publish` - Publikacja postów
- `PUT /posts/{id}/schedule` - Harmonogram publikacji
- `PUT /posts/{id}/publish` - Natychmiastowa publikacja
- `GET /posts/{id}/preview` - Preview posta
- `GET /posts` - Lista postów z filterami
- `POST /upload-image` - Upload obrazów
- `GET /health` - Health check z Ghost API status
- `GET /metrics` - Metrics dla monitoring

### **Wymagane zmienne środowiskowe:**
```bash
GHOST_API_URL=https://your-ghost-site.com
GHOST_API_KEY=your_admin_api_key_here
```

### **Docker deployment:**
```bash
# Uruchomienie Ghost Adapter
make build-ghost
make up-ghost

# Testy
make test-ghost-full
```

### **Następne kroki:**
System jest gotowy do integracji z AI Writing Flow i może obsługiwać pełny workflow publikacji treści w Ghost CMS, włączając w to zarządzanie mediami, harmonogram publikacji i monitoring statusu API.