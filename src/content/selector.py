import logging
import random
from datetime import datetime, timezone
from typing import List, Dict, Any, Tuple
from config.settings import settings
from src.content.tmdb_client import TMDBClient
from src.utils.history_manager import HistoryManager

logger = logging.getLogger(__name__)

CONCEPT_TYPES = [
    "Genre-Diverse Trio",
    "Underrated Trio",
    "Trending Trio",
    "Upcoming Spotlight Trio",
    "Decade Spotlight Trio"
]

class ContentSelector:
    def __init__(self, tmdb_client: TMDBClient, history_manager: HistoryManager):
        self.tmdb = tmdb_client
        self.history = history_manager

    def select_daily_content(self, run_start_time: str) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Selects a concept type and 3 titles.
        Records history immediately at selection time.
        """
        concept_type = self._pick_concept_type()
        logger.info(f"Selected concept type: {concept_type}")

        candidates = self._fetch_candidates_for_concept(concept_type)
        
        # Filter out titles on 30-day cooldown
        valid_candidates = []
        for c in candidates:
            if not self.history.is_title_on_cooldown(
                tmdb_id=c["tmdb_id"],
                title=c["title"],
                run_start_time=run_start_time
            ):
                valid_candidates.append(c)

        if len(valid_candidates) < 3:
            logger.warning(f"Not enough non-cooldown candidates for {concept_type} ({len(valid_candidates)} found). Expanding search pool with available candidates.")
            for c in candidates:
                if c["tmdb_id"] not in [vc["tmdb_id"] for vc in valid_candidates]:
                    valid_candidates.append(c)
                    if len(valid_candidates) >= 3:
                        break

        # Select 3 titles based on concept rules
        selected_titles = self._filter_trio_for_concept(concept_type, valid_candidates)
        if len(selected_titles) < 3:
            selected_titles = candidates[:3]

        # RECORD SELECTIONS IMMEDIATELY AT SELECTION TIME
        self.history.record_title_selections(selected_titles, concept_type, run_start_time)
        self.history.record_concept_selection(concept_type)

        return concept_type, selected_titles

    def _pick_concept_type(self) -> str:
        available = [c for c in CONCEPT_TYPES if not self.history.is_concept_on_cooldown(c)]
        if not available:
            logger.info("All concept types are on cooldown. Resetting concept selection to random.")
            available = CONCEPT_TYPES
        return random.choice(available)

    def _fetch_candidates_for_concept(self, concept_type: str) -> List[Dict[str, Any]]:
        if concept_type == "Genre-Diverse Trio":
            return self.tmdb.get_popular(media_type="movie")
        elif concept_type == "Underrated Trio":
            candidates = self.tmdb.get_top_rated(media_type="movie")
            # Apply absolute popularity floor to avoid calling mainstream movies underrated
            return [
                c for c in candidates 
                if c.get("vote_count", 0) >= settings.UNDERRATED_MIN_VOTE_COUNT
                and c.get("popularity", 0) >= settings.UNDERRATED_MIN_POPULARITY
            ]
        elif concept_type == "Trending Trio":
            return self.tmdb.get_trending(media_type="movie")
        elif concept_type == "Upcoming Spotlight Trio":
            return self.tmdb.get_upcoming_or_now_playing()
        elif concept_type == "Decade Spotlight Trio":
            return self.tmdb.get_popular(media_type="movie")
        else:
            return self.tmdb.get_trending()

    def _filter_trio_for_concept(
        self,
        concept_type: str,
        candidates: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        if concept_type == "Genre-Diverse Trio":
            selected = []
            used_genres = set()
            for c in candidates:
                c_genres = set(c.get("genres", []))
                if not used_genres.intersection(c_genres):
                    selected.append(c)
                    used_genres.update(c_genres)
                    if len(selected) == 3:
                        break
            if len(selected) < 3:
                # Fill remaining if strict 0 overlap isn't fully achievable
                for c in candidates:
                    if c not in selected:
                        selected.append(c)
                        if len(selected) == 3:
                            break
            return selected[:3]

        elif concept_type == "Decade Spotlight Trio":
            decades = ["1990s", "2000s", "2010s"]
            target_decade = random.choice(decades)
            start_year = int(target_decade[:4])
            end_year = start_year + 9

            decade_candidates = [
                c for c in candidates
                if c.get("year").isdigit() and start_year <= int(c.get("year")) <= end_year
            ]
            if len(decade_candidates) >= 3:
                return random.sample(decade_candidates, 3)
            return candidates[:3]

        else:
            return candidates[:3]
