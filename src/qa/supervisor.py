import logging
from pathlib import Path
from typing import List, Dict, Any
from src.qa.checks import QAChecks
from src.utils.history_manager import HistoryManager

logger = logging.getLogger(__name__)

class SupervisorQAGate:
    def __init__(self, history_manager: HistoryManager):
        self.history = history_manager

    def evaluate_pipeline_output(
        self,
        video_path: Path,
        duration: float,
        audio_path: Path,
        ass_path: Path,
        word_events: List[Dict[str, Any]],
        script_data: Dict[str, Any],
        concept_type: str,
        titles: List[Dict[str, Any]],
        asset_manifests: List[Dict[str, Any]],
        video_title: str,
        run_start_time: str
    ) -> Dict[str, Any]:
        """
        Executes all 12 itemized QA checks.
        Returns detailed summary report. ANY single check failure sets upload_allowed = False.
        """
        checks_results = []

        # 1. Resolution & Format Check
        p1, r1 = QAChecks.check_resolution_and_format(video_path, duration)
        checks_results.append({"name": "1. Resolution & Format (1080x1920 9:16)", "passed": p1, "reason": r1})

        # 2. Audio & Caption Sync Check
        p2, r2 = QAChecks.check_audio_caption_sync(audio_path, ass_path, word_events)
        checks_results.append({"name": "2. Audio & Caption Sync", "passed": p2, "reason": r2})

        # 3. Visual Segment Alignment Check
        p3, r3 = QAChecks.check_visual_segment_alignment(asset_manifests)
        checks_results.append({"name": "3. Visual Segment Alignment", "passed": p3, "reason": r3})

        # 4. Script Naturalness Check
        p4, r4 = QAChecks.check_script_naturalness(script_data, concept_type, titles)
        checks_results.append({"name": "4. Script Naturalness (No N/A, duplicates, clichés)", "passed": p4, "reason": r4})

        # 5. Retention Hook Check
        p5, r5 = QAChecks.check_retention_hook(script_data)
        checks_results.append({"name": "5. Retention Hook Strength", "passed": p5, "reason": r5})

        # 6. Fact Audit Check
        p6, r6 = QAChecks.check_fact_audit(script_data, titles)
        checks_results.append({"name": "6. Fact Audit vs Source Data", "passed": p6, "reason": r6})

        # 7. Policy Risk Check
        p7, r7 = QAChecks.check_policy_risk(script_data, video_title)
        checks_results.append({"name": "7. Policy Risk (No view/money claims)", "passed": p7, "reason": r7})

        # 8. Copyright & Rights License Check
        p8, r8 = QAChecks.check_copyright_license(asset_manifests)
        checks_results.append({"name": "8. Copyright & Rights License Status", "passed": p8, "reason": r8})

        # 9. Script Originality Check
        p9, r9 = QAChecks.check_originality(script_data, self.history)
        checks_results.append({"name": "9. Script Originality & Edit Distance", "passed": p9, "reason": r9})

        # 10. Structural Variety Check
        p10, r10 = QAChecks.check_structural_variety(script_data, self.history)
        checks_results.append({"name": "10. Structural Variety (Hooks & Outros)", "passed": p10, "reason": r10})

        # 11. Video Title Variety Check
        p11, r11 = QAChecks.check_video_title_variety(video_title, concept_type, self.history)
        checks_results.append({"name": "11. Video Title Variety", "passed": p11, "reason": r11})

        # 12. Title Cooldown Check
        p12, r12 = QAChecks.check_title_cooldown(titles, run_start_time, self.history)
        checks_results.append({"name": "12. Title Cooldown Verification", "passed": p12, "reason": r12})

        # ANY single check failure strictly blocks upload
        overall_passed = all(c["passed"] for c in checks_results)
        upload_allowed = overall_passed

        summary = {
            "overall_passed": overall_passed,
            "upload_allowed": upload_allowed,
            "total_checks": len(checks_results),
            "passed_count": sum(1 for c in checks_results if c["passed"]),
            "failed_count": sum(1 for c in checks_results if not c["passed"]),
            "itemized_checks": checks_results
        }

        if overall_passed:
            logger.info("SUPERVISOR QA GATE: PASSED (12/12 checks passed). Upload allowed.")
        else:
            failed_names = [c['name'] for c in checks_results if not c['passed']]
            logger.error(f"SUPERVISOR QA GATE: FAILED. Failed checks: {failed_names}. Upload BLOCKED.")

        return summary
