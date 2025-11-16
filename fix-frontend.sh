#!/bin/bash

# Fix frontend showing default nginx page

set -e

echo "=========================================="
echo "Frontend Fix Script"
echo "=========================================="
echo ""

echo "1. Checking frontend container logs..."
docker logs wastewater-frontend 2>&1 | tail -30
echo ""

echo "2. Checking if build files exist in container..."
docker exec wastewater-frontend ls -la /usr/share/nginx/html/ 2>&1 || echo "Container not running or error accessing"
echo ""

echo "3. Rebuilding frontend..."
echo "   This will rebuild the frontend container with the correct build output"
echo ""

# Rebuild frontend
docker compose -f docker-compose.prod.yml build frontend

echo ""
echo "4. Restarting frontend..."
docker compose -f docker-compose.prod.yml up -d --force-recreate frontend

echo ""
echo "5. Waiting for frontend to start..."
sleep 5

echo ""
echo "6. Checking frontend status..."
docker ps | grep frontend

echo ""
echo "7. Testing frontend..."
FRONTEND_PORT=${FRONTEND_PORT:-80}
if curl -s http://localhost:${FRONTEND_PORT}/health > /dev/null 2>&1; then
    echo "✅ Frontend health check passed"
else
    echo "⚠️  Frontend health check failed"
fi

echo ""
echo "=========================================="
echo "✅ Frontend fix complete!"
echo "=========================================="
echo ""
echo "If you still see the default nginx page:"
echo "  1. Check build logs: docker logs wastewater-frontend"
echo "  2. Verify build output: docker exec wastewater-frontend ls -la /usr/share/nginx/html/"
echo "  3. Check nginx config: docker exec wastewater-frontend cat /etc/nginx/conf.d/default.conf"
echo ""

