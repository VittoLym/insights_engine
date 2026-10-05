# CAEngine (insights_engine)

Analyzes a GitHub repository, finds the code that shows real engineering skill (transactions, idempotency, event-driven messaging, auth guards, caching) and turns it into ready-to-publish content: a LinkedIn post, an X thread, a code screenshot and an architecture diagram.

> **Status:** personal project, work in progress. Content generation works end to end. Publishing modules for X, Bluesky, dev.to and LinkedIn are implemented but **disabled by default** (the calls are commented out in `main.py`).

## How it works

1. **Scan** the target repository and rank its files by relevance (`repo_scanner.py`).
2. **Audit seniority**: assigns a rank and a score based on the patterns found.
3. **Detect concepts** from five categories: concurrency, resilience, event-driven patterns, security and performance.
4. **Extract the best snippet** with local heuristics, falling back to an LLM when the result is weak.
5. **Generate content** with LLMs (Gemini and Groq): a LinkedIn post and an X thread.
6. **Render visuals**: a code image (Ray.so through Playwright) and an architecture diagram (Mermaid).
7. **Save a media kit** per topic under `content_factory/`.

Output example:

```
content_factory/
└── Kit_1_serie_1_real-world_concurrency_2026-06-09/
    ├── linkedin.md
    ├── x_thread.md
    ├── 1_authority_shot.png
    └── 2_architecture.png
```

## Tech stack

- Python
- Google Gemini (`google-genai`) and Groq for content generation
- Playwright for rendering code screenshots
- Platform APIs: X, Bluesky, dev.to, LinkedIn (disabled by default)

## Getting started

```bash
git clone https://github.com/VittoLym/insights_engine.git
cd insights_engine
python -m venv .venv
.venv\Scripts\activate          # Windows (use source .venv/bin/activate on Linux/macOS)
pip install -r requirements.txt
playwright install chromium
cp .env.example .env            # then fill in your keys
```

Set the repository to analyze in `main.py` (the `SOURCE` variable at the bottom of the file), then run:

```bash
python main.py
```

> The target repository is currently hardcoded. Accepting it as a command-line argument is on the roadmap.

## Configuration

Copy `.env.example` to `.env`. At minimum you need `GEMINI_API_KEY` and `GROQ_API_KEY` to generate content. The X, Bluesky, LinkedIn and dev.to variables are only needed if you enable publishing.

## Enabling publishing

In the `__main__` block of `main.py`, the publish calls are commented out. Uncomment only the platforms you have configured:

```python
# publish_linkedin(linked_post, [pngPath])
# publish_thread_bluesky(x_thread)
# publish_thread_x(x_thread)
# publish_devto(...)
```

Review the generated content in `content_factory/` before you publish anything.

## Privacy note

To render visuals, code snippets are sent to third-party services: Ray.so (code image) and mermaid.ink (diagram). Do not run the tool on private or confidential repositories unless you are comfortable with that.

## Roadmap

- [ ] Accept the target repository as a CLI argument
- [ ] Split `main.py` into modules (scanner, content, media, publishers)
- [ ] Remove unused code left over from earlier iterations
- [ ] Unit tests for scoring and snippet extraction
- [ ] Meta (Instagram / Facebook) support
- [ ] Scheduled publishing

## How I used AI in this project

- **Tools used:** [TODO: e.g. Claude, Gemini, Copilot]
- **What I delegated:** [TODO]
- **What I decided and wrote myself:** [TODO]
- **How I reviewed AI output:** [TODO]

## Author

**Alexander Assón**, Backend / Full Stack Engineer, Mendoza, Argentina.
[LinkedIn](https://linkedin.com/in/devvitto) · [GitHub](https://github.com/VittoLym)