# Quick Start: Styleguide + Kolegium + TypeFully Integration

## 🚀 TL;DR
Integracja Vector Wave styleguide z AI Kolegium Redakcyjne i publikacją na X przez TypeFully.

## 📋 Prerequisites
- AI Kolegium Redakcyjne (działające)
- TypeFully API key
- Folder z content (`/content/ready/`)
- Python 3.11+

## 🏗️ Architektura

```
Folder → Styleguide Processor → AI Kolegium → Validator → TypeFully → X
```

## ⚡ MVP w 3 krokach

### Krok 1: Styleguide Parser (15 min)

```python
# styleguide_parser.py
STYLEGUIDE_RULES = {
    "forbidden_phrases": [
        "in today's fast-paced world",
        "leverage", "seamless integration", 
        "revolutionary", "game-changing",
        "cutting-edge", "delve into"
    ],
    "required_elements": {
        "data_points_min": 3,
        "sources_max_age_months": 6,
        "completion_rate_target": 0.70
    },
    "audience_weights": {
        "technical_founder": 0.35,
        "senior_engineer": 0.30,
        "decision_maker": 0.25,
        "skeptical_learner": 0.10
    }
}
```

### Krok 2: Kolegium Context Update (20 min)

Dodaj do `src/ai_kolegium_redakcyjne/main.py`:

```python
def run():
    inputs = {
        'categories': ['AI', 'Technology', 'Digital Culture', 'Startups'],
        'current_date': datetime.now().strftime("%Y-%m-%d"),
        'max_topics': 10,
        'controversy_threshold': 0.7,
        # NOWE: Styleguide context
        'styleguide': {
            'mission': "Decode technology's real impact through unflinching analysis",
            'forbidden_phrases': STYLEGUIDE_RULES['forbidden_phrases'],
            'audience_focus': 'technical_founder',  # Primary persona
            'quality_bar': STYLEGUIDE_RULES['required_elements']
        }
    }
```

### Krok 3: TypeFully Publisher (25 min)

```python
# typefully_publisher.py
import httpx
from typing import List, Dict

class TypeFullyPublisher:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.typefully.com/v1"
    
    def create_thread(self, tweets: List[str], schedule_time=None):
        """Tworzy thread na X"""
        payload = {
            "content": tweets,
            "schedule": schedule_time,
            "platforms": ["twitter"]
        }
        
        response = httpx.post(
            f"{self.base_url}/drafts",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json=payload
        )
        return response.json()
```

## 📁 Struktura folderów

```
vector-wave/
├── content/
│   ├── raw/           # Pomysły, notatki
│   ├── ready/         # Do przetworzenia przez kolegium
│   └── published/     # Archiwum z metrykami
└── kolegium/
    └── ai_kolegium_redakcyjne/
        ├── styleguide_parser.py
        ├── content_validator.py
        └── typefully_publisher.py
```

## 🔄 Workflow

### 1. Folder Watcher (opcjonalny dla MVP)
```bash
# Ręczne wywołanie
python process_content.py /content/ready/new-article.md
```

### 2. Validation Pipeline
```python
# content_validator.py
def validate_content(text: str, rules: dict) -> dict:
    """Waliduje content względem styleguide"""
    
    issues = []
    score = 1.0
    
    # Check forbidden phrases
    for phrase in rules['forbidden_phrases']:
        if phrase.lower() in text.lower():
            issues.append(f"Forbidden phrase: '{phrase}'")
            score -= 0.1
    
    # Check data density
    data_points = len(re.findall(r'\d+\.?\d*[%$]?', text))
    if data_points < rules['required_elements']['data_points_min']:
        issues.append(f"Too few data points: {data_points}")
        score -= 0.2
    
    return {
        'score': max(0, score),
        'issues': issues,
        'passed': score >= 0.7
    }
```

### 3. Integration Script
```python
# process_content.py
async def process_content_pipeline(file_path: str):
    """Full pipeline: file → kolegium → validation → TypeFully"""
    
    # 1. Read content
    with open(file_path, 'r') as f:
        content = f.read()
    
    # 2. Process with kolegium (with styleguide context)
    kolegium_result = run_kolegium_with_context(content)
    
    # 3. Validate output
    validation = validate_content(
        kolegium_result['processed_content'],
        STYLEGUIDE_RULES
    )
    
    if validation['passed']:
        # 4. Create Twitter thread
        thread = create_twitter_thread(kolegium_result)
        
        # 5. Publish via TypeFully
        publisher = TypeFullyPublisher(os.getenv('TYPEFULLY_API_KEY'))
        result = publisher.create_thread(thread)
        
        print(f"✅ Published: {result['url']}")
    else:
        print(f"❌ Validation failed: {validation['issues']}")
```

## 🎯 Przykład Twitter Thread

```python
def create_twitter_thread(content: dict) -> List[str]:
    """Konwertuje kolegium output na Twitter thread"""
    
    tweets = []
    
    # Tweet 1: Hook (Level 1 - assume smart but not specialized)
    hook = f"{content['title']}\n\nHere's what {content['data_point_1']} tells us about {content['main_topic']}:"
    tweets.append(hook)
    
    # Tweet 2-3: Main insights with data
    for insight in content['key_insights'][:2]:
        tweet = f"{insight['point']}\n\nData: {insight['evidence']}"
        tweets.append(tweet)
    
    # Tweet 4: Value for reader
    value = f"Why this matters for {content['target_audience']}:\n{content['reader_value']}"
    tweets.append(value)
    
    # Tweet 5: CTA
    cta = "What's your experience with this? Let me know below 👇"
    tweets.append(cta)
    
    return tweets
```

## 📊 Metryki

```python
# metrics_tracker.py
def track_performance(post_id: str, metrics: dict):
    """Zapisuje metryki dla feedback loop"""
    
    data = {
        'post_id': post_id,
        'timestamp': datetime.now(),
        'style_compliance': metrics['validation_score'],
        'engagement': {
            'likes': 0,  # Update from TypeFully API
            'retweets': 0,
            'replies': 0
        },
        'audience_fit': metrics['audience_match'],
        'issues_caught': metrics['validation_issues']
    }
    
    # Save to metrics store
    save_metrics(data)
```

## 🚦 Uruchomienie

### 1. Environment setup
```bash
export TYPEFULLY_API_KEY="your-key"
export OPENAI_API_KEY="your-key"
```

### 2. Install dependencies
```bash
pip install httpx pydantic crewai
```

### 3. Test run
```bash
# Pojedynczy plik
python process_content.py content/ready/test-article.md

# Batch processing
python process_content.py --folder content/ready/
```

## 🔧 Troubleshooting

### Problem: "Forbidden phrase found"
```python
# Dodaj do validator config
'replacements': {
    'leverage': 'use',
    'revolutionary': 'significant',
    'seamless': 'smooth'
}
```

### Problem: "Too few data points"
```python
# Zwiększ data extraction w kolegium
'require_sources': True,
'min_statistics': 3
```

### Problem: "TypeFully API error"
```python
# Dodaj retry logic
@retry(attempts=3, delay=2)
def publish_to_typefully(content):
    # ... publish logic
```

## 📈 Next Steps

1. **Automation**: Dodaj file watcher lub cron job
2. **Analytics**: Połącz z TypeFully analytics API
3. **Learning**: ML model na successful posts
4. **Scaling**: Queue system (Redis) dla batch processing

---

**Remember**: Start simple, measure everything, iterate based on data. Style compliance + engagement = success. 🚀