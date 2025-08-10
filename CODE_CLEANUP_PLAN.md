# Plan Refaktoryzacji i Czyszczenia Kodu Legacy

## 1. Wprowadzenie i Cele

Celem tego planu jest systematyczne uporządkowanie bazy kodu projektu Vector Wave poprzez archiwizację lub usunięcie przestarzałych skryptów, osieroconych modułów i kodu tymczasowego. Działania te mają na celu:
- **Zwiększenie czytelności:** Usunięcie nieużywanych plików, które zaciemniają obraz aktualnej architektury.
- **Redukcję długu technicznego:** Pozbycie się kodu, który nie jest już utrzymywany i nie pasuje do obecnych standardów.
- **Ułatwienie onboardingu:** Zapewnienie, że nowi deweloperzy i agenci AI skupiają się wyłącznie na relevantnym, produkcyjnym kodzie.
- **Zgodność z architekturą docelową:** Doprowadzenie struktury projektu do stanu, który w pełni odzwierciedla plany z folderu `target-version`.

## 2. Główne Zasady

1.  **Bezpieczeństwo przede wszystkim:** Żaden plik nie zostanie trwale usunięty. Wszystkie zidentyfikowane komponenty zostaną przeniesione do folderu `archive/`, co umożliwi ich ewentualne przywrócenie.
2.  **Nienaruszalność `target-version`:** Podobnie jak w przypadku dokumentacji, żadne pliki wewnątrz folderu `/target-version` nie będą modyfikowane.
3.  **Stopniowe działanie:** Plan jest podzielony na logiczne fazy, aby umożliwić kontrolę i weryfikację na każdym etapie.

---

## 3. Plan Działania

### Faza 1: Archiwizacja Skryptów Jednorazowych (Niskie Ryzyko)

**Cel:** Bezpieczne zarchiwizowanie skryptów, które były używane jednorazowo podczas migracji i nie są już potrzebne do działania aplikacji.

**Kroki:**

1.  **Utworzenie dedykowanego folderu w archiwum:**
    -   Zostanie utworzony folder `archive/legacy-scripts/`.

2.  **Przeniesienie skryptów migracyjnych:**
    -   Cała zawartość folderu `editorial-service/migration/` zostanie przeniesiona do `archive/legacy-scripts/editorial-service-migration/`.

3.  **Przeniesienie starych skryptów testowych i deweloperskich:**
    -   Następujące pliki zostaną przeniesione do `archive/legacy-scripts/`:
        -   `publisher/scripts/test-substack-adapter.js`
        -   `publisher/scripts/test-session-management.js`
        -   `kolegium/ai_kolegium_redakcyjne/test_local_content.py`
        -   `kolegium/ai_writing_flow/working_example.py`
        -   `kolegium/ai_writing_flow/final_working_example.py`
        -   `kolegium/ai_writing_flow/process_example.py`

### Faza 2: Archiwizacja Komponentów PoC (Niskie Ryzyko)

**Cel:** Usunięcie z głównego drzewa projektu uproszczonych wersji serwisów, które powstały na etapie Proof of Concept.

**Kroki:**

1.  **Przeniesienie uproszczonych wersji serwisu edytorskiego:**
    -   Następujące pliki z `editorial-service/` zostaną przeniesione do `archive/legacy-scripts/editorial-service-poc/`:
        -   `minimal_server.py`
        -   `simple_main.py`
        -   `simple_requirements.txt`

2.  **Przeniesienie osieroconego pliku `app.py`:**
    -   Plik `kolegium/app.py` zostanie przeniesiony do `archive/legacy-scripts/`.

### Faza 3: Weryfikacja i Potwierdzenie (Opcjonalnie)

**Cel:** Upewnienie się, że usunięcie powyższych plików nie wpłynęło na działanie systemu.

**Kroki:**

1.  **Uruchomienie pełnego zestawu testów:**
    -   Po zakończeniu Fazy 1 i 2, należy uruchomić wszystkie testy w projekcie, aby potwierdzić, że żadna z usuniętych części nie była ukrytą zależnością.
    ```bash
    # (Przykład komendy, może wymagać dostosowania)
    pytest
    ```

2.  **Uruchomienie środowiska deweloperskiego:**
    -   Należy uruchomić całe środowisko za pomocą `docker compose up` i manualnie zweryfikować działanie kluczowych przepływów.

---

## 4. Podsumowanie

Po wykonaniu tego planu, baza kodu zostanie oczyszczona z ponad 20 plików i skryptów, które nie są już częścią docelowej architektury. Zwiększy to spójność projektu i ułatwi jego dalsze utrzymanie, jednocześnie zachowując historyczny kod w bezpiecznym archiwum.
