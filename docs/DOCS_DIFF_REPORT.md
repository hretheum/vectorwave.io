# Raport rozbieżności vs `target-version`

Data: 2025-08-13
Źródło: docs/DOCS_INVENTORY.md, katalog `target-version/` oraz bieżący kod usług.

Uwaga operacyjna: poniższe punkty zawierają rekomendację i priorytet (P0–P2).

1) Gamma.app service – stan vs plan
- Różnica: W `target-version/ANALYTICS_SERVICE_ARCHITECTURE.md` i roadmapie zakładany jest działający serwis Gamma; w repo `kolegium/gamma-ppt-generator/README.md` wskazuje szkielet bez pełnej implementacji `/generate`.
- Rekomendacja: Dostarczyć MVP: `/health`, `/generate` (PPTX/PDF) oraz obraz docker. Dodać testy kontraktowe.
- Priorytet: P1
- Referencje: kolegium/gamma-ppt-generator/README.md; target-version/VECTOR_WAVE_MIGRATION_ROADMAP.md

2) Publisher ↔ Gamma toggle + fallback
- Różnica: W planie docelowym Publisher posiada przełącznik i fallback na Presenton. W kodzie brak konfiguracji `GAMMA_ENABLED` i klienta Gamma w ścieżkach publikacji.
- Rekomendacja: Wprowadzić flagę środowiskową i prosty klient HTTP; scenariusze happy-path + fallback.
- Priorytet: P1
- Referencje: publisher/README.md; target-version/VECTOR_WAVE_MIGRATION_ROADMAP.md

3) Harvester – uproszczona architektura vs plan
- Różnica: W `target-version` sugerowano bardziej rozbudowane przepływy; realnie Harvester nie używa CrewAI, posiada selektywny triage i promuje do TM.
- Rekomendacja: Zaktualizować dokumentację Harvester, podkreślić brak agentów, dodać aktualne endpointy i przykłady.
- Priorytet: P0
- Referencje: harvester/README.md, harvester/ARCHITECTURE.md; target-version/REVISED_HARVESTER_PLAN.md

4) Topic Manager – brak scraperów vs historyczne wzmianki
- Różnica: W starszych dokumentach pojawiają się wzmianki o scraperach TM; w implementacji ich nie ma (integracja z Harvester i ChromaDB).
- Rekomendacja: Usunąć/archiwizować stare odniesienia; doprecyzować novelty-check/suggestion.
- Priorytet: P0
- Referencje: topic-manager/README.md; target-version/README.md

5) Analytics Service – status
- Różnica: W `target-version/ANALYTICS_SERVICE_ARCHITECTURE.md` opisany jest serwis; w repo brak pełnego wdrożenia (placeholdery/plan, README w kolegium/analytics-service).
- Rekomendacja: Zachować jako P2 backlog z minimalnym `/health` i szkicem `/metrics`.
- Priorytet: P2
- Referencje: kolegium/analytics-service/README.md; target-version/ANALYTICS_SERVICE_ARCHITECTURE.md

6) Orchestrator – brak odniesień do Gamma w publikacji
- Różnica: Plan przewiduje integrację Gamma przez orchestrator/publisher; w kontraktach brak tej ścieżki.
- Rekomendacja: Opisać planowane API lub potwierdzić, że integracja pozostaje w Publisher.
- Priorytet: P1
- Referencje: crewai-orchestrator/README.md; publisher/API_SPECIFICATION.md

7) Dokumentacja „Status projektu” vs kod
- Różnica: target-version/STATUS.md deklaruje wyższy poziom kompletności (np. monitoring enterprise) niż obecny kod niektórych modułów (Analytics, Gamma).
- Rekomendacja: Zaktualizować STATUS.md pod faktyczny stan.
- Priorytet: P0
- Referencje: target-version/STATUS.md

8) Kanban / Vikunja – kolumny i etykiety vs workflow
- Różnica: W `target-version/KANBAN.md` brak szczegółów o etykietach domenowych/epikach; w praktyce wymagane są EPIC + domenowe.
- Rekomendacja: Dodać sekcję o etykietach i relacjach; dołączyć link do PROJECT_CONTEXT.
- Priorytet: P1
- Referencje: target-version/KANBAN.md; PROJECT_CONTEXT.md

9) Comments/Labels API – wersja instancji
- Różnica: Instancja Vikunja nie obsługuje wprost endpointu komentarzy i części operacji etykiet przez surowe API, mimo wzmianki w publicznej dokumentacji.
- Rekomendacja: Dla operacji etykiet/komentarzy używać MCP lub UI; dopisać w README sekcję „Known differences vs upstream API”.
- Priorytet: P2
- Referencje: PROJECT_CONTEXT.md (sekcja MCP); docs/DOCS_INVENTORY.md

10) Knowledge Base – zgodność z planami
- Obserwacja: KB jest rozbudowane i zgodne z planem, ale część dokumentów w target-version dubluje treści z KB.
- Rekomendacja: Konsolidacja – wskazać jeden źródłowy dokument i archiwizować duplikaty.
- Priorytet: P1
- Referencje: knowledge-base/README.md; docs/DOCS_INVENTORY.md

11) Port allocation – brak krzyżowej referencji
- Różnica: W dokumentach usług nie zawsze małe README wskazuje na centralny rejestr portów.
- Rekomendacja: Dodać link do docs/integration/PORT_ALLOCATION.md z każdego README.
- Priorytet: P2
- Referencje: docs/integration/PORT_ALLOCATION.md; docs/README.md

12) PROJECT_CONTEXT a stan Kanbana
- Różnica: Brak sekcji MCP/Kanban w starszej części PROJECT_CONTEXT; dopisano nową sekcję (2025‑08‑13), ale należy zsynchronizować z KANBAN.
- Rekomendacja: Utrzymywać pojedyncze źródło prawdy i cyklicznie odświeżać.
- Priorytet: P1
- Referencje: PROJECT_CONTEXT.md; target-version/KANBAN.md

---

Wskazówki wykonawcze:
- Przed edycjami: korzystaj z docs/DOCS_INVENTORY.md jako spisu treści – łatwiej zidentyfikować pliki do zmiany i ich lokalizację.
- Po PR: dołącz zrzuty ekranu/wyjścia `curl` dla weryfikacji.
