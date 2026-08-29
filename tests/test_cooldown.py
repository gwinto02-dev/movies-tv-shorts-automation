import pytest
from datetime import datetime, timezone, timedelta
from src.utils.history_manager import HistoryManager

def test_title_cooldown_self_blocking_prevention(tmp_path):
    history = HistoryManager(data_dir=tmp_path)
    
    run_start_time = datetime.now(timezone.utc).isoformat()
    
    titles = [
        {"tmdb_id": 999, "title": "Inception"}
    ]
    
    # Record titles at selection time
    history.record_title_selections(titles, "Genre-Diverse Trio", run_start_time)
    
    # Re-checking cooldown with SAME run_start_time must NOT self-block
    is_cooldown = history.is_title_on_cooldown(
        tmdb_id=999,
        title="Inception",
        run_start_time=run_start_time
    )
    
    assert is_cooldown is False, "Run falsely flagged its own just-selected titles as a cooldown violation against itself!"

def test_title_cooldown_blocks_past_run(tmp_path):
    history = HistoryManager(data_dir=tmp_path)
    
    past_run_time = (datetime.now(timezone.utc) - timedelta(days=5)).isoformat()
    current_run_time = datetime.now(timezone.utc).isoformat()
    
    titles = [
        {"tmdb_id": 888, "title": "Interstellar"}
    ]
    
    # Record in a past run
    history.record_title_selections(titles, "Trending Trio", past_run_time)
    
    # Checking in current run MUST detect 30-day cooldown
    is_cooldown = history.is_title_on_cooldown(
        tmdb_id=888,
        title="Interstellar",
        run_start_time=current_run_time
    )
    
    assert is_cooldown is True, "Title on 30-day cooldown was not flagged!"
