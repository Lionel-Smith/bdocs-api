from quart_auth import QuartAuth

auth_manager = QuartAuth()


def init_extensions(app):
    """Initialize Quart extensions"""
    auth_manager.init_app(app)

    # Configure JWT-like auth
    from config import FLASK_ENV
    app.config['QUART_AUTH_COOKIE_SECURE'] = FLASK_ENV == "production"
    app.config['QUART_AUTH_DURATION'] = 86400  # 1 day in seconds
