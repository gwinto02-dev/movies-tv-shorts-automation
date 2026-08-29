import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional
from config.settings import settings

logger = logging.getLogger(__name__)

class HistoryManager:
    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or settings.DATA_DIR
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.title_cooldown_file = self.data_dir / "title_cooldown_history.json"
        self.concept_cooldown_file = self.data_dir / "concept_cooldown_history.json"
        self.script_history_file = self.data_dir / "script_history.json"
        self.cta_history_file = self.data_dir / "cta_history.json"
        self.video_title_history_file = self.data_dir / "video_title_history.json"

    def _read_json(self, path: Path) -> List[Dict[str, Any]]:
        if not path.exists():
            return []
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                return json.loads(content) if content else []
        except Exception as e:
            logger.error(f"Error reading JSON from {path}: {e}")
            return []

    def _write_json(self, path: Path, data: List[Dict[str, Any]]) -> None:
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error writing JSON to {path}: {e}")

    def is_title_on_cooldown(
        self,
        tmdb_id: int,
        title: str,
        run_start_time: str,
        cooldown_days: int = settings.TITLE_COOLDOWN_DAYS
    ) -> bool:
        """
        Check if a title is on cooldown.
        IMPORTANT: Excludes entries recorded at or after `run_start_time` so a run
        does NOT falsely flag its own selections as a cooldown violation.
        """
        history = self._read_json(self.title_cooldown_file)
        if not history:
            return False

        now = datetime.now(timezone.utc)
        run_start_dt = datetime.fromisoformat(run_start_time)
        cutoff_date = now - timedelta(days=cooldown_days)

        for entry in history:
            entry_time_str = entry.get("timestamp") or entry.get("recorded_at")
            if not entry_time_str:
                continue

            entry_dt = datetime.fromisoformat(entry_time_str)

            # Exclude entries written by THIS run itself
            if entry_dt >= run_start_dt:
                continue

            # Check if within cooldown window
            if entry_dt >= cutoff_date:
                if entry.get("tmdb_id") == tmdb_id or entry.get("title", "").strip().lower() == title.strip().lower():
                    logger.info(f"Title '{title}' (ID {tmdb_id}) is on cooldown (Recorded: {entry_time_str})")
                    return True

        return False

    def record_title_selections(
        self,
        titles: List[Dict[str, Any]],
        concept_type: str,
        run_start_time: str
    ) -> None:
        """Record title selections immediately at selection time."""
        history = self._read_json(self.title_cooldown_file)

        for t in titles:
            entry = {
                "tmdb_id": t.get("tmdb_id"),
                "title": t.get("title"),
                "concept_type": concept_type,
                "timestamp": run_start_time,
                "run_start_time": run_start_time
            }
            history.append(entry)

        self._write_json(self.title_cooldown_file, history)
        logger.info(f"Recorded {len(titles)} titles in title_cooldown_history.json at selection time.")

    def is_concept_on_cooldown(
        self,
        concept_type: str,
        cooldown_days: int = settings.CONCEPT_COOLDOWN_DAYS
    ) -> bool:
        history = self._read_json(self.concept_cooldown_file)
        if not history:
            return False

        now = datetime.now(timezone.utc)
        cutoff_date = now - timedelta(days=cooldown_days)

        for entry in history:
            entry_time_str = entry.get("timestamp")
            if not entry_time_str:
                continue
            entry_dt = datetime.fromisoformat(entry_time_str)
            if entry_dt >= cutoff_date and entry.get("concept_type") == concept_type:
                return True

        return False

    def record_concept_selection(self, concept_type: str) -> None:
        history = self._read_json(self.concept_cooldown_file)
        entry = {
            "concept_type": concept_type,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        history.append(entry)
        self._write_json(self.concept_cooldown_file, history)

    def get_recent_ctas(self, limit: int = 5) -> List[str]:
        history = self._read_json(self.cta_history_file)
        return [h.get("cta_style") for h in history[-limit:] if h.get("cta_style")]

    def record_cta_usage(self, cta_style: str, text: str) -> None:
        history = self._read_json(self.cta_history_file)
        history.append({
            "cta_style": cta_style,
            "text": text,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        self._write_json(self.cta_history_file, history)

    def get_recent_scripts(self, limit: int = 10) -> List[str]:
        history = self._read_json(self.script_history_file)
        return [h.get("full_text", "") for h in history[-limit:]]

    def record_script(self, script_data: Dict[str, Any]) -> None:
        history = self._read_json(self.script_history_file)
        history.append({
            "hook": script_data.get("hook"),
            "full_text": script_data.get("full_text"),
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        self._write_json(self.script_history_file, history)

    def get_recent_video_titles(self, limit: int = 10) -> List[str]:
        history = self._read_json(self.video_title_history_file)
        return [h.get("video_title", "") for h in history[-limit:]]

    def record_video_title(self, title: str, concept_type: str) -> None:
        history = self._read_json(self.video_title_history_file)
        history.append({
            "video_title": title,
            "concept_type": concept_type,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        self._write_json(self.video_title_history_file, history)
