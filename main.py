import os
import time
from datetime import datetime
from gemini_adp import refine_post,generate_visual_prompts,generate_x_thread 
import re
import json
from textwrap import dedent
import requests
import base64
from urllib.parse import quote
from playwright.sync_api import sync_playwright
from bluesky_publisher import publish_thread_bluesky
from x_publisher import publish_thread_x
from dev_publisher import publish_devto
from repo_scanner import analyze_repo, audit_seniority
from gemini_adp import extract_snippet_with_ai
CONCEPT_MAP = {
    "CONCURRENCY": {
        "signals": ["transaction", "lock", "stock", "decrement", "atomic"],
        "extract_keywords": ["$transaction", "tx.", "decrement", "updateMany", "isolationLevel"],
        "series": "Serie 1: Real-World Concurrency",
        "seniority_weight": 8,
        "description": "Handling race conditions and data integrity in high-traffic systems."
    },
    "RESILIENCE": {
        "signals": ["retry", "circuitbreaker", "timeout", "idempotency", "const"],
        "extract_keywords": ["idempotency", "IdempotencyKey", "catch", "throw new", "RetryStrategy"],
        "series": "Serie 2: Resilient Architecture",
        "seniority_weight": 10,
        "description": "How to build systems that survive partial failures."
    },
    "EVENT_DRIVEN": {
        "signals": ["rabbitmq", "pubsub", "event", "emit", "listener"],
        "extract_keywords": ["@EventPattern", "Transport.RMQ", "client.emit", "Payload", "Ctx"],
        "series": "Serie 3: Event-Driven Patterns",
        "seniority_weight": 9,
        "description": "Decoupling services using asynchronous message brokers."
    },
    "SECURITY_PITFALLS": {
        "signals": ["jwt", "refresh", "auth", "guard", "session", "bcrypt"],
        "extract_keywords": ["@UseGuards", "JwtService", "validatePayload", "PassportStrategy", "canActivate"],
        "series": "Serie 4: Security Deep-Dives",
        "seniority_weight": 7,
        "description": "Securing APIs beyond the basic authentication tutorials."
    },
    "PERFORMANCE": {
        "signals": ["cache", "redis", "index", "optimization", "warmup"],
        "extract_keywords": ["RedisService", "cacheManager", "setex", "ttl", "cluster"],
        "series": "Serie 5: High-Performance Backend",
        "seniority_weight": 8,
        "description": "Scaling throughput and reducing latency with strategic caching."
    }
}

TARGET_KEYWORDS = [
    "idempotency",
    "rabbitmq",
    "guard",
    "jwt",
    "prisma",
    "transaction",
]

MAX_SNIPPET_LINES = 15
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
PERSON_URN   = os.getenv("URN_PERSON")

def generate_architecture_diagram(topic, folder_path):
    """Genera un diagrama Mermaid basado en el tópico del post."""
    print(f"        [📊] Generando diagrama de arquitectura...")
    
    # Definimos plantillas lógicas según el tópico
    templates = {
        "CONCURRENCY": "sequenceDiagram\n  Participant C as Client\n  Participant API as NestJS\n  Participant DB as Postgres\n  C->>API: Request\n  Note right of API: Start Transaction\n  API->>DB: Select FOR UPDATE\n  DB-->>API: Locked Row\n  API->>DB: Update State\n  Note right of API: Commit\n  API-->>C: Success",
        "SECURITY": "graph LR\n  A[Client] -->|JWT| B(AuthGuard)\n  B -->|Validate| C{Redis Blacklist}\n  C -->|Valid| D[Controller]\n  C -->|Invalid| E[401 Unauthorized]",
        "RESILIENCE": "graph TD\n  A[Request] --> B{Circuit Breaker}\n  B -->|Open| C[Fallback Response]\n  B -->|Closed| D[External Service]\n  D -->|Timeout| B"
    }
    
    # Seleccionamos la plantilla o una genérica
    key = next((k for k in templates if k in topic.upper()), None)
    mermaid_code = templates.get(key, "graph LR\n  A[Client] --> B[Service]\n  B --> C[Database]")
    
    # Codificamos para Mermaid.ink
    mermaid_bytes = mermaid_code.encode('utf-8')
    base64_mermaid = base64.b64encode(mermaid_bytes).decode('utf-8')
    img_url = f"https://mermaid.ink/img/{base64_mermaid}?type=png&bgColor=1a1b26"
    
    try:
        res = requests.get(img_url, timeout=20)
        if res.status_code == 200:
            with open(f"{folder_path}/2_architecture.png", 'wb') as f:
                f.write(res.content)
            return True
    except Exception as e:
        print(e)
        return False
    
    return False

