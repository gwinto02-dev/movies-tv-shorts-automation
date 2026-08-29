import math
import logging
from pathlib import Path
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class SubtitleGenerator:
    @staticmethod
    def format_timestamp_ass(seconds: float) -> str:
        """Converts float seconds to ASS timestamp format H:MM:SS.cs"""
        hrs = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        cs = int(round((seconds - int(seconds)) * 100))
        if cs >= 100:
            cs = 99
        return f"{hrs}:{mins:02d}:{secs:02d}.{cs:02d}"

    @classmethod
    def generate_karaoke_ass(
        cls,
        word_events: List[Dict[str, Any]],
        output_ass_path: Path,
        words_per_line: int = 4
    ) -> Path:
        """
        Generates ASS subtitle file with karaoke word highlight effect.
        Groups words into small lines (3-4 words) for optimal vertical video display.
        """
        if not word_events:
            logger.warning("No word events provided for subtitle generation.")
            return output_ass_path

        header = """[Script Info]
Title: Karaoke Subtitles
ScriptType: v4.00+
WrapStyle: 0
PlayResX: 1080
PlayResY: 1920
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Karaoke,Arial,65,&H00FFFFFF,&H0000FFFF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,5,3,2,50,50,450,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

        events = []
        # Chunk word events into groups of words_per_line
        chunks = [word_events[i:i + words_per_line] for i in range(0, len(word_events), words_per_line)]

        for chunk in chunks:
            chunk_start = chunk[0]["start"]
            chunk_end = chunk[-1]["end"]
            
            # For each word in chunk, emit a frame state where that word is highlighted yellow
            for active_idx, target_word in enumerate(chunk):
                w_start = target_word["start"]
                w_end = target_word["end"]
                
                # Format text: words before active are white, active is yellow, after are white
                formatted_words = []
                for idx, w in enumerate(chunk):
                    w_text = w["word"]
                    if idx == active_idx:
                        # Highlight active word in bright yellow (&H0000FFFF in BGR hex)
                        formatted_words.append(f"{{\\c&H00FFFF&\\fscx110\\fscy110}}{w_text}{{\\r}}")
                    else:
                        formatted_words.append(f"{{\\c&HFFFFFF&}}{w_text}{{\\r}}")

                line_text = " ".join(formatted_words)
                start_str = cls.format_timestamp_ass(w_start)
                end_str = cls.format_timestamp_ass(w_end)
                
                event_line = f"Dialogue: 0,{start_str},{end_str},Karaoke,,0,0,0,,{line_text}"
                events.append(event_line)

        ass_content = header + "\n".join(events) + "\n"
        with open(output_ass_path, "w", encoding="utf-8") as f:
            f.write(ass_content)

        logger.info(f"Generated Karaoke ASS subtitles at {output_ass_path}")
        return output_ass_path
