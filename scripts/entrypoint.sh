#!/bin/bash
# BDOCS API Entrypoint Script
# Runs database migrations before starting the server

set -e

echo "========================================"
echo "BDOCS Prison Information System API"
echo "========================================"
echo "Environment: ${FLASK_ENV:-production}"
echo "Database Host: ${POSTGRES_HOST:-localhost}"
echo "========================================"

# Wait for database to be ready
echo "Waiting for PostgreSQL..."
MAX_RETRIES=30
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if python -c "
import asyncio
import asyncpg
import os

async def check_db():
    try:
        conn = await asyncpg.connect(
            host=os.environ.get('POSTGRES_HOST', 'localhost'),
            port=int(os.environ.get('POSTGRES_PORT', 5432)),
            user=os.environ.get('POSTGRES_USER', 'postgres'),
            password=os.environ.get('POSTGRES_PASSWORD', 'postgres'),
            database=os.environ.get('POSTGRES_DB', 'bdocs')
        )
        await conn.close()
        return True
    except Exception:
        return False

result = asyncio.run(check_db())
exit(0 if result else 1)
" 2>/dev/null; then
        echo "PostgreSQL is ready!"
        break
    fi
    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo "PostgreSQL not ready yet. Retry $RETRY_COUNT/$MAX_RETRIES..."
    sleep 2
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo "ERROR: Could not connect to PostgreSQL after $MAX_RETRIES attempts"
    exit 1
fi

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

if [ $? -eq 0 ]; then
    echo "Migrations completed successfully!"
else
    echo "ERROR: Migration failed!"
    exit 1
fi

echo "========================================"
echo "Starting Hypercorn server..."
echo "========================================"

# Execute the main command
exec "$@"
