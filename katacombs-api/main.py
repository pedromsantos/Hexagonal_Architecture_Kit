"""Katacombs API - Text-based adventure game API
Following DDD and Hexagonal Architecture principles
"""

import uvicorn

from src.katacombs.infrastructure.adapters.fastapi_app import create_app


def main() -> None:
    """Main entry point for the application."""
    app = create_app()
    uvicorn.run(app, host="127.0.0.1", port=8000)


if __name__ == "__main__":
    main()
