"""Pluggable LLM provider layer supporting OpenAI and Google Gemini.

Selection is driven by env vars (see .env.example):
  LLM_PROVIDER = "openai" | "gemini"
If the selected provider has no key, we fall back to the other one.
All functions degrade gracefully when no key is configured.
"""
from __future__ import annotations

import json
import os
from typing import Iterator

from dotenv import load_dotenv

load_dotenv()


class LLMNotConfigured(RuntimeError):
    """Raised when no provider has a usable API key."""


def _openai_key() -> str | None:
    return os.getenv("OPENAI_API_KEY") or None


def _gemini_key() -> str | None:
    return os.getenv("GEMINI_API_KEY") or None


def active_provider() -> str | None:
    """Return the provider we can actually use, honouring LLM_PROVIDER + keys."""
    preferred = (os.getenv("LLM_PROVIDER") or "openai").lower()
    have = {
        "openai": bool(_openai_key()),
        "gemini": bool(_gemini_key()),
    }
    if have.get(preferred):
        return preferred
    for name, ok in have.items():
        if ok:
            return name
    return None


def is_available() -> bool:
    return active_provider() is not None


def status() -> dict:
    return {
        "available": is_available(),
        "provider": active_provider(),
        "openai": bool(_openai_key()),
        "gemini": bool(_gemini_key()),
    }


# --------------------------------------------------------------------------- #
# Message helpers                                                              #
# --------------------------------------------------------------------------- #
def _split_system(messages: list[dict]) -> tuple[str, list[dict]]:
    """Return (system_text, non_system_messages)."""
    system_parts = [m["content"] for m in messages if m.get("role") == "system"]
    turns = [m for m in messages if m.get("role") != "system"]
    return "\n\n".join(system_parts), turns


# --------------------------------------------------------------------------- #
# OpenAI                                                                       #
# --------------------------------------------------------------------------- #
def _openai_client():
    from openai import OpenAI

    return OpenAI(api_key=_openai_key())


def _openai_stream(messages: list[dict]) -> Iterator[str]:
    client = _openai_client()
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    stream = client.chat.completions.create(
        model=model, messages=messages, stream=True, temperature=0.6
    )
    for chunk in stream:
        delta = chunk.choices[0].delta.content if chunk.choices else None
        if delta:
            yield delta


def _openai_complete(messages: list[dict], json_mode: bool = False) -> str:
    client = _openai_client()
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    kwargs = {"model": model, "messages": messages, "temperature": 0.2}
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}
    resp = client.chat.completions.create(**kwargs)
    return resp.choices[0].message.content or ""


# --------------------------------------------------------------------------- #
# Gemini                                                                       #
# --------------------------------------------------------------------------- #
def _gemini_client():
    from google import genai

    return genai.Client(api_key=_gemini_key())


def _gemini_contents(turns: list[dict]) -> list[dict]:
    out = []
    for m in turns:
        role = "model" if m.get("role") == "assistant" else "user"
        out.append({"role": role, "parts": [{"text": m.get("content", "")}]})
    return out


def _gemini_stream(messages: list[dict]) -> Iterator[str]:
    from google.genai import types

    client = _gemini_client()
    model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    system, turns = _split_system(messages)
    config = types.GenerateContentConfig(
        system_instruction=system or None, temperature=0.6
    )
    for chunk in client.models.generate_content_stream(
        model=model, contents=_gemini_contents(turns), config=config
    ):
        if getattr(chunk, "text", None):
            yield chunk.text


def _gemini_complete(messages: list[dict], json_mode: bool = False) -> str:
    from google.genai import types

    client = _gemini_client()
    model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    system, turns = _split_system(messages)
    config = types.GenerateContentConfig(
        system_instruction=system or None,
        temperature=0.2,
        response_mime_type="application/json" if json_mode else None,
    )
    resp = client.models.generate_content(
        model=model, contents=_gemini_contents(turns), config=config
    )
    return resp.text or ""


# --------------------------------------------------------------------------- #
# Public API                                                                   #
# --------------------------------------------------------------------------- #
def stream_chat(messages: list[dict]) -> Iterator[str]:
    """Yield response text chunks. `messages` = [{role, content}, ...]."""
    provider = active_provider()
    if provider is None:
        raise LLMNotConfigured("No LLM API key configured.")
    if provider == "openai":
        yield from _openai_stream(messages)
    else:
        yield from _gemini_stream(messages)


def complete(messages: list[dict], json_mode: bool = False) -> str:
    provider = active_provider()
    if provider is None:
        raise LLMNotConfigured("No LLM API key configured.")
    if provider == "openai":
        return _openai_complete(messages, json_mode=json_mode)
    return _gemini_complete(messages, json_mode=json_mode)


def translate_fields(fields: dict[str, str], target_lang: str) -> dict[str, str]:
    """Translate a dict of {field_name: text} into `target_lang`.

    Returns a dict with the same keys. Empty inputs are passed through.
    """
    payload = {k: v for k, v in fields.items() if (v or "").strip()}
    if not payload:
        return {k: "" for k in fields}
    system = (
        "You are a professional culinary translator for Indian recipes. "
        f"Translate the given JSON string values into {target_lang}. "
        "Preserve newlines and numbered steps. Keep quantities and units. "
        "Return ONLY a JSON object with the same keys and translated values."
    )
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
    ]
    raw = complete(messages, json_mode=True)
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        data = {}
    return {k: data.get(k, fields.get(k, "")) for k in fields}
