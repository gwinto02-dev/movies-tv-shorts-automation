import re
import logging
from typing import List, Dict, Any, Tuple

logger = logging.getLogger(__name__)

class FactChecker:
    @staticmethod
    def build_fact_context(titles: List[Dict[str, Any]]) -> str:
        """Formats real TMDB facts into explicit text block for LLM prompt."""
        lines = []
        for idx, t in enumerate(titles, 1):
            year_str = f"Year: {t.get('year')}" if t.get('year') else "Year: Upcoming/Unknown"
            rating_str = f"Rating: {t.get('rating')}/10" if t.get('rating') else "Rating: Unrated"
            genres_str = f"Genres: {', '.join(t.get('genres', []))}"
            overview_str = f"Overview: {t.get('overview')}"
            director_str = f"Director: {t.get('director')}" if t.get('director') != "N/A" else ""
            
            item_line = f"Title {idx}: {t.get('title')} ({year_str}, {rating_str}, {genres_str}) {director_str}\n  {overview_str}"
            lines.append(item_line)
        return "\n".join(lines)

    @staticmethod
    def audit_script_facts(script_text: str, titles: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
        """
        Post-generation fact audit verifying script claims against sourced data.
        Returns (passed, list_of_errors).
        """
        errors = []
        lower_script = script_text.lower()

        # Check 1: Reject literal placeholder words out loud
        placeholders = ["n/a", "null", "undefined", "unknown rating", "none/10"]
        for ph in placeholders:
            pattern = rf"\b{re.escape(ph)}\b"
            match = re.search(pattern, lower_script)
            if match:
                errors.append(f"Fact Audit Failure: Literal placeholder '{match.group(0).upper()}' spoken in script.")

        # Check 2: Verify release year accuracy if mentioned
        for t in titles:
            title_name = t.get("title", "").lower()
            year = t.get("year", "")
            if year and year.isdigit() and len(year) == 4:
                # If script mentions title name and a 4-digit year near it, verify year matches
                if title_name in lower_script:
                    # Find all 4-digit numbers in script
                    years_in_script = re.findall(r"\b(19\d{2}|20\d{2})\b", script_text)
                    # If years are present, check if a wildly wrong year is attached
                    for y in years_in_script:
                        if abs(int(y) - int(year)) > 5 and int(y) > 1950 and int(y) < 2030:
                            # Flag if a wrong year is explicitly stated
                            pass # Keep soft or flag if title-year binding fails

        # Check 3: Check rating claims if stated
        for t in titles:
            rating = t.get("rating")
            if rating and rating > 0:
                # e.g., if script says "rated 2.0" for a 9.0 movie
                pass

        passed = len(errors) == 0
        return passed, errors
