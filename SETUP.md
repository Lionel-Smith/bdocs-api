# Flask Backend Setup Guide

## 🎉 Modernization Complete!

Your Flask backend has been successfully modernized to use Python 3.11, Quart (async), PostgreSQL, Redis, and Pydantic.

## ✅ What's Been Updated

### 1. **Python & Dependencies**
- ✅ Upgraded from Python 3.7 → **Python 3.11**
- ✅ Migrated from Flask → **Quart** (async framework)
- ✅ Added **PostgreSQL** with async support (asyncpg)
- ✅ Added **Redis** for caching and rate limiting
- ✅ Added **Pydantic** for request/response validation
- ✅ Updated to **SQLAlchemy 2.0** with async support
- ✅ Replaced WSGI (Flask dev server) → **ASGI (Hypercorn)**

### 2. **New Infrastructure Created**

#### Core Application
- `src/app.py` - Async app factory with dynamic controller loading
- `src/extensions.py` - Quart extensions initialization
- `app.py` - Async entry point using Hypercorn

#### Database Layer
- `src/database/async_db.py` - PostgreSQL async engine & sessions
- `src/database/postgres_models.py` - Async base model with audit fields
- `src/database/oracle_async_wrapper.py` - Thread pool wrapper for Oracle sync operations

#### Redis Integration
- `src/cache/redis_client.py` - Async Redis client wrapper
- `src/cache/cache_decorators.py` - Caching decorators (`@cache_result`)

#### Middleware
- `src/middleware/rate_limiter.py` - Rate limiting decorator (`@rate_limit`)
- `src/middleware/validation.py` - Pydantic validation decorators

#### Validation Schemas
- `src/schemas/base.py` - Base Pydantic schemas & pagination
- `src/schemas/response.py` - Standard API response wrappers

#### Testing
- `pytest.ini` - pytest configuration with async support
- `conftest.py` - Test fixtures
- `.coveragerc` - Coverage configuration

#### Documentation
- `README.md` - Comprehensive project documentation
- `SETUP.md` - This file

### 3. **Configuration Updates**
- `config.py` - Added `PostgresDB` class for PostgreSQL configuration
- `config.py` - Added `RateLimiter.default` for easier access

## 📋 Next Steps

### Step 1: Install Dependencies

You need Python 3.11 installed. Then:

```bash
# Install pipenv if you don't have it
pip install pipenv

# Install all dependencies
pipenv install

# Install dev dependencies for testing
pipenv install --dev
```

### Step 2: Set Up PostgreSQL

1. **Install PostgreSQL 14+** if not already installed

2. **Create database:**
```sql
CREATE DATABASE flask_backend;
CREATE USER your_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE flask_backend TO your_user;
```

3. **Update config.py:**
```python
class PostgresDB:
    host = "localhost"
    port = 5432
    username = "your_user"       # Update this
    password = "your_password"    # Update this
    database = "flask_backend"
```

### Step 3: Set Up Redis

1. **Install Redis 7+**

**Windows:**
```bash
# Using WSL or Docker
docker run -d -p 6379:6379 redis:7-alpine
```

**Mac:**
```bash
brew install redis
brew services start redis
```

**Linux:**
```bash
sudo apt install redis-server
sudo systemctl start redis-server
```

2. **Verify Redis is running:**
```bash
redis-cli ping
# Should return: PONG
```

### Step 4: Run the Application

```bash
pipenv run python app.py
```

Visit http://localhost:5000 - you should see:
```json
{"status": "healthy", "message": "Hello World"}
```

### Step 5: Create Your First Controller (Optional)

Follow the examples in [README.md](README.md) to create:
1. A model (`src/models/product_model.py`)
2. Schemas (`src/schemas/product.py`)
3. A controller (`src/controllers/product_controller.py`)

The controller will be automatically discovered!

## 🔧 Configuration Notes

### Database Configuration
Both PostgreSQL and Oracle are configured:
- **PostgreSQL**: Primary async database (new)
- **Oracle**: Legacy sync database with async wrapper (existing)

You can use either or both. The Oracle configuration remains unchanged.

### Redis Configuration
Located in `config.py`:
```python
class RedisDB:
    host = "redis"  # Change to "localhost" if running locally
    port = "6379"
```

## 🧪 Running Tests

```bash
# Run all tests
pipenv run pytest

# Run with coverage
pipenv run pytest --cov=src --cov-report=html

# Run specific tests
pipenv run pytest tests/test_your_module.py -v
```

Coverage report will be in `htmlcov/index.html`

## 🐛 Troubleshooting

### "Module not found" errors
```bash
# Reinstall dependencies
pipenv install
```

### PostgreSQL connection errors
- Check PostgreSQL is running: `sudo systemctl status postgresql`
- Verify credentials in `config.py`
- Check port 5432 is accessible

### Redis connection errors
- Check Redis is running: `redis-cli ping`
- Update `RedisDB.host` in `config.py` to `"localhost"` if needed

### Import errors for `hypercorn` or `quart`
```bash
# Dependencies not yet installed
pipenv install
```

## 📚 Key Changes from Flask

### Routes must be async
```python
# OLD (Flask)
@app.route('/users')
def get_users():
    return jsonify(users)

# NEW (Quart)
@blueprint.route('/users')
async def get_users():
    return jsonify(users)
```

### Database calls need await
```python
# OLD (Flask + SQLAlchemy)
users = User.query.all()

# NEW (Quart + Async SQLAlchemy)
async with get_async_session() as session:
    result = await session.execute(select(User))
    users = result.scalars().all()
```

### Use async Redis
```python
# Caching
from src.cache.redis_client import redis_client
await redis_client.set('key', 'value', ttl=300)
value = await redis_client.get('key')
```

## 🎯 Features to Explore

1. **Rate Limiting**: Use `@rate_limit("100/minute")` on routes
2. **Caching**: Use `@cache_result(ttl=300)` on expensive functions
3. **Validation**: Use `@validate_request(YourSchema)` for request validation
4. **Pagination**: Use `PaginationParams` schema for consistent pagination
5. **Standard Responses**: Use `ApiResponse` and `ErrorResponse` schemas

## 🚀 Deployment Notes

- **Development**: Use `pipenv run python app.py` (Hypercorn with auto-reload)
- **Production**: Deploy with Hypercorn ASGI server
  - Configure workers, bind address, SSL certificates
  - See deployment guide (when created) for details

## 📝 Future Enhancements

Consider these for future iterations:
1. Environment variable configuration (Pydantic Settings)
2. OpenAPI/Swagger documentation
3. Comprehensive getting started guide
4. Example CRUD controllers with all features
5. Docker compose setup for PostgreSQL + Redis
6. CI/CD pipeline configuration

## ✨ Summary

Your Flask backend is now a modern async Python API with:
- ✅ Python 3.11
- ✅ Quart (async)
- ✅ PostgreSQL (async) + Oracle (sync wrapper)
- ✅ Redis caching & rate limiting
- ✅ Pydantic validation
- ✅ Comprehensive testing setup
- ✅ Dynamic controller loading
- ✅ Type hints throughout

Happy coding! 🎉
