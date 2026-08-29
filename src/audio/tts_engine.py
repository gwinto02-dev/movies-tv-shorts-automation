import asyncio
import os
import re
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from config.settings import settings

logger = logging.getLogger(__name__)

class TTSEngine:
    def __init__(self, voice_name: Optional[str] = None):
        self.voice_name = voice_name or settings.VOICE_NAME

    def generate_narration(
        self,
        script_text: str,
        output_mp3_path: Path
    ) -> Tuple[Path, List[Dict[str, Any]]]:
        """
        Generates audio file and word-level timings.
        Returns (audio_file_path, list_of_word_timing_dicts).
        """
        try:
            return asyncio.run(self._generate_edge_tts(script_text, output_mp3_path))
        except Exception as e:
            logger.warning(f"Edge-TTS generation failed ({e}). Using estimated fallback audio.")
            return self._generate_fallback_audio(script_text, output_mp3_path)

    async def _generate_edge_tts(
        self,
        text: str,
        output_mp3_path: Path
    ) -> Tuple[Path, List[Dict[str, Any]]]:
        import edge_tts

        communicate = edge_tts.Communicate(text, self.voice_name)
        word_events = []

        with open(output_mp3_path, "wb") as audio_file:
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_file.write(chunk["data"])
                elif chunk["type"] == "WordBoundary":
                    start_sec = chunk["offset"] / 10_000_000.0
                    duration_sec = chunk["duration"] / 10_000_000.0
                    end_sec = start_sec + duration_sec
                    word_events.append({
                        "word": chunk["text"],
                        "start": round(start_sec, 3),
                        "end": round(end_sec, 3)
                    })

        # Fallback word timing estimation if WordBoundary events were not emitted
        if not word_events and text:
            words = re.findall(r"\S+", text)
            sec_per_word = 0.4
            curr_time = 0.0
            for w in words:
                word_events.append({
                    "word": w,
                    "start": round(curr_time, 3),
                    "end": round(curr_time + sec_per_word, 3)
                })
                curr_time += sec_per_word

        return output_mp3_path, word_events

    def _generate_fallback_audio(
        self,
        text: str,
        output_mp3_path: Path
    ) -> Tuple[Path, List[Dict[str, Any]]]:
        """Generates fallback timing data and silence audio file when TTS fails or offline."""
        words = re.findall(r"\S+", text)
        word_events = []

        sec_per_word = 0.4  # ~150 WPM
        curr_time = 0.0

        for w in words:
            start_sec = curr_time
            end_sec = curr_time + sec_per_word
            word_events.append({
                "word": w,
                "start": round(start_sec, 3),
                "end": round(end_sec, 3)
            })
            curr_time = end_sec

        total_duration = max(curr_time, 1.0)
        
        # Generate minimal WAV or MP3 file at output_mp3_path
        try:
            import wave
            import struct
            sample_rate = 22050
            num_samples = int(sample_rate * total_duration)
            output_mp3_path.parent.mkdir(parents=True, exist_ok=True)
            with wave.open(str(output_mp3_path), "w") as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(sample_rate)
                for _ in range(num_samples):
                    wav_file.writeframesraw(struct.pack("<h", 0))
            return output_mp3_path, word_events
        except Exception as ex:
            logger.error(f"Failed to generate fallback wav file: {ex}")
            output_mp3_path.write_bytes(b"\x00" * 1000)
            return output_mp3_path, word_events

Tuple_Path_WordEvents = Tuple[Path, List[Dict[str, Any]]]
