"""Runtime secret loading with a Vault seam and a local-development fallback."""

from __future__ import annotations

import json
from dataclasses import dataclass
from os import getenv
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.core.config import Settings


@dataclass(frozen=True)
class RuntimeSecrets:
    """Secrets that the backend needs at runtime."""

    auth_signing_key: str
    source: str
    vault_enabled: bool


def _fetch_vault_json(settings: Settings) -> dict[str, object]:
    """Fetch a KV v2 secret payload from Vault if Vault is configured."""

    token = settings.vault_token or getenv("VAULT_TOKEN")
    if not token:
        raise RuntimeError("Vault is configured, but no Vault token was provided.")

    vault_url = settings.vault_address.rstrip("/")
    secret_path = settings.vault_secret_path.strip("/")
    mount = settings.vault_secret_mount.strip("/")
    request_url = f"{vault_url}/v1/{mount}/data/{secret_path}"

    request = Request(
        request_url,
        headers={
            "Accept": "application/json",
            "X-Vault-Token": token,
        },
    )

    try:
        with urlopen(request, timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError) as exc:  # pragma: no cover - network-specific
        raise RuntimeError(f"Unable to load secrets from Vault at {request_url}.") from exc

    data = payload.get("data", {})
    if not isinstance(data, dict):
        raise RuntimeError("Vault returned an unexpected secret payload.")

    nested = data.get("data", {})
    if not isinstance(nested, dict):
        raise RuntimeError("Vault secret payload is missing the KV v2 data envelope.")

    return nested


def build_runtime_secrets(settings: Settings) -> RuntimeSecrets:
    """Build runtime secrets from Vault or fall back to the local env value."""

    if settings.vault_address:
        secret_payload = _fetch_vault_json(settings)
        signing_key = str(secret_payload.get("auth_signing_key") or settings.auth_signing_key)
        return RuntimeSecrets(
            auth_signing_key=signing_key,
            source="vault",
            vault_enabled=True,
        )

    return RuntimeSecrets(
        auth_signing_key=settings.auth_signing_key,
        source="env",
        vault_enabled=False,
    )
