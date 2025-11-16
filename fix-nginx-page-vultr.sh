#!/bin/bash

# Comprehensive fix for nginx welcome page on Vultr

set -e

echo "=========================================="
echo "Fixing Nginx Welcome Page on Vultr"
echo "=========================================="
echo ""

echo "1. Checking what's running on port 80..."
if command -v netstat &> /dev/null; then
    echo "Processes on port 80:"
    netstat -tulpn | grep :80 || echo "Nothing found with netstat"
elif command -v ss &> /dev/null; then
    echo "Processes on port 80:"
    ss -tulpn | grep :80 || echo "Nothing found with ss"
fi

echo ""
echo "2. Checking for system nginx..."
if systemctl is-active --quiet nginx 2>/dev/null; then
    echo "⚠️  System nginx is running! Stopping it..."
    systemctl stop nginx
    systemctl disable nginx
    echo "✅ System nginx stopped"
else
    echo "✅ System nginx not running"
fi

echo ""
echo "3. Checking for nginx containers..."
if docker ps -a | grep -q nginx; then
    echo "⚠️  Found nginx containers:"
    docker ps -a | grep nginx
    echo "Stopping and removing..."
    docker stop $(docker ps -a | grep nginx | awk '{print $1}') 2>/dev/null || true
    docker rm $(docker ps -a | grep nginx | awk '{print $1}') 2>/dev/null || true
    echo "✅ Nginx containers removed"
else
    echo "✅ No nginx containers found"
fi

echo ""
echo "4. Stopping frontend container..."
docker compose -f docker-compose.prod.yml stop frontend 2>/dev/null || true
docker compose -f docker-compose.prod.yml rm -f frontend 2>/dev/null || true

echo ""
echo "5. Removing old frontend images..."
docker images | grep frontend | awk '{print $3}' | xargs -r docker rmi -f 2>/dev/null || echo "No old frontend images"

echo ""
echo "6. Rebuilding frontend (this will take a few minutes)..."
echo "   Watch for 'Building application...' and 'Build completed successfully!'"
docker compose -f docker-compose.prod.yml build --no-cache frontend

echo ""
echo "7. Starting frontend..."
docker compose -f docker-compose.prod.yml up -d frontend

echo ""
echo "8. Waiting for frontend to start..."
sleep 15

echo ""
echo "9. Checking frontend container..."
docker ps | grep frontend

echo ""
echo "10. Checking frontend logs..."
docker logs wastewater-frontend 2>&1 | tail -30

echo ""
echo "11. Checking what's in the container..."
docker exec wastewater-frontend ls -la /app/build/ 2>&1 || echo "Cannot access build directory"

echo ""
echo "12. Checking what process is running in container..."
docker exec wastewater-frontend ps aux 2>&1 | head -10

echo ""
echo "13. Testing frontend..."
FRONTEND_PORT=${FRONTEND_PORT:-80}
sleep 5
if curl -s http://localhost:${FRONTEND_PORT} | grep -q "nginx"; then
    echo "❌ Still seeing nginx page!"
    echo "   This might be system nginx or cached response"
    echo "   Try: curl -H 'Cache-Control: no-cache' http://localhost:${FRONTEND_PORT}"
else
    echo "✅ Frontend appears to be working (no nginx detected)"
fi

echo ""
echo "=========================================="
echo "✅ Fix complete!"
echo "=========================================="
echo ""
echo "If you still see nginx:"
echo "  1. Clear browser cache (Ctrl+Shift+R or Cmd+Shift+R)"
echo "  2. Check: docker logs -f wastewater-frontend"
echo "  3. Verify: docker exec wastewater-frontend ps aux | grep serve"
echo "  4. Check system nginx: systemctl status nginx"
echo ""

