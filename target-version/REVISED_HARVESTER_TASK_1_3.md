### Task 1.3 (Decomposed): Core Data Ingestion Pipeline (2 days) ⏱️ 16h

This task is decomposed into smaller, incremental steps to allow for testing and validation of each API integration individually.

##### Task 1.3.1: Fetcher & Storage Foundation (0.5 days) ⏱️ 4h
```yaml
objective: "Create the foundational components for the data ingestion pipeline"
deliverable: "A `Fetcher Engine` structure, a `Storage Service` to connect to ChromaDB, and a standardized `RawTrendItem` Pydantic model"
acceptance_criteria:
  - The `Fetcher Engine` is designed to be modular, allowing for easy addition of new data source "fetchers".
  - The `Storage Service` can successfully connect to the `raw_trends` ChromaDB collection and save a list of `RawTrendItem` objects.
  - The `POST /harvest/trigger` endpoint is created but initially does nothing or calls an empty engine.
  - Unit tests for the Storage Service are created and pass.

validation_commands:
  - "pytest harvester/tests/test_storage_service.py"
```

##### Task 1.3.2: Implement Hacker News Fetcher (2h)
```yaml
objective: "Implement the first data source integration for Hacker News"
deliverable: "A functional `HackerNewsFetcher` module integrated into the Fetcher Engine"
acceptance_criteria:
  - The fetcher correctly queries the Hacker News API for top stories.
  - Raw API data is successfully normalized into the `RawTrendItem` model.
  - The integration is resilient to API errors.

validation_commands: |
  docker compose --profile harvester up -d --build
  sleep 15
  curl -X POST http://localhost:8043/harvest/trigger
  sleep 15
  python scripts/verify_chroma_collection.py --collection raw_trends --where '{"source":"hacker-news"}' --min-count 5
```

##### Task 1.3.3: Implement ArXiv Fetcher (2h)
```yaml
objective: "Add support for fetching scientific papers from ArXiv"
deliverable: "A functional `ArXivFetcher` module integrated into the Fetcher Engine"
acceptance_criteria:
  - The fetcher correctly queries the ArXiv API for recent papers in AI-related categories (cs.AI, cs.LG, etc.).
  - The XML response from ArXiv is correctly parsed and normalized into the `RawTrendItem` model.

validation_commands: |
  docker compose --profile harvester up -d --build
  sleep 15
  curl -X POST http://localhost:8043/harvest/trigger
  sleep 15
  python scripts/verify_chroma_collection.py --collection raw_trends --where '{"source":"arxiv"}' --min-count 5
```

##### Task 1.3.4: Implement Dev.to Fetcher (2h)
```yaml
objective: "Add support for fetching developer articles from Dev.to"
deliverable: "A functional `DevToFetcher` module integrated into the Fetcher Engine"
acceptance_criteria:
  - The fetcher correctly queries the Dev.to API for articles tagged with 'ai', 'machinelearning', etc.
  - The fetcher correctly uses the provided API key for authentication.

validation_commands: |
  docker compose --profile harvester up -d --build
  sleep 15
  curl -X POST http://localhost:8043/harvest/trigger
  sleep 15
  python scripts/verify_chroma_collection.py --collection raw_trends --where '{"source":"dev-to"}' --min-count 5
```

##### Task 1.3.5: Implement NewsData.io Fetcher (2h)
```yaml
objective: "Add support for fetching global news from NewsData.io"
deliverable: "A functional `NewsDataFetcher` module integrated into the Fetcher Engine"
acceptance_criteria:
  - The fetcher correctly queries the NewsData.io API for news related to AI.
  - The fetcher correctly uses the provided API key for authentication.

validation_commands: |
  docker compose --profile harvester up -d --build
  sleep 15
  curl -X POST http://localhost:8043/harvest/trigger
  sleep 15
  python scripts/verify_chroma_collection.py --collection raw_trends --where '{"source":"newsdata-io"}' --min-count 5
```

##### Task 1.3.6: Implement GitHub Fetcher (2h)
```yaml
objective: "Add support for discovering trending open-source projects from GitHub"
deliverable: "A functional `GitHubFetcher` module integrated into the Fetcher Engine"
acceptance_criteria:
  - The fetcher uses the GitHub Search API to find recently created repositories with a high number of stars, tagged with 'ai' or 'llm'.
  - The fetcher correctly uses the provided Personal Access Token for authentication.

validation_commands: |
  docker compose --profile harvester up -d --build
  sleep 15
  curl -X POST http://localhost:8043/harvest/trigger
  sleep 15
  python scripts/verify_chroma_collection.py --collection raw_trends --where '{"source":"github"}' --min-count 5
```

##### Task 1.3.7: Implement Product Hunt Fetcher (2h)
```yaml
objective: "Add support for discovering new tech products from Product Hunt"
deliverable: "A functional `ProductHuntFetcher` module integrated into the Fetcher Engine"
acceptance_criteria:
  - The fetcher correctly queries the Product Hunt v2 GraphQL API for recent top-voted products.
  - The fetcher correctly uses the provided Developer Token for authentication.

validation_commands: |
  docker compose --profile harvester up -d --build
  sleep 15
  curl -X POST http://localhost:8043/harvest/trigger
  sleep 15
  python scripts/verify_chroma_collection.py --collection raw_trends --where '{"source":"product-hunt"}' --min-count 5
```
