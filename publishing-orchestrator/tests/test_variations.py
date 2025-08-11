from src.variations import generate_variations


def test_generate_variations_three():
    vs = generate_variations("Base content", num=3)
    assert len(vs) == 3
    assert vs[0]["content"].startswith("Base content")
