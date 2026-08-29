#!/usr/bin/env python3
"""
Content-Aware JSON Merge Driver
Unions entries from JSON array history files, deduplicating entries and sorting by timestamp.
Prevents git text merge conflicts on data/*.json files in GitHub Actions.
"""

import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

def merge_json_arrays(file_a: Path, file_b: Path, output_file: Path) -> bool:
    """
    Unions two JSON array files, deduplicating by exact content or key timestamp,
    and sorting chronologically by timestamp.
    """
    data_a = load_json_array(file_a)
    data_b = load_json_array(file_b)

    combined = data_a + data_b
    unique_entries = []
    seen = set()

    for item in combined:
        if isinstance(item, dict):
            # Key for deduplication
            tmdb_id = item.get("tmdb_id")
            title = item.get("title")
            concept = item.get("concept_type")
            ts = item.get("timestamp") or item.get("recorded_at")
            video_title = item.get("video_title")
            
            key = (tmdb_id, title, concept, ts, video_title)
            if key not in seen:
                seen.add(key)
                unique_entries.append(item)
        else:
            item_str = str(item)
            if item_str not in seen:
                seen.add(item_str)
                unique_entries.append(item)

    # Sort by timestamp if available
    def get_sort_key(entry):
        if isinstance(entry, dict):
            return entry.get("timestamp") or entry.get("recorded_at") or ""
        return str(entry)

    unique_entries.sort(key=get_sort_key)

    try:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(unique_entries, f, indent=2, ensure_ascii=False)
        logger.info(f"Merged {len(data_a)} and {len(data_b)} entries -> {len(unique_entries)} unique entries in {output_file.name}")
        return True
    except Exception as e:
        logger.error(f"Failed to write merged JSON to {output_file}: {e}")
        return False

def load_json_array(path: Path) -> List[Any]:
    if not path.exists():
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read().strip()
            return json.loads(content) if content else []
    except Exception as e:
        logger.error(f"Error loading {path}: {e}")
        return []

def main():
    if len(sys.argv) < 2:
        # Merge all files in data/ directory against themselves (clean duplicates)
        data_dir = Path(__file__).resolve().parent.parent / "data"
        for json_file in data_dir.glob("*.json"):
            merge_json_arrays(json_file, json_file, json_file)
        sys.exit(0)

    if len(sys.argv) == 4:
        # Usage: merge_history.py file_a file_b output_file
        file_a = Path(sys.argv[1])
        file_b = Path(sys.argv[2])
        out_file = Path(sys.argv[3])
        success = merge_json_arrays(file_a, file_b, out_file)
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
