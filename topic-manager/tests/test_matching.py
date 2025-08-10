import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from matching import suggest_platforms


def test_suggest_platforms_deterministic():
    t = {"title": "AI for Enterprise", "keywords": ["AI", "B2B"]}
    p1 = suggest_platforms(t)
    p2 = suggest_platforms(t)
    assert p1 == p2
    assert "linkedin" in p1 and "twitter" in p1


def test_suggest_platforms_default():
    t = {"title": "Random", "keywords": []}
    p = suggest_platforms(t)
    assert p == ["twitter", "linkedin"] or p == ["linkedin", "twitter"]
