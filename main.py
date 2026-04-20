import os
import time
from datetime import datetime
from gemini_adp import refine_post,generate_visual_prompts,generate_x_thread 

CONCEPT_MAP = {
    "CONCURRENCY": {
        "signals": ["transaction", "lock", "stock", "decrement", "atomic"],
        "series": "Serie 1: Real-World Concurrency",
        "seniority_weight": 8
    },
    "RESILIENCE": {
        "signals": ["retry", "circuitbreaker", "timeout", "idempotency"],
        "series": "Serie 2: Resilient Architecture",
        "seniority_weight": 10
    },
    "SECURITY_PITFALLS": {
        "signals": ["jwt", "refresh", "auth", "guard", "session"],
        "series": "Serie 3: Security Deep-Dives",
        "seniority_weight": 7
    }
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

def analyze_repo(repo_path):
    repo_data = {"structure": [], "content": {}, "summary": ""}
    target_extensions = ('.ts', '.py', '.js', '.prisma', '.md')
    ignore_folders = {'node_modules', 'dist', '.git', '__pycache__', 'env', '.env'}

    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in ignore_folders]
        for file in files:
            if file.endswith(target_extensions):
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, repo_path)
                repo_data["structure"].append(rel_path)
                # Solo leemos archivos clave para el contexto de la IA
                if file in ['README.md', 'main.ts', 'app.py', 'schema.prisma'] or 'service' in file:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        repo_data["content"][rel_path] = f.read()[:2000]
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
    """Detección Dinámica basada en CONCEPT_MAP."""
    drafts = []
    
    for path, content in repo_data["content"].items():
        for category, config in CONCEPT_MAP.items():
            # Buscamos si alguna señal de la categoría está en el archivo
            found_signals = [s for s in config["signals"] if s.lower() in content.lower()]
            
            if found_signals:
                # Calculamos score basado en señales y tamaño de archivo
                base_score = config["seniority_weight"] + (len(found_signals) * 2)
                if len(content) > 1200: base_score += 5

                drafts.append({
                    "score": base_score,
                    "topic": config["series"],
                    "signals": found_signals,
                    "file": path,
                    "body": f"Technical analysis of {path}. Found patterns: {', '.join(found_signals)}.",
                    "snippet": content[:800], # Snippet más largo para mejor contexto
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