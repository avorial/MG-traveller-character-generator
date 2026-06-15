"""
ai_narrative.py — Turn the factual capsule into an actual story using the
player's own AI ("bring your own key").

Two provider paths:
  • "anthropic"           — official Anthropic SDK (Claude). Default model
                            claude-opus-4-8; adaptive thinking enabled.
  • "openai_compatible"   — any OpenAI-style /chat/completions endpoint:
                            Ollama, LM Studio, OpenRouter, OpenAI, LiteLLM…

The API key is supplied per-request by the client (it lives in the player's
browser localStorage) and is never stored server-side. The template capsule
from generate_capsule() is used as the fact sheet the model must stay
faithful to, so the story can't drift from the actual lifepath.
"""
from __future__ import annotations

import re
from typing import Optional

import httpx

from .character import Character


class AIStoryError(Exception):
    """Provider/transport failure with an HTTP status to surface to the client."""

    def __init__(self, status_code: int, detail: str):
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


TONES: dict[str, str] = {
    "neutral":  "Plain, grounded prose — let the events speak for themselves.",
    "gritty":   "Gritty and hard-edged — decades in the service leave scars, debts and regrets.",
    "noir":     "Noir — cynical, atmospheric, shadows and bad decisions remembered over a drink.",
    "military": "Military memoir — terse, professional, understated dry wit.",
    "pulp":     "Pulp adventure — energetic, colourful, larger than life.",
}

_SYSTEM_PROMPT = (
    "You are a skilled science-fiction author who writes character backstories "
    "for the Traveller roleplaying game (Mongoose 2nd edition, the Charted Space "
    "setting). You write tight, evocative prose with concrete detail."
)


def build_story_prompt(character: Character, tone: str) -> tuple[str, str]:
    """Return (system_prompt, user_prompt) for the story request."""
    # Import here to avoid a circular import (lifepath imports nothing from us).
    from . import lifepath

    facts = lifepath.generate_capsule(character)["capsule"]
    tone_line = TONES.get(tone, TONES["neutral"])

    # NPC flavour: weave in the Character Quirk and (for patrons) the Patron role.
    flavour = ""
    extra_rules = ""
    if getattr(character, "npc_patron_type", None):
        flavour += f"\n- This character is a Patron of type: {character.npc_patron_type}."
        extra_rules += ("\n- This is a patron NPC the player characters might work for; "
                        "reflect their patron role naturally in the story.")
    if getattr(character, "npc_quirk", None):
        flavour += f"\n- Defining character quirk: {character.npc_quirk}."
        extra_rules += ("\n- Work the character quirk into the story so it comes through "
                        "in their personality or situation.")

    user = (
        "Write a 400-600 word backstory for the Traveller character described "
        "by the fact sheet below.\n\n"
        "Rules:\n"
        "- Stay strictly faithful to the facts: do not invent major events, "
        "change ranks or careers, alter ages, or rename any person. You may "
        "add small sensory and emotional detail that fits between the facts.\n"
        "- Third person, past tense.\n"
        f"- Tone: {tone_line}\n"
        "- Plain prose only: no headings, no bullet points, no markdown. "
        "Separate paragraphs with a blank line.\n"
        "- Do not mention game mechanics, dice, terms, or rules."
        f"{extra_rules}\n\n"
        f"FACT SHEET\n----------\n{facts}{flavour}"
    )
    return _SYSTEM_PROMPT, user


def _clean_story(text: str) -> str:
    """Strip markdown fences/headers the model might add despite instructions."""
    t = (text or "").strip()
    t = re.sub(r"^```[a-z]*\n?", "", t)
    t = re.sub(r"\n?```$", "", t)
    t = re.sub(r"^#{1,4}\s+.*\n+", "", t)  # drop a leading heading line
    return t.strip()


