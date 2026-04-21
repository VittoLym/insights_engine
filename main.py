import os
import time
from datetime import datetime
from gemini_adp import refine_post,generate_visual_prompts,generate_x_thread 
import re
import json
from textwrap import dedent

CONCEPT_MAP = {
    "CONCURRENCY": {
        "signals": ["transaction", "lock", "stock", "decrement", "atomic"],
        "extract_keywords": ["$transaction", "tx.", "decrement", "updateMany", "isolationLevel"],
        "series": "Serie 1: Real-World Concurrency",
        "seniority_weight": 8,
        "description": "Handling race conditions and data integrity in high-traffic systems."
    },
    "RESILIENCE": {
        "signals": ["retry", "circuitbreaker", "timeout", "idempotency"],
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

def extract_best_snippet(content, specific_keywords):
    lines = content.split("\n")
    best_start = -1
    candidates = []

    for i, line in enumerate(lines):
        if any(kw.lower() in line.lower() for kw in specific_keywords):
            if 'import' not in line:
                best_start = i
                break
        if best_start  == -1 and i >= 40:
            return None # Si no hay nada interesante, no generamos kit basura

        snippet_lines = []
        brace_count = 0
        found_first_brace = False
        
        for j in range(best_start, len(lines)):
            current_line = lines[j]
            clean_line = current_line.strip()
            if clean_line.startswith("import") or " from '" in clean_line:
                if j == best_start:
                    snippet_lines.append(current_line)
                continue
            snippet_lines.append(current_line)
            open_braces = current_line.count("{")
            close_braces = current_line.count("}")
            brace_count += open_braces
            brace_count -= close_braces
            if "{" in current_line:
                found_first_brace = True
            if found_first_brace and brace_count <= 0:
                if clean_line == "}" or clean_line.startswith("}"):
                    if(snippet_lines is not None and len(snippet_lines) > 0 ):
                        snippet = "".join(snippet_lines)
                        print(snippet)
                        score = calculate_score(snippet,specific_keywords)
                        candidates.append({"score":score, "code":snippet_lines})
                    break
        if not candidates:
            return None
        best = max(candidates, key=lambda x: x["score"])
        print(best)
        return best['code']

def format_for_ray(snippet):
    snippet = snippet.strip()

    # limpiar espacios excesivos
    snippet = re.sub(r"\n{3,}", "\n\n", snippet)

    return snippet

def calculate_score(snippet, keywords):
    score = 0
    # Más palabras clave = Más relevancia técnica
    for kw in keywords:
        score += snippet.lower().count(kw.lower()) * 10
    
    # Castigo por ser demasiado corto (menos de 5 líneas no es un post)
    line_count = len(snippet.split('\n'))
    if line_count < 5: score -= 50
    
    # Bonus por complejidad (si tiene catch o try es un mejor insight)
    if "catch" in snippet.lower(): score += 20
    if "await" in snippet.lower(): score += 5
    
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

def save_media_kit(index, post_data, linked_post, x_thread, visuals):
    """Crea una carpeta única para el kit y guarda los archivos individuales."""
    # Nombre de carpeta limpio: Kit_1_Resilient_Architecture_2026-04-19
    date_str = datetime.now().strftime("%Y-%m-%d")
    topic_slug = post_data['topic'].replace(" ", "_").replace(":", "").lower()
    folder_name = f"content_factory/Kit_{index+1}_{topic_slug}_{date_str}"
    
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)

    # 1. Guardar Post de LinkedIn
    with open(f"{folder_name}/linkedin.md", 'w', encoding='utf-8') as f:
        f.write(linked_post)
    
    # 2. Guardar Hilo de X
    with open(f"{folder_name}/x_thread.md", 'w', encoding='utf-8') as f:
        f.write(x_thread)
        
    # 3. Guardar Estrategia Visual y Contexto
    with open(f"{folder_name}/visual_strategy.txt", 'w', encoding='utf-8') as f:
        content = f"TOPIC: {post_data['topic']}\n"
        content += f"SOURCE FILE: {post_data['file']}\n"
        content += f"SIGNALS: {post_data['signals']}\n"
        content += "="*30 + "\n"
        content += visuals
        f.write(content)
        
    return folder_name

def save_output(data):
    with open("carousels.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    print("✅ carousels.json generated")

def analyze_repo(repo_path):
    repo_data = {"structure": [], "content": {}, "summary": ""}
    target_extensions = ('.ts', '.py', '.prisma') # Quitamos .md para los snippets, no rinden en Ray.so
    ignore_folders = {'node_modules', 'dist', '.git', '__pycache__', 'env', '.env','dto'}
    results = []

    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in ignore_folders]
        for file in files:
            if file.endswith(target_extensions):
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, repo_path)
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                except Exception:
                    continue
                # 1. EVALUACIÓN: ¿Este archivo tiene algo interesante según el CONCEPT_MAP?
                best_category = None
                best_config = None
                
                for category, config in CONCEPT_MAP.items():
                    if any(signal.lower() in content.lower() for signal in config["signals"]):
                        best_category = category
                        best_config = config
                        break
                if best_category:
                    snippet = extract_best_snippet(content, best_config["extract_keywords"])
                    if snippet and len(snippet.split('\n')) > 4:
                        snippet = format_for_ray(snippet)
                        
                        # Generamos el contenido del carrusel usando el contexto de la categoría
                        hook = generate_hook(snippet, best_category) 
                        carousel = generate_carousel(snippet, hook, best_category)

                        results.append({
                            "file": rel_path,
                            "category": best_category,
                            "carousel": carousel
                        })
                        
                        # Guardamos para el contexto global de la IA
                        repo_data["content"][rel_path] = content[:2000]

    save_output(results)
    print(repo_data)
    return repo_data

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

