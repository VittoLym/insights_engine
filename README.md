Este README está diseñado para posicionar tu herramienta no como un simple script, sino como un **producto de ingeniería** (un "AI Content Engine"). Está redactado en inglés para atraer a la comunidad global y resaltar tu perfil de Arquitecto.

---

# 🚀 AI Content Engine for Developers (v2.0)

**From Clean Code to Authority-Driven Content in seconds.**

This is a high-performance content pipeline designed for Software Architects and Senior Developers. It audits your local repositories, identifies high-level technical patterns (Concurrency, Resilience, Security), and generates a full **Media Kit** (LinkedIn posts, X threads, and Visual Strategies) in English.



## 🧠 The Philosophy
Most AI-generated content sounds like "marketing fluff." This engine is different. It uses a **Zero-Footprint Utility-First** strategy:
* **Code-First:** It extracts real snippets from your repo to ground the content in reality.
* **Honesty-Driven:** It highlights trade-offs and technical debt, not just "perfect systems."
* **Senior-Tone:** It uses a pragmatic, cynical, and technical voice that resonates with Lead Engineers.

---

## 🛠️ Tech Stack
* **Language:** Python 3.x
* **LLM:** Google Gemini 1.5 Flash (via `google-genai`)
* **Database Integration:** Prisma (Detection Layer)
* **Architecture:** Modular Pipeline (Extraction -> Scoring -> Generation -> File System)

---

## 🚀 Features

### 1. Technical Pattern Detection (`CONCEPT_MAP`)
The engine doesn't just "read text." It looks for **Architectural Signals**:
* **Concurrency:** Transactions, Locks, Atomic Operations.
* **Resilience:** Retry strategies, Timeouts, Circuit Breakers, Idempotency.
* **Security:** JWT Rotation, Session Management, Audit Logs.

### 2. Automated Media Kits
For every detected pattern, the system creates a folder containing:
* `linkedin.md`: A deep-dive post focused on trade-offs and engineering decisions.
* `x_thread.md`: A punchy, 5-tweet technical thread with high-impact hooks.
* `visual_strategy.txt`: Instructions for generating diagrams (Excalidraw/Mermaid) and code shots (Ray.so).

### 3. Seniority Audit
The script runs a heuristic audit on your repo and ranks it (Junior / Mid / Senior / Architect) based on the presence of advanced patterns like Event-Driven Architecture or Financial Precision.

---

## 📂 Project Structure
```text
/content_factory               # Automated output directory
  /Kit_1_security_deep-dives   # Targeted content folder
    - linkedin.md              # Ready to post
    - x_thread.md              # Thread-ready
    - visual_strategy.txt      # Blueprint for images
```

---

## ⚙️ Setup & Usage

1. **Clone and Install:**
   ```bash
   pip install google-genai
   ```

2. **Configure API Key:**
   Set your `GEMINI_API_KEY` in your environment variables.

3. **Run the Engine:**
   ```bash
   python main.py
   ```

---

## 📈 Roadmap
- [x] Automated File System (Multi-kit folders)
- [x] Multi-platform generation (LinkedIn & X)
- [ ] **Mermaid.js Integration:** Auto-generate diagram code.
- [ ] **CLI Tool:** A proper Command Line Interface for faster scanning.
- [ ] **Scheduler:** Automated posting via Buffer/Hootsuite APIs.

---

## 🤝 Contributing
Contributions are welcome! If you have ideas for new `CONCEPT_MAP` signals or better "Senior-tone" prompts, feel free to open a PR.

---

### 💬 "Code is documentation. This engine makes it your brand."

---
*Developed by [Vitto]* 🚀
