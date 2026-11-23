import os
import re
import subprocess
import shutil
import tempfile
from pathlib import Path
CODE_EXTENSIONS = {
    '.ts', '.tsx', '.js', '.jsx',   # JS ecosystem
    '.py',                           # Python
    '.go',                           # Go
    '.java', '.kt',                  # JVM
    '.rs',                           # Rust
    '.rb',                           # Ruby
    '.php',                          # PHP
    '.cs',                           # C#
}

# Carpetas que nunca tienen lógica interesante
IGNORE_FOLDERS = {
    'node_modules', 'dist', 'build', '.git', '__pycache__',
    'venv', '.venv', 'env', 'coverage', '.nyc_output',
    'migrations', '.pytest_cache', '.mypy_cache', 'vendor',
    'public', 'static', 'assets', 'fixtures', 'mocks',
    '__mocks__', 'generated', '.next', '.nuxt', 'out',
}

# Archivos que son casi siempre boilerplate
IGNORE_FILES = {
    'index.ts', 'index.js', 'index.py',
    '__init__.py', 'manage.py', 'wsgi.py', 'asgi.py',
    'main.ts',          # solo bootstrapping en NestJS
    'app.module.ts',    # solo imports en NestJS
    'conftest.py',
    'jest.config.ts', 'jest.config.js',
    'webpack.config.js', 'vite.config.ts',
    'eslint.config.js', '.eslintrc.js',
    'prettier.config.js', 'tsconfig.json',
}

# Patrones de complejidad agnósticos al lenguaje
# Son constructos que aparecen en código complejo en CUALQUIER lenguaje
COMPLEXITY_PATTERNS = [
    # Control de flujo complejo
    r'\btry\b', r'\bcatch\b', r'\bfinally\b',
    r'\bthrow\b', r'\braise\b',
    # Async/concurrencia
    r'\basync\b', r'\bawait\b', r'\bPromise\b',
    r'\bThread\b', r'\bLock\b', r'\bSemaphore\b',
    r'\bgather\b', r'\bconcurrent\b',
    # Transacciones y atomicidad
    r'\btransaction\b', r'\batomic\b', r'\brollback\b',
    r'\bcommit\b', r'\bbegin\b',
    # Patrones de resiliencia
    r'\bretry\b', r'\btimeout\b', r'\bcircuit\b',
    r'\bidempoten\w+\b', r'\bfallback\b', r'\bbackoff\b',
    # Seguridad
    r'\btoken\b', r'\bjwt\b', r'\bauth\w*\b',
    r'\bencrypt\b', r'\bdecrypt\b', r'\bhash\b',
    r'\bsecret\b', r'\bpermission\b',
    # Mensajería y eventos
    r'\bqueue\b', r'\bevent\b', r'\bpublish\b',
    r'\bsubscrib\w+\b', r'\bconsumer\b', r'\bproducer\b',
    r'\bmessage\b', r'\bchannel\b',
    # Performance
    r'\bcache\b', r'\bindex\b', r'\bbatch\b',
    r'\bbulk\b', r'\bpaginat\w+\b', r'\bstream\b',
    # Observabilidad
    r'\blog\w*\b', r'\btrace\b', r'\bmetric\b',
    r'\bmonitor\b', r'\balert\b',
]

# Patrones que suben mucho el score — señales de código senior
SENIOR_SIGNALS = [
    r'\bidempoten\w+\b',          # idempotency
    r'\bselect.for.update\b',     # db locking
    r'\bcircuit.breaker\b',       # resilience pattern
    r'\bdead.letter\b',           # message queue pattern
    r'\boutbox\b',                # outbox pattern
    r'\bsaga\b',                  # saga pattern
    r'\bcqrs\b',                  # CQRS
    r'\bevent.sourcing\b',        # event sourcing
    r'\boptimistic.lock\w*\b',    # optimistic locking
    r'\btwo.phase\b',             # two-phase commit
    r'Promise\.all\(',            # parallel async
    r'asyncio\.gather',           # parallel async Python
]

# Patrones que BAJAN el score — señales de código junior o boilerplate
JUNIOR_SIGNALS = [
    r'\bconsole\.log\b',          # debug prints
    r'\bprint\(',                 # debug prints Python
    r'\bTODO\b', r'\bFIXME\b',  # deuda técnica explícita
    r'except:\s*\n\s*pass',       # silenciar errores Python
    r'catch\s*\(\w+\)\s*\{\s*\}', # silenciar errores JS/TS
    r'any\b',                     # TypeScript any
    r'@ts-ignore',                # ignorar errores TS
]


# ── Funciones de acceso al repo ───────────────────────────────────

def clone_repo(github_url: str) -> str:
    """
    Clona un repo de GitHub en un directorio temporal.
    Retorna el path local del repo clonado.
    """
    tmp_dir = tempfile.mkdtemp(prefix="insights_engine")
    print(f"    [📥] Clonando {github_url}...")
    
    try:
        subprocess.run(
            ["git", "clone", "--depth=1", github_url, tmp_dir],
            check=True,
            capture_output=True,
            text=True
        )
        print(f"    [✓] Repo clonado en {tmp_dir}")
        return tmp_dir
    except subprocess.CalledProcessError as e:
        print(f"    [❌] Error clonando repo: {e.stderr}")
        shutil.rmtree(tmp_dir, ignore_errors=True)
        raise

def cleanup_repo(tmp_path: str):
    shutil.rmtree(tmp_path, ignore_errors=True)
    print(f"    [🧹] Directorio temporal eliminado")

def get_repo(source: str) -> tuple[str, bool]:
    """
    Acepta URL de GitHub o path local.
    Retorna (path, es_temporal) — es_temporal indica si hay que limpiar después.
    """
    if source.startswith("http") or source.startswith("git@"):
        return clone_repo(source), True
    else:
        return source, False