def _story_via_anthropic(system: str, user: str, api_key: str,
                         model: str, base_url: Optional[str]) -> str:
    try:
        import anthropic
    except ImportError as exc:  # pragma: no cover — dependency is in requirements
        raise AIStoryError(500, "The 'anthropic' package is not installed on the server.") from exc

    if not api_key:
        raise AIStoryError(400, "An Anthropic API key is required for the Claude provider.")

    client_kwargs: dict = {"api_key": api_key, "max_retries": 1, "timeout": 180.0}
    if base_url:
        client_kwargs["base_url"] = base_url
    client = anthropic.Anthropic(**client_kwargs)

    try:
        response = client.messages.create(
            model=model or "claude-opus-4-8",
            max_tokens=16000,
            thinking={"type": "adaptive"},
            system=system,
            messages=[{"role": "user", "content": user}],
        )
    except anthropic.AuthenticationError as exc:
        raise AIStoryError(401, "Invalid Anthropic API key.") from exc
    except anthropic.PermissionDeniedError as exc:
        raise AIStoryError(403, "This Anthropic API key lacks permission for that model.") from exc
    except anthropic.NotFoundError as exc:
        raise AIStoryError(404, f"Unknown Claude model: '{model}'.") from exc
    except anthropic.RateLimitError as exc:
        raise AIStoryError(429, "Anthropic rate limit hit — wait a moment and try again.") from exc
    except anthropic.BadRequestError as exc:
        raise AIStoryError(400, f"Claude rejected the request: {exc.message}") from exc
    except anthropic.APIConnectionError as exc:
        raise AIStoryError(502, "Could not reach the Anthropic API — check your network.") from exc
    except anthropic.APIStatusError as exc:
        raise AIStoryError(502, f"Anthropic API error ({exc.status_code}).") from exc

    story = "".join(block.text for block in response.content if block.type == "text")
    if not story.strip():
        raise AIStoryError(502, "Claude returned an empty story — try again.")
    return _clean_story(story)


def _story_via_openai_compatible(system: str, user: str, api_key: str,
                                 model: str, base_url: Optional[str]) -> str:
    if not base_url:
        raise AIStoryError(400, "A base URL is required for an OpenAI-compatible provider "
                                "(e.g. http://localhost:11434/v1 for Ollama).")
    if not model:
        raise AIStoryError(400, "A model name is required (e.g. 'llama3.1' for Ollama).")

    url = base_url.rstrip("/") + "/chat/completions"
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "max_tokens": 2048,
    }

    try:
        # Local models can be slow to first token — be generous.
        resp = httpx.post(url, json=payload, headers=headers, timeout=300.0)
    except httpx.ConnectError as exc:
        raise AIStoryError(
            502,
            f"Could not connect to {base_url}. If the app runs in Docker and the model is on "
            f"the host, use http://host.docker.internal:<port>/v1 instead of localhost.",
        ) from exc
    except httpx.TimeoutException as exc:
        raise AIStoryError(504, "The AI endpoint timed out — local models can be slow; try again.") from exc
    except httpx.HTTPError as exc:
        raise AIStoryError(502, f"HTTP error talking to the AI endpoint: {exc}") from exc

    if resp.status_code == 401:
        raise AIStoryError(401, "The AI endpoint rejected the API key.")
    if resp.status_code == 404:
        raise AIStoryError(404, f"The AI endpoint returned 404 — check the base URL and that "
                                f"model '{model}' exists.")
    if resp.status_code != 200:
        snippet = resp.text[:200]
        raise AIStoryError(502, f"AI endpoint error {resp.status_code}: {snippet}")

    try:
        data = resp.json()
        story = data["choices"][0]["message"]["content"]
    except (ValueError, KeyError, IndexError, TypeError) as exc:
        raise AIStoryError(502, "The AI endpoint returned an unexpected response shape.") from exc

    if not (story or "").strip():
        raise AIStoryError(502, "The AI returned an empty story — try again.")
    return _clean_story(story)


def generate_ai_story(character: Character, provider: str, api_key: str,
                      model: str, base_url: Optional[str], tone: str) -> dict:
    """Generate a narrative story for *character* via the chosen provider.

    Returns {"story": str, "provider": str, "model": str}. Raises AIStoryError
    with a client-appropriate status code on any failure.
    """
    system, user = build_story_prompt(character, tone)
    if provider == "anthropic":
        story = _story_via_anthropic(system, user, api_key, model, base_url)
        used_model = model or "claude-opus-4-8"
    elif provider == "openai_compatible":
        story = _story_via_openai_compatible(system, user, api_key, model, base_url)
        used_model = model
    else:
        raise AIStoryError(400, f"Unknown provider: '{provider}' "
                                f"(use 'anthropic' or 'openai_compatible').")
    return {"story": story, "provider": provider, "model": used_model}
