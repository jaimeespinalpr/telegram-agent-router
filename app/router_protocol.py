import json
import re
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Dispatch:
    to: str
    message: str


LINE_PATTERN = re.compile(r"^@?(?P<to>[a-zA-Z0-9_-]+)\s*:\s*(?P<message>.+)$")


def parse_dispatches(text: str) -> list[Dispatch]:
    text = _strip_code_fence(text.strip())
    if not text:
        return []

    json_dispatches = _parse_json_dispatches(text)
    if json_dispatches:
        return json_dispatches

    dispatches: list[Dispatch] = []
    for line in text.splitlines():
        match = LINE_PATTERN.match(line.strip())
        if match:
            dispatches.append(
                Dispatch(to=match.group("to").strip(), message=match.group("message").strip())
            )
    return dispatches


def _strip_code_fence(text: str) -> str:
    if text.startswith("```") and text.endswith("```"):
        lines = text.splitlines()
        if len(lines) >= 3:
            return "\n".join(lines[1:-1]).strip()
    return text


def _parse_json_dispatches(text: str) -> list[Dispatch]:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return []

    items = payload if isinstance(payload, list) else [payload]
    dispatches: list[Dispatch] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        targets = item.get("to")
        message = item.get("message")
        if not targets or not isinstance(message, str):
            continue
        for target in _target_list(targets):
            dispatches.append(Dispatch(to=target, message=message.strip()))
    return dispatches


def _target_list(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value.strip().lstrip("@")]
    if isinstance(value, list):
        return [str(item).strip().lstrip("@") for item in value if str(item).strip()]
    return []
