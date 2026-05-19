# Swing Trading Academy — Project Context

## Hard Rules for Claude Code

- **Never use the Agent tool.** Do all work directly in the main conversation. This includes wiki rebuilds, file analysis, and any large context tasks. Spawning agents makes API calls that incur costs outside the subscription.
- The only thing allowed to use the Anthropic API key is the Streamlit app (`analyst-brains/app.py`) via Streamlit Cloud secrets.

---

## What This Is

A personal knowledge management system for a swing trading educator. It does two things:

1. **Video-to-Tutorial Pipeline** — converts raw lecture MP4/MKV files into structured markdown tutorials
2. **Investment Research** — extracts and organizes macro/equity research into structured signal files

---

## Trading Strategy (Phil's Rules)

**Long-term investing:**
- Hold 5-10 years, monthly TF, logarithmic chart
- 5-10% position size, add on dips, exit if thesis breaks

**Swing trading (core workflow):**
- Monthly TF + logarithmic chart only
- Entry sequence: monthly support → daily confirmation candle (BBOS/engulfing) → LEAP options
- LEAPs: ATM strike, 13-14 months minimum expiry
- Stop: below monthly support. Target: next monthly resistance
- Macro research = watchlist input only, not trade trigger

**Day trading (UK100):**
- London open breakouts only
- 1% risk per trade, 1:2 R/R minimum

---

## Project Structure

```
swing-trading-academy/
├── pipeline/               # Python pipeline scripts
│   ├── run_pipeline.py     # Orchestrator (--steps 1,2,3,4)
│   ├── config.py           # Paths, model settings
│   ├── step1_extract_audio.py
│   ├── step2_transcribe.py
│   ├── step3_detect_sections.py   # Claude API
│   └── step4_generate_tutorials.py # Claude API
├── output/
│   ├── audio/              # Extracted WAV files
│   ├── transcripts/        # JSON + TXT per video
│   ├── sections/           # Detected sections JSON per video
│   ├── tutorials/          # Generated markdown (one dir per video)
│   └── research_picks/     # Investment signal output files
├── investment_research/    # Raw research source docs (PDFs + markdown)
│   ├── index.md
│   ├── watchlist.md
│   ├── marlin-capital/
│   └── lyn-alden/
├── ta/                     # Technical Analysis source videos
├── options/                # Options Strategy source videos
├── trading_strategy/
├── trading_confirmation/
├── trading_psychology/
├── risk_management/
├── investing/
├── phill_calls/            # Academy trader call recordings
└── phil-live-sessions/     # Live trading session recordings
```

---

## Pipeline Workflow

**Step 1** — ffmpeg extracts audio from MP4/MKV → 16kHz mono WAV → `output/audio/`

**Step 2** — OpenAI Whisper (medium model, local) transcribes WAV → JSON (with word-level timestamps) + TXT → `output/transcripts/`

**Step 3** — Claude API reads transcript → detects logical topic sections → JSON array with title, start_time, end_time, summary, key_concepts → `output/sections/`

**Step 4** — Claude API reads each section's transcript slice → generates polished markdown tutorial with YAML front-matter + review questions → `output/tutorials/<video-slug>/`

**Steps 3 and 4 are handled directly by Claude Code** (not just the pipeline scripts). When asked to process a video's sections or generate tutorials, do it directly using the Claude API or by running the pipeline scripts.

### Tutorial Output Format

Each tutorial file:
```markdown
---
title: "Section Title"
source: "Video Name"
section: 1
start_time: "00:00:00"
end_time: "00:09:20"
---

# Section Title

**Summary:** 2-3 sentences.

**Key Concepts:** comma-separated list

---

[Polished instructional prose with ## subheadings, **bold** key terms, bullet lists]

## Review Questions

1. ...
```

Each video directory also gets an `index.md` with a table linking all sections.

---

## Investment Research Workflow

**Input:** PDFs or markdown in `investment_research/` (Lyn Alden, Marlin Capital, Luke Gromen, Doomberg, etc.)

**Output:** Structured signal files in `output/research_picks/`

### Research Pick Format

```markdown
## Video/Report Context
- Creator, date, main thesis, confidence level

## Investment Themes
3-5 themes with: direction, timeline, LEAP fit (yes/no), evidence

## Sector & Asset Implications
Table: sector/asset | direction | confidence | tickers

## Watchlist
Ticker | entry zone | stop | target | R/R | setup status
```

**Regional files:** `latin-america.md`, `singapore-southeast-asia.md`, `china.md`, `other-em.md`, `canada.md`
**Creator files:** `luke-gromen/`, `doomberg/` — one main file + one watchlist file per report

---

## Key Technical Details

- **Python 3.13**, `.venv/` virtual environment
- **Claude model in pipeline:** `claude-sonnet-4-20250514`
- **Whisper model:** `medium` (runs locally)
- **API key:** stored in `.env` as `ANTHROPIC_API_KEY`
- **Run pipeline:** `source .venv/bin/activate && python pipeline/run_pipeline.py --steps 3,4`

---

## Custom Agent

`.claude/agents/youtube-macro-signal-extractor.md` — extracts investment signals from macro YouTube videos (yt-dlp for captions, outputs structured research pick format). Calibrated for monthly TF swing trader using LEAPs.

---

## What Claude Code Does Here

1. Run or modify pipeline scripts (steps 3-4 most commonly)
2. Generate research pick files from investment research sources
3. Analyze open/potential trades against Phil's strategy rules
4. Maintain trade tracking (entries, targets, stops, R/R)
5. Help structure and edit tutorial output
