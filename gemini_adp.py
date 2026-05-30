import re
import os
from google import genai
from dotenv import load_dotenv
import time
from groq import Groq

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=API_KEY)
client_groq = Groq(api_key=os.getenv("GROQ_API_KEY"))

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

def refine_post(topic, body, snippet):
    max_retries = 3

    system_persona = """You are a senior backend engineer. 10+ years in production systems.
You write LinkedIn posts for other senior engineers.

RULES (non-negotiable):
- Max 220 words
- No markdown headers, no emojis, no hashtags in the body
- No bullets unless absolutely necessary (max 3)
- No corporate words: robust, scalable, leverage, innovative, game-changer
- No preachy openings: "Stop doing X", "Most devs...", "You're doing X wrong"
- No explaining what JWT or bcrypt IS — assume they know
- Never sound like an AI summary

STRUCTURE:
1. One-line hook — a real engineering pain or consequence (not clickbait)
2. What this code does and WHY it exists (2-3 sentences max)
3. What silently breaks if this is missing (concrete: outage, data corruption, duplicate charge, security hole)
4. One honest trade-off
5. One genuine question a senior engineer would actually debate

The code snippet is the anchor. Talk about decisions, not syntax."""

    # Body enriquecido con el snippet real
    enriched_body = f"""
File: {topic}
Detected patterns: {body}

The post must be centered around this specific code:

```typescript
{snippet.strip()}
```

Do NOT summarize the code line by line.
Focus on: why this implementation exists, what production problem it solves,
and what happens in a real system when it's absent or wrong.
"""

    for attempt in range(max_retries):
        # Intento 1: Gemini
        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=enriched_body,
                config={"system_instruction": system_persona}
            )
            text = response.text.strip()
            if is_valid_output(text):
                print(f"    [✓] Gemini OK (attempt {attempt+1})")
                return text
        except Exception as e:
            print(f"    [❌] Gemini error (attempt {attempt+1}): {e}")

        # Intento 2: Groq como fallback real
        try:
            response = client_groq.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_persona},
                    {"role": "user", "content": enriched_body}
                ],
                temperature=0.7,
                max_tokens=600
            )
            text = response.choices[0].message.content.strip()
            if is_valid_output(text):
                print(f"    [✓] Groq fallback OK (attempt {attempt+1})")
                return text
        except Exception as e:
            print(f"    [❌] Groq error (attempt {attempt+1}): {e}")

        wait_time = 2 ** attempt
        print(f"    [⏳] Retrying in {wait_time}s...")
        time.sleep(wait_time)

    return None

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
        time.sleep(2)
        response = client.models.generate_content(
            model="gemini-3-flash-preview", 
            contents=prompt,
            config={"system_instruction": system_instruction}
        )
        text = response.text.strip()
        if is_valid_output(text):
            print(f"    [✓] Gemini OK ")
            return text
    except Exception as e:
        print(f"    [❌] Gemini error: {e}")
    try:
            response = client_groq.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=600
            )
            text = response.choices[0].message.content.strip()
            if is_valid_output(text):
                print(f"    [✓] Groq fallback OK")
                return text
    except Exception as e:
        print(f"    [❌] Groq error (attempt: {e}")

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
    """Genera una estrategia visual técnica para LinkedIn/X."""
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