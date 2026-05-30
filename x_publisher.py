import requests
import re
import time
import os
from dotenv import load_dotenv
from requests_oauthlib import OAuth1

load_dotenv()
API_KEY             = os.getenv("X_API_KEY")
API_SECRET          = os.getenv("X_API_SECRET")
ACCESS_TOKEN        = os.getenv("X_ACCESS_TOKEN")
ACCESS_TOKEN_SECRET = os.getenv("X_ACCESS_TOKEN_SECRET")

def get_auth():
    return OAuth1(API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET)

def post_tweet(text, reply_to_id=None):
    """Publica un tweet individual, opcionalmente como reply."""
    url = "https://api.twitter.com/2/tweets"
    payload = {"text": text[:280]}

    if reply_to_id:
        payload["reply"] = {"in_reply_to_tweet_id": reply_to_id}

    r = requests.post(url, auth=get_auth(), json=payload)
    r.raise_for_status()
    return r.json()  # tiene id y text

def parse_thread(x_thread_text):
    """Divide el thread por el patrón 1/, 2/, etc."""
    parts = re.split(r'\n(?=\d+/)', x_thread_text.strip())
    return [p.strip() for p in parts if p.strip()]

def publish_thread_x(x_thread_text):
    """Publica el thread completo encadenado en X."""
    print("    [🐦] Publicando en X...")

    posts = parse_thread(x_thread_text)
    if not posts:
        print("    [❌] Thread vacío.")
        return False

    try:
        last_id = None

        for i, text in enumerate(posts):
            result = post_tweet(text, reply_to_id=last_id)
            last_id = result["data"]["id"]
            print(f"    [✓] Tweet {i+1}/{len(posts)} publicado (id: {last_id})")
            time.sleep(1)  # pequeño delay entre tweets

        print(f"    [🐦] Thread completo en X ({len(posts)} tweets)")
        return True

    except requests.HTTPError as e:
        print(f"    [❌] Error HTTP X: {e.response.text}")
        return False
    except Exception as e:
        print(f"    [❌] Error X: {e}")
        return False