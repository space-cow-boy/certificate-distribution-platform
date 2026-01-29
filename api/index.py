"""Vercel Serverless Function entrypoint.

This exposes the FastAPI `app` for the Python runtime (ASGI).
Routes are rewritten in `vercel.json` so `/verify`, `/certificate`, etc map here.
"""

from app.main import app as fastapi_app

app = fastapi_app
