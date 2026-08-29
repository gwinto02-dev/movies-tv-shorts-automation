# Daily Movies & TV Shorts — YouTube Automation (TMDB)

A fully automated, **$0-budget** daily movie/TV recommendation system built for YouTube Shorts. Powered by TMDB, Edge-TTS, Pexels/Pixabay stock b-roll, Gemini LLM (with robust offline template fallback), and GitHub Actions.

---

## 🌟 Key Features

1. **$0-Budget Architecture**:
   - Uses free TMDB API key for title metadata, posters, and backdrop artwork.
   - Uses free Microsoft Edge TTS (`edge-tts`) for high-quality neural narration.
   - Uses Pexels & Pixabay Video APIs for royalty-free commercial stock b-roll.
   - Free GitHub Actions scheduled runner (public repository).
   - Negligible/Free LLM usage via Gemini API, with a rich offline fallback template pool.

2. **Copyright & Visual Safety Guardrails**:
   - Uses official TMDB poster and backdrop images per title (never movie scene footage or official trailers).
   - Supplements with generic genre/mood stock video clips (e.g. dark alley, space starfield, crowd reaction).
   - Tracks source and license metadata for every visual asset.

3. **Strict YouTube Upload Guardrails**:
   - **Uploads default to Private** (`privacyStatus = "private"`).
   - **Explicitly sets Made for Kids to No** (`selfDeclaredMadeForKids: false`).
   - Defined YouTube OAuth scopes: `youtube.upload` and `youtube.readonly`.

4. **Sibling Project Production Bug Fixes (Built-in)**:
   - **Title Cooldown & Self-Blocking Prevention**: 30-day title cooldown tracked at selection time. Filters out entries written at or after `run_start_time` so a run never flags its own selections as a cooldown violation.
   - **Underrated Trio Popularity Floor**: Requires `vote_count >= 100` and `popularity >= 15.0` to avoid mislabeling popular movies.
   - **Fact Audit & Natural Script QA**: Injects TMDB facts into LLM prompt context, audits claims post-generation, rejects literal "N/A" placeholders, and detects consecutive duplicate words.
   - **Retention Hooks & CTA Variety**: Structural hook styles (`question`, `bold_claim`, `scenario`, `you_wont_believe`, `direct_statement`) and rotating CTA pools (`direct_ask`, `utility_framed`, `series_continuation`).
   - **Keyword Sync & Stopword Stripping**: Strips stopwords and trailing `Season N` / episode numbers (handling dashed, colon, and non-dashed forms).
   - **LLM Circuit Breaker**: Trips on 1 failure and switches to offline template engine for rest of run.
   - **Consolidated Supervisor QA Gate**: 12 itemized checks. ANY single failure strictly blocks upload.
   - **Content-Aware JSON Merge**: Prevents Git merge conflicts on history logs in GitHub Actions.

---

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.10+
- FFmpeg installed (`sudo apt-get install ffmpeg` or via package manager)

### 2. Installation
```bash
git clone <your-repo-url>
cd "YouTube Automation TMDB"
pip install -r requirements.txt
```

### 3. Setup Environment Variables (`.env`)
Create a `.env` file in the root directory:
```env
TMDB_API_KEY=your_free_tmdb_api_key
GEMINI_API_KEY=your_gemini_api_key_optional
PEXELS_API_KEY=your_pexels_api_key_optional
PIXABAY_API_KEY=your_pixabay_api_key_optional
```

### 4. YouTube OAuth One-Time Authorization
1. Download `client_secret.json` from Google Cloud Console.
2. Run the setup script:
   ```bash
   python scripts/setup_youtube_oauth.py
   ```
3. Copy the content of `token.json` into a GitHub Repository Secret named `YOUTUBE_TOKEN_DATA`.

### 5. Running the Pipeline
- **Dry-Run (Simulate generation without YouTube upload)**:
  ```bash
  python scripts/run_pipeline.py --dry-run
  ```
- **Live Run**:
  ```bash
  python scripts/run_pipeline.py
  ```

### 6. Running Unit & Regression Tests
```bash
python -m pytest tests/ -v
```

---

## 🛠️ Repository Structure

```
├── .github/workflows/daily_shorts.yml # GHA workflow with state commit-back
├── config/settings.py                 # Settings and environment loader
├── data/                              # Committed persistent state JSON files
├── src/
│   ├── content/                       # TMDB client, concept selector, stock video
│   ├── script/                        # Generator, templates, fact checker
│   ├── audio/                         # Edge-TTS engine and timing parser
│   ├── video/                         # 9:16 compositor and Karaoke subtitles
│   ├── qa/                            # Supervisor QA Gate (12 checks) and Circuit Breaker
│   ├── youtube/                       # OAuth and Private upload guardrail
│   ├── notify/                        # HTML daily review email generator
│   └── utils/                         # History manager & stopword text processing
├── scripts/                           # CLI entry points and JSON merge script
└── tests/                             # Unit & regression test suite
```

---

## 📄 License

This project is licensed under the MIT License. Visual assets are sourced via TMDB API and Pexels/Pixabay Free Commercial Licenses.
