# AGENTS.md

Guidance for AI coding agents working in this repository.

## Project

CAEngine (`insights_engine`) analyzes a GitHub repository, finds the code that shows real engineering skill and turns it into a media kit: a LinkedIn post, an X thread, a code image and an architecture diagram. It is a personal project in progress. Content generation works end to end.

## Layout

- `main.py`: entry point and most of the logic (snippet extraction, scoring, media generation, kit saving, LinkedIn publishing). The `__main__` block at the bottom drives the pipeline.
- `repo_scanner.py`: scans the target repository, ranks files, `audit_seniority`.
- `gemini_adp.py`: LLM calls (Gemini and Groq): post refinement, X thread, visual prompts, snippet extraction fallback.
- `x_publisher.py`, `bluesky_publisher.py`, `dev_publisher.py`: publishers. Each only reads its credentials with `os.getenv`.
- `content_factory/`: generated output. Git-ignored.

## Commands

```bash
python -m venv venv
pip install -r requirements.txt
playwright install chromium
cp .env.example .env        # then fill in the keys
python main.py
```

The target repository is the `SOURCE` variable in the `__main__` block of `main.py`. There is no test suite yet.

## Rules

- Never commit `.env` or any key. Read credentials only with `os.getenv`, and never print or log them.
- Publishing is disabled by default: the `publish_*` calls in `main.py` are commented out. Do not enable them, and do not add code that publishes automatically, unless the maintainer asks for it.
- Do not run the tool against private repositories: snippets are sent to third-party services (Ray.so for the code image, mermaid.ink for the diagram).
- Keep `requirements.txt` pinned and in sync when adding an external import.
- Do not commit generated output (`content_factory/`, `carousels.json`, `linkedin.md`, `x_thread.md`, `visual_strategy.txt`).
- Existing comments and docstrings are mostly in Spanish. New documentation and READMEs are in English.
- Commit messages follow Conventional Commits, in English.

## Known gaps

- `main.py` mixes several responsibilities and needs to be split into modules.
- The target repository is hardcoded.
- Some code left over from earlier iterations is still there.
- No unit tests. Scoring and snippet extraction are the first candidates.

## How AI is used here

The maintainer did the research and the design, created every API account and key, and validated the code. AI assistants wrote the repetitive parts. Agents must not change scoring heuristics or generated-content prompts without the maintainer reviewing the result.