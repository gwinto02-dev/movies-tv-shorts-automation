import re
from typing import List, Set
from difflib import SequenceMatcher

STOPWORDS: Set[str] = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of",
    "with", "by", "from", "up", "about", "into", "over", "after", "is", "are",
    "was", "were", "be", "been", "being", "have", "has", "had", "do", "does",
    "did", "season", "one", "two", "three", "four", "five", "part", "vol",
    "volume", "chapter", "episode", "movie", "film", "series"
}

def strip_season_and_episode_numbering(title: str) -> str:
    """
    Strips trailing 'Season N' or episode numbering whether or not preceded by a dash or colon.
    Handles dashed ('The Chosen - Season 3'), colon ('The Chosen: Season 3'),
    and non-dashed ('The Chosen Season 3' or 'The Chosen S3') forms.
    """
    if not title:
        return ""

    # Patterns matching trailing season/episode annotations
    patterns = [
        r"[\:\-\s]+season\s+\d+.*$",
        r"[\:\-\s]+s\d+.*$",
        r"[\:\-\s]+part\s+\d+.*$",
        r"[\:\-\s]+vol(ume)?\s+\d+.*$",
        r"\s+season\s+\d+.*$",
        r"\s+s\d+.*$",
        r"\s+part\s+\d+.*$"
    ]

    clean = title
    for p in patterns:
        clean = re.sub(p, "", clean, flags=re.IGNORECASE)

    return clean.strip()

def extract_sync_keywords(title: str) -> List[str]:
    """
    Strips season numbering AND common English stopwords from title to produce
    clean, non-ambiguous keywords for narration-to-visual segment sync.
    """
    cleaned_title = strip_season_and_episode_numbering(title)
    words = re.findall(r"\b[a-zA-Z0-9']+\b", cleaned_title.lower())
    
    # Filter out stopwords
    keywords = [w for w in words if w not in STOPWORDS and len(w) > 1]
    return keywords if keywords else [cleaned_title.lower()]

def find_near_duplicate_title(candidate: str, past_titles: List[str], threshold: float = 0.80) -> str:
    """
    Returns the first past title that is a near-duplicate of `candidate` (character-level
    similarity ratio above `threshold`), or "" if none match. Shared by the script generator
    (to retry/steer generation away from repeats) and the QA supervisor's title variety check
    (to block near-duplicates that slipped through), so both use the same definition of "too similar".
    """
    for past in past_titles:
        if not past:
            continue
        ratio = SequenceMatcher(None, candidate, past).ratio()
        if ratio > threshold:
            return past
    return ""
