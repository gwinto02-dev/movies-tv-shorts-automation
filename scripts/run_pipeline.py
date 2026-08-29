#!/usr/bin/env python3
"""
Master Pipeline CLI Runner for Daily Movies & TV Shorts (TMDB YouTube Automation)
"""

import sys
import argparse
import logging
from datetime import datetime, timezone
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config.settings import settings
from src.content.tmdb_client import TMDBClient
from src.content.selector import ContentSelector
from src.content.stock_video import VisualAssetManager
from src.script.generator import ScriptGenerator
from src.audio.tts_engine import TTSEngine
from src.video.subtitles import SubtitleGenerator
from src.video.compositor import VideoCompositor
from src.qa.supervisor import SupervisorQAGate
from src.youtube.uploader import YouTubeUploader
from src.notify.daily_report import DailyReporter
from src.utils.history_manager import HistoryManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("MainPipeline")

def run_pipeline(dry_run: bool = False) -> bool:
    # Capture run start time at the very beginning of pipeline
    run_start_time = datetime.now(timezone.utc).isoformat()
    logger.info(f"Starting TMDB Shorts Pipeline (Run Start Time: {run_start_time}) [Dry Run: {dry_run}]")

    settings.ensure_directories()
    history = HistoryManager()
    tmdb = TMDBClient()

    # Phase 2: Content Selection & Immediate Cooldown Recording
    selector = ContentSelector(tmdb, history)
    concept_type, titles = selector.select_daily_content(run_start_time)
    logger.info(f"Featured Titles selected for '{concept_type}': {[t['title'] for t in titles]}")

    # Phase 3: Fact-Checked Script Generation
    script_gen = ScriptGenerator(history)
    script_data = script_gen.generate_script(concept_type, titles)
    logger.info(f"Script Generated: '{script_data['video_title']}' (Hook Style: {script_data.get('hook_style')})")

    # Phase 4: Visual Asset Sourcing (Posters, Backdrops, Stock Video)
    asset_mgr = VisualAssetManager()
    asset_manifests = []
    for idx, t in enumerate(titles, 1):
        manifest = asset_mgr.prepare_visual_assets_for_title(t, idx)
        asset_manifests.append(manifest)

    # Phase 5: Edge-TTS Narration & Subtitle Generation
    tts = TTSEngine()
    narration_mp3 = settings.OUTPUT_DIR / "narration.mp3"
    narration_path, word_events = tts.generate_narration(script_data["full_text"], narration_mp3)

    subtitle_ass = settings.OUTPUT_DIR / "subtitles.ass"
    SubtitleGenerator.generate_karaoke_ass(word_events, subtitle_ass)

    # Phase 6: Vertical 9:16 Video Assembly
    compositor = VideoCompositor()
    output_mp4 = settings.OUTPUT_DIR / "final_short.mp4"
    duration = word_events[-1]["end"] if word_events else 30.0
    
    video_path = compositor.render_short_video(
        script_data=script_data,
        asset_manifests=asset_manifests,
        narration_mp3_path=narration_path,
        word_events=word_events,
        subtitle_ass_path=subtitle_ass,
        output_mp4_path=output_mp4
    )

    # Phase 7 & 8: Consolidated Supervisor QA Gate Evaluation
    supervisor = SupervisorQAGate(history)
    qa_summary = supervisor.evaluate_pipeline_output(
        video_path=video_path,
        duration=duration,
        audio_path=narration_path,
        ass_path=subtitle_ass,
        word_events=word_events,
        script_data=script_data,
        concept_type=concept_type,
        titles=titles,
        asset_manifests=asset_manifests,
        video_title=script_data["video_title"],
        run_start_time=run_start_time
    )

    # Phase 9: YouTube Upload (Private Guardrail)
    youtube_video_id = None
    if qa_summary["upload_allowed"]:
        uploader = YouTubeUploader()
        youtube_video_id = uploader.upload_short_video(
            video_path=video_path,
            title=script_data["video_title"],
            description=f"{script_data['full_text']}\n\n#Shorts #{concept_type.replace(' ', '')} #TMDB",
            dry_run=dry_run
        )
        # Record script and title history upon QA pass
        history.record_script(script_data)
        history.record_video_title(script_data["video_title"], concept_type)
    else:
        logger.error("Supervisor QA Gate failed! Upload was strictly blocked.")

    # Phase 10: Daily Summary Report & Dashboard
    reporter = DailyReporter()
    reporter.generate_report(
        concept_type=concept_type,
        titles=titles,
        script_data=script_data,
        qa_summary=qa_summary,
        youtube_video_id=youtube_video_id
    )

    logger.info("Pipeline execution completed.")
    return qa_summary["overall_passed"]

def main():
    parser = argparse.ArgumentParser(description="TMDB Daily Movie Shorts Automation Pipeline")
    parser.add_argument("--dry-run", action="store_true", help="Simulate pipeline without uploading to YouTube")
    args = parser.parse_args()

    success = run_pipeline(dry_run=args.dry_run)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
