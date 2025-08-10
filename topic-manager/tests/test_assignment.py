import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1] / 'src'))

from matching import suggest_platforms


def test_assignment_is_deterministic():
    topic = {"title": "AI for Enterprise", "keywords": ["AI", "B2B"]}
    out1 = suggest_platforms(topic)
    out2 = suggest_platforms(topic)
    assert out1 == out2


def test_assignment_rules_cover_defaults():
    topic = {"title": "Misc", "keywords": ["random"]}
    out = suggest_platforms(topic)
    assert out == ["twitter", "linkedin"] or out == ["linkedin", "twitter"]
