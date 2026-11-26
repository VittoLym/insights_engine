import re
import os
from google import genai
from dotenv import load_dotenv
import time
from groq import Groq
from llm import generate

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL")
GROQ_MODEL = os.getenv("GROQ_MODEL")
_FENCE_LANG = {"ts": "typescript", "tsx": "tsx", "js": "javascript", "py": "python", "go": "go"}

LINKEDIN_SYSTEM = """You write LinkedIn posts for a backend developer with about 4 years of experience
    who builds real projects and shares what he learns while building them.
    Write in first person about HIS project and HIS decisions. Never call yourself "senior"
    and never mention years of experience.

    GROUNDING (most important rule):
    - Only state what is visible in the code snippet or in the author's note.
    - Do NOT invent numbers, TTLs, latencies, traffic, infrastructure (Redis, replicas, queues, logs),
    algorithms or libraries that are not in the snippet. If you are unsure, leave it out.
    - Do not claim that real incidents or outages happened. Talk about what COULD go wrong in this design.
    - If there is no author's note, do not invent motives: describe the design and its visible trade-offs.

    STYLE:
    - Max 180 words, plain paragraphs. No headers, no emojis, no hashtags, max 3 bullets.
    - No corporate words: robust, scalable, leverage, innovative, game-changer.
    - No dramatic or absolute words (brutal, purely, always, never) unless the code proves it.
    - No preachy openings ("Stop doing X", "Most devs...", "You're doing X wrong").
    - Do not explain what well-known tools (JWT, bcrypt, Prisma) are.
    - Never sound like an AI summary. Talk about decisions, not syntax.

    STRUCTURE:
    1. Hook: one concrete engineering tension you can see in this code.
    2. What the code does and why, in 2-3 sentences, anchored in "my project".
    3. The cost or risk that follows from this design (only what the code implies).
    4. What you would change, or an alternative you are weighing (only if the note or the code suggests one).
    5. One genuine question a developer could actually debate.

    Output ONLY the post text, written in the requested language."""


def extract_snippet_with_ai(content: str, category: str, description: str) -> str | None:
    """Usa IA para extraer el snippet más valioso cuando el regex no alcanza."""
    prompt = f"""...   # tu prompt actual, sin cambios

    CODE:
    {content[:3000]}"""

    text = generate(
        "You extract code snippets exactly as written. Never modify or invent code.",
        prompt,
        max_tokens=800,
        temperature=0.2,   # bajo para que no invente código
        validate=lambda t: len(t.split("\n")) >= 3,
    )
    if not text:
        return None
    # por si el modelo devuelve fences de markdown
    return re.sub(r"^```[a-zA-Z]*\n|\n```$", "", text.strip())

def parse_pro_content(filename):
    """Extrae el insight de mayor score del plan de contenido."""
    if not os.path.exists(filename):
        return None, None, None
        
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()

    try:
        # Regex optimizada para capturar solo el primer bloque
        topic = re.search(r"TOPIC: (.*)", content).group(1).strip()
        body = re.search(r"BODY:\n(.*?)\n\nSNIPPET:", content, re.DOTALL).group(1).strip()
        snippet = re.search(r"SNIPPET:\n(.*?)\nKEY INSIGHT:", content, re.DOTALL).group(1).strip()
        return topic, body, snippet
    except (AttributeError, IndexError):
        return None, None, None

def is_valid_output(text: str) -> bool:
    if not text:
        return False

    text = text.strip()

    banned_patterns = [
        "503",
        "UNAVAILABLE",
        "API Error",
        "limit reached",
        "quota exceeded",
        "internal server error",
        "model is currently experiencing high demand",
        "try again later",
        "rate limit",
        "service unavailable",
        "error occurred",
    ]

    lower_text = text.lower()

    for pattern in banned_patterns:
        if pattern.lower() in lower_text:
            return False

    # Muy corto = probablemente roto
    if len(text) < 80:
        return False

    return True

def refine_post(topic, snippet, file_path, project, author_note=None, language="English"):
    ext = os.path.splitext(file_path)[1].lstrip(".").lower()
    fence = _FENCE_LANG.get(ext, ext)
    user_prompt = f"""Language: {language}
        Project: {project}
        File: {file_path}
        Theme: {topic}
        Author's note (their own words, the only source for motives): {author_note or "(none given)"}

        Code snippet:
        ```{fence}
        {snippet.strip()}
        ```
        Do NOT summarize the code line by line. Focus on the decision behind it and its trade-off.
    """
    return generate(LINKEDIN_SYSTEM, user_prompt, max_tokens=1500,temperature=0.4, validate=is_valid_output)
def generate_x_thread(topic, final_post):
    """Convierte el post en un hilo de X (Twitter) técnico y viral en inglés."""
    system_instruction = (
        "You are a technical ghostwriter for Senior Engineers. "
        "Convert the input into a 5-tweet X thread. "
        "Rules: "
        "1. Tweet 1: High-impact hook (The 'Why' or a strong opinion). "
        "2. Tweets 2-4: The 'Technical Meat' (One key takeaway per tweet). "
        "3. Tweet 5: Closing takeaway and CTA (Call to Action). "
        "4. Tone: Punchy, direct, no emojis unless they add technical context. "
        "5. Language: English."
    )
    
    prompt = f"Topic: {topic}\n\nPost: {final_post}"
    
    try:
        return generate(system_instruction, prompt, max_tokens=1500, validate=is_valid_output)
    except Exception as e:
        print(f"    [❌] Groq error (attempt: {e}")
        return None

def generate_visual_prompts(topic, snippet):
    diagram_concept = "a system architecture flow"
    if "Security" in topic:
        diagram_concept = "a secure token exchange flow between client and server"
    elif "Resilient" in topic:
        diagram_concept = "a service handling a connection timeout with retry logic"
    elif "Concurrency" in topic:
        diagram_concept = "two concurrent database transactions with a lock mechanism"

    return f"""
        🎨 **VISUAL STRATEGY: {topic.upper()}**

        1️⃣ **The Authority Shot (Code)**:
        - Tool: Ray.so | Theme: Dracula
        - Snippet: {snippet}...

        2️⃣ **The Architecture Diagram**:
        - Concept: {diagram_concept}. Minimalist, dark mode, engineering style.

        3️⃣ **Alt-Text**:
        - English: "Technical diagram illustrating {topic}. Focused on system reliability and production-grade implementation."
    """
        # Genera una estrategia visual técnica para LinkedIn/X.
        # Extraemos solo las primeras líneas del snippet para evitar basura visual
    clean_snippet = snippet[:300] if snippet else "" 
    return f"""
        🎨 **VISUAL STRATEGY: {topic.upper()}**

        1️⃣ **The Authority Shot (Code)**:
        - Tool: Ray.so / Carbon.now.sh
        - Theme: Dracula / Night Owl
        - Content: {clean_snippet}...
        - Tip: Highlight the specific lines where the logic (e.g., @unique or transaction) happens.

        2️⃣ **The Architecture Diagram (Concept)**:
        - Prompt for AI/Designer: "A minimalist sequence diagram showing two concurrent requests hitting a database. The first one commits, the second one fails with a 'Unique Constraint' error. Clean, professional, dark mode aesthetic."

        3️⃣ **Accessibility (Alt-Text)**:
        - English: "Technical diagram illustrating the {topic} pattern. It shows how the system handles high-concurrency without data corruption by using database-level constraints."
    """