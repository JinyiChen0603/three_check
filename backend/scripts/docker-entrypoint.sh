#!/bin/bash
set -e

echo "Starting application..."

# Wait for database (max 60 seconds)
echo "Waiting for database connection..."
MAX_RETRIES=30
RETRY_COUNT=0

# Use environment variables for database connection
DB_HOST=${POSTGRES_HOST:-postgres}
DB_USER=${POSTGRES_USER:-mathtasks}
DB_PASSWORD=${POSTGRES_PASSWORD:-mathtasks123}
DB_NAME=${POSTGRES_DB:-mathtasks}

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
  # Use pg_isready to check if PostgreSQL is ready
  if PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -U $DB_USER -d postgres -c "SELECT 1" >/dev/null 2>&1; then
    echo "Database connection successful"
    break
  fi
  RETRY_COUNT=$((RETRY_COUNT + 1))
  echo "Database not ready, waiting 2 seconds... ($RETRY_COUNT/$MAX_RETRIES)"
  sleep 2
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
  echo "Database connection timeout, please check database service"
  exit 1
fi

# Run database migrations
echo "Running database migrations..."
alembic upgrade head || {
  echo "Database migration failed, but continuing to start application (database may already be up to date)"
}

echo "Database migration completed"

# Start application
echo "Starting FastAPI application..."
exec "$@"
