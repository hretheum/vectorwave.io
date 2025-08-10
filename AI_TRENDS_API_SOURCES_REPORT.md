# Raport: Analiza Źródeł API do Śledzenia Trendów w AI

**Data:** 10 sierpnia 2025
**Autor:** Gemini Code Assistant
**Status:** UKOŃCZONO

## 1. Wprowadzenie i Cel

Niniejszy dokument przedstawia wyniki analizy publicznie dostępnych API, które mogą służyć jako źródło danych dla modułu `Topic Manager` w ramach zadania **Task 2.4: Auto-Scraping Integration**. Celem było zidentyfikowanie darmowych lub posiadających hojny plan darmowy (free tier) interfejsów programistycznych, dostarczających informacji o nowościach, trendach, narzędziach i publikacjach w dziedzinie sztucznej inteligencji. Wszystkie informacje zostały zweryfikowane pod kątem aktualności na dzień 10 sierpnia 2025.

## 2. Metodologia

Analiza została przeprowadzona w trzech krokach:
1.  **Identyfikacja Kandydatów:** Zidentyfikowano kluczowe platformy będące centrami wymiany informacji w branży technologicznej.
2.  **Weryfikacja API:** Dla każdej platformy zweryfikowano istnienie, dokumentację, politykę dostępu, limity darmowego użytkowania (rate limits) oraz wymagania autentykacyjne.
3.  **Ocena Jakości i Złożoności:** Oceniono jakość i relewantność danych dostarczanych przez API w kontekście AI oraz oszacowano złożoność techniczną integracji z istniejącym systemem.

---

## 3. Rekomendowane Źródła API

### Kategoria 1: Newsy, Artykuły i Dyskusje Społeczności

#### 3.1. Hacker News (Y Combinator)

-   **Opis:** Jeden z najważniejszych agregatorów newsów technologicznych. Często pojawiają się tu jako pierwsze informacje o przełomowych projektach AI.
-   **API:** Oficjalne, publiczne API dostarczane przez Firebase.
-   **Dostęp i Ceny:**
    -   **Koszt:** Całkowicie darmowe.
    -   **Autentykacja:** Nie jest wymagana.
    -   **Limity:** Brak oficjalnych, sztywnych limitów (rate limits). API jest bardzo wydajne, ale zaleca się rozsądne użytkowanie.
-   **Jakość Danych:** Bardzo wysoka. Linki i dyskusje, które trafiają na stronę główną, są silnym sygnałem o rosnącym trendzie.
-   **Złożoność Integracji:** **Niska.** Proste, REST-owe endpointy do pobierania list ID najpopularniejszych artykułów oraz szczegółów każdego z nich.

#### 3.2. Dev.to API

-   **Opis:** Popularna platforma blogowa dla deweloperów. Źródło praktycznych artykułów, tutoriali i opinii na temat nowych narzędzi AI.
-   **API:** Oficjalne, publiczne API.
-   **Dostęp i Ceny:**
    -   **Koszt:** Całkowicie darmowe.
    -   **Autentykacja:** Opcjonalna (wyższe limity z kluczem API).
    -   **Limity:** Hojne limity dla zapytań (kilkaset na minutę), w zupełności wystarczające do okresowego skanowania.
-   **Jakość Danych:** Dobra. Artykuły tagowane jako `#ai`, `#machinelearning` itp. są świetnym źródłem informacji o tym, jak deweloperzy faktycznie używają nowych technologii.
-   **Złożoność Integracji:** **Niska.** Standardowe API REST z prostą autentykacją opartą na kluczu.

#### 3.3. Reddit API

-   **Opis:** Kluczowe źródło dyskusji społecznościowych, np. w subredditach takich jak `r/MachineLearning`, `r/OpenAI`, `r/LocalLLaMA`.
-   **API:** Oficjalne API.
-   **Dostęp i Ceny:**
    -   **Koszt:** Darmowy dostęp jest **bardzo restrykcyjny**.
    -   **Autentykacja:** Wymagany OAuth 2.0 dla każdej aplikacji.
    -   **Limity:** **100 zapytań na minutę na klienta OAuth.** Jest to limit współdzielony przez wszystkich użytkowników aplikacji, co czyni go problematycznym dla skalowalnych rozwiązań. Użycie komercyjne wymaga płatnego planu.
-   **Jakość Danych:** Unikalna. Dostęp do opinii, problemów i niszowych dyskusji, których nie ma w oficjalnych newsach.
-   **Złożoność Integracji:** **Wysoka.** Wymaga implementacji pełnego przepływu OAuth 2.0 i starannego zarządzania limitami. Ryzyko zablokowania aplikacji jest znaczące.

### Kategoria 2: Prace Naukowe i Publikacje

#### 3.4. ArXiv API

-   **Opis:** Główne, otwarte repozytorium prac naukowych w dziedzinach ścisłych, w tym najważniejsze publikacje z dziedziny AI.
-   **API:** Oficjalne, publiczne API.
-   **Dostęp i Ceny:**
    -   **Koszt:** Całkowicie darmowe.
    -   **Autentykacja:** Nie jest wymagana.
    -   **Limity:** Zalecane jest nie więcej niż **1 zapytanie na 3 sekundy**. Należy unikać zapytań równoległych.
