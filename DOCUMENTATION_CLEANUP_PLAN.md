# Plan Restrukturyzacji i Konsolidacji Dokumentacji Vector Wave

## 1. Wprowadzenie i Cele

Celem tego planu jest uporządkowanie i skonsolidowanie dokumentacji projektu Vector Wave, aby odzwierciedlała ona aktualną, zmigrowaną architekturę opisaną w folderze `target-version`. Plan ma na celu:
- **Zwiększenie przejrzystości:** Stworzenie jednego, łatwego do znalezienia źródła prawdy.
- **Eliminację przestarzałych informacji:** Usunięcie dokumentów opisujących stare, nieużywane już mechanizmy.
- **Uspójnienie wiedzy:** Zgromadzenie rozproszonych informacji w logicznych, scentralizowanych lokalizacjach.
- **Ułatwienie onboardingu:** Przygotowanie struktury, która przyspieszy wdrażanie nowych członków zespołu i LLM-ów.

## 2. Główne Zasady

Plan opiera się na dwóch kluczowych zasadach, aby zapewnić bezpieczeństwo i zgodność z bieżącymi pracami:

1.  **Nienaruszalność `target-version`:** Żadne pliki wewnątrz folderu `/target-version` nie będą modyfikowane, przenoszone ani usuwane. Folder ten jest traktowany jako aktywne środowisko pracy dla innego LLM-a i pozostanie nietknięty.
2.  **Stopniowe Wdrażanie:** Zmiany będą wprowadzane w trzech logicznych, nieniszczących fazach, aby zminimalizować ryzyko i umożliwić weryfikację na każdym etapie.

---

## 3. Plan Działania

### Faza 1: Fundamenty i Redukcja Szumu (Działania Niskiego Ryzyka) - ✅ **UKOŃCZONA**

**Cel:** Natychmiastowe zmniejszenie chaosu informacyjnego poprzez archiwizację oczywistych anachronizmów i stworzenie nowego, centralnego punktu nawigacyjnego.

**Status:** Faza została w pełni zrealizowana. Przestarzałe pliki zostały przeniesione do folderu `archive/`, a główny `README.md` został przebudowany, aby służyć jako centralny hub informacyjny.

### Faza 2: Porządkowanie Dokumentacji na Poziomie Serwisów - ✅ **UKOŃCZONA**

**Cel:** Ujednolicenie i aktualizacja dokumentacji wewnątrz każdego kluczowego serwisu, aby była ona samodzielna i spójna.

**Status:** Faza została w pełni zrealizowana. Pliki `README.md` dla kluczowych serwisów (`editorial-service`, `publisher`, `kolegium`, `ai_writing_flow`, `vector-wave-ui`, `knowledge-base`, `linkedin`) zostały ustandaryzowane i wzbogacone o skonsolidowane informacje. Rozproszona dokumentacja została zarchiwizowana.

### Faza 3: Finalna Konsolidacja (Po Zakończeniu Prac w `target-version`) - ⏳ **DO WYKONANIA**

**Cel:** Stworzenie ostatecznej, czystej struktury dokumentacji po zakończeniu bieżącej migracji.

**Kroki (do wykonania w przyszłości):**

1.  **Przeniesienie dokumentacji z `target-version`:**
    -   Po potwierdzeniu, że prace w `target-version` są zakończone, kluczowe dokumenty (`VECTOR_WAVE_TARGET_SYSTEM_ARCHITECTURE.md`, `COMPLETE_API_SPECIFICATIONS.md` itp.) zostaną przeniesione do głównego folderu `docs/`.
    -   Folder `target-version` zostanie zarchiwizowany.

2.  **Aktualizacja linków:**
    -   Wszystkie linki w głównym `README.md` i `README.md` serwisów zostaną zaktualizowane, aby wskazywały na nowe lokalizacje w `docs/`.

3.  **Ostateczny przegląd:**
    -   Końcowy przegląd całej dokumentacji w celu zapewnienia jej 100% spójności.