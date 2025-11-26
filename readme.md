# Flask Backend - Modern Async Python API

A production-ready async Python backend starter template built with **Quart**, supporting dual databases (PostgreSQL async + Oracle sync), Redis caching, comprehensive API validation, and automatic documentation.

## ✨ Features

- **Async/Await Support**: Built on Quart for high-performance async operations
- **Dual Database Support**:
  - PostgreSQL (async via asyncpg) - Primary database
  - Oracle (sync via cx_Oracle with async wrapper) - Legacy support
- **Redis Integration**: Caching and rate limiting with async client
- **API Validation**: Pydantic schemas for request/response validation
- **Security**: JWT authentication via Quart-Auth
- **Dynamic Loading**: Automatic controller and model discovery
- **3-Layer Architecture**: Clean separation (Controllers → Services → Data Access)
- **Type Safety**: Comprehensive type hints throughout
- **Testing Ready**: pytest with async support, fixtures, and factories

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 14+ (primary database)
- Redis 7+ (caching and rate limiting)
- Oracle Database (optional, for legacy support)

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd flask-backend
```

2. **Install dependencies**
```bash
pip install pipenv
pipenv install
```

3. **Configure database settings**

Edit [config.py](config.py) and update the `PostgresDB` class:
```python
class PostgresDB:
    host = "localhost"
    port = 5432
    username = "your_postgres_user"
    password = "your_password"
    database = "flask_backend"
```

4. **Run the application**
```bash
pipenv run python app.py
```

Visit http://localhost:5000 to verify the application is running.

## 📁 Project Structure

```
flask-backend/
├── app.py                      # ASGI entry point (Hypercorn)
├── config.py                   # Configuration classes
├── Pipfile                     # Dependencies (Python 3.11)
├── src/
│   ├── app.py                  # Async app factory
│   ├── extensions.py           # Quart extensions
│   ├── database/
│   │   ├── async_db.py         # PostgreSQL async connections
│   │   ├── postgres_models.py  # Async base model
│   │   ├── oracle_async_wrapper.py  # Oracle thread pool wrapper
│   │   ├── oracle_db_service.py     # Oracle sync service
│   │   ├── baseModel.py        # Oracle ORM base
│   │   └── scripts/            # Database setup SQL
│   ├── models/                 # Auto-discovered *_model.py
│   ├── controllers/            # Auto-discovered *_controller.py
│   ├── schemas/                # Pydantic validation schemas
│   │   ├── base.py             # Base schemas
│   │   └── response.py         # API response wrappers
│   ├── cache/
│   │   ├── redis_client.py     # Async Redis wrapper
│   │   └── cache_decorators.py # Caching decorators
│   └── middleware/
│       ├── rate_limiter.py     # Rate limiting
│       └── validation.py       # Request validation
├── tests/                      # Test suites
└── docs/                       # Documentation

```

## 🎯 Creating Your First Endpoint

### 1. Create a Model

Create `src/models/product_model.py`:
```python
from sqlalchemy import Column, String, Numeric, Text
from src.database.postgres_models import AsyncBaseModel

class Product(AsyncBaseModel):
    __tablename__ = 'products'

    name = Column(String(200), nullable=False)
    description = Column(Text)
    price = Column(Numeric(10, 2), nullable=False)
    sku = Column(String(50), unique=True, nullable=False)
```

### 2. Create Validation Schemas

Create `src/schemas/product.py`:
```python
from pydantic import Field
from decimal import Decimal
from src.schemas.base import BaseSchema, TimestampMixin

class ProductCreateSchema(BaseSchema):
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    price: Decimal = Field(..., gt=0)
    sku: str = Field(..., min_length=1, max_length=50)

class ProductResponseSchema(ProductCreateSchema, TimestampMixin):
    id: int
```

### 3. Create a Controller

Create `src/controllers/product_controller.py`:
```python
from quart import Blueprint, jsonify
from src.database.async_db import get_async_session
from src.models.product_model import Product
from src.schemas.product import ProductCreateSchema, ProductResponseSchema
from src.schemas.response import ApiResponse
from src.middleware.validation import validate_request
from src.middleware.rate_limiter import rate_limit

blueprint = Blueprint('products', __name__, url_prefix='/api/products')

@blueprint.route('/', methods=['POST'])
@rate_limit("10/minute")
@validate_request(ProductCreateSchema)
async def create_product(validated_data: ProductCreateSchema):
    async with get_async_session() as session:
        product = Product(**validated_data.model_dump())
        session.add(product)
        await session.commit()
        await session.refresh(product)

        response_data = ProductResponseSchema.model_validate(product)
        return jsonify(ApiResponse(
            data=response_data.model_dump(),
            message="Product created successfully"
        ).model_dump()), 201
```

The controller will be **automatically discovered and loaded** at startup!

## 🔧 Key Concepts

### Dynamic Module Loading

Controllers and models are automatically discovered based on naming convention:
- **Controllers**: `*_controller.py` files anywhere in `src/`
- **Models**: `*_model.py` files anywhere in `src/`

No manual imports needed!

### Async Database Access

```python
from src.database.async_db import get_async_session

async with get_async_session() as session:
    result = await session.execute(select(Product))
    products = result.scalars().all()
```

### Caching

```python
from src.cache.cache_decorators import cache_result

@cache_result(ttl=300, key_prefix="products")
async def get_products():
    # Cached for 5 minutes
    return await fetch_products()
```

### Rate Limiting

```python
from src.middleware.rate_limiter import rate_limit

@rate_limit("100/minute")
async def my_route():
    return "Limited to 100 requests per minute"
```

### Request Validation

```python
from src.middleware.validation import validate_request

@validate_request(MySchema)
async def create_item(validated_data: MySchema):
    # validated_data is already a Pydantic model
    return validated_data.model_dump()
```

## 🧪 Testing

```bash
# Run all tests
pipenv run pytest

# Run with coverage
pipenv run pytest --cov=src --cov-report=html

# Run specific test file
pipenv run pytest tests/test_product_controller.py
```

## 📚 Documentation

- [Getting Started Guide](docs/GETTING_STARTED.md) - Detailed setup and first controller
- [Architecture Overview](docs/ARCHITECTURE.md) - System design and patterns
- [Database Setup](docs/DATABASE_SETUP.md) - Database configuration
- [API Documentation](docs/API.md) - API endpoints
- [Deployment Guide](docs/DEPLOYMENT.md) - Production deployment

## 🔄 Migration from Flask

This starter has been migrated from Flask to Quart. Key changes:
- All routes must be `async def`
- Database calls require `await`
- Uses Hypercorn (ASGI) instead of Flask dev server
- SQLAlchemy 2.0 async syntax

## 🤝 Contributing

1. Create controllers following the `*_controller.py` naming convention
2. Add models as `*_model.py` files
3. Use Pydantic schemas for validation
4. Write tests in the `tests/` directory
5. Follow the 3-layer architecture pattern

## 📝 License

[Your License Here]

## 🆘 Support

For issues and questions, please open an issue on GitHub.