-   **Jakość Danych:** Najwyższa. Bezpośredni dostęp do źródłowych prac naukowych, często na wiele miesięcy przed ich oficjalną publikacją w recenzowanych czasopismach.
-   **Złożoność Integracji:** **Niska.** Proste API oparte na HTTP GET z parametrami w URL. Wyniki zwracane są w formacie Atom (XML), co wymaga prostego parsowania.

### Kategoria 3: Nowe Narzędzia i Projekty Open-Source

#### 3.5. GitHub API

-   **Opis:** Największe repozytorium kodu na świecie. Kluczowe źródło informacji o nowych narzędziach, bibliotekach i frameworkach AI.
-   **API:** Oficjalne API REST.
-   **Dostęp i Ceny:**
    -   **Koszt:** Darmowe.
    -   **Autentykacja:** Możliwa bez autentykacji, ale z bardzo niskim limitem. Zalecana autentykacja za pomocą Personal Access Token.
    -   **Limity:** Bez autentykacji: **60 zapytań/godzinę**. Z autentykacją: **5000 zapytań/godzinę**.
-   **Jakość Danych:** Bardzo wysoka. Możliwość wyszukiwania repozytoriów po tematach (`topic:ai`), sortowania po liczbie gwiazdek i aktywności pozwala precyzyjnie identyfikować zyskujące na popularności projekty.
-   **Złożoność Integracji:** **Średnia.** API jest bardzo rozbudowane. Wymaga autentykacji (prosty token) do sensownego użytku. Nie ma bezpośredniego endpointu `/trending`, ale można go symulować przez wyszukiwanie repozytoriów z dużą liczbą gwiazdek w ostatnim czasie.

#### 3.6. Product Hunt API v2

-   **Opis:** Platforma do odkrywania nowych produktów technologicznych, w tym wielu narzędzi opartych na AI.
-   **API:** Oficjalne API v2 oparte na GraphQL.
-   **Dostęp i Ceny:**
    -   **Koszt:** Darmowe do użytku niekomercyjnego.
    -   **Autentykacja:** Wymagany klucz API (Developer Token).
    -   **Limity:** Hojne, oparte na "złożoności" zapytania (6250 punktów na 15 minut). W praktyce pozwala to na setki zapytań na godzinę.
-   **Jakość Danych:** Bardzo dobra. Skoncentrowane na nowo uruchomionych produktach, co jest idealne do wychwytywania "gorących" narzędzi AI.
-   **Złożoność Integracji:** **Średnia.** Wymaga użycia GraphQL, co jest nieco bardziej skomplikowane niż REST, ale daje większą elastyczność w definiowaniu potrzebnych danych.

---

## 4. Tabela Podsumowująca

| Źródło | Typ Danych | Koszt | Autentykacja | Limity (Free Tier) | Złożoność Integracji | Rekomendacja |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Hacker News** | Newsy, Trendy | Darmowe | Nie | Brak (hojne) | **Niska** | **Wysoki Priorytet** |
| **ArXiv** | Prace Naukowe | Darmowe | Nie | 1 zapytanie / 3s | **Niska** | **Wysoki Priorytet** |
| **GitHub** | Projekty OS | Darmowe | Token (zalecany) | 5000 zapytań / h | **Średnia** | **Wysoki Priorytet** |
| **Product Hunt** | Nowe Narzędzia | Darmowe (niekomerc.) | Klucz API | Hojne (GraphQL) | **Średnia** | **Wysoki Priorytet** |
| **Dev.to** | Artykuły Tech | Darmowe | Opcjonalna | Hojne | **Niska** | Średni Priorytet |
| **Reddit** | Dyskusje | Darmowe (restrykcyjne) | OAuth 2.0 | 100 zapytań / min | **Wysoka** | Niski Priorytet (Opcjonalnie) |

## 5. Wnioski i Rekomendacje

Zidentyfikowano sześć solidnych źródeł API, które mogą zasilać moduł auto-scrapingu. Rekomenduje się wdrożenie ich w następującej kolejności, aby zmaksymalizować wartość przy minimalnym wysiłku:

1.  **Implementacja Priorytetowa:** Rozpocząć od integracji z **Hacker News** i **ArXiv** ze względu na ich prostotę i bardzo wysoką jakość sygnału.
2.  **Druga Faza:** Dodać **GitHub** i **Product Hunt**, które wymagają obsługi kluczy API, ale dostarczają kluczowych danych o nowych projektach i narzędziach.
3.  **Uzupełnienie:** Wdrożyć **Dev.to** jako dodatkowe źródło treści od deweloperów.
4.  **Opcjonalnie:** Rozważyć integrację z **Reddit** na samym końcu, jeśli dane z dyskusji społecznościowych okażą się niezbędne, mając na uwadze wysoką złożoność i ryzyko.
