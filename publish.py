"""Publica SOLO los kits aprobados. Sin --confirm es un ensayo (no envía nada)."""
import argparse
import time
from datetime import datetime, timezone

from kits import list_kits, save_kit


def _load_publishers():
    from publishers.bluesky_publisher import publish_thread_bluesky
    from publishers.x_publisher import publish_thread_x
    return {"bluesky": publish_thread_bluesky, "x": publish_thread_x}


def run(platforms, confirm=False, limit=1, gap=60):
    pubs = _load_publishers()
    done = 0
    for kit in list_kits(["approved", "published"]):
        pending = [p for p in platforms if p not in kit["published"]]
        if not pending:
            continue
        if done >= limit:
            break
        label = f"{kit['project']} | {kit['file']}"
        for p in pending:
            if not confirm:
                print(f"[ENSAYO] publicaría en {p}: {label}")
                continue
            try:
                ok = pubs[p](kit["x_thread"])
            except Exception as e:
                print(f"[❌] {p}: {e}")
                continue
            if ok is False:
                print(f"[❌] {p}: el publisher devolvió False")
                continue
            kit["published"][p] = datetime.now(timezone.utc).isoformat(timespec="seconds")
            kit["status"] = "published"
            save_kit(kit)          # se guarda al instante: una re-ejecución no repite
            print(f"[✅] {p}: {label}")
        done += 1
        if confirm and done < limit:
            time.sleep(gap)
    if done == 0:
        print("No hay kits aprobados para publicar en esas plataformas.")
    return done


def main():
    ap = argparse.ArgumentParser(description="Publica los kits aprobados")
    ap.add_argument("--platforms", default="bluesky", help="coma: bluesky,x")
    ap.add_argument("--confirm", action="store_true", help="publicar de verdad (sin esto es un ensayo)")
    ap.add_argument("--limit", type=int, default=1, help="máximo de kits por corrida")
    ap.add_argument("--gap", type=int, default=60, help="segundos entre kits")
    a = ap.parse_args()
    run([p.strip() for p in a.platforms.split(",")], a.confirm, a.limit, a.gap)


if __name__ == "__main__":
    main()