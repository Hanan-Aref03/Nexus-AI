"""Authentication and authorization helpers for the Phase 1.5 hardening slice."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, Iterable

from fastapi import Depends, Header, HTTPException, Request, status
from opentelemetry import trace

from app.core.redaction import redact_mapping
from app.core.secrets import RuntimeSecrets


logger = logging.getLogger("nexusai.security")

TOKEN_PREFIX = "nexusai.v1"


class AuthenticationError(ValueError):
    """Raised when a bearer token is missing or invalid."""


@dataclass(frozen=True, slots=True)
class SecurityPrincipal:
    """Authenticated actor and their tenant-scoped permissions."""

    subject: str
    tenant_id: str
    roles: tuple[str, ...]
    issued_at: datetime
    expires_at: datetime
    issuer: str
    audience: str

    def has_role(self, role: str) -> bool:
        """Return `True` when the principal is allowed to use a specific role."""

        return role in self.roles

    def has_any_role(self, required_roles: Iterable[str]) -> bool:
        """Return `True` when any required role is granted to the principal."""

        return any(role in self.roles for role in required_roles)


def _encode_base64url(value: bytes) -> str:
    """Encode bytes in a URL-safe form without trailing padding."""

    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _decode_base64url(value: str) -> bytes:
    """Decode a URL-safe string that may be missing padding."""

    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(f"{value}{padding}")


def _sign_payload(payload_segment: str, signing_key: str) -> str:
    """Create an HMAC signature for a token payload."""

    signature = hmac.new(
        signing_key.encode("utf-8"),
        payload_segment.encode("ascii"),
        hashlib.sha256,
    ).digest()
    return _encode_base64url(signature)


def create_access_token(
    runtime_secrets: RuntimeSecrets,
    *,
    subject: str,
    tenant_id: str,
    roles: Iterable[str],
    issuer: str,
    audience: str,
    expires_in_minutes: int = 60,
) -> str:
    """Create a signed bearer token for tests, demos, and local development.

    The first security PR keeps the token format intentionally small and local
    so the app can prove authz, tenant scoping, and audit logging without
    pulling in a full identity provider yet.
    """

    issued_at = datetime.now(UTC)
    expires_at = issued_at + timedelta(minutes=expires_in_minutes)
    payload = {
        "aud": audience,
        "exp": int(expires_at.timestamp()),
        "iat": int(issued_at.timestamp()),
        "iss": issuer,
        "roles": sorted(set(roles)),
        "sub": subject,
        "tenant_id": tenant_id,
    }
    payload_segment = _encode_base64url(json.dumps(payload, sort_keys=True).encode("utf-8"))
    signature_segment = _sign_payload(payload_segment, runtime_secrets.auth_signing_key)
    return f"{TOKEN_PREFIX}.{payload_segment}.{signature_segment}"


def decode_access_token(
    token: str,
    runtime_secrets: RuntimeSecrets,
    *,
    expected_issuer: str,
    expected_audience: str,
) -> SecurityPrincipal:
    """Validate a bearer token and convert it into a security principal."""

    token_parts = token.split(".")
    if len(token_parts) != 4 or token_parts[0] != "nexusai" or token_parts[1] != "v1":
        raise AuthenticationError("Unsupported bearer token format.")

    _, _, encoded_payload, encoded_signature = token_parts
    expected_signature = _sign_payload(encoded_payload, runtime_secrets.auth_signing_key)
    if not hmac.compare_digest(expected_signature, encoded_signature):
        raise AuthenticationError("Bearer token signature verification failed.")

    try:
        payload_bytes = _decode_base64url(encoded_payload)
        payload = json.loads(payload_bytes.decode("utf-8"))

        roles = payload.get("roles", [])
        if not isinstance(roles, list):
            raise AuthenticationError("Bearer token roles are invalid.")

        issued_at = datetime.fromtimestamp(int(payload["iat"]), tz=UTC)
        expires_at = datetime.fromtimestamp(int(payload["exp"]), tz=UTC)
        now = datetime.now(UTC)
        if expires_at <= now:
            raise AuthenticationError("Bearer token has expired.")

        issuer = str(payload["iss"])
        audience = str(payload["aud"])
        if issuer != expected_issuer:
            raise AuthenticationError("Bearer token issuer mismatch.")
        if audience != expected_audience:
            raise AuthenticationError("Bearer token audience mismatch.")

        return SecurityPrincipal(
            subject=str(payload["sub"]),
            tenant_id=str(payload["tenant_id"]),
            roles=tuple(str(role) for role in roles),
            issued_at=issued_at,
            expires_at=expires_at,
            issuer=issuer,
            audience=audience,
        )
    except AuthenticationError:
        raise
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise AuthenticationError("Bearer token payload is invalid.") from exc


def _trace_identifier() -> str | None:
    """Return the current trace id in hex form when tracing is active."""

    span = trace.get_current_span()
    context = span.get_span_context()
    if not context.is_valid:
        return None
    return f"{context.trace_id:032x}"


def emit_security_event(
    request: Request | None,
    *,
    action: str,
    outcome: str,
    principal: SecurityPrincipal | None = None,
    details: dict[str, Any] | None = None,
) -> None:
    """Emit a SIEM-friendly audit event with sensitive fields redacted."""

    payload: dict[str, Any] = {
        "action": action,
        "outcome": outcome,
        "principal": None
        if principal is None
        else {
            "subject": principal.subject,
            "tenant_id": principal.tenant_id,
            "roles": list(principal.roles),
        },
        "request_id": getattr(getattr(request, "state", None), "request_id", None),
        "trace_id": _trace_identifier(),
        "details": details or {},
    }
    logger.info(json.dumps(redact_mapping(payload), sort_keys=True))


async def get_current_principal(
    request: Request,
    authorization: str | None = Header(default=None),
) -> SecurityPrincipal:
    """Authenticate the caller with a signed bearer token."""

    if not authorization:
        emit_security_event(request, action="auth.authenticate", outcome="denied")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        emit_security_event(request, action="auth.authenticate", outcome="denied")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header must use Bearer authentication.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    settings = request.app.state.settings
    runtime_secrets = request.app.state.runtime_secrets
    try:
        principal = decode_access_token(
            token,
            runtime_secrets,
            expected_issuer=settings.auth_token_issuer,
            expected_audience=settings.auth_token_audience,
        )
    except AuthenticationError as exc:
        emit_security_event(
            request,
            action="auth.authenticate",
            outcome="denied",
            details={"reason": str(exc)},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    span = trace.get_current_span()
    if span.is_recording():
        span.set_attribute("enduser.id", principal.subject)
        span.set_attribute("enduser.scope", ",".join(principal.roles))
        span.set_attribute("nexusai.tenant_id", principal.tenant_id)

    emit_security_event(request, action="auth.authenticate", outcome="allowed", principal=principal)
    return principal


def require_roles(*required_roles: str):
    """Build a FastAPI dependency that enforces role-based authorization."""

    async def dependency(
        request: Request,
        principal: SecurityPrincipal = Depends(get_current_principal),
    ) -> SecurityPrincipal:
        if not principal.has_any_role(required_roles):
            emit_security_event(
                request,
                action="auth.authorize",
                outcome="denied",
                principal=principal,
                details={"required_roles": list(required_roles)},
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Missing required role.",
            )

        emit_security_event(
            request,
            action="auth.authorize",
            outcome="allowed",
            principal=principal,
            details={"required_roles": list(required_roles)},
        )
        return principal

    return dependency
