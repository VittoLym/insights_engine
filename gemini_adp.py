import re
import os
from google import genai
from dotenv import load_dotenv
import time

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=API_KEY)

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

def refine_post(topic, body, snippet):
    """Refina el contenido con personalidad de Lead Engineer en INGLÉS."""
    
    # Inyectamos la instrucción del idioma y el tono pragmático
    system_persona = (
        "You are a pragmatic Lead Software Engineer. "
        "Your tone is direct, technical, and cynical toward marketing hype. "
        "Language: English (US). " # <--- Obligatorio
        "\n\nWRITING RULES:"
        "\n1. NO corporate fluff or buzzwords (e.g., 'revolutionary', 'game-changer')."
        "\n2. Structure: Technical Problem -> Code Solution -> Trade-offs & Reality Check."
        "\n3. Focus on failure: What happens if this is NOT implemented? (e.g., data corruption, outages)."
        "\n4. Use professional but conversational English (Senior Dev style)."
        "\n5. Format: Short paragraphs and technical bullet points."
    )

    config = {
        "system_instruction": system_persona
    }
    
    prompt = f"""
    TECHNICAL CONTEXT:
    Project: Scalable E-commerce API
    Topic: {topic}
    File Analysis: {body}
    
    REFERENCE CODE:
    {snippet}

    TASK:
    Write a LinkedIn post (max 400 words) dissecting this implementation.
    Explain why we chose this pattern over a simpler one.
    Include a 'Trade-offs' section.
    End with a question that challenges senior engineers' perspective.
    """
    
    try:
        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=prompt,
            config=config
        )
        return response.text
    except Exception as e:
        return f"API Error: {e}"

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
        return response.text
    except: 
        return "Error generating thread."

def generate_visual_prompts(topic, snippet):
    clean_snippet = snippet[:300] if snippet else ""
    
    # Lógica simple para variar el diagrama según el tema
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
   - Snippet: {clean_snippet}...

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