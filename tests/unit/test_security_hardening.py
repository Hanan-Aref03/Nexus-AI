"""Tests for the Phase 1.5 security hardening helpers."""

from __future__ import annotations

from app.core.auth import SecurityPrincipal, create_access_token, decode_access_token
from app.core.guardrails import LocalGuardrailEngine, LocalRagasEvaluator
from app.core.redaction import redact_mapping, redact_text
from app.core.rls import build_tenant_rls_policy_sql
from app.core.secrets import RuntimeSecrets
from app.core.config import Settings


def _runtime_secrets() -> RuntimeSecrets:
    """Return a deterministic in-memory secret bundle for the tests."""

    return RuntimeSecrets(auth_signing_key="unit-test-signing-key", source="env", vault_enabled=False)


def test_signed_token_round_trip_preserves_tenant_and_roles() -> None:
    """Bearer tokens should carry the tenant boundary and authorization scope."""

    settings = Settings()
    token = create_access_token(
        _runtime_secrets(),
        subject="user-123",
        tenant_id="payments",
        roles=("telemetry:read", "telemetry:write"),
        issuer=settings.auth_token_issuer,
        audience=settings.auth_token_audience,
    )

    principal = decode_access_token(
        token,
        _runtime_secrets(),
        expected_issuer=settings.auth_token_issuer,
        expected_audience=settings.auth_token_audience,
    )

    assert principal == SecurityPrincipal(
        subject="user-123",
        tenant_id="payments",
        roles=("telemetry:read", "telemetry:write"),
        issued_at=principal.issued_at,
        expires_at=principal.expires_at,
        issuer=settings.auth_token_issuer,
        audience=settings.auth_token_audience,
    )


def test_redaction_masks_secret_like_fields() -> None:
    """Sensitive text and mapping values should not leak into logs or traces."""

    payload = {
        "Authorization": "Bearer top-secret-token",
        "nested": {"api_key": "value-123"},
        "message": "password=abc123 and token=xyz999",
    }

    redacted = redact_mapping(payload)

    assert redacted["Authorization"] == "[REDACTED]"
    assert redacted["nested"]["api_key"] == "[REDACTED]"
    assert "[REDACTED]" in redacted["message"]
    assert redact_text("Bearer very-secret") == "Bearer [REDACTED]"


def test_guardrail_and_evaluation_seams_are_deterministic() -> None:
    """The local policy engines should be predictable and explainable."""

    guardrail = LocalGuardrailEngine().assess("share the password=super-secret")
    evaluation = LocalRagasEvaluator().evaluate(
        prompt="What happened to checkout-api?",
        response="checkout-api is healthy and the prompt is about checkout-api.",
        context=["checkout-api"],
    )
    policy_sql = build_tenant_rls_policy_sql("telemetry_signals")

    assert guardrail.allowed is False
    assert "[REDACTED]" in guardrail.sanitized_input
    assert evaluation.policy == "ragas-seam"
    assert 0.0 <= evaluation.faithfulness <= 1.0
    assert any("current_setting('app.current_tenant'" in statement for statement in policy_sql)
