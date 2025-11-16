#!/bin/bash

# Rebuild frontend without nginx

set -e

echo "=========================================="
echo "Rebuilding Frontend (No Nginx)"
echo "=========================================="
echo ""

echo "1. Stopping frontend container..."
docker compose -f docker-compose.prod.yml stop frontend 2>/dev/null || true
docker compose -f docker-compose.prod.yml rm -f frontend 2>/dev/null || true

echo ""
echo "2. Removing old frontend image..."
docker rmi flow-optimize-frontend 2>/dev/null || docker rmi $(docker images | grep frontend | awk '{print $3}') 2>/dev/null || echo "No old image to remove"

echo ""
echo "3. Rebuilding frontend with new Dockerfile (no nginx, using serve)..."
docker compose -f docker-compose.prod.yml build --no-cache frontend

echo ""
echo "4. Starting frontend..."
docker compose -f docker-compose.prod.yml up -d frontend

echo ""
echo "5. Waiting for frontend to start..."
sleep 10

echo ""
echo "6. Checking frontend logs..."
docker logs wastewater-frontend 2>&1 | tail -20

echo ""
echo "7. Checking what's running on port 80..."
FRONTEND_PORT=${FRONTEND_PORT:-80}
if command -v netstat &> /dev/null; then
    netstat -tuln | grep ":${FRONTEND_PORT} " || echo "Nothing listening on port ${FRONTEND_PORT}"
elif command -v ss &> /dev/null; then
    ss -tuln | grep ":${FRONTEND_PORT} " || echo "Nothing listening on port ${FRONTEND_PORT}"
fi

echo ""
echo "8. Testing frontend..."
sleep 5
if curl -s http://localhost:${FRONTEND_PORT} > /dev/null 2>&1; then
    echo "✅ Frontend is responding"
    echo "   Check: http://$(hostname -I | awk '{print $1}'):${FRONTEND_PORT}"
else
    echo "⚠️  Frontend not responding yet"
fi

echo ""
echo "=========================================="
echo "✅ Frontend rebuild complete!"
echo "=========================================="
echo ""
echo "If you still see nginx welcome page:"
echo "  1. Check logs: docker logs -f wastewater-frontend"
echo "  2. Verify container: docker ps | grep frontend"
echo "  3. Check what's in container: docker exec wastewater-frontend ls -la /app/build/"
echo ""

