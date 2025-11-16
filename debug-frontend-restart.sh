#!/bin/bash

# Debug frontend nginx restart loop

set -e

echo "=========================================="
echo "Frontend Restart Loop Debug"
echo "=========================================="
echo ""

echo "1. Checking container status..."
docker ps -a | grep frontend
echo ""

echo "2. Recent logs (last 50 lines)..."
docker logs wastewater-frontend 2>&1 | tail -50
echo ""

echo "3. Checking if container can start..."
docker inspect wastewater-frontend --format='{{.State.Status}}' 2>/dev/null || echo "Container not found"
echo ""

echo "4. Checking nginx config syntax..."
docker exec wastewater-frontend nginx -t 2>&1 || echo "Cannot test config (container may not be running)"
echo ""

echo "5. Checking if build files exist..."
docker exec wastewater-frontend ls -la /usr/share/nginx/html/ 2>&1 || echo "Cannot access (container may not be running)"
echo ""

echo "6. Checking nginx error log..."
docker exec wastewater-frontend cat /var/log/nginx/error.log 2>&1 | tail -20 || echo "Cannot access error log"
echo ""

echo "7. Checking if nginx.conf exists..."
docker exec wastewater-frontend ls -la /etc/nginx/conf.d/ 2>&1 || echo "Cannot access"
echo ""

echo "=========================================="
echo "Common Issues:"
echo "=========================================="
echo "1. Nginx config syntax error"
echo "2. Missing build files"
echo "3. Port conflict"
echo "4. Missing nginx.conf file"
echo ""

