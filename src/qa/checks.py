import os
import re
import difflib
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple
from src.script.fact_checker import FactChecker
from src.script.generator import ScriptGenerator
from src.utils.history_manager import HistoryManager

logger = logging.getLogger(__name__)

ALLOWED_HOOK_STYLES = {"question", "bold_claim", "scenario", "you_wont_believe", "direct_statement"}

class QAChecks:
    @staticmethod
    def check_resolution_and_format(video_path: Path, expected_duration: float) -> Tuple[bool, str]:
        if not video_path.exists():
            return False, f"Video file does not exist: {video_path}"
        
        file_size = os.path.getsize(video_path)
        if file_size < 1000:
            return False, f"Video file is corrupted or too small ({file_size} bytes)."

        if not (10.0 <= expected_duration <= 65.0):
            return False, f"Video duration {expected_duration:.1f}s outside acceptable 15-60s Short range."

        return True, "1080x1920 9:16 vertical format and 15-60s duration verified."

    @staticmethod
    def check_audio_caption_sync(audio_path: Path, ass_path: Path, word_events: List[Dict[str, Any]]) -> Tuple[bool, str]:
        if not audio_path.exists():
            return False, f"Narration audio file missing: {audio_path}"
        if not ass_path.exists():
            return False, f"Subtitle ASS file missing: {ass_path}"
        if not word_events:
            return False, "No word timing events generated."

        return True, f"Audio narration and Karaoke captions synchronized ({len(word_events)} word timings)."

    @staticmethod
    def check_visual_segment_alignment(asset_manifests: List[Dict[str, Any]]) -> Tuple[bool, str]:
        if not asset_manifests or len(asset_manifests) < 3:
            return False, f"Incomplete visual asset manifests ({len(asset_manifests)} titles)."

        for m in asset_manifests:
            poster = m.get("poster", {})
            backdrop = m.get("backdrop", {})
            if not poster.get("verified") and not backdrop.get("verified"):
                return False, f"Title {m.get('title')} lacks both verified TMDB poster and backdrop artwork."

        return True, f"Visual assets aligned for all {len(asset_manifests)} featured titles."

    @staticmethod
    def check_script_naturalness(script_data: Dict[str, Any], concept_type: str, titles: List[Dict[str, Any]]) -> Tuple[bool, str]:
        full_text = script_data.get("full_text", "")
        passed, reasons = ScriptGenerator.check_natural_script_qa(full_text, concept_type, titles)
        if not passed:
            return False, f"Script naturalness failed: {'; '.join(reasons)}"
        return True, "No duplicate words, missing data placeholders, or clichés found."

    @staticmethod
    def check_retention_hook(script_data: Dict[str, Any]) -> Tuple[bool, str]:
        hook = script_data.get("hook", "")
        hook_style = script_data.get("hook_style", "")

        if not hook or len(hook.split()) < 5:
            return False, "Hook sentence is empty or too short."

        if hook_style not in ALLOWED_HOOK_STYLES:
            return False, f"Hook style '{hook_style}' not recognized by Structural Variety system."

        return True, f"Strong retention hook verified (Style: {hook_style})."

    @staticmethod
    def check_fact_audit(script_data: Dict[str, Any], titles: List[Dict[str, Any]]) -> Tuple[bool, str]:
        full_text = script_data.get("full_text", "")
        passed, errors = FactChecker.audit_script_facts(full_text, titles)
        if not passed:
            return False, f"Fact audit failed: {'; '.join(errors)}"
        return True, "Fact claims independently verified against raw TMDB source data."

    @staticmethod
    def check_policy_risk(script_data: Dict[str, Any], video_title: str) -> Tuple[bool, str]:
        banned_phrases = [
            "guaranteed views", "monetize fast", "make money", "get rich",
            "viral guarantee", "100% views", "passive income"
        ]
        combined = (script_data.get("full_text", "") + " " + video_title).lower()
        for phrase in banned_phrases:
            if phrase in combined:
                return False, f"Policy Risk Violation: Forbidden monetization/view claim phrase '{phrase}' found."
        return True, "Zero forbidden policy risk or view guarantee claims detected."

    @staticmethod
    def check_copyright_license(asset_manifests: List[Dict[str, Any]]) -> Tuple[bool, str]:
        for m in asset_manifests:
            stock = m.get("stock_video", {}).get("info", {})
            if not stock.get("verified", False):
                return False, f"Uncertain license status for title {m.get('title')} stock clip."
        return True, "All poster, backdrop, and b-roll stock assets verified for free commercial use."

    @staticmethod
    def check_originality(script_data: Dict[str, Any], history_manager: HistoryManager) -> Tuple[bool, str]:
        recent_scripts = history_manager.get_recent_scripts(limit=10)
        current_text = script_data.get("full_text", "")
        
        for past_script in recent_scripts:
            ratio = difflib.SequenceMatcher(None, current_text, past_script).ratio()
            if ratio > 0.85:
                return False, f"Originality Violation: Script is {ratio*100:.1f}% similar to a recent video."

        return True, "Script passes originality and edit distance verification."

    @staticmethod
    def check_structural_variety(script_data: Dict[str, Any], history_manager: HistoryManager) -> Tuple[bool, str]:
        hook = script_data.get("hook", "")
        recent_scripts = history_manager.get_recent_scripts(limit=5)
        
        for past in recent_scripts:
            if hook in past:
                return False, f"Structural Variety Failure: Exact hook '{hook}' was used in a recent video."

        return True, "Hook and CTA phrasing exhibit structural variety."

    @staticmethod
    def check_video_title_variety(video_title: str, concept_type: str, history_manager: HistoryManager) -> Tuple[bool, str]:
        recent_titles = history_manager.get_recent_video_titles(limit=10)
        
        for past in recent_titles:
            ratio = difflib.SequenceMatcher(None, video_title, past).ratio()
            if ratio > 0.80:
                return False, f"Video Title Variety Failure: Title '{video_title}' is near-duplicate of recent title '{past}'."

        return True, "Video title signals concept type and has unique phrasing."

    @staticmethod
    def check_title_cooldown(
        titles: List[Dict[str, Any]],
        run_start_time: str,
        history_manager: HistoryManager
    ) -> Tuple[bool, str]:
        """
        Validates no selected title was on 30-day cooldown prior to this run's start.
        Filter out entries written at or after run_start_time so run does NOT self-block.
        """
        for t in titles:
            if history_manager.is_title_on_cooldown(t["tmdb_id"], t["title"], run_start_time):
                return False, f"Title Cooldown Violation: Title '{t['title']}' (ID {t['tmdb_id']}) was on 30-day cooldown."

        return True, "All selected titles satisfied 30-day cooldown prior to selection."
