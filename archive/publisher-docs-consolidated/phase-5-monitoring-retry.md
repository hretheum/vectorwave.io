# Faza 5: Monitoring, retry, alerting

## Cel fazy
Zapewnienie monitoringu, automatycznego retry oraz alertowania dla całego systemu publikacji.

---

### Zadanie 5.1: Eksportowanie metryk Prometheus z każdego serwisu
- **Wartość**: Każdy serwis udostępnia endpoint `/metrics` zgodny z Prometheus.
- **Test**: `curl http://localhost:<port>/metrics` zwraca metryki Prometheus.

### Zadanie 5.1.1: Implementacja Prometheus Client w Orchestrator
- **Wartość**: Orchestrator eksportuje metryki: publikacji total, błędów, queue depth, response time.
- **Test**: `/metrics` endpoint zawiera wszystkie kluczowe metryki z proper labels.

### Zadanie 5.1.2: Prometheus Metrics w Platform Adapters
- **Wartość**: Każdy adapter eksportuje platform-specific metrics (rate limits, session status).
- **Test**: Adapter metrics endpoint zawiera platform health i performance data.

### Zadanie 5.2: Dashboard Grafana z kluczowymi metrykami
- **Wartość**: Dashboard pokazuje liczbę publikacji, błędów, retry, czas odpowiedzi.
- **Test**: Po wdrożeniu dashboardu, metryki są widoczne w Grafanie.

### Zadanie 5.2.1: Grafana Dashboard Configuration
- **Wartość**: Pre-configured dashboard z panels dla każdej platformy i kluczowych metryk.
- **Test**: Dashboard importuje się poprawnie i pokazuje real-time data z Prometheus.

### Zadanie 5.2.2: Grafana Alerting Rules Setup
- **Wartość**: Alerty w Grafanie dla high error rates, queue overload, platform downtime.
- **Test**: Po symulacji problemu, alert jest triggered w Grafana notifications.

### Zadanie 5.3: Retry zadań po błędach tymczasowych
- **Wartość**: System automatycznie ponawia zadania po błędach sieciowych, rate limitach itp.
- **Test**: Po zasymulowaniu błędu, zadanie jest ponawiane i kończy się sukcesem.

### Zadanie 5.3.1: Exponential Backoff Implementation
- **Wartość**: Retry mechanism z exponential backoff dla different error types.
- **Test**: Retry intervals zwiększają się exponentially: 1s, 2s, 4s, 8s, 16s.

### Zadanie 5.3.2: Error-Specific Retry Logic
- **Wartość**: Different retry strategies dla rate limits, network errors, server errors.
- **Test**: Rate limit errors mają longer delays, network errors mają immediate retry.

### Zadanie 5.3.3: Maximum Retry Limits Configuration
- **Wartość**: Configurable max retry counts per error type z circuit breaker pattern.
- **Test**: Po przekroczeniu max retries, job jest moved do failed queue.

### Zadanie 5.4: Alerty (telegram/discord/webhook) przy krytycznych błędach ✅ **COMPLETED** (2025-08-07)
- **Wartość**: System wysyła alerty o krytycznych błędach (np. platforma niedostępna, 3x retry fail).
- **Test**: Po zasymulowaniu krytycznego błędu, alert pojawia się na telegram/discord/webhook.
- **Implementacja**: AlertManager class z obsługą 3 kanałów, 7 typów alertów, rate limiting
- **Status**: PRODUCTION READY - wszystkie alert types zaimplementowane i przetestowane

### Zadanie 5.5: Monitoring statusu adapterów i kolejki
- **Wartość**: System monitoruje status adapterów i głębokość kolejki, alertuje o przeciążeniu.
- **Test**: Po przeciążeniu kolejki, alert pojawia się w systemie monitoringu.