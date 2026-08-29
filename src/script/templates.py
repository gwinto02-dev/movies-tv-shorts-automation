import random
import logging
from typing import List, Dict, Any, Tuple
from src.utils.history_manager import HistoryManager

logger = logging.getLogger(__name__)

HOOK_POOL = [
    {
        "style": "question",
        "template": "Looking for your next movie binge? Here are 3 incredible films you need to watch right now."
    },
    {
        "style": "question",
        "template": "What happens when cinema gets so intense you can't look away? Let's break down 3 top recommendations."
    },
    {
        "style": "bold_claim",
        "template": "These 3 movies are absolute masterpieces that will keep you glued to your screen."
    },
    {
        "style": "bold_claim",
        "template": "If you consider yourself a true film fan, these 3 titles belong at the very top of your watchlist."
    },
    {
        "style": "scenario",
        "template": "Imagine starting a movie so gripping that midnight turns into 3 AM before you even realize it."
    },
    {
        "style": "you_wont_believe",
        "template": "You won't believe how good these 3 movies are until you stream them yourself."
    },
    {
        "style": "you_wont_believe",
        "template": "You won't believe these 3 hidden gems flew under the radar for so long."
    },
    {
        "style": "direct_statement",
        "template": "Here are 3 incredible movies you definitely shouldn't sleep on tonight."
    }
]

CTA_POOL = [
    {
        "style": "direct_ask",
        "templates": [
            "Which of these 3 are you watching first? Let me know in the comments!",
            "Have you seen any of these? Drop your favorite in the comments!"
        ]
    },
    {
        "style": "utility_framed",
        "templates": [
            "Save this video right now so you don't forget these for movie night!",
            "Bookmark this list for your next weekend streaming marathon!"
        ]
    },
    {
        "style": "series_continuation",
        "templates": [
            "Subscribe for daily top-tier movie and TV recommendations!",
            "Hit subscribe so you never run out of incredible movies to watch!"
        ]
    }
]

class TemplateEngine:
    def __init__(self, history_manager: HistoryManager):
        self.history = history_manager

    def select_fresh_hook(self, recent_hooks: List[str]) -> Dict[str, str]:
        """Proactively selects a hook that hasn't been used recently."""
        available = [h for h in HOOK_POOL if h["template"] not in recent_hooks]
        if not available:
            available = HOOK_POOL
        return random.choice(available)

    def select_fresh_cta(self, recent_cta_styles: List[str]) -> Tuple[str, str]:
        """Selects a CTA style that avoids recent consecutive usage."""
        available_styles = [c for c in CTA_POOL if c["style"] not in recent_cta_styles]
        if not available_styles:
            available_styles = CTA_POOL
        
        chosen_group = random.choice(available_styles)
        style = chosen_group["style"]
        text = random.choice(chosen_group["templates"])
        return style, text

    def generate_fallback_script(
        self,
        concept_type: str,
        titles: List[Dict[str, Any]],
        recent_hooks: List[str],
        recent_cta_styles: List[str]
    ) -> Dict[str, Any]:
        """Generates a complete rule-based script using high-quality templates."""
        hook_obj = self.select_fresh_hook(recent_hooks)
        hook_text = hook_obj["template"]
        
        cta_style, cta_text = self.select_fresh_cta(recent_cta_styles)
        
        segments = []
        full_speech_parts = [hook_text]

        for idx, t in enumerate(titles, 1):
            title_name = t.get("title")
            year = f"from {t.get('year')}" if t.get('year') else "release"
            genres = ", ".join(t.get('genres', [])[:2]) or "drama"
            overview = t.get("overview", "")
            
            # Format clean overview snippet without placeholders
            snippet = overview[:120].rsplit(" ", 1)[0] if len(overview) > 120 else overview
            if not snippet or snippet == "N/A":
                snippet = f"A thrilling {genres} story that keeps you guessing."
            
            seg_text = f"First up is {title_name}, a {genres} film {year}. {snippet}."
            if idx == 2:
                seg_text = f"Next up, {title_name}. A gripping {genres} choice {year}. {snippet}."
            elif idx == 3:
                seg_text = f"And finally, {title_name}. An unforgettable {genres} title {year}. {snippet}."

            segments.append({
                "index": idx,
                "tmdb_id": t.get("tmdb_id"),
                "title": title_name,
                "text": seg_text
            })
            full_speech_parts.append(seg_text)

        full_speech_parts.append(cta_text)
        full_text = " ".join(full_speech_parts)

        # Video Title generation with concept signal + variety
        video_title = self.generate_video_title(concept_type, titles)

        return {
            "concept_type": concept_type,
            "hook": hook_text,
            "hook_style": hook_obj["style"],
            "segments": segments,
            "cta_style": cta_style,
            "cta_text": cta_text,
            "full_text": full_text,
            "video_title": video_title
        }

    def generate_video_title(self, concept_type: str, titles: List[Dict[str, Any]]) -> str:
        """Generates a YouTube Short title signaling concept type with varied phrasing."""
        t_names = [t.get("title") for t in titles]
        joined = ", ".join(t_names[:2])
        
        patterns = [
            f"3 Must-Watch Movies You Need to Stream Right Now! ({concept_type})",
            f"Stop Scrolling! 3 Incredible Movies To Watch Tonight ({concept_type})",
            f"3 Movies That Will Keep You Hooked Until The End! ({joined})",
            f"Top 3 Movie Recommendations You Can't Miss ({concept_type})"
        ]
        return random.choice(patterns)

Tuple_CTA = tuple[str, str]
