# Plan konsolidacji dokumentacji

Data: 2025-08-13
Źródła: docs/DOCS_INVENTORY.md, docs/DOCS_DIFF_REPORT.md, PROJECT_CONTEXT.md, katalog `target-version/`.

## Cele
- Jednoznaczna nawigacja (Start → Kontekst → Roadmapa → Per‑service).
- Pojedyncze źródło prawdy dla każdego tematu (koniec duplikatów).
- Minimalny czas onboardingu (≤ 30 min do uruchomienia stacka).
- Łatwy audyt zgodności (lint linków, spójność portów, health‑checki).

## Struktura docelowa (SPOF per temat)
- README.md (root) — skrót projektu i link do QUICK_START.
- QUICK_START.md — szybki start (docker compose, zdrowie usług, najczęstsze problemy).
- PROJECT_CONTEXT.md — kontekst, aktualny stan, MCP/Vikunja (Kanban) i zasady.
- ROADMAP.md — wysokopoziomowe kamienie milowe.
- docs/
  - README.md — indeks dokumentacji + zasady techniczne.
  - DEPENDENCIES_MAP.md
  - integration/PORT_ALLOCATION.md (rejestr portów; link zwrotny z per‑service README).
  - DOCS_INVENTORY.md (generowany, nieedytowalny ręcznie).
  - DOCS_DIFF_REPORT.md (raport rozbieżności z target‑version).
- per‑service: <module>/README.md (jednolity szablon)
  - Cel → Metryki sukcesu → Walidacja (komendy curl/pytest)
  - Architektura (skrócona) + link do szczegółów (ARCHITECTURE.md jeśli istnieje)
  - Konfiguracja (env, porty, zależności; link do PORT_ALLOCATION.md)
  - Health i testy dymne (przykłady)
  - FAQ/Troubleshooting

## Mapowanie obecnych dokumentów → docelowe miejsce
- Harvester: harvester/README.md, ARCHITECTURE.md, API_SPECIFICATIONS.md → pozostają; usunąć wzmianki o CrewAI; dodać sekcję „Metryki/Walidacja/Porty”.
- Topic Manager: topic-manager/README.md → doprecyzować novelty‑check/suggestion, brak scraperów.
- Publisher: publisher/README.md, API_SPECIFICATION.md → dodać sekcję „Gamma toggle/fallback (plan)”.
- Analytics: kolegium/analytics-service/README.md → status + /health (szkic), odwołanie do target-version/ANALYTICS_SERVICE_ARCHITECTURE.md.
- Gamma: kolegium/gamma-ppt-generator/README.md → MVP: /health, /generate (plan), integracja w Publisher.
- Orchestrator/ES/TM/Harvester — każdy README: dodać link do PORT_ALLOCATION.md.

Szczegóły i pełna lista plików: docs/DOCS_INVENTORY.md.

## Zasady archiwizacji
- Pliki nieaktualne przenosić do archive/<ścieżka‑oryginalna> z nagłówkiem „Archived (data, powód)”.
- Zostawiać stub w miejscu źródłowym tylko jeśli często linkowany (link do wersji w archive/).
- Każdy PR z archiwizacją uruchamia sprawdzanie martwych linków.

## Nawigacja (UI)
- README (root) → QUICK_START → PROJECT_CONTEXT → ROADMAP → moduły.
- W per‑service README stałe bloki (Cel/Metryki/Walidacja/Porty/Health/FAQ).

## Własność
- Harvester — owner: data
- Topic Manager — owner: platform
- Publisher — owner: publishing
- Orchestrator/AI flows — owner: kolegium
- Analytics — owner: analytics
- Gamma — owner: publishing

## Kroki migracji (checklista PR‑owa)
1. Utwórz/uzupełnij QUICK_START.md (lub zaktualizuj sekcję w README root).
2. Zaktualizuj per‑service README zgodnie z szablonem (Cel/Metryki/Walidacja/Porty/Health).
3. Dodaj link zwrotny do docs/integration/PORT_ALLOCATION.md.
4. Zarchiwizuj duplikaty i stare dokumenty (archive/…).
5. Uruchom lint linków i health‑checki.
6. Zaktualizuj ROADMAP.md/PROJECT_CONTEXT.md jeśli dotyczy.

## Walidacja
- Link checker dla całego repo (markdown‑link‑check / lychee).
- `curl` do health endpointów wszystkich usług (wg QUICK_START).
- Sprawdzenie braku odniesień do archiwizowanych plików (grep w repo).

## Harmonogram
- Tydzień 1: Harvester/Topic Manager/Publisher.
- Tydzień 2: Orchestrator/Editorial Service/Analytics.
- Tydzień 3: Gamma (MVP) + konsolidacja i porządki.

## Odniesienia
- docs/DOCS_INVENTORY.md — spis wszystkich dokumentów.
- docs/DOCS_DIFF_REPORT.md — lista różnic i priorytety zmian.
- docs/integration/PORT_ALLOCATION.md — rejestr portów.
- PROJECT_CONTEXT.md — stan projektu i MCP/Kanban.
