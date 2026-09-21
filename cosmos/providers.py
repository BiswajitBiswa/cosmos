"""Optional LLM providers for the dream cycle. Zero-dependency core; Anthropic uses the official SDK if installed."""
from __future__ import annotations

import json
import os
import urllib.request
from typing import Any, Dict, List, Optional

MEMORY_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "memories": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "category": {"type": "string", "enum": ["architecture", "decision", "convention", "constraint", "bug", "dependency", "workflow", "domain", "rejected", "finding"]},
                    "importance": {"type": "number"},
                    "merge_of": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["text", "category", "importance", "merge_of"],
                "additionalProperties": False,
            },
        },
        "contradictions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "older": {"type": "string"}, "newer": {"type": "string"},
                    "verdict": {"type": "string", "enum": ["newer_supersedes", "older_stands", "both_valid", "unclear"]},
                    "reason": {"type": "string"},
                },
                "required": ["older", "newer", "verdict", "reason"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["memories", "contradictions"],
    "additionalProperties": False,
}

CURATE_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {"items": {"type": "array", "items": {"type": "object", "properties": {
        "id": {"type": "string"}, "keep": {"type": "boolean"},
        "text": {"type": "string", "description": "the fact rewritten crisply in third person, absolute dates, no narration"},
        "category": {"type": "string", "enum": ["architecture", "decision", "convention", "constraint", "bug", "dependency", "workflow", "domain", "rejected"]},
        "lane": {"type": "string", "description": "feature / module a product manager would recognise, kebab-case; reuse an existing lane when one fits"},
        "importance": {"type": "number"}, "why_dropped": {"type": "string"}},
        "required": ["id", "keep"], "additionalProperties": False}}},
    "required": ["items"], "additionalProperties": False}

CURATE_SYSTEM = (
    "You curate engineering memory for a software team. Each candidate is a sentence captured from an AI coding session. "
    "Keep only durable, specific knowledge a new developer would need to know six months from now: architecture, decisions with "
    "reasons, conventions, constraints, bug root causes, dependency limits, workflows, domain rules. DROP narration about the "
    "session, one-off task status, speculation, questions, generic advice, anything about the AI tool itself, and anything that "
    "reads like pasted documentation or prompt text. For kept items: rewrite crisply (third person, absolute dates - today is {today}), "
    "assign the category, and assign a LANE = the feature or module a product manager would recognise (e.g. billing, auth, "
    "universe-import, payments). Prefer the existing lanes given; propose a new one only when nothing fits. Never invent facts. Candidates starting with 'Work done:' are journal lines (what was asked, files edited, commit messages): keep one only when a commit message or the ask states a durable decision or constraint, rewritten as that fact; otherwise drop it."
)

SYSTEM = (
    "You consolidate engineering memory for a software team. Input: candidate observations (id, text, category, files) "
    "and existing memories. Output only durable, specific, non-obvious facts a new developer would need: architecture, "
    "decisions with reasons, conventions, constraints, bug root causes, dependency limits, workflows, domain rules. "
    "Merge duplicates (list their ids in merge_of), rewrite in crisp third person with absolute dates (today is {today}), "
    "drop narration, speculation, one-off tasks and anything secret-like. For pairs that conflict, emit a contradiction "
    "with a verdict grounded in the evidence given."
)


def _first_json(text: str) -> Optional[Dict[str, Any]]:
    """Parse the first JSON object in a model reply (tolerates prose / code fences around it)."""
    if not text:
        return None
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        text = text[text.find("{"):] if "{" in text else text
    try:
        return json.loads(text)
    except Exception:
        pass
    start = text.find("{")
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[start:i + 1])
                except Exception:
                    return None
    return None


