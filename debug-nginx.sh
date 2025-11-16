#!/bin/bash

# Debug nginx container issues

echo "=========================================="
echo "Nginx Debugging Script"
echo "=========================================="
echo ""

echo "1. Checking nginx container status..."
docker ps -a | grep nginx
echo ""

echo "2. Checking nginx logs..."
docker logs wastewater-nginx 2>&1 | tail -50
echo ""

echo "3. Testing nginx configuration..."
docker exec wastewater-nginx nginx -t 2>&1 || echo "Container not running or config error"
echo ""

echo "4. Checking if nginx is listening..."
docker exec wastewater-nginx netstat -tuln 2>&1 | grep :80 || echo "Cannot check (container may not be running)"
echo ""

echo "5. Testing health endpoint from inside container..."
docker exec wastewater-nginx wget -qO- http://localhost/health 2>&1 || echo "Health check failed"
echo ""

echo "6. Checking nginx process..."
docker exec wastewater-nginx ps aux | grep nginx || echo "Nginx process not found"
echo ""

echo "7. Checking mounted volumes..."
docker inspect wastewater-nginx | grep -A 10 Mounts
echo ""

echo "=========================================="
echo "Common Issues:"
echo "=========================================="
echo "1. If 'nginx -t' fails: Configuration syntax error"
echo "2. If container keeps restarting: Check logs above"
echo "3. If health check fails: wget might not be installed"
echo "4. If port binding fails: Port 80 already in use"
echo ""

