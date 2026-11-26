"""Cadena de modelos con fallback. Orden y modelos se definen en .env (LLM_CHAIN)."""
import os
import time

from dotenv import load_dotenv

load_dotenv()

_clients = {}
_cooldown = {}          # "provider:modelo" -> momento hasta el que se lo saltea
COOLDOWN_SECONDS = 90
_TRANSIENT = ("503", "unavailable", "429", "resource_exhausted", "rate limit", "overloaded")


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


def _call(provider, model, system, prompt, max_tokens, temperature):
    client = _client(provider)
    if provider == "gemini":
        resp = client.models.generate_content(
            model=model,
            contents=prompt,
            config={"system_instruction": system, "max_output_tokens": max_tokens, "temperature": temperature},
        )
        return resp.text
    kwargs = {}
    if model.startswith("openai/gpt-oss"):
        kwargs["extra_body"] = {"reasoning_effort": "low"}  # que no gaste los tokens pensando
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
        temperature=temperature,
        max_completion_tokens=max_tokens,
        **kwargs,
    )
    return resp.choices[0].message.content


def generate(system, prompt, max_tokens=2000, validate=None, rounds=2, temperature=0.7):
    chain = _chain()
    for r in range(rounds):
        now = time.time()
        available = [c for c in chain if _cooldown.get(f"{c[0]}:{c[1]}", 0) <= now] or chain
        for provider, model in available:
            tag = f"{provider}:{model}"
            try:
                text = (_call(provider, model, system, prompt, max_tokens, temperature) or "").strip()
                text = text.replace("\u2011", "-").replace("\u00a0", " ").replace("\u202f", " ")
            except Exception as e:
                msg = str(e)
                print(f"    [❌] {tag}: {msg[:160]}")
                if any(t in msg.lower() for t in _TRANSIENT):
                    _cooldown[tag] = time.time() + COOLDOWN_SECONDS
                continue
            if text and (validate is None or validate(text)):
                print(f"    [✓] {tag}")
                return text
            print(f"    [⚠️] {tag}: respuesta vacía o inválida")
            if not text:
                print(f"    [⚠️] {tag}: respuesta vacía")
                continue
            if validate is not None and not validate(text):
                print(f"    [⚠️] {tag}: rechazada por validate: {text[:80]!r}")
                continue
            print(f"    [✓] {tag}")
            return text
        if r < rounds - 1:
            time.sleep(2 ** (r + 1))
    return None