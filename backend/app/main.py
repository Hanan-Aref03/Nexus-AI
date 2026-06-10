"""ASGI entrypoint for the NexusAI backend."""

from app.factory import create_app

app = create_app()

