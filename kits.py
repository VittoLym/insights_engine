import glob
import json
import os
from datetime import datetime, timezone

KITS_DIR = "content_factory"


def save_kit_json(folder, *, repo, project, post_data, linkedin_post, x_thread, warnings):
    """Crea kit.json (estado 'pending'). No pisa un kit ya aprobado o publicado."""
    path = os.path.join(folder, "kit.json")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            if json.load(f).get("status") in ("approved", "published"):
                print("    [⚠️] Este kit ya estaba aprobado o publicado; no lo piso.")
                return
    data = {
        "version": 1,
        "status": "pending",   # pending | approved | discarded | published
        "created": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "repo": repo,
        "project": project,
        "file": post_data["file"],
        "topic": post_data["topic"],
        "linkedin_post": linkedin_post,
        "x_thread": x_thread or "",
        "warnings": warnings or [],
        "published": {},       # plataforma -> fecha de publicación
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def list_kits(statuses=None):
    """Devuelve los kits (más viejos primero), opcionalmente filtrados por estado."""
    kits = []
    for path in sorted(glob.glob(os.path.join(KITS_DIR, "*", "kit.json"))):
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        data["_path"] = path
        if statuses is None or data["status"] in statuses:
            kits.append(data)
    return kits


def save_kit(kit):
    data = {k: v for k, v in kit.items() if k != "_path"}
    with open(kit["_path"], "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)