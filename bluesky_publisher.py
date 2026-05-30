import os
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv
load_dotenv()

BLUESKY_HANDLE = os.getenv("BS_HANDLE")  # o tu dominio custom
BLUESKY_PASSWORD = os.getenv("BS_PASSWORD")       # OJO: usar App Password, no tu contraseña real

def create_session():
    """Login y obtención del token."""
    r = requests.post(
        "https://bsky.social/xrpc/com.atproto.server.createSession",
        json={
            "identifier": BLUESKY_HANDLE,
            "password": BLUESKY_PASSWORD
        }
    )
    r.raise_for_status()
    return r.json()  # tiene accessJwt y did

def publish_post(session, text, reply_to=None):
    """Publica un post individual. Opcionalmente como reply de otro."""
    record = {
        "$type": "app.bsky.feed.post",
        "text": text[:300],  # Bluesky permite 300 chars
        "createdAt": datetime.now(timezone.utc).isoformat()
    }

    # Si es una respuesta dentro del thread
    if reply_to:
        record["reply"] = {
            "root": reply_to["root"],
            "parent": reply_to["parent"]
        }

    r = requests.post(
        "https://bsky.social/xrpc/com.atproto.repo.createRecord",
        headers={"Authorization": f"Bearer {session['accessJwt']}"},
        json={
            "repo": session["did"],
            "collection": "app.bsky.feed.post",
            "record": record
        }
    )
    r.raise_for_status()
    return r.json()  # tiene uri y cid del post creado

def parse_thread(x_thread_text):
    """
    Convierte el texto del thread en una lista de posts.
    Asume que cada parte está separada por línea vacía + número (1/, 2/, etc.)
    """
    import re
    # Dividimos por el patrón de numeración de tweets: "1/", "2/", etc.
    parts = re.split(r'\n(?=\d+/)', x_thread_text.strip())
    
    # Limpiamos cada parte
    posts = []
    for part in parts:
        clean = part.strip()
        if clean:
            posts.append(clean)
    
    return posts

def publish_thread_bluesky(x_thread_text):
    """
    Función principal: toma el thread generado por generate_x_thread()
    y lo publica como thread encadenado en Bluesky.
    """
    print("    [🦋] Publicando en Bluesky...")

    posts = parse_thread(x_thread_text)
    if not posts:
        print("    [❌] No se encontraron posts en el thread.")
        return False

    try:
        session = create_session()
        root_ref = None
        parent_ref = None

        for i, text in enumerate(posts):
            reply_to = None

            if i > 0:
                # A partir del segundo post, encadenamos
                reply_to = {
                    "root": root_ref,
                    "parent": parent_ref
                }

            result = publish_post(session, text, reply_to)

            # Guardamos la referencia del primer post (root del thread)
            ref = {
                "uri": result["uri"],
                "cid": result["cid"]
            }
            if i == 0:
                root_ref = ref
            parent_ref = ref

            print(f"    [✓] Post {i+1}/{len(posts)} publicado")

        print(f"    [🦋] Thread completo en Bluesky ({len(posts)} posts)")
        return True

    except requests.HTTPError as e:
        print(f"    [❌] Error HTTP Bluesky: {e.response.text}")
        return False
    except Exception as e:
        print(f"    [❌] Error Bluesky: {e}")
        return False