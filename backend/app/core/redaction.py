"""Redaction helpers for logs, traces, and audit payloads.

The first security hardening slice keeps sensitive data out of observability
signals by redacting keys and free-text patterns before they are emitted.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any


REDACTED_VALUE = "[REDACTED]"

SENSITIVE_KEY_MARKERS = (
    "authorization",
    "access_token",
    "refresh_token",
    "api_key",
    "apikey",
    "client_secret",
    "password",
    "private_key",
    "secret",
    "token",
    "vault_token",
    "jwt",
)

TEXT_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (
        re.compile(r"(?i)(authorization\s*:\s*bearer\s+)([A-Za-z0-9\-._~+/=]+)"),
        r"\1[REDACTED]",
    ),
    (
        re.compile(r"(?i)(bearer\s+)([A-Za-z0-9\-._~+/=]+)"),
        r"\1[REDACTED]",
    ),
    (
        re.compile(r"(?i)(\b(?:api[_-]?key|secret|password|token|client_secret|private_key)\b\s*[:=]\s*)([^,\s]+)"),
        r"\1[REDACTED]",
    ),
)


def _is_sensitive_key(key: str) -> bool:
    """Return `True` when a mapping key likely contains secret material."""

    lowered = key.lower()
    return any(marker in lowered for marker in SENSITIVE_KEY_MARKERS)


def redact_text(value: str) -> str:
    """Redact common secret-like patterns from free-form text."""

    redacted = value
    for pattern, replacement in TEXT_PATTERNS:
        redacted = pattern.sub(replacement, redacted)
    return redacted


def redact_value(value: Any) -> Any:
    """Redact arbitrary nested values while preserving safe structure."""

    if isinstance(value, str):
        return redact_text(value)

    if isinstance(value, Mapping):
        return redact_mapping(value)

    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray, str)):
        return [redact_value(item) for item in value]

    return value


def redact_mapping(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Redact mapping keys recursively without flattening the payload."""

    redacted: dict[str, Any] = {}
    for key, value in payload.items():
        if _is_sensitive_key(str(key)):
            redacted[str(key)] = REDACTED_VALUE
        else:
            redacted[str(key)] = redact_value(value)
    return redacted
