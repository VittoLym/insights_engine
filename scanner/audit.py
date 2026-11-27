import re

INTENT_RE = re.compile(
    r"\bI(?:'m| am)?\s+(?:currently\s+|now\s+)?"
    r"(?:weighing|considering|planning|thinking about|evaluating|exploring|moving to)\b", re.I)
TOOLS = ["redis", "memcached", "kafka", "rabbitmq", "sqs", "pub/sub", "dead-letter",
         "dead letter", "outbox", "lru", "kubernetes", "nginx", "elasticsearch"]


def audit_post(post, snippet, note=None, file_path=""):
    """Avisos para revisar a mano antes de publicar. No bloquea nada."""
    base = f"{snippet}\n{note or ''}\n{file_path}".lower()
    warnings = []
    if INTENT_RE.search(post):
        warnings.append("afirma una intención ('weighing/considering...'): ¿la dijiste vos?")
    nums = set(re.findall(r"(?<![\w/])\d+(?:[.,]\d+)?(?![\w/])", post))
    missing = sorted(n for n in nums if n not in base)
    if missing:
        warnings.append(f"cifras que no están en el código ni en tu nota: {', '.join(missing)}")
    tools = [t for t in TOOLS if t in post.lower() and t not in base]
    if tools:
        warnings.append(f"menciona herramientas que no están en el snippet: {', '.join(tools)}")
    return warnings