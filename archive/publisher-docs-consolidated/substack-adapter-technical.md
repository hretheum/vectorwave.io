# Substack Adapter - Dokumentacja Techniczna

## Przegląd

Substack Adapter implementuje wzorzec "ondemand session initializer" dla automatyzacji publikacji na platformie Substack. System składa się z dwóch głównych komponentów:

1. **CLI do zarządzania sesjami** (`scripts/substack-cli.js`)
2. **Adapter do automatycznej publikacji** (`src/adapters/substack-adapter.js`)

## Architektura

### 1. Session Management Flow

```
Użytkownik → CLI (session create) → Browser (ręczne logowanie) → Session Storage → Adapter (automatyczna publikacja)
```

### 2. Komponenty

#### CLI (`scripts/substack-cli.js`)
- **Biblioteki**: `yargs`, `dotenv`, `@browserbasehq/stagehand`
- **Komendy**:
  - `session create --account <nazwa>` - Inicjalizacja nowej sesji
  - `session validate --account <nazwa>` - Walidacja istniejącej sesji

#### Adapter (`src/adapters/substack-adapter.js`)
- **Klasa**: `SubstackAdapter`
- **Metody główne**:
  - `initialize(accountName)` - Wczytuje zapisaną sesję
  - `startBrowser()` - Uruchamia przeglądarkę z przywróconą sesją
  - `publishPost(postData)` - Publikuje post na Substack

### 3. Format Danych Sesji

Sesje zapisywane w `data/sessions/{account}_substack.json`:

```json
{
  "accountName": "personal",
  "createdAt": "2025-08-06T19:40:32.237Z",
  "validUntil": "2025-09-05T19:40:32.237Z",
  "platform": "substack",
  "cookies": [...],
  "localStorage": {...},
  "sessionStorage": {...},
  "userAgent": "...",
  "url": "https://tojamarek.substack.com/"
}
```

## Implementacja

### Session Creation (CLI)

1. **Browser Launch**: Uruchomienie lokalnego Chromium z Stagehand
2. **Manual Login**: Użytkownik loguje się ręcznie w przeglądarce
3. **Context Extraction**: Automatyczne wyciągnięcie:
   - Cookies (wszystkie domeny .substack.com)
   - localStorage content
   - sessionStorage content
   - User Agent
   - Current URL
4. **Persistence**: Zapis do pliku JSON z 30-dniowym TTL

### Session Validation

```javascript
// Walidacja obejmuje:
1. Sprawdzenie daty wygaśnięcia (validUntil)
2. Próba przywrócenia sesji w headless browser
3. Navigacja do Substack + przywrócenie kontekstu
4. Weryfikacja loginów poprzez wyszukiwanie elementów UI
```

### Automated Publishing

#### Flow publikacji:
1. **Session Restore**: Przywrócenie cookies, localStorage, sessionStorage
2. **Navigation**: Przejście do `https://{subdomain}.substack.com/publish/post`
3. **Form Filling**: Wypełnienie tytułu i treści posta
4. **Continue Click**: Przejście do drugiego kroku (settings)
5. **Tags Handling**: Próba dodania tagów (pomijana przy anti-bot protection)
6. **Draft/Publish**: Draft = nie kliknięcie "Send to everyone now"

#### Obsługiwane parametry:
```javascript
const postData = {
  title: "Tytuł posta",
  content: "Treść posta (markdown/html)",
  draft: true,                    // true = draft, false = publish
  tags: ["tag1", "tag2"],         // opcjonalne (może być pomijane)
  scheduledTime: "ISO string"     // opcjonalny scheduling
};
```

## Konfiguracja

### Wymagane zmienne środowiskowe (.env):
```bash
SUBSTACK_SUBDOMAIN=tojamarek        # Subdomena newslettera
OPENAI_API_KEY=sk-...               # Klucz OpenAI (wymagany przez Stagehand)
BROWSERBASE_API_KEY=bb_live_...     # Opcjonalny (jeśli używasz Browserbase)
BROWSERBASE_PROJECT_ID=...          # Opcjonalny
```

### Dependencies:
- `@browserbasehq/stagehand` - Browser automation
- `yargs` - CLI argument parsing  
- `dotenv` - Environment variables
- `fs/promises` - File operations

## Obsługa błędów

### Anti-Bot Protection
- **Problem**: Substack ukrywa pole tagów przed botami (element z zerowymi wymiarami)
- **Rozwiązanie**: Wykrywanie via `getBoundingClientRect()` i eleganckie pomijanie
- **Fallback**: Publikacja kontynuowana bez tagów

### Session Expiry
- **Wykrywanie**: Sprawdzenie `validUntil` + test logowania
- **Handling**: Informowanie użytkownika o potrzebie nowej sesji
- **Recovery**: Automatyczne skierowanie do `session create`

### Network/Browser Issues
- **Timeouts**: Konfigurowane timeout dla wszystkich operacji Playwright
- **Retry Logic**: Wielokrotne próby dla kritycznych operacji
- **Graceful Degradation**: Kontynuacja przy drobnych błędach

## Bezpieczeństwo

### Session Storage
- **Lokalizacja**: `data/sessions/` (w .gitignore)
- **Format**: JSON z czułymi danymi (cookies, storage)
- **TTL**: 30 dni automatycznego wygaśnięcia
- **Permissions**: Tylko lokalny dostęp

### Anti-Detection
- **User Agent**: Standardowy Chrome UA
- **Behavioral Patterns**: Random delays między akcjami
- **Session Reuse**: Wykorzystanie prawdziwych sesji użytkownika

## Testowanie

### Test Manual:
```bash
# 1. Inicjalizacja sesji
node publisher/scripts/substack-cli.js session create --account test

# 2. Walidacja
node publisher/scripts/substack-cli.js session validate --account test

# 3. Test publikacji
node publisher/scripts/test-substack-adapter.js
```

### Expectedresults:
- ✅ Successful session creation with manual login
- ✅ Session validation passes  
- ✅ Automated post creation as draft
- ⚠️ Tags skipped due to anti-bot protection (expected)

## Limity i ograniczenia

1. **Anti-Bot Protection**: Tagi wymagają ręcznego dodania
2. **Single Session**: Jedna aktywna sesja per account
3. **Manual Login**: Wymagane ręczne logowanie przy inicjalizacji
4. **Subdomain Dependency**: Wymaga konfiguracji subdomeny w .env
5. **Browser Dependency**: Wymaga lokalnego Chrome/Chromium

## Roadmap

### Zadania do realizacji:
- **1.8**: Session rotation i automatyczne odnawianie
- **Phase 2**: Twitter adapter z podobnym mechanizmem
- **Phase 3**: Beehiiv integration
- **Phase 4**: Unified orchestrator API

### Potencjalne ulepszenia:
- Obejście anti-bot protection dla tagów
- Support dla scheduled posts
- Bulk publishing capabilities
- Session sharing między instancjami