def generate_code_image(snippet, folder_path, title="Senior Dev Insight"):
    """
    Usa Playwright para entrar a Ray.so, renderizar el código y guardar el PNG.
    """
    print(f"        [🎭] Playwright: Iniciando renderizado para {title}...")

    clean_snippet = snippet.encode("utf-8", errors="ignore").decode("utf-8")
    code_bytes = clean_snippet.encode('utf-8')
    code_base64 = base64.b64encode(code_bytes).decode('utf-8')
    code_final = code_base64.replace('+', '-').replace('/', '_').replace('=', '')
    ray_url = f"https://ray.so/#code={code_final}&theme=dark&background=true&language=typescript&title={title}"

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(device_scale_factor=2)
            page = context.new_page()
            page.set_viewport_size({"width": 1600, "height": 1200})
            page.goto(ray_url, wait_until="networkidle")
            time.sleep(2)
            target_id = "#frame"
            if page.locator(target_id).is_visible():
                output_path = f"{folder_path}/1_authority_shot.png"
                page.locator(target_id).screenshot(path=output_path, omit_background=True)
                print(f"        [✓] Imagen guardada: {output_path}")
                success = True
            else:
                print("        [⚠️] No se encontró el frame, intentando captura de emergencia...")
                page.screenshot(
                    path=f"{folder_path}/1_emergency_shot.png", 
                    clip={"x": 200, "y": 150, "width": 1200, "height": 800},
                    omit_background=True
                )
                success = True
                
            browser.close()
            return success
    except Exception as e:
        print(f"        [❌] Error en Playwright: {str(e)}")
        return False

def save_media_kit(index, post_data, linked_post, x_thread, visuals):
    date_str = datetime.now().strftime("%Y-%m-%d")
    topic_slug = post_data['topic'].replace(" ", "_").replace(":", "").lower()
    folder_name = f"content_factory/Kit_{index+1}_{topic_slug}_{date_str}"
    
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)

    # 1. Guardar archivos de texto
    with open(f"{folder_name}/linkedin.md", 'w', encoding='utf-8') as f:
        f.write(linked_post)
    with open(f"{folder_name}/x_thread.md", 'w', encoding='utf-8') as f:
        f.write(x_thread)

    # 2. GENERACIÓN AUTOMÁTICA DE IMÁGENES
    # Generamos la imagen del código (Authority Shot)
    clean_snippet = trim_snippet_for_rayso(post_data['snippet'], max_lines=35)
    generate_code_image(clean_snippet, folder_name)
    
    # Generamos el diagrama (System Design Insight)
    generate_architecture_diagram(post_data['topic'], folder_name)
        
    return folder_name

def trim_snippet_for_rayso(snippet: str, max_lines: int = 35) -> str:
    """
    Si el snippet es muy largo para Ray.so, corta en un punto limpio
    (cierre de bloque lógico) en lugar de cortar arbitrariamente.
    """
    lines = snippet.split('\n')
    if len(lines) <= max_lines:
        return snippet

    # Buscamos el último cierre de bloque antes del límite
    for i in range(max_lines, max_lines - 10, -1):
        stripped = lines[i].strip()
        if stripped in ('}', '};', '});', '})', 'end'):
            return '\n'.join(lines[:i+1])

    # Si no hay cierre limpio, cortamos con indicador
    return '\n'.join(lines[:max_lines]) + '\n  // ...'

