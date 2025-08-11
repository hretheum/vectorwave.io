from src.adapters import linkedin_adapter, twitter_adapter, beehiiv_adapter, ghost_adapter


def test_linkedin_adapter():
    out = linkedin_adapter(" Hello ", {"title": "X"})
    assert out["content"] == "Hello"
    assert out["meta"]["platform"] == "linkedin"


def test_twitter_adapter():
    content = "a" * 500
    out = twitter_adapter(content, {"title": "X"})
    assert len(out["content"]) <= 281
    assert out["meta"]["platform"] == "twitter"


def test_beehiiv_adapter():
    out = beehiiv_adapter("Body", {"title": "T"})
    assert out["subject"] == "T"


def test_ghost_adapter():
    out = ghost_adapter("Body", {"title": "T"})
    assert out["title"] == "T"
