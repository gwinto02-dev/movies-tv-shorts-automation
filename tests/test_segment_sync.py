import pytest
from src.utils.text_processing import strip_season_and_episode_numbering, extract_sync_keywords

def test_strip_season_and_episode_numbering():
    # Dashed form
    assert strip_season_and_episode_numbering("The Chosen - Season 3") == "The Chosen"
    # Colon form
    assert strip_season_and_episode_numbering("The Chosen: Season 3") == "The Chosen"
    # Non-dashed form (silently failed on regexes that only handled dashed form in sibling project)
    assert strip_season_and_episode_numbering("The Chosen Season 3") == "The Chosen"
    # S3 short form
    assert strip_season_and_episode_numbering("Reacher S2") == "Reacher"

def test_extract_sync_keywords():
    keywords = extract_sync_keywords("The Chosen: Season 3")
    assert "chosen" in keywords
    assert "the" not in keywords
    assert "season" not in keywords
