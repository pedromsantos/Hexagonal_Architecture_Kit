#!/usr/bin/env python3
"""
Katacombs API - Text-based adventure game API
Following DDD and Hexagonal Architecture principles
"""

import uvicorn
from src.katacombs.infrastructure.adapters.fastapi_app import create_app


def main():
    """Main entry point for the application"""
    app = create_app()
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
