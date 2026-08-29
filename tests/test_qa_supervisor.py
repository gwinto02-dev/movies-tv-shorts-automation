import pytest
from pathlib import Path
from src.qa.supervisor import SupervisorQAGate
from src.utils.history_manager import HistoryManager

def test_supervisor_qa_gate_blocks_upload_on_any_failure(tmp_path):
    history = HistoryManager(data_dir=tmp_path)
    supervisor = SupervisorQAGate(history)
    
    # Pass non-existent video path to trigger Resolution & Format check failure
    fake_video = tmp_path / "non_existent.mp4"
    
    summary = supervisor.evaluate_pipeline_output(
        video_path=fake_video,
        duration=30.0,
        audio_path=tmp_path / "audio.mp3",
        ass_path=tmp_path / "subs.ass",
        word_events=[{"word": "hi", "start": 0, "end": 1}],
        script_data={"full_text": "Clean script", "hook": "Valid hook sentence here", "hook_style": "question", "video_title": "Clean Title"},
        concept_type="Trending Trio",
        titles=[{"tmdb_id": 1, "title": "Inception"}],
        asset_manifests=[{"title": "Inception", "poster": {"verified": True}, "stock_video": {"info": {"verified": True}}}],
        video_title="Clean Title",
        run_start_time="2026-08-29T00:00:00+00:00"
    )
    
    assert summary["overall_passed"] is False, "Supervisor gate did not mark overall_passed = False on check failure!"
    assert summary["upload_allowed"] is False, "Supervisor gate allowed upload despite QA check failure!"
