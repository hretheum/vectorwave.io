# Skonsolidowany Raport: Analiza Źródeł API do Śledzenia Trendów w AI

**Data:** 10 sierpnia 2025
**Autor:** Gemini Code Assistant (konsolidacja)
**Status:** UKOŃCZONO

## 1. Wprowadzenie i Cel

Niniejszy dokument stanowi skonsolidowaną analizę publicznie dostępnych API, które mogą służyć jako źródło danych dla modułu `Topic Manager` w ramach zadania **Task 2.4: Auto-Scraping Integration**. Raport łączy wyniki dwóch niezależnych analiz, aby stworzyć jeden, spójny i kompletny obraz najlepszych źródedeł do śledzenia trendów, nowinek, narzędzi i publikacji w dziedzinie AI. Wszystkie informacje zostały zweryfikowane pod kątem aktualności na dzień 10 sierpnia 2025.

**Kluczowe Odkrycie (Lipiec 2025):** Google po raz pierwszy w historii udostępniło **oficjalne API do Google Trends**, co stanowi fundamentalną zmianę w krajobrazie analizy trendów. Jednocześnie popularne nieoficjalne narzędzia, takie jak `pytrends`, zostały wycofane.

## 2. Zestawienie Tabelaryczne Rekomendowanych API

| Źródło | Kategoria | Koszt (Free Tier) | Limity (Free Tier) | Link do Dokumentacji | Złożoność |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Google Trends API** | Wyszukiwania | Darmowe (Alpha) | Niepubliczne (limitowany dostęp) | [Aplikuj o dostęp](https://trends.google.com/trends/hottrends/api) | Wysoka (Alpha) |
| **NewsData.io** | Newsy | **Darmowe (użytek komerc.)** | **200 zapytań / dzień** | [Dokumentacja](https://newsdata.io/docs) | Niska |
| **YouTube Data API** | Wideo, Trendy | Darmowe | 10,000 jednostek / dzień | [Dokumentacja](https://developers.google.com/youtube/v3/getting-started) | Niska |
| **Hacker News** | Newsy, Trendy Tech | Darmowe | Brak (bardzo hojne) | [Dokumentacja API](https://github.com/HackerNews/API) | Niska |
| **ArXiv API** | Prace Naukowe | Darmowe | 1 zapytanie / 3s | [Dokumentacja API](https://arxiv.org/help/api/user-manual) | Niska |
| **GitHub API** | Projekty Open-Source | Darmowe | 5000 zapytań / h (z tokenem) | [Dokumentacja API](https://docs.github.com/en/rest) | Średnia |
| **Stack Overflow API** | Trendy Deweloperskie | Darmowe | 10,000 zapytań / dzień | [Dokumentacja API](https://api.stackexchange.com/docs) | Niska |
| **Currents API** | Newsy (Analiza AI) | Darmowe | 600 zapytań / miesiąc | [Dokumentacja](https://currentsapi.services/en/docs/api) | Niska |
| **Product Hunt API** | Nowe Narzędzia | Darmowe (niekomerc.) | Hojne (GraphQL) | [Dokumentacja API](https://api.producthunt.com/v2/docs) | Średnia |
| **Reddit API** | Dyskusje Społeczności | Płatne ($0.24/1k) | 100 zapytań / min (darmowe) | [Dokumentacja API](https://www.reddit.com/dev/api/) | Wysoka |

---

## 3. Szczegółowa Analiza Źródeł

### Kategoria 1: Trendy Wyszukiwania

#### 3.1. Google Trends API (Oficjalne)
-   **Ocena:** **Przełomowe, ale wczesne.** Po raz pierwszy Google udostępniło oficjalne API. Obecnie w fazie alpha z limitowanym dostępem, co czyni je strategicznym celem na przyszłość, ale ryzykownym do natychmiastowej implementacji produkcyjnej.
-   **Kluczowe Cechy:** Dostęp do danych z 5 lat, agregacje dzienne/tygodniowe/miesięczne, porównywanie wielu terminów.
-   **Rekomendacja:** **Aplikować o dostęp natychmiast.** Rozpocząć eksperymenty, ale nie opierać na nim krytycznej funkcjonalności do czasu osiągnięcia statusu bety.

### Kategoria 2: Newsy i Artykuły

#### 3.2. NewsData.io
-   **Ocena:** **Najlepsza darmowa opcja do newsów.** Bardzo hojny plan darmowy (200 zapytań/dzień), który oficjalnie pozwala na użytek komercyjny. Pokrycie 84,000 źródeł i tagowanie AI czynią go niezwykle wartościowym.
-   **Rekomendacja:** **Wysoki priorytet.** Idealny punkt startowy do agregacji newsów o AI.

#### 3.3. Currents API
-   **Ocena:** **Lider w analizie.** Wyróżnia się wbudowanymi funkcjami analizy sentymentu i grupowania tematycznego. Darmowy plan (600 zapytań/miesiąc) jest ograniczony, ale wystarczający do testów.
-   **Rekomendacja:** Rozważyć jako płatne ulepszenie, jeśli wbudowana analiza AI okaże się kluczowa.

#### 3.4. Hacker News (Y Combinator)
-   **Ocena:** **Niezbędne źródło "pulsu branży".** Całkowicie darmowe, bez limitów i autentykacji. Proste API dostarcza najwyższej jakości sygnału o tym, co jest aktualnie istotne w świecie technologii i AI.
-   **Rekomendacja:** **Najwyższy priorytet.** Należy zintegrować jako jedno z pierwszych źródeł.

### Kategoria 3: Wideo i Media Społecznościowe

#### 3.5. YouTube Data API
-   **Ocena:** **Darmowy lider wideo.** Hojny limit 10,000 jednostek dziennie pozwala na kompleksową analizę trendów wideo, które są kluczowym medium dla treści o AI.
-   **Rekomendacja:** **Wysoki priorytet.** Integracja jest prosta i daje dostęp do unikalnego formatu treści.

#### 3.6. Reddit API
-   **Ocena:** **Wartościowe, ale kosztowne i skomplikowane.** Daje wgląd w autentyczne dyskusje, problemy i opinie społeczności. Jednak restrykcyjny darmowy tier i wysoka złożoność integracji (OAuth 2.0) czynią go zasobem "premium".
-   **Rekomendacja:** **Niski priorytet.** Wdrożyć tylko jeśli inne źródła okażą się niewystarczające.

### Kategoria 4: Prace Naukowe i Projekty Open-Source

#### 3.7. ArXiv & Semantic Scholar API
-   **Ocena:** **Kluczowe dla badań i rozwoju.** Oba API są darmowe i oferują bezpośredni dostęp do najnowszych prac naukowych, co jest niezbędne do śledzenia przełomów w AI. Semantic Scholar dodatkowo wzbogaca dane o analizę AI.
-   **Rekomendacja:** **Najwyższy priorytet.** Zintegrować ArXiv (prostsze) jako podstawę, a Semantic Scholar jako rozszerzenie.

#### 3.8. GitHub API
-   **Ocena:** **Niezbędne do śledzenia narzędzi.** Hojny limit (5000 zapytań/h) pozwala na efektywne monitorowanie popularności bibliotek i frameworków AI. Brak endpointu `/trending` jest minusem, ale można go obejść.
-   **Rekomendacja:** **Wysoki priorytet.** Kluczowe dla identyfikacji nowych, popularnych narzędzi.

#### 3.9. Stack Overflow API
-   **Ocena:** **Barometr problemów deweloperskich.** Darmowe i proste w użyciu, pozwala śledzić, z jakimi technologiami AI deweloperzy mają problemy lub o które najczęściej pytają, co jest świetnym wskaźnikiem adopcji.
-   **Rekomendacja:** **Wysoki priorytet.** Łatwa integracja, wartościowe dane.

## 4. Strategia Implementacji

1.  **Fundament (Must-Have):** Rozpocząć od integracji z darmowymi, prostymi i wysokiej jakości źródłami: **Hacker News, ArXiv, YouTube Data API, Stack Overflow API**. Ta kombinacja zapewni solidne pokrycie newsów, nauki i trendów deweloperskich bez żadnych kosztów.
2.  **Rozszerzenie o Narzędzia:** W drugim kroku dodać **GitHub API** i **Product Hunt API**, aby uzyskać wgląd w nowe projekty open-source i komercyjne narzędzia AI. Wymaga to obsługi kluczy API.
3.  **Zaawansowana Analiza Newsów:** Zintegrować **NewsData.io** jako główne, skalowalne źródło wiadomości z całego świata.
4.  **Eksperymenty i Przyszłość:**
    -   **Google Trends API:** Równolegle aplikować o dostęp i prowadzić prace badawcze.
    -   **Currents API / Reddit API:** Rozważyć w przyszłości jako płatne źródła premium, jeśli zajdzie potrzeba głębszej analizy sentymentu lub dyskusji społecznościowych.

Przyjęcie tej strategii pozwoli na szybkie zbudowanie wartościowego systemu auto-scrapingu przy minimalnych kosztach i złożoności, jednocześnie tworząc fundament pod przyszłe, bardziej zaawansowane integracje.