def extract_snippet(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        best_start = -1
        
        for i, line in enumerate(lines):
            for sp,config in CONCEPT_MAP.items():
                if any(kw.lower() in line.lower() for kw in config["extract_keywords"]):
                    if 'import' not in line:
                        best_start = i
                        break

        if best_start == -1:
            return None # Si no hay nada interesante, no generamos kit basura

        snippet_lines = []
        brace_count = 0
        found_first_brace = False
        
        for j in range(best_start, len(lines)):
            current_line = lines[j]
            snippet_lines.append(current_line)
            
            brace_count += current_line.count("{")
            brace_count -= current_line.count("}")
            
            if "{" in current_line:
                found_first_brace = True
            
            # Si el bloque se cierra o nos pasamos de largo, cortamos
            if (found_first_brace and brace_count <= 0) or len(snippet_lines) > 20:
                break
                
        return "".join(snippet_lines)

    except Exception as e:
        return None

def extract_best_snippet(content: str, keywords: list) -> str | None:
    """
    Extrae el método/función con más señales de seniority del archivo.
    Agnóstico al lenguaje: detecta funciones por patrones universales.
    """
    lines = content.split('\n')
    
    # Patrones que indican el INICIO de una función/método en cualquier lenguaje
    FUNCTION_START_PATTERNS = [
        r'^\s*(async\s+)?function\s+\w+',          # JS/TS function
        r'^\s*(public|private|protected|async).*\w+\s*\(',  # TS class method
        r'^\s*async\s+\w+\s*\(',                    # async method
        r'^\s*def\s+\w+\s*\(',                      # Python
        r'^\s*func\s+\w+\s*\(',                     # Go
        r'^\s*(pub\s+)?fn\s+\w+\s*\(',              # Rust
    ]
    
    # Señales que suben el score del método
    SENIOR_BONUS = {
        'transaction':      40,
        'atomic':           40,
        'idempoten':        45,
        'retry':            30,
        'circuit':          35,
        'rollback':         35,
        'promise.all':      30,
        'gather':           30,
        'lock':             25,
        'try':              10,
        'catch':            10,
        'throw':            10,
        'await':            8,
        'async':            5,
        'rabbitmq':         20,
        'publish':          15,
        'subscribe':        15,
        'cache':            15,
        'jwt':              15,
        'verify':           12,
        'decrypt':          20,
        'encrypt':          20,
        'hash':             15,
        'timeout':          20,
        'event':            10,
    }

    # Señales que BAJAN el score
    JUNIOR_PENALTY = {
        'console.log':      -15,
        'console.error':    -10,
        'print(':           -15,
        'TODO':             -10,
        'FIXME':            -10,
        'any':              -8,
        '@ts-ignore':       -20,
        'except:\n':        -25,
    }

    def extract_method_block(start_idx: int) -> list[str]:
        """Extrae el bloque completo desde el inicio del método."""
        block = []
        brace_count = 0
        indent_count = 0
        found_opening = False
        is_indent_based = False  # para Python

        for j in range(start_idx, min(start_idx + 80, len(lines))):
            line = lines[j]
            block.append(line)

            # Detectar si es indentación (Python) o llaves (JS/TS/Go)
            if '{' in line:
                brace_count += line.count('{')
                brace_count -= line.count('}')
                found_opening = True
            
            # Corte por llaves (JS/TS/Go/Rust)
            if found_opening and brace_count <= 0 and len(block) > 2:
                break

            # Corte por longitud máxima
            if len(block) >= 35:
                break

        return block

    def score_block(block: list[str]) -> int:
        """Puntúa un bloque por señales de seniority."""
        score = 0
        full_text = '\n'.join(block).lower()

        for signal, bonus in SENIOR_BONUS.items():
            if signal.lower() in full_text:
                score += bonus

        for signal, penalty in JUNIOR_PENALTY.items():
            if signal.lower() in full_text:
                score += penalty  # ya son negativos

        # Bonus si además tiene keywords del CONCEPT_MAP
        for kw in keywords:
            if kw.lower() in full_text:
                score += 15

        # Longitud ideal
        if 10 <= len(block) <= 30:
            score += 20
        elif len(block) < 5:
            score -= 30

        return score

    # ── Pipeline principal ──────────────────────────────────────

    candidates = []

    for i, line in enumerate(lines):
        # Ignorar imports, comentarios, decoradores
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith(('//', '#', '*', '/*', '@', 'import', 'from', 'export type', 'interface', 'type ')):
            continue

        # Detectar si la línea es inicio de función
        is_function_start = any(
            re.match(pattern, line)
            for pattern in FUNCTION_START_PATTERNS
        )

        if not is_function_start:
            continue

        block = extract_method_block(i)
        if len(block) < 4:
            continue

        score = score_block(block)

        # Solo consideramos bloques con score positivo
        if score > 0:
            candidates.append({
                "score": score,
                "start_line": i,
                "block": block,
            })

    if not candidates:
        return None

    # Tomamos el bloque con mayor score
    best = max(candidates, key=lambda x: x["score"])
    
    print(f"        [✓] Mejor snippet: línea {best['start_line']+1}, score={best['score']}, {len(best['block'])} líneas")
    
    def clean_snippet(block: list[str]) -> list[str]:
        """Limpia el snippet antes de publicar."""
        cleaned = []
        for line in block:
            stripped = line.strip()
            # Eliminar console.logs y prints de debug
            if re.search(r'console\.(log|error|warn|debug)\(', line):
                continue
            # Eliminar comentarios que mencionan pruebas o debug
            if re.search(r'//.*?(TODO|FIXME|PRUEBA|debug|temporal|simplificado)', line, re.IGNORECASE):
                continue
            cleaned.append(line)
        return cleaned
    best_block = clean_snippet(best["block"])
    return '\n'.join(best_block).strip()
def format_for_ray(snippet):
    snippet = snippet.strip()

    # limpiar espacios excesivos
    snippet = re.sub(r"\n{3,}", "\n\n", snippet)

    return snippet

def calculate_score(snippet, keywords):
    score = 0
    lines = snippet.split('\n')
    lower_snippet = snippet.lower()

    # 1. PESO POR KEYWORDS (RELEVANCIA)
    for kw in keywords:
        # Multiplicamos por la cantidad de veces que aparece la keyword
        score += lower_snippet.count(kw.lower()) * 15

    # 2. BONUS POR "SENIORITY SIGNALS" (DENSIDAD TÉCNICA)
    senior_signals = {
        "$transaction": 50,  # Esto es oro puro para el algoritmo
        "await promise.all": 40,
        "try": 20,
        "catch": 20,
        "verifyasync": 25,
        "updateMany": 30,
        "ReturnType": 35,    # Tipado avanzado
        "Injectable": -10,   # Bajamos puntos si es solo una definición de clase
    }

    for signal, bonus in senior_signals.items():
        if signal.lower() in lower_snippet:
            score += bonus

    # 3. PENALIZACIÓN POR "CÓDIGO BASURA"
    if "import {" in lower_snippet and len(lines) < 10:
        score -= 100  # Matamos los snippets que son solo imports
    
    # 4. EL "DULCE" DE LA LONGITUD
    # Un snippet de entre 12 y 22 líneas es el tamaño perfecto para un carrusel
    if 12 <= len(lines) <= 22:
        score += 40
    elif len(lines) > 25:
        score -= 30 # Muy largo se vuelve aburrido

    return score

def generate_hook(snippet, file_path):
    if "idempotency" in snippet.lower():
        return "Your API is charging users twice and you don't even know it."

    if "rabbitmq" in snippet.lower():
        return "Your microservices are tightly coupled and will fail together."

    if "guard" in snippet.lower():
        return "Your API is probably exposed right now."

    return f"Most developers ignore what happens inside {os.path.basename(file_path)}."

def generate_carousel(snippet, hook, file_path):
    return {
        "slides": [
            {
                "title": hook,
                "subtitle": "Distributed systems fail. Your code must not."
            },
            {
                "title": "The Problem",
                "content": "Retries happen automatically.\nYour system executes the same request twice."
            },
            {
                "title": "The Impact",
                "content": "• Double charges\n• Data inconsistency\n• Broken state"
            },
            {
                "title": "Reality",
                "content": "Exactly-once delivery is a myth.\nYou get at-least-once."
            },
            {
                "title": "The Fix",
                "content": "Use idempotency keys."
            },
            {
                "title": "Implementation",
                "content": snippet
            },
            {
                "title": "Pro Tip",
                "content": "Enforce idempotency at DB level.\nNot in application logic."
            },
            {
                "title": "Final Thought",
                "content": "If your system can't handle retries,\nyou don't have a scalable system."
            }
        ],
        "rayso": {
            "theme": "midnight",
            "language": "typescript",
            "code": snippet
        },
        "caption": f"{hook}\n\nBreak your system before production does.\n\n#backend #microservices #softwarearchitecture"
    }

def save_output(data):
    with open("carousels.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    print("✅ carousels.json generated")

def score_file(path):
    score = 0
    weights = {"service": 5, "guard": 4, "prisma": 4, "controller": 2, "dto": 1}
    for key, val in weights.items():
        if key in path.lower(): score += val
    if any(core in path.lower() for core in ["order", "payment", "auth"]):
        score += 3
    return score

def calculate_post_score(findings, content):
    score = 0
    # Seniority: ¿Usa patrones complejos?
    score += len(findings) * 5 
    # Technical Depth: ¿El archivo es largo y complejo o es un boilerplate?
    if len(content) > 1000: score += 10 
    return score

def is_valid_output(text):
    banned_phrases = ["503", "UNAVAILABLE", "API Error", "limit reached"]
    return not any(phrase in text for phrase in banned_phrases)

def generate_pro_drafts(top_files: list) -> list:
    """
    Genera drafts a partir de los top archivos detectados por el scanner.
    Usa IA para extraer el snippet más valioso de cada archivo.
    """
    drafts = []
    seen_topics = set()  # Para evitar duplicados de mismo tema

    for file_data in top_files:
        path    = file_data["path"]
        content = file_data["content"]
        score   = file_data["score"]
        signals = file_data.get("concepts", [])

        # Detectamos qué categorías del CONCEPT_MAP aplican
        for category, config in CONCEPT_MAP.items():
            found_signals = [
                s for s in config["signals"]
                if s.lower() in content.lower()
            ]
            if not found_signals:
                continue

            # Evitamos publicar el mismo tema dos veces
            dedup_key = f"{category}_{os.path.basename(path)}"
            if dedup_key in seen_topics:
                continue
            seen_topics.add(dedup_key)

            # Primero intentamos extraer snippet localmente (rápido)
            relevant_snippet = extract_best_snippet(content, config["extract_keywords"])

            # Si el archivo tiene score alto y no encontramos buen snippet → usamos IA
            if not relevant_snippet or (score > 60 and len(relevant_snippet.split('\n')) < 5):
                print(f"        [🤖] IA extrayendo snippet de {path}...")
                relevant_snippet = extract_snippet_with_ai(content, category, config["description"])

            if not relevant_snippet:
                continue

            base_score = (
                score +                          # score del scanner
                config["seniority_weight"] +     # peso del concepto
                len(found_signals) * 3           # bonus por señales encontradas
            )

            drafts.append({
                "score":   base_score,
                "topic":   config["series"],
                "signals": found_signals,
                "file":    path,
                "snippet": relevant_snippet,
                "body":    (
                    f"Signals found: {', '.join(found_signals)}. "
                    f"Seniority weight: {config['seniority_weight']}. "
                    f"{config['description']}"
                ),
                "insight": f"Implementation of {category} patterns in production-ready code."
            })

    return sorted(drafts, key=lambda x: x["score"], reverse=True)

def get_first_png(folder_path):
    png_files = sorted([
        f for f in os.listdir(folder_path)
        if f.lower().endswith(".png")
    ])

    if not png_files:
        return None

    return os.path.join(folder_path, png_files[0])

def register_upload():
    url = "https://api.linkedin.com/v2/assets?action=registerUpload"

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0",
        "LinkedIn-Version": "202501"
    }

    body = {
        "registerUploadRequest": {
            "recipes": [
                "urn:li:digitalmediaRecipe:feedshare-image"
            ],
            "owner": PERSON_URN,
            "serviceRelationships": [
                {
                    "relationshipType": "OWNER",
                    "identifier": "urn:li:userGeneratedContent"
                }
            ]
        }
    }

    r = requests.post(
        url,
        headers=headers,
        json=body
    )

    return r.json()

def publish_linkedin(text: str, media_paths: str=[]):
    media_assets = []
    for path in media_paths:
        asset = upload_image(path)
        media_assets.append({
            "status": "READY",
            "media": asset
        })
    url = "https://api.linkedin.com/v2/ugcPosts"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0"
    }
    body = {
        "author": PERSON_URN,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": text},
                "shareMediaCategory": (
                    "IMAGE"
                    if media_assets
                    else "NONE"
                ),
                "media": media_assets
            }
            
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        }
    }
    try:
        r = requests.post(
            url,
            headers=headers,
            json=body
        )

        print(f"STATUS: {r.status_code}")
        print("RAW RESPONSE:")
        print(r.text)

        return r.status_code, r.json()

    except Exception as e:
        print("❌ Publish error:", e)
        return None, str(e)

