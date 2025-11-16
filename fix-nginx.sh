#!/bin/bash

# Fix nginx issues

set -e

echo "=========================================="
echo "Nginx Fix Script"
echo "=========================================="
echo ""

# Check if nginx container exists
if ! docker ps -a | grep -q wastewater-nginx; then
    echo "❌ Nginx container not found"
    exit 1
fi

echo "1. Checking nginx logs for errors..."
docker logs wastewater-nginx 2>&1 | tail -20
echo ""

echo "2. Testing nginx configuration..."
if docker exec wastewater-nginx nginx -t 2>&1; then
    echo "✅ Nginx configuration is valid"
else
    echo "❌ Nginx configuration has errors"
    echo "   Check the errors above and fix nginx/nginx.conf"
    exit 1
fi
echo ""

echo "3. Checking if wget is available in container..."
if docker exec wastewater-nginx which wget > /dev/null 2>&1; then
    echo "✅ wget is available"
else
    echo "⚠️  wget not found, installing..."
    docker exec wastewater-nginx sh -c "apk add --no-cache wget" || echo "Failed to install wget"
fi
echo ""

echo "4. Testing health endpoint..."
if docker exec wastewater-nginx wget -qO- http://localhost/health 2>&1; then
    echo "✅ Health endpoint is working"
else
    echo "⚠️  Health endpoint test failed (this might be normal if nginx just started)"
fi
echo ""

echo "5. Restarting nginx container..."
docker compose -f docker-compose.prod.yml restart nginx
echo ""

echo "6. Waiting for nginx to start..."
sleep 5

echo "7. Checking nginx status..."
docker ps | grep nginx
echo ""

echo "=========================================="
echo "✅ Nginx fix complete!"
echo "=========================================="
echo ""
echo "If nginx is still not working:"
echo "  1. Check logs: docker logs wastewater-nginx"
echo "  2. Run debug: ./debug-nginx.sh"
echo "  3. Verify config: docker exec wastewater-nginx nginx -t"
echo ""

