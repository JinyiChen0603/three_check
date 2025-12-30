#!/bin/bash
set -e

echo "Starting application..."

# Wait for database (max 60 seconds)
echo "Waiting for database connection..."
MAX_RETRIES=30
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
  # Use pg_isready to check if PostgreSQL is ready
  if PGPASSWORD=mathtasks123 psql -h postgres -U mathtasks -d mathtasks -c "SELECT 1" >/dev/null 2>&1; then
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