def upload_image(image_path):

    upload_data = register_upload()

    upload_url = (
        upload_data["value"]
        ["uploadMechanism"]
        ["com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"]
        ["uploadUrl"]
    )

    asset = upload_data["value"]["asset"]

    with open(image_path, "rb") as f:
        image_binary = f.read()

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}"
    }

    r = requests.put(
        upload_url,
        data=image_binary,
        headers=headers
    )

    print("UPLOAD:", r.status_code)

    return asset

if __name__ == "__main__":
    SOURCE = 'https://github.com/VittoLym/Scalable_ecommerce_api'
    
    print("[+] Step 1: Analyzing Repository...")
    data = analyze_repo(SOURCE, top_n=5)
    print("[+] Step 2: Running Seniority Audit...")
    points, rank, details = audit_seniority(data)
    print(f"    RANK: {rank} ({points} pts)")
    for d in details:
        print(f"    {d}")
    print("[+] Step 3: Generating Targeted Insights...")
    drafts = generate_pro_drafts(data["top_files"])
    print(len(drafts))
    if drafts:
        top_drafts = drafts[:4]
        print(f"[+] Step 4: Building {len(top_drafts)} Automated Media Kits...")
        for i, post_data in enumerate(top_drafts):
            print(f"    [>] Processing Kit {i+1}...")
            
            # Generación con IA
            linked_post = refine_post(post_data['topic'], post_data['body'], post_data['snippet'])
            time.sleep(2)
            
            # Manejo del error en X Thread
            x_thread = generate_x_thread(post_data['topic'], linked_post)
            if "Error" in x_thread:
                x_thread = "⚠️ API Error. Please manually convert the LinkedIn post to a thread."
            
            visuals = generate_visual_prompts(post_data['topic'], post_data['snippet'])

            # Guardar en su propia carpeta
            path = save_media_kit(i, post_data, linked_post, x_thread, visuals)
            print(f"    [✓] Kit {i+1} saved to: {path}")
            pngPath = get_first_png(path)
            #publish_linkedin(linked_post,[pngPath])
            #publish_thread_bluesky(x_thread)
            time.sleep(3)
            #publish_thread_x(x_thread)
            time.sleep(3)
            #publish_devto(
            #    topic=post_data['topic'],
            #    linkedin_post=linked_post,
            #    snippet=post_data['snippet'],
            #    series_name=post_data['topic'],  # ya tiene el nombre de la serie
            #    signals=post_data['signals'],
            #    published=True
            #)
            time.sleep(5) # Cooldown
        print(f"\n[#] PIPELINE COMPLETE. Content factory is ready.")
        
    