class Provider:
    """One method matters: complete(system, user, schema) -> dict. consolidate() is built on it."""
    name = "none"

    def complete(self, system: str, user: str, schema: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        raise NotImplementedError

    def consolidate(self, payload: Dict[str, Any], today: str) -> Optional[Dict[str, Any]]:
        return self.complete(SYSTEM.format(today=today), json.dumps(payload, ensure_ascii=False), MEMORY_SCHEMA)


class ClaudeCodeProvider(Provider):
    """Uses the developer's own Claude Code login via `claude -p` (headless). No API key, no SDK, no config.
    Slower than the API (a few seconds per call) - fine for dreams, not for hooks."""
    name = "claude-code"

    def __init__(self, model: Optional[str] = None, timeout: int = 180):
        import shutil
        self.bin = shutil.which("claude")
        if not self.bin:
            raise RuntimeError("claude CLI not on PATH")
        self.model, self.timeout = model, timeout

    def complete(self, system: str, user: str, schema: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        import subprocess
        prompt = system + "\n\nRespond with ONE JSON object only - no prose, no code fences." + (f" It must match this JSON schema: {json.dumps(schema)}" if schema else "") + "\n\nINPUT:\n" + user
        cmd = [self.bin, "-p", prompt, "--output-format", "json"]
        if self.model:
            cmd += ["--model", self.model]
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=self.timeout, cwd="/")
        try:
            env = json.loads(out.stdout)
        except Exception:
            return _first_json(out.stdout)
        if env.get("is_error"):
            raise RuntimeError(str(env.get("result", "claude -p failed"))[:200])
        return _first_json(str(env.get("result", "")))


class AnthropicProvider(Provider):
    name = "anthropic"

    def __init__(self, model: str = "claude-opus-5"):
        import anthropic  # optional dependency: pip install cosmos-dev[anthropic]
        self.client = anthropic.Anthropic()
        self.model = model

    def complete(self, system: str, user: str, schema: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        kwargs: Dict[str, Any] = {}
        if schema:
            kwargs["output_config"] = {"format": {"type": "json_schema", "schema": schema}}
        resp = self.client.messages.create(model=self.model, max_tokens=16000, system=system,
                                           messages=[{"role": "user", "content": user}], **kwargs)
        if resp.stop_reason == "refusal":
            return None
        text = next((b.text for b in resp.content if b.type == "text"), "")
        return _first_json(text)


class OpenAICompatibleProvider(Provider):
    """OpenAI / Ollama / any /v1/chat/completions endpoint. Uses stdlib only."""
    name = "openai-compatible"

    def __init__(self, model: str, base_url: str, api_key: str = ""):
        self.model, self.base_url, self.api_key = model, base_url.rstrip("/"), api_key

    def complete(self, system: str, user: str, schema: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        body = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system + (" Respond with JSON matching: " + json.dumps(schema) if schema else " Respond with one JSON object.")},
                {"role": "user", "content": user},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0,
        }
        req = urllib.request.Request(self.base_url + "/chat/completions", data=json.dumps(body).encode(),
                                     headers={"Content-Type": "application/json", **({"Authorization": f"Bearer {self.api_key}"} if self.api_key else {})})
        with urllib.request.urlopen(req, timeout=120) as r:
            data = json.loads(r.read())
        content = data["choices"][0]["message"]["content"]
        return _first_json(content)


def get_provider(cfg_llm: Dict[str, Any]) -> Optional[Provider]:
    """provider: auto (default) | claude-code | anthropic | openai | ollama | compatible | none.
    auto = Anthropic API if a key + SDK are present, else the developer's Claude Code login, else nothing."""
    prov = os.environ.get("COSMOS_LLM_PROVIDER") or (cfg_llm or {}).get("provider", "auto")
    model = (cfg_llm or {}).get("model")
    try:
        if prov == "none":
            return None
        if prov == "auto":
            if os.environ.get("ANTHROPIC_API_KEY"):
                try:
                    return AnthropicProvider(model or "claude-opus-5")
                except Exception:
                    pass
            try:
                return ClaudeCodeProvider(model)
            except Exception:
                return None
        if prov == "claude-code":
            return ClaudeCodeProvider(model)
        if prov == "anthropic":
            try:
                return AnthropicProvider(model or "claude-opus-5")
            except Exception:
                # legacy default without SDK/key: fall through to the developer's Claude Code login
                try:
                    return ClaudeCodeProvider(None)
                except Exception:
                    return None
        if prov == "openai":
            return OpenAICompatibleProvider(model or "gpt-4.1", cfg_llm.get("base_url", "https://api.openai.com/v1"), os.environ.get("OPENAI_API_KEY", ""))
        if prov == "ollama":
            return OpenAICompatibleProvider(model or "llama3.1", cfg_llm.get("base_url", "http://localhost:11434/v1"))
        if prov == "compatible":
            return OpenAICompatibleProvider(model, cfg_llm["base_url"], os.environ.get(cfg_llm.get("api_key_env", "LLM_API_KEY"), ""))
    except Exception:
        return None
    return None
