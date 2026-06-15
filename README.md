# CAEngine 🚀

> **Turn any GitHub repository into social media content — automatically.**

CAEngine analyzes GitHub repositories, evaluates code quality and seniority level, extracts the most interesting technical insights, and publishes them across your social platforms without manual effort.

---

## What it does

Most developers build great things and never talk about them. CAEngine fixes that.

Point it at any GitHub repo and it will:

1. **Analyze** the codebase — structure, complexity, commit history, and overall seniority signal
2. **Extract** the most shareable insights — architecture decisions, interesting patterns, key features
3. **Generate** platform-optimized content for each network
4. **Publish** automatically across your connected accounts

---

## Supported platforms

| Platform | Status |
|----------|--------|
| 𝕏 (Twitter) | ✅ Live |
| Bluesky | ✅ Live |
| dev.to | ✅ Live |
| LinkedIn | ✅ Live |
| Meta (Instagram/Facebook) | 🔜 Coming soon |

---

## Tech stack

- **Python** — core engine
- **GitHub API** — repository analysis and data extraction
- **LLM integration** — content generation and insight extraction
- Platform APIs — X, Bluesky, dev.to, LinkedIn

---

## Use cases

- **Developers** who want to build an audience without writing posts manually
- **Open source maintainers** who want more visibility for their projects
- **Tech teams** looking to showcase their engineering culture on social media
- **Freelancers** building a personal brand through their work

---

## Getting started

```bash
git clone https://github.com/devvitto/caengine
cd caengine
pip install -r requirements.txt
```

Configure your API keys in `.env`:

```env
GITHUB_TOKEN=your_github_token
TWITTER_API_KEY=your_key
BLUESKY_HANDLE=your_handle
DEVTO_API_KEY=your_key
LINKEDIN_TOKEN=your_token
```

Run it:

```bash
python main.py --repo https://github.com/user/repo
```

---

## Example output

Given a repo, CAEngine might generate:

**For X/Twitter:**
> "Just analyzed this Node.js REST API — clean separation of concerns, solid error handling, and a smart use of middleware chains. Here's what stood out 🧵"

**For dev.to:**
> A full breakdown article with code snippets, architecture insights, and lessons learned.

**For LinkedIn:**
> A professional post highlighting the engineering decisions and their business impact.

---

## Roadmap

- [x] GitHub repository analysis
- [x] Seniority scoring system
- [x] Multi-platform publishing
- [ ] Meta (Instagram / Facebook) support
- [ ] Scheduled publishing
- [ ] Web UI / dashboard
- [ ] Repo comparison mode

---

## Author

Built by [Vitto](https://www.linkedin.com/in/devvitto/) — Full Stack Developer & Automation Specialist based in Argentina.

---

*CAEngine is part of a broader set of developer tools I'm building. If you're interested in automating your own workflows, feel free to reach out.*