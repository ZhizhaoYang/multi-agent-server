"""
Main entry point for the Multi-Agent Server.
This file imports and exposes the FastAPI app for uvicorn.
"""

from app.main import app

# Export the app for uvicorn to find
__all__ = ["app"]
