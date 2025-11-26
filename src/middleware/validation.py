from functools import wraps
from typing import Type
from quart import request, jsonify
from pydantic import BaseModel, ValidationError
from src.schemas.response import ErrorResponse


def validate_request(schema: Type[BaseModel]):
    """
    Decorator to validate request body against Pydantic schema

    Usage:
        @validate_request(UserCreateSchema)
        async def create_user(validated_data):
            # validated_data is already a Pydantic model instance
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                # Get request JSON
                json_data = await request.get_json()

                # Validate with Pydantic
                validated_data = schema(**json_data)

                # Inject validated data as argument
                return await func(*args, validated_data=validated_data, **kwargs)

            except ValidationError as e:
                error_response = ErrorResponse(
                    error="Validation Error",
                    message="Request data validation failed",
                    details=e.errors()
                )
                return jsonify(error_response.model_dump()), 422

            except Exception as e:
                error_response = ErrorResponse(
                    error="Bad Request",
                    message=str(e)
                )
                return jsonify(error_response.model_dump()), 400

        return wrapper
    return decorator


def validate_query_params(schema: Type[BaseModel]):
    """
    Decorator to validate query parameters against Pydantic schema

    Usage:
        @validate_query_params(PaginationParams)
        async def list_users(validated_params):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                # Get query parameters
                query_params = request.args.to_dict()

                # Validate with Pydantic
                validated_params = schema(**query_params)

                # Inject validated params
                return await func(*args, validated_params=validated_params, **kwargs)

            except ValidationError as e:
                error_response = ErrorResponse(
                    error="Validation Error",
                    message="Query parameter validation failed",
                    details=e.errors()
                )
                return jsonify(error_response.model_dump()), 422

        return wrapper
    return decorator
