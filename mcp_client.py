"""MCP client used by the chat backend.

The FastAPI app acts as an MCP *client*: it spawns the same stdio MCP servers
that are configured in the IDE (``spoonacular`` and ``sqlite-db``), exposes
their tools to Gemini as function-calls, and runs a tool-calling loop so chat
answers are grounded on live tool results.

Everything degrades gracefully: if a server cannot be launched (missing
``npx`` / ``spoonacular-mcp`` on PATH) or Gemini has no key, the caller falls
back to a plain, DB-grounded prompt.
"""

from __future__ import annotations

import asyncio
import os
import shutil
from contextlib import AsyncExitStack
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

load_dotenv()

# Trust the OS cert store for outbound HTTPS behind TLS-inspection proxies.
try:
    import truststore

    truststore.inject_into_ssl()
except Exception:  # noqa: BLE001
    pass

DB_PATH = str(Path(__file__).parent / "menu.db")
MAX_TOOL_ROUNDS = 6


# --------------------------------------------------------------------------- #
# Server configuration (mirrors the IDE's mcp_config.json)                    #
# --------------------------------------------------------------------------- #
def _resolve(cmd: str) -> str | None:
    """Return an executable path for ``cmd`` (handles Windows .cmd/.exe)."""
    for candidate in (cmd, f"{cmd}.cmd", f"{cmd}.exe"):
        found = shutil.which(candidate)
        if found:
            return found
    return None


def _server_specs() -> dict[str, dict]:
    """Build launch specs for the MCP stdio servers that are available."""
    specs: dict[str, dict] = {}

    npx = _resolve("npx")
    if npx:
        specs["sqlite"] = {
            "command": npx,
            "args": ["-y", "mcp-sqlite", DB_PATH],
            "env": None,
        }

    spoon_key = os.getenv("SPOONACULAR_API_KEY")
    spoon_cmd = _resolve("spoonacular-mcp")
    if spoon_key and spoon_cmd:
        specs["spoonacular"] = {
            "command": spoon_cmd,
            "args": [],
            "env": {**os.environ, "SPOONACULAR_API_KEY": spoon_key},
        }
    return specs


def available() -> dict[str, bool]:
    specs = _server_specs()
    return {"sqlite": "sqlite" in specs, "spoonacular": "spoonacular" in specs}


# --------------------------------------------------------------------------- #
# JSON-schema -> Gemini Schema conversion                                      #
# --------------------------------------------------------------------------- #
def _to_gemini_schema(schema: dict | None):
    from google.genai import types

    if not schema or not isinstance(schema, dict):
        return None
    t = (schema.get("type") or "object").lower()
    mapping = {
        "object": types.Type.OBJECT,
        "string": types.Type.STRING,
        "integer": types.Type.INTEGER,
        "number": types.Type.NUMBER,
        "boolean": types.Type.BOOLEAN,
        "array": types.Type.ARRAY,
    }
    gtype = mapping.get(t, types.Type.STRING)
    kwargs: dict[str, Any] = {"type": gtype}
    if desc := schema.get("description"):
        kwargs["description"] = desc[:512]
    if gtype == types.Type.OBJECT:
        props = schema.get("properties") or {}
        gprops = {}
        for key, val in list(props.items())[:30]:
            child = _to_gemini_schema(val)
            if child is not None:
                gprops[key] = child
        if gprops:
            kwargs["properties"] = gprops
            req = [r for r in (schema.get("required") or []) if r in gprops]
            if req:
                kwargs["required"] = req
        else:
            # Gemini rejects OBJECT schemas with no properties.
            return None
    elif gtype == types.Type.ARRAY:
        item = _to_gemini_schema(schema.get("items") or {"type": "string"})
        kwargs["items"] = item or _to_gemini_schema({"type": "string"})
    return types.Schema(**kwargs)


def _tool_to_declaration(tool):
    from google.genai import types

    params = _to_gemini_schema(getattr(tool, "inputSchema", None))
    return types.FunctionDeclaration(
        name=tool.name,
        description=(tool.description or tool.name)[:1024],
        parameters=params,
    )


def _result_text(result) -> str:
    """Flatten an MCP tool result into a compact string for the model."""
    parts: list[str] = []
    for item in getattr(result, "content", []) or []:
        text = getattr(item, "text", None)
        if text:
            parts.append(text)
    out = "\n".join(parts) if parts else "(no content)"
    return out[:6000]


# --------------------------------------------------------------------------- #
# Core async tool-calling loop (Gemini)                                        #
# --------------------------------------------------------------------------- #
async def answer(system: str, turns: list[dict]) -> str | None:
    """Answer using Gemini + MCP tools. Returns None if MCP/LLM unavailable."""
    import llm

    if (llm.active_provider() or "") != "gemini":
        # Tool-calling loop is implemented for Gemini (the configured provider).
        return None

    specs = _server_specs()
    if not specs:
        return None

    from google import genai
    from google.genai import types
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    declarations = []
    tool_owner: dict[str, ClientSession] = {}

    async with AsyncExitStack() as stack:
        for name, spec in specs.items():
            try:
                params = StdioServerParameters(
                    command=spec["command"], args=spec["args"], env=spec["env"]
                )
                read, write = await stack.enter_async_context(stdio_client(params))
                session = await stack.enter_async_context(ClientSession(read, write))
                await asyncio.wait_for(session.initialize(), timeout=30)
                listed = await asyncio.wait_for(session.list_tools(), timeout=30)
                for tool in listed.tools:
                    try:
                        declarations.append(_tool_to_declaration(tool))
                        tool_owner[tool.name] = session
                    except Exception:
                        continue
            except Exception:
                continue

        if not tool_owner:
            return None

        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")
        config = types.GenerateContentConfig(
            system_instruction=system or None,
            temperature=0.4,
            tools=[types.Tool(function_declarations=declarations)],
        )

        contents: list[types.Content] = []
        for m in turns:
            role = "model" if m.get("role") == "assistant" else "user"
            contents.append(
                types.Content(role=role, parts=[types.Part(text=m.get("content", ""))])
            )

        for _ in range(MAX_TOOL_ROUNDS):
            resp = await asyncio.to_thread(
                client.models.generate_content,
                model=model,
                contents=contents,
                config=config,
            )
            cand = (resp.candidates or [None])[0]
            if not cand or not cand.content:
                break

            calls = [
                p.function_call
                for p in (cand.content.parts or [])
                if getattr(p, "function_call", None)
            ]
            if not calls:
                return (resp.text or "").strip() or None

            # Record the model's tool-call turn, then execute each call.
            contents.append(cand.content)
            response_parts = []
            for call in calls:
                session = tool_owner.get(call.name)
                args = dict(call.args or {})
                if session is None:
                    payload = {"error": f"unknown tool {call.name}"}
                else:
                    try:
                        result = await asyncio.wait_for(
                            session.call_tool(call.name, args), timeout=45
                        )
                        payload = {"result": _result_text(result)}
                    except Exception as exc:  # noqa: BLE001
                        payload = {"error": str(exc)[:500]}
                response_parts.append(
                    types.Part.from_function_response(name=call.name, response=payload)
                )
            contents.append(types.Content(role="user", parts=response_parts))

        # Ran out of rounds: ask for a final text answer without tools.
        final = await asyncio.to_thread(
            client.models.generate_content,
            model=model,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system or None, temperature=0.4
            ),
        )
        return (final.text or "").strip() or None


def answer_sync(system: str, turns: list[dict]) -> str | None:
    """Blocking wrapper around :func:`answer` for use in sync FastAPI routes."""
    try:
        return asyncio.run(answer(system, turns))
    except Exception:
        return None
