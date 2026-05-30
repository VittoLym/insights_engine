import requests
import os
import re
from dotenv import load_dotenv

load_dotenv()
DEVTO_API_KEY = os.getenv("DEVTO_API_KEY")

def linkedin_to_article(topic, linkedin_post, snippet, series_name):
    """
    Convierte el LinkedIn post en un artículo completo para Dev.to.
    El post de LinkedIn es el resumen, el artículo expande cada punto.
    """
    return f"""## The Problem

{linkedin_post}

## The Implementation

```typescript
{snippet}
```

## Why This Matters in Production

This pattern directly prevents common failure modes in distributed systems.
Without it, you're exposed to race conditions, data inconsistency, and cascading failures.

## Trade-offs

Every architectural decision has a cost. This approach adds complexity to your
codebase and requires your team to understand the pattern deeply before modifying it.

## Key Takeaways

- Understand the failure mode before implementing the solution
- Test the unhappy path, not just the happy path  
- Document the *why*, not just the *what*

---

*Part of the {series_name} series.*
"""

def extract_tags(topic, signals):
    """Genera tags relevantes basados en el topic detectado."""
    base_tags = ["backend", "typescript", "webdev"]
    
    topic_tags = {
        "CONCURRENCY": ["database", "postgres"],
        "RESILIENCE": ["architecture", "microservices"],
        "EVENT_DRIVEN": ["rabbitmq", "eventdriven"],
        "SECURITY_PITFALLS": ["security", "jwt"],
        "PERFORMANCE": ["redis", "performance"],
    }
    
    for key, tags in topic_tags.items():
        if key in topic.upper():
            base_tags.extend(tags)
            break
    
    return base_tags[:4]  # Dev.to acepta máximo 4 tags

def publish_devto(topic, linkedin_post, snippet, series_name, signals, published=False):
    """
    Publica un artículo en Dev.to.
    published=False → queda como draft para revisar antes de publicar.
    published=True  → se publica directo.
    """
    print("    [📝] Publicando en Dev.to...")

    article_body = linkedin_to_article(topic, linkedin_post, snippet, series_name)
    tags = extract_tags(topic, signals)

    payload = {
        "article": {
            "title": f"{topic} — Production Patterns",
            "body_markdown": article_body,
            "published": published,
            "tags": tags,
            "series": series_name  # Dev.to agrupa artículos en series automáticamente
        }
    }

    try:
        r = requests.post(
            "https://dev.to/api/articles",
            headers={
                "api-key": DEVTO_API_KEY,
                "Content-Type": "application/json"
            },
            json=payload
        )
        r.raise_for_status()
        data = r.json()
        url = data.get("url", "")
        print(f"    [✓] Dev.to {'publicado' if published else 'draft guardado'}: {url}")
        return url

    except requests.HTTPError as e:
        print(f"    [❌] Error Dev.to: {e.response.text}")
        return None
    except Exception as e:
        print(f"    [❌] Error Dev.to: {e}")
        return None