def generate_pro_drafts(repo_data):
    print(repo_data)
    """Detección Dinámica basada en CONCEPT_MAP."""
    drafts = []
    
    for path, content in repo_data["content"].items():
        for category, config in CONCEPT_MAP.items():
            # Buscamos si alguna señal de la categoría está en el archivo
            found_signals = [s for s in config["signals"] if s.lower() in content.lower()]
            
            if found_signals:
                # Calculamos score basado en señales y tamaño de archivo
                relevant_snippet = extract_best_snippet(content, config["extract_keywords"])
                print(relevant_snippet)
                if not relevant_snippet: continue
                base_score = config["seniority_weight"] + (len(found_signals) * 2)
                if len(content) > 1200: base_score += 5
                drafts.append({
                    "score": base_score,
                    "topic": config["series"],
                    "signals": found_signals,
                    "file": path,
                    "body": f"Technical analysis of {path}. Found patterns: {', '.join(found_signals)}.",
                    "snippet": relevant_snippet, # Snippet más largo para mejor contexto
                    "insight": f"Implementation of {category} patterns in production-ready code."
                })
    
    # Eliminamos duplicados de temas muy cercanos y ordenamos por score
    return sorted(drafts, key=lambda x: x['score'], reverse=True)

def audit_seniority(repo_data):
    points = 0
    findings = []
    senior_patterns = {
        "idempotencyKey": (25, "Idempotency Pattern"),
        "Transport.RMQ": (20, "Event-Driven Architecture"),
        "Decimal": (15, "Financial Precision"),
        "@UseGuards": (10, "Aspect-Oriented Security"),
        "Transaction": (10, "Atomic Operations")
    }
    content_all = " ".join(repo_data["content"].values())
    for p, (v, d) in senior_patterns.items():
        if p in content_all:
            points += v
            findings.append(f"✅ [+{v}] {d}")
    
    level = "Senior/Architect" if points > 60 else "Mid-Level" if points > 30 else "Junior"
    return points, level, findings

if __name__ == "__main__":
    REPO_PATH = 'C:/Users/PC/Documents/Projects/Scalable_ecommerce_api'
    
    print("[+] Step 1: Analyzing Repository...")
    data = analyze_repo(REPO_PATH)

    print("[+] Step 2: Running Seniority Audit...")
    points, rank, details = audit_seniority(data)
    print(f"    RANK: {rank} ({points}/100)")

    print("[+] Step 3: Generating Targeted Insights...")
    drafts = generate_pro_drafts(data)
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
            
            time.sleep(5) # Cooldown

        print(f"\n[#] PIPELINE COMPLETE. Content factory is ready.")