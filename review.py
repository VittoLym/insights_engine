"""Revisión por consola: aprobar, descartar o editar cada kit pendiente."""
import os
import re
import subprocess
import tempfile

from kits import list_kits, save_kit

X_LIMIT = 280


def edit_text(text):
    """Abre el texto en tu editor (EDITOR, o notepad/nano) y devuelve lo editado.
    Con VS Code:  $env:EDITOR = "code --wait"   """
    editor = os.environ.get("EDITOR") or ("notepad" if os.name == "nt" else "nano")
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write(text)
        tmp = f.name
    subprocess.run(f'{editor} "{tmp}"', shell=True)
    with open(tmp, encoding="utf-8") as f:
        new = f.read().strip()
    os.remove(tmp)
    return new


def too_long(thread_text):
    parts = [p.strip() for p in re.split(r"\n(?=\d+/)", thread_text.strip()) if p.strip()]
    return [i for i, p in enumerate(parts, 1) if len(p) > X_LIMIT]


def show(kit, i, total):
    print("\n" + "=" * 70)
    print(f"Kit {i}/{total}  |  {kit['project']}  |  {kit['file']}")
    print(f"Serie: {kit['topic']}   Carpeta: {os.path.dirname(kit['_path'])}")
    print("=" * 70)
    if kit["warnings"]:
        print("🔎 AVISOS:")
        for w in kit["warnings"]:
            print(f"   - {w}")
        print("-" * 70)
    print("LINKEDIN:\n")
    print(kit["linkedin_post"])
    print("\n" + "-" * 70)
    print("HILO DE X:\n")
    print(kit["x_thread"] or "(sin hilo)")
    bad = too_long(kit["x_thread"]) if kit["x_thread"] else []
    if bad:
        print(f"\n⚠️ Tweets de más de {X_LIMIT} caracteres: {bad}")


def main():
    kits = list_kits(["pending"])
    if not kits:
        print("No hay kits pendientes.")
        return
    for i, kit in enumerate(kits, 1):
        while True:
            show(kit, i, len(kits))
            choice = input("\n[a]probar  [d]escartar  [p] editar post  [t] editar hilo  [s]altar  [q]uitar > ").strip().lower()
            if choice == "a":
                if kit["warnings"] and input("Tiene avisos. ¿Aprobar igual? (s/n) > ").strip().lower() != "s":
                    continue
                if kit["x_thread"] and too_long(kit["x_thread"]):
                    print("No se puede aprobar: hay tweets demasiado largos. Editá el hilo (t).")
                    continue
                kit["status"] = "approved"
                save_kit(kit)
                print("✅ Aprobado")
                break
            if choice == "d":
                kit["status"] = "discarded"
                save_kit(kit)
                print("🗑️  Descartado")
                break
            if choice == "p":
                kit["linkedin_post"] = edit_text(kit["linkedin_post"])
                kit["warnings"] = []   # lo editaste vos: los avisos ya no aplican
                save_kit(kit)
            elif choice == "t":
                kit["x_thread"] = edit_text(kit["x_thread"])
                save_kit(kit)
            elif choice == "s":
                break
            elif choice == "q":
                return
    print("\nRevisión terminada.")


if __name__ == "__main__":
    main()