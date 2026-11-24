"""Cadena de modelos con fallback. Orden y modelos se definen en .env (LLM_CHAIN)."""
import os
import time

from dotenv import load_dotenv

load_dotenv()

_clients = {}


def _chain():
    chain = []
    for item in os.getenv("LLM_CHAIN", "").split(","):
        provider, _, model = item.strip().partition(":")
        if provider and model:
            chain.append((provider.strip().lower(), model.strip()))
    if not chain:
        raise SystemExit("Definí LLM_CHAIN en tu .env (ver .env.example)")
    return chain


def _client(provider):
    if provider not in _clients:
        if provider == "gemini":
            from google import genai
            _clients[provider] = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        elif provider == "groq":
            from groq import Groq
            _clients[provider] = Groq(api_key=os.getenv("GROQ_API_KEY"))
        else:
            raise ValueError(f"Proveedor desconocido: {provider}")
    return _clients[provider]


def _call(provider, model, system, prompt, max_tokens):
    client = _client(provider)
    if provider == "gemini":
        resp = client.models.generate_content(
            model=model,
            contents=prompt,
            config={"system_instruction": system, "max_output_tokens": max_tokens},
        )
        return resp.text
    kwargs = {}
    if model.startswith("openai/gpt-oss"):
        kwargs["extra_body"] = {"reasoning_effort": "low"}  # que no gaste los tokens pensando
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
        temperature=0.7,
        max_completion_tokens=max_tokens,
        **kwargs,
    )
    return resp.choices[0].message.content


def generate(system, prompt, max_tokens=2000, validate=None, rounds=2):
    """Prueba cada modelo de la cadena en orden. Devuelve el texto o None si todos fallan."""
    chain = _chain()
    for r in range(rounds):
        for provider, model in chain:
            tag = f"{provider}:{model}"
            try:
                text = (_call(provider, model, system, prompt, max_tokens) or "").strip()
            except Exception as e:
                print(f"    [❌] {tag}: {str(e)[:160]}")
                continue
            if text and (validate is None or validate(text)):
                print(f"    [✓] {tag}")
                return text
            print(f"    [⚠️] {tag}: respuesta vacía o inválida")
        if r < rounds - 1:
            time.sleep(2 ** (r + 1))
    return None