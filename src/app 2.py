import os
import glob
import importlib.util
from quart import Quart, jsonify
from quart_cors import cors
from config import JWTConfig
from src.database.async_db import init_db, close_db
from src.cache.redis_client import redis_client
from src.extensions import init_extensions


async def create_app() -> Quart:
    """Application factory for creating Quart app instance"""
    app = Quart(__name__, template_folder="templates")

    # Apply CORS
    app = cors(app, allow_origin="*")

    # Configure app
    app.config['JSON_AS_ASCII'] = False
    app.config['SECRET_KEY'] = JWTConfig.secret

    # Initialize extensions
    init_extensions(app)

    # Database and Redis initialization
    @app.before_serving
    async def startup():
        await init_db()
        await redis_client.connect()

    @app.after_serving
    async def shutdown():
        await close_db()
        await redis_client.close()

    # Import models module to trigger dynamic model loading
    import src.models  # noqa: F401 - imported for side effects (dynamic *_model.py discovery)

    # Dynamically load controllers
    await load_controllers(app)

    # Register error handlers
    register_error_handlers(app)

    # Health check endpoint
    @app.route('/')
    async def index():
        return jsonify({"status": "healthy", "message": "Hello World"}), 200

    return app


async def load_controllers(app: Quart):
    """Dynamically load all *_controller.py files"""
    root_path = os.path.dirname(os.path.dirname(__file__))
    pattern = os.path.join(root_path, "src", "**", "*_controller.py")

    for filepath in glob.glob(pattern, recursive=True):
        module_name = os.path.basename(filepath)[:-3]
        spec = importlib.util.spec_from_file_location(module_name, filepath)
        if spec and spec.loader:
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)

            # Register blueprint if controller defines one
            if hasattr(mod, 'blueprint'):
                app.register_blueprint(mod.blueprint)


def register_error_handlers(app: Quart):
    """Register global error handlers"""
    from werkzeug.exceptions import HTTPException
    import json

    @app.errorhandler(HTTPException)
    async def handle_http_exception(e):
        response = await e.get_response()
        response.data = json.dumps({
            "code": e.code,
            "name": e.name,
            "description": e.description,
        })
        response.content_type = "application/json"
        return response

    @app.errorhandler(Exception)
    async def handle_generic_exception(e):
        app.logger.error(f"Unhandled exception: {str(e)}", exc_info=True)
        from config import FLASK_ENV
        return jsonify({
            "error": "Internal server error",
            "message": str(e) if FLASK_ENV == "development" else "An unexpected error occurred"
        }), 500
