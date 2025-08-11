import os
import pathlib
import sys
import pytest

# Allow running from repo root
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1] / 'src'))

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

from infrastructure.embeddings import OpenAIEmbeddingProvider  # type: ignore

run_smoke = os.getenv("RUN_OPENAI_SMOKE") == "1" and bool(os.getenv("OPENAI_API_KEY"))

@pytest.mark.skipif(not run_smoke, reason="Set RUN_OPENAI_SMOKE=1 and OPENAI_API_KEY to run")
def test_openai_embeddings_smoke_roundtrip():
    provider = OpenAIEmbeddingProvider()
    texts = [
        "Hello world",
        "OpenAI embeddings smoke test",
        "Another sample text"
    ]
    vectors = pytest.run(async_fn=provider.embed_texts, texts=texts) if hasattr(pytest, 'run') else None
    # Fallback: simple event loop when pytest utility not available
    if vectors is None:
        import asyncio
        vectors = asyncio.get_event_loop().run_until_complete(provider.embed_texts(texts))
    assert isinstance(vectors, list) and len(vectors) == len(texts)
    for v in vectors:
        assert isinstance(v, list) and len(v) >= 256
        assert all(isinstance(x, (int, float)) for x in v)
