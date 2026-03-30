#!/bin/bash
# DEPLOYMENT SCRIPT - PostgreSQL Migration
# Rapid deployment after migration
# Usage: bash deploy.sh

set -e  # Exit on error

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

echo "========================================================================"
echo "  PostgreSQL Migration - Rapid Deployment Script"
echo "========================================================================"

# Step 1: Verify environment
echo ""
echo "[1/7] Verifying environment..."

if ! command -v docker &> /dev/null; then
    echo "  ✗ Docker not found. Please install Docker."
    exit 1
fi
echo "  ✓ Docker found"

if ! command -v python3 &> /dev/null; then
    echo "  ✗ Python 3 not found. Please install Python 3.10+"
    exit 1
fi
echo "  ✓ Python 3 found"

# Step 2: Stop old containers
echo ""
echo "[2/7] Cleaning up old containers..."
docker-compose -f docker-compose.postgres.yml down --volumes 2>/dev/null || true
echo "  ✓ Old containers removed"

# Step 3: Start PostgreSQL
echo ""
echo "[3/7] Starting PostgreSQL..."
docker-compose -f docker-compose.postgres.yml up -d
sleep 5

# Verify PostgreSQL is running
if ! docker-compose -f docker-compose.postgres.yml ps | grep -q "Up"; then
    echo "  ✗ PostgreSQL failed to start"
    docker-compose -f docker-compose.postgres.yml logs
    exit 1
fi
echo "  ✓ PostgreSQL started (inventario and inventario_test databases created)"

# Step 4: Install Python dependencies
echo ""
echo "[4/7] Installing Python dependencies..."
python3 -m pip install --quiet -r requirements.txt
echo "  ✓ Dependencies installed"

# Step 5: Run migrations
echo ""
echo "[5/7] Running Alembic migrations..."
alembic upgrade head
echo "  ✓ Database schema created"

# Step 6: Validate migration
echo ""
echo "[6/7] Validating PostgreSQL migration..."
python3 validate_postgres_migration.py

if [ $? -ne 0 ]; then
    echo "  ✗ Validation failed"
    exit 1
fi
echo "  ✓ Validation passed"

# Step 7: Ready for deployment
echo ""
echo "========================================================================"
echo "  ✓ DEPLOYMENT READY"
echo "========================================================================"
echo ""
echo "Next steps:"
echo ""
echo "  1. Start the API server:"
echo "     uvicorn main_api:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "  2. Test the API:"
echo "     curl http://localhost:8000/api/health"
echo ""
echo "  3. Run tests:"
echo "     pytest tests/ -v"
echo ""
echo "  4. View database:"
echo "     docker exec inventario-db psql -U inventario_user -d inventario"
echo ""
echo "  5. Monitor logs:"
echo "     docker-compose -f docker-compose.postgres.yml logs -f"
echo ""
echo "========================================================================"
