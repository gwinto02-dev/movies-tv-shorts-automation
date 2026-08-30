import re
import json
import logging
from typing import List, Dict, Any, Tuple, Optional
from config.settings import settings
from src.qa.circuit_breaker import circuit_breaker
from src.script.fact_checker import FactChecker
from src.script.templates import TemplateEngine
from src.utils.history_manager import HistoryManager

logger = logging.getLogger(__name__)

class ScriptGenerator:
    def __init__(self, history_manager: HistoryManager):
        self.history = history_manager
        self.templates = TemplateEngine(history_manager)

    def generate_script(
        self,
        concept_type: str,
        titles: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generates script using LLM if available, otherwise fallback template engine.
        Performs natural script QA and fact-checking audits.
        """
        recent_hooks = self.history.get_recent_hooks(limit=10)
        recent_scripts = self.history.get_recent_scripts(limit=10)
        recent_ctas = self.history.get_recent_ctas(limit=5)
        recent_video_titles = self.history.get_recent_video_titles(limit=10)

        fact_context = FactChecker.build_fact_context(titles)

        script_data = None
        max_attempts = 2
        
        # Try LLM generation if key is present and circuit breaker isn't tripped
        if settings.GEMINI_API_KEY and circuit_breaker.can_execute():
            for attempt in range(1, max_attempts + 1):
                try:
                    logger.info(f"Attempting Gemini LLM script generation (Attempt {attempt}/{max_attempts})...")
                    llm_script = self._generate_with_gemini(concept_type, titles, fact_context, recent_hooks)
                    
                    # Validate natural script QA
                    qa_ok, qa_reasons = self.check_natural_script_qa(llm_script["full_text"], concept_type, titles)
                    fact_ok, fact_reasons = FactChecker.audit_script_facts(llm_script["full_text"], titles)

                    if qa_ok and fact_ok:
                        circuit_breaker.record_success()
                        script_data = llm_script
                        break
                    else:
                        logger.warning(f"LLM script QA/Fact audit failed: QA={qa_reasons}, Fact={fact_reasons}")
                except Exception as e:
                    logger.error(f"Gemini LLM generation exception: {e}")
                    circuit_breaker.record_failure(str(e))
                    break  # Circuit breaker tripped, fall back immediately

        # Fallback to rule-based template generator if LLM was skipped or failed
        if not script_data:
            logger.info("Using Fallback Template Engine for script generation.")
            script_data = self.templates.generate_fallback_script(
                concept_type=concept_type,
                titles=titles,
                recent_hooks=recent_hooks,
                recent_cta_styles=recent_ctas,
                recent_full_texts=recent_scripts,
                recent_video_titles=recent_video_titles
            )

        # Record CTA usage
        self.history.record_cta_usage(script_data["cta_style"], script_data["cta_text"])
        return script_data

    def _generate_with_gemini(
        self,
        concept_type: str,
        titles: List[Dict[str, Any]],
        fact_context: str,
        recent_hooks: List[str]
    ) -> Dict[str, Any]:
        import google.generativeai as genai
        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel(settings.GEMINI_MODEL_NAME)

        prompt = f"""
You are an expert YouTube Shorts scriptwriter for a Movie/TV recommendation channel.
Your goal is high viewer retention, fast pacing, and strong curiosity-driven hooks.

Concept Type: {concept_type}

FACTS Context (DO NOT alter any ratings, years, or titles):
{fact_context}

REQUIREMENTS:
1. Total spoken duration must be 15 to 45 seconds (approx 75 to 110 words).
2. Start with a curiosity or tension-driven HOOK (question, bold claim, or scenario).
3. Cover each of the 3 titles in 1 snappy sentence per movie.
4. Finish with a clear Call to Action (CTA) asking viewers to comment, save, or subscribe.
5. NEVER say "N/A", "null", or missing data placeholders out loud.
6. NEVER use clichés like "In a world where..." or "Buckle up!".
7. NEVER repeat the same word twice in a row (e.g. "recommendations recommendations").

Return ONLY valid JSON matching this structure:
{{
  "hook": "<hook sentence>",
  "hook_style": "question" | "bold_claim" | "scenario" | "you_wont_believe" | "direct_statement",
  "segments": [
    {{"index": 1, "tmdb_id": <id>, "title": "<title1>", "text": "<sentence for title 1>"}},
    {{"index": 2, "tmdb_id": <id>, "title": "<title2>", "text": "<sentence for title 2>"}},
    {{"index": 3, "tmdb_id": <id>, "title": "<title3>", "text": "<sentence for title 3>"}}
  ],
  "cta_style": "direct_ask" | "utility_framed" | "series_continuation",
  "cta_text": "<CTA sentence>",
  "full_text": "<complete combined narration text>",
  "video_title": "<engaging YouTube Short title>"
}}
"""
        response = model.generate_content(prompt)
        text_resp = response.text.strip()

        # Parse JSON
        if "```json" in text_resp:
            text_resp = text_resp.split("```json")[1].split("```")[0].strip()
        elif "```" in text_resp:
            text_resp = text_resp.split("```")[1].split("```")[0].strip()

        parsed = json.loads(text_resp)
        return parsed

    @staticmethod
    def check_natural_script_qa(
        script_text: str,
        concept_type: str,
        titles: List[Dict[str, Any]]
    ) -> Tuple[bool, List[str]]:
        """
        Validates natural speech quality:
        - No consecutive duplicate words (e.g. "recommendations recommendations")
        - No literal placeholder text ("N/A", "null", "undefined")
        - No banned clichés
        """
        reasons = []
        lower_text = script_text.lower()

        # Check 1: Consecutive duplicate words (e.g. "movie movie", "recommendations recommendations")
        # Match case-insensitive duplicated words separated by whitespace or punctuation
        dup_match = re.search(r"\b([a-zA-Z]{2,})\s+\1\b", lower_text)
        if dup_match:
            reasons.append(f"Natural QA Failure: Consecutive duplicate word detected: '{dup_match.group(0)}'")

        # Check 2: Literal placeholders spoken out loud
        placeholders = ["n/a", "null", "undefined", "unknown year", "none/10"]
        for ph in placeholders:
            if re.search(rf"\b{re.escape(ph)}\b", lower_text):
                reasons.append(f"Natural QA Failure: Placeholder '{ph}' present in script text.")

        # Check 3: Banned clichés
        cliches = ["in a world where", "buckle up", "grab your popcorn", "without further ado"]
        for c in cliches:
            if c in lower_text:
                reasons.append(f"Natural QA Failure: Banned cliché detected: '{c}'")

        passed = len(reasons) == 0
        return passed, reasons
