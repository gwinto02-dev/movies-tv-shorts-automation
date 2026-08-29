import pytest
from src.script.fact_checker import FactChecker

def test_fact_checker_context_building():
    titles = [
        {
            "tmdb_id": 1,
            "title": "Dune",
            "year": "2021",
            "rating": 8.0,
            "genres": ["Sci-Fi", "Adventure"],
            "overview": "A mythic journey.",
            "director": "Denis Villeneuve"
        }
    ]
    ctx = FactChecker.build_fact_context(titles)
    assert "Dune" in ctx
    assert "2021" in ctx
    assert "8.0/10" in ctx

def test_fact_checker_detects_literal_placeholders():
    titles = [{"tmdb_id": 1, "title": "Dune", "year": "2021"}]
    
    bad_script = "Check out this movie Dune. Rating is N/A out loud."
    passed, errors = FactChecker.audit_script_facts(bad_script, titles)
    
    assert passed is False
    assert any("N/A" in err for err in errors)
