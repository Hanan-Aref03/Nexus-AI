"""Request tracing middleware.

This middleware keeps the implementation explicit and easy to follow without
depending on an extra instrumentation package.
"""

from __future__ import annotations

from typing import Callable

from fastapi import Request
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


class OpenTelemetryMiddleware(BaseHTTPMiddleware):
    """Create one request span per inbound HTTP call."""

    async def dispatch(self, request: Request, call_next: Callable[[Request], Response]) -> Response:
        tracer = trace.get_tracer("nexusai.http")
        span_name = f"{request.method} {request.url.path}"

        with tracer.start_as_current_span(span_name) as span:
            span.set_attribute("http.method", request.method)
            span.set_attribute("http.target", request.url.path)
            span.set_attribute("http.scheme", request.url.scheme)
            if request.client:
                span.set_attribute("net.peer.ip", request.client.host)

            try:
                response = await call_next(request)
            except Exception as exc:  # pragma: no cover - exercised in failure paths
                span.record_exception(exc)
                span.set_status(Status(StatusCode.ERROR, str(exc)))
                raise

            span.set_attribute("http.status_code", response.status_code)
            if response.status_code >= 500:
                span.set_status(Status(StatusCode.ERROR))
            return response

