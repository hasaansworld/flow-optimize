#!/bin/bash

# Fix frontend restart loop

set -e

echo "=========================================="
echo "Fixing Frontend Restart Loop"
echo "=========================================="
echo ""

echo "1. Stopping frontend container..."
docker compose -f docker-compose.prod.yml stop frontend 2>/dev/null || true
docker compose -f docker-compose.prod.yml rm -f frontend 2>/dev/null || true

echo ""
echo "2. Checking for build issues..."
echo "   Checking if frontend source files exist..."
if [ ! -d "frontend/src" ]; then
    echo "❌ ERROR: frontend/src directory not found!"
    exit 1
fi

if [ ! -f "frontend/package.json" ]; then
    echo "❌ ERROR: frontend/package.json not found!"
    exit 1
fi

echo "✅ Frontend source files found"

echo ""
echo "3. Rebuilding frontend (this may take a few minutes)..."
docker compose -f docker-compose.prod.yml build --no-cache frontend

echo ""
echo "4. Starting frontend..."
docker compose -f docker-compose.prod.yml up -d frontend

echo ""
echo "5. Waiting for frontend to start..."
sleep 10

echo ""
echo "6. Checking frontend status..."
docker ps | grep frontend || echo "⚠️  Frontend not running"

echo ""
echo "7. Checking logs..."
docker logs wastewater-frontend 2>&1 | tail -20

echo ""
echo "=========================================="
echo "✅ Fix complete!"
echo "=========================================="
echo ""
echo "If frontend is still restarting:"
echo "  1. Check logs: docker logs -f wastewater-frontend"
echo "  2. Run debug: ./debug-frontend-restart.sh"
echo "  3. Check build: docker compose -f docker-compose.prod.yml build frontend"
echo ""

