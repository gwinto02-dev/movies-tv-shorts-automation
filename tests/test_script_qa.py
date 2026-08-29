import pytest
from src.script.generator import ScriptGenerator

def test_duplicate_word_detection():
    # Duplicate words like "recommendations recommendations" or "movie movie"
    bad_script = "Here are top recommendations recommendations for movie movie fans."
    passed, reasons = ScriptGenerator.check_natural_script_qa(bad_script, "Concept", [])
    
    assert passed is False
    assert any("duplicate word" in r.lower() for r in reasons)

def test_clean_script_passes_natural_qa():
    clean_script = "Looking for your next movie binge? First up is Inception from 2010. It is a thrilling Sci-Fi film. Save this for movie night!"
    passed, reasons = ScriptGenerator.check_natural_script_qa(clean_script, "Concept", [])
    
    assert passed is True
    assert len(reasons) == 0
