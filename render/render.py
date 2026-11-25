import base64
def generate_architecture_diagram(topic, folder_path):
    """Genera un diagrama Mermaid basado en el tópico del post."""
    print(f"        [📊] Generando diagrama de arquitectura...")
    
    # Definimos plantillas lógicas según el tópico
    templates = {
        "CONCURRENCY": "sequenceDiagram\n  Participant C as Client\n  Participant API as NestJS\n  Participant DB as Postgres\n  C->>API: Request\n  Note right of API: Start Transaction\n  API->>DB: Select FOR UPDATE\n  DB-->>API: Locked Row\n  API->>DB: Update State\n  Note right of API: Commit\n  API-->>C: Success",
        "SECURITY": "graph LR\n  A[Client] -->|JWT| B(AuthGuard)\n  B -->|Validate| C{Redis Blacklist}\n  C -->|Valid| D[Controller]\n  C -->|Invalid| E[401 Unauthorized]",
        "RESILIENCE": "graph TD\n  A[Request] --> B{Circuit Breaker}\n  B -->|Open| C[Fallback Response]\n  B -->|Closed| D[External Service]\n  D -->|Timeout| B"
    }
    
    # Seleccionamos la plantilla o una genérica
    key = next((k for k in templates if k in topic.upper()), None)
    mermaid_code = templates.get(key, "graph LR\n  A[Client] --> B[Service]\n  B --> C[Database]")
    
    # Codificamos para Mermaid.ink
    mermaid_bytes = mermaid_code.encode('utf-8')
    base64_mermaid = base64.urlsafe_b64encode(mermaid_code.encode("utf-8")).decode("utf-8")
    img_url = f"https://mermaid.ink/img/{base64_mermaid}?type=png&bgColor=1a1b26"

    try:
        res = requests.get(img_url, timeout=20)
        if res.status_code == 200:
            with open(f"{folder_path}/2_architecture.png", "wb") as f:
                f.write(res.content)
            print("        [✓] Diagrama guardado")
            return True
        print(f"        [⚠️] mermaid.ink respondió {res.status_code}")
    except Exception as e:
        print(f"        [⚠️] Diagrama falló: {e}")
    return False

def generate_code_image(snippet, folder_path, title="Senior Dev Insight"):
    """
    Usa Playwright para entrar a Ray.so, renderizar el código y guardar el PNG.
    """
    print(f"        [🎭] Playwright: Iniciando renderizado para {title}...")

    clean_snippet = snippet.encode("utf-8", errors="ignore").decode("utf-8")
    code_bytes = clean_snippet.encode('utf-8')
    code_base64 = base64.b64encode(code_bytes).decode('utf-8')
    code_final = code_base64.replace('+', '-').replace('/', '_').replace('=', '')
    ray_url = f"https://ray.so/#code={code_final}&theme=dark&background=true&language=typescript&title={title}"

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(device_scale_factor=2)
            page = context.new_page()
            page.set_viewport_size({"width": 1600, "height": 1200})
            page.goto(ray_url, wait_until="networkidle")
            time.sleep(2)
            target_id = "#frame"
            if page.locator(target_id).is_visible():
                output_path = f"{folder_path}/1_authority_shot.png"
                page.locator(target_id).screenshot(path=output_path, omit_background=True)
                print(f"        [✓] Imagen guardada: {output_path}")
                success = True
            else:
                print("        [⚠️] No se encontró el frame, intentando captura de emergencia...")
                page.screenshot(
                    path=f"{folder_path}/1_emergency_shot.png", 
                    clip={"x": 200, "y": 150, "width": 1200, "height": 800},
                    omit_background=True
                )
                success = True
                
            browser.close()
            return success
    except Exception as e:
        print(f"        [❌] Error en Playwright: {str(e)}")
        return False

def trim_snippet_for_rayso(snippet: str, max_lines: int = 35) -> str:
    """
    Si el snippet es muy largo para Ray.so, corta en un punto limpio
    (cierre de bloque lógico) en lugar de cortar arbitrariamente.
    """
    lines = snippet.split('\n')
    if len(lines) <= max_lines:
        return snippet

    # Buscamos el último cierre de bloque antes del límite
    for i in range(max_lines, max_lines - 10, -1):
        stripped = lines[i].strip()
        if stripped in ('}', '};', '});', '})', 'end'):
            return '\n'.join(lines[:i+1])

    # Si no hay cierre limpio, cortamos con indicador
    return '\n'.join(lines[:max_lines]) + '\n  // ...'
