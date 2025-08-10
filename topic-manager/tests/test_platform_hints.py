import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1] / 'src'))
from platform_hints import platform_hints


def test_platform_hints_basic():
    lk = platform_hints("linkedin")
    assert lk["max_length"] == 1300
    assert "hook" in lk["sections"]

    tw = platform_hints("twitter")
    assert tw["max_length"] == 280
    assert tw["tone"] == "conversational"
