import json
import pytest
from scripts.merge_history import merge_json_arrays

def test_content_aware_json_merge(tmp_path):
    file_a = tmp_path / "history_a.json"
    file_b = tmp_path / "history_b.json"
    out_file = tmp_path / "merged.json"

    data_a = [
        {"tmdb_id": 101, "title": "Inception", "timestamp": "2026-08-01T12:00:00+00:00"},
        {"tmdb_id": 102, "title": "Interstellar", "timestamp": "2026-08-02T12:00:00+00:00"}
    ]
    data_b = [
        {"tmdb_id": 102, "title": "Interstellar", "timestamp": "2026-08-02T12:00:00+00:00"}, # Duplicate
        {"tmdb_id": 103, "title": "The Dark Knight", "timestamp": "2026-08-03T12:00:00+00:00"}
    ]

    file_a.write_text(json.dumps(data_a), encoding="utf-8")
    file_b.write_text(json.dumps(data_b), encoding="utf-8")

    success = merge_json_arrays(file_a, file_b, out_file)
    assert success is True

    merged_data = json.loads(out_file.read_text(encoding="utf-8"))
    assert len(merged_data) == 3, f"Expected 3 unique entries, got {len(merged_data)}"
    assert merged_data[0]["tmdb_id"] == 101
    assert merged_data[1]["tmdb_id"] == 102
    assert merged_data[2]["tmdb_id"] == 103
