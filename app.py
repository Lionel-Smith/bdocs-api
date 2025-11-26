import os
import sys
from hypercorn.config import Config
from hypercorn.asyncio import serve
import asyncio

ROOT_PATH = os.path.dirname(os.path.realpath(__file__))
os.environ.update({'ROOT_PATH': ROOT_PATH})
sys.path.append(os.path.join(ROOT_PATH, 'src'))

from src.app import create_app
from config import Flask as FlaskConfig, FLASK_ENV


async def main():
    """Main entry point for Quart application"""
    app = await create_app()

    config = Config()
    config.bind = [f"{FlaskConfig.host}:{FlaskConfig.port}"]
    config.use_reloader = FLASK_ENV == "development"
    config.accesslog = "-" if FLASK_ENV == "development" else None

    print(f"Starting Quart application on {FlaskConfig.host}:{FlaskConfig.port}")
    print(f"Environment: {FLASK_ENV}")

    await serve(app, config)


if __name__ == '__main__':
    asyncio.run(main())