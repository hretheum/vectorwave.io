# Faza 7: Integracja z LinkedIn Module (Production Ready)

## Cel fazy
Integracja istniejącego, production-ready LinkedIn Module z Multi-Channel Publisher przez utworzenie Python wrapper dla Node.js CLI.

---

### Zadanie 7.1: Implementacja LinkedInModuleWrapper klasy
- **Wartość**: Python wrapper dla existing LinkedIn Node.js module z CLI execution.
- **Test**: Wrapper poprawnie wykonuje `node scripts/linkedin-cli.js --help` i parsuje output.

### Zadanie 7.2: CLI Command Execution i Output Parsing
- **Wartość**: Wrapper wykonuje LinkedIn CLI commands i parsuje success/error responses.
- **Test**: Po wykonaniu `publish`, wrapper zwraca structured response z success/error status.

### Zadanie 7.3: Session Validation Integration
- **Wartość**: Wrapper sprawdza status LinkedIn session przed publikacją.
- **Test**: `validate_session()` zwraca poprawny status dla aktywnych i wygasłych sesji.

### Zadanie 7.4: Error Handling dla LinkedIn-Specific Issues
- **Wartość**: Wrapper kategoryzuje błędy LinkedIn (selector changes, session expired, rate limits).
- **Test**: Different error types są poprawnie rozpoznawane i mapped do error codes.

### Zadanie 7.5: Content Adaptation dla LinkedIn Format
- **Wartość**: Wrapper adaptuje content z AI Writing Flow do LinkedIn requirements (hashtags, mentions, PDF).
- **Test**: Content jest poprawnie formatowany zgodnie z LinkedIn best practices.

### Zadanie 7.6: Scheduled Publication Support
- **Wartość**: Wrapper obsługuje scheduled posts przez LinkedIn CLI scheduling mechanism.
- **Test**: Scheduled post jest poprawnie utworzony i widoczny w LinkedIn scheduler.

### Zadanie 7.7: Media Upload Integration
- **Wartość**: Wrapper obsługuje PDF i image uploads przez LinkedIn CLI.
- **Test**: Media files są poprawnie uploading i attachowane do posts.

### Zadanie 7.8: Integration Testing z Orchestrator
- **Wartość**: LinkedInModuleWrapper jest zintegrowany z Orchestrator i Redis queue.
- **Test**: Publikacja przez Orchestrator używa LinkedIn wrapper i kończy się sukcesem.