# ── Scoring heurístico local ──────────────────────────────────────

def score_file_complexity(path: str, content: str) -> dict:
    """
    Scoring rápido y agnóstico al lenguaje.
    No usa IA — puro análisis de patrones.
    """
    score = 0
    matched_concepts = []
    lines = content.split('\n')
    lower = content.lower()

    # 1. Peso por complejidad ciclomática aproximada
    complexity_hits = sum(
        1 for pattern in COMPLEXITY_PATTERNS
        if re.search(pattern, lower)
    )
    score += complexity_hits * 8
    
    # 2. Bonus por señales senior
    for pattern in SENIOR_SIGNALS:
        if re.search(pattern, lower):
            score += 30
            matched_concepts.append(pattern)

    # 3. Penalización por señales junior
    for pattern in JUNIOR_SIGNALS:
        if re.search(pattern, content):  # case-sensitive para algunos
            score -= 12

    # 4. Bonus por tipo de archivo (services > controllers > utils)
    filename = os.path.basename(path).lower()
    file_weights = {
        'service': 20, 'repository': 20, 'handler': 15,
        'middleware': 15, 'guard': 15, 'interceptor': 12,
        'controller': 10, 'resolver': 10, 'worker': 15,
        'consumer': 15, 'producer': 12, 'job': 10,
        'util': 5, 'helper': 5, 'config': -10,
        'dto': -20, 'entity': -5, 'schema': -5,
        'spec': -50, 'test': -50,  # nunca queremos tests
        'mock': -50, 'seed': -30,
    }
    for key, weight in file_weights.items():
        if key in filename:
            score += weight
            break

    # 5. Longitud óptima (ni muy corto ni muy largo)
    total_lines = len(lines)
    if 50 <= total_lines <= 300:
        score += 20
    elif total_lines < 20:
        score -= 30  # probablemente boilerplate
    elif total_lines > 500:
        score -= 10  # demasiado grande para un buen snippet

    # 6. Densidad de lógica (ratio código/comentarios)
    code_lines = [l for l in lines if l.strip() and not l.strip().startswith(('//', '#', '*', '/*'))]
    if total_lines > 0:
        density = len(code_lines) / total_lines
        if density > 0.7:
            score += 15

    return {
        "score": score,
        "complexity_hits": complexity_hits,
        "senior_signals": len(matched_concepts),
        "concepts": matched_concepts,
        "lines": total_lines,
    }


def analyze_repo(source: str, top_n: int = 8) -> dict:
    """
    Pipeline completo de análisis.
    Acepta URL de GitHub o path local.
    """
    repo_path, is_temp = get_repo(source)
    
    try:
        print(f"    [🔍] Escaneando archivos...")
        candidates = []

        for root, dirs, files in os.walk(repo_path):
            # Filtrar carpetas ignoradas
            dirs[:] = [d for d in dirs if d not in IGNORE_FOLDERS]
            
            for file in files:
                ext = Path(file).suffix
                if ext not in CODE_EXTENSIONS:
                    continue
                if file in IGNORE_FILES:
                    continue

                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, repo_path)

                try:
                    with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                except Exception:
                    continue

                # Descartar archivos demasiado cortos
                if len(content.strip()) < 150:
                    continue

                result = score_file_complexity(rel_path, content)
                
                # Solo guardamos archivos con score positivo
                if result["score"] > 0:
                    candidates.append({
                        "path": rel_path,
                        "content": content,
                        **result
                    })

        # Ordenamos y tomamos los mejores
        candidates.sort(key=lambda x: x["score"], reverse=True)
        top_files = candidates[:top_n]

        print(f"    [📊] {len(candidates)} archivos relevantes → top {len(top_files)} seleccionados")
        for f in top_files:
            print(f"         score={f['score']:>4} | {f['path']}")

        return {
            "source": source,
            "top_files": top_files,
            "total_scanned": len(candidates),
        }

    finally:
        if is_temp:
            cleanup_repo(repo_path)


def audit_seniority(repo_data: dict) -> tuple[int, str, list]:
    """Seniority audit agnóstico basado en señales universales."""
    points = 0
    findings = []

    all_content = " ".join(f["content"] for f in repo_data["top_files"]).lower()

    universal_patterns = {
        "idempoten":            (40, "Idempotency Pattern"),
        "circuit":              (35, "Circuit Breaker"),
        "dead letter":          (35, "Dead Letter Queue"),
        "outbox":               (40, "Transactional Outbox"),
        "saga":                 (35, "Saga Pattern"),
        "select for update":    (30, "Pessimistic Locking"),
        "optimistic lock":      (30, "Optimistic Locking"),
        "two-phase":            (35, "Two-Phase Commit"),
        "promise.all":          (25, "Parallel Async"),
        "asyncio.gather":       (25, "Parallel Async Python"),
        "rollback":             (20, "Transaction Management"),
        "retry":                (20, "Retry Strategy"),
        "timeout":              (15, "Timeout Handling"),
        "cache":                (15, "Caching Layer"),
        "event":                (10, "Event-Driven Design"),
    }

    for pattern, (value, label) in universal_patterns.items():
        if pattern in all_content:
            points += value
            findings.append(f"✅ [+{value}] {label}")

    # Bonus por volumen de archivos de alta complejidad
    high_complexity = sum(1 for f in repo_data["top_files"] if f["score"] > 60)
    if high_complexity >= 5:
        points += 20
        findings.append(f"✅ [+20] {high_complexity} high-complexity files")

    level = (
        "Staff/Architect" if points > 100 else
        "Senior"          if points > 60  else
        "Mid-Level"       if points > 30  else
        "Junior"
    )

    return points, level, findings