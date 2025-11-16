#!/bin/bash

# Remove nginx container completely

set -e

echo "=========================================="
echo "Removing Nginx Container"
echo "=========================================="
echo ""

echo "1. Stopping nginx container..."
docker stop wastewater-nginx 2>/dev/null || echo "Container not running"

echo ""
echo "2. Removing nginx container..."
docker rm wastewater-nginx 2>/dev/null || echo "Container not found"

echo ""
echo "3. Checking for any nginx containers..."
docker ps -a | grep nginx || echo "No nginx containers found"

echo ""
echo "4. Removing nginx from docker-compose if it exists..."
# This will fail if nginx service doesn't exist, which is fine
docker compose -f docker-compose.prod.yml stop nginx 2>/dev/null || true
docker compose -f docker-compose.prod.yml rm -f nginx 2>/dev/null || true

echo ""
echo "5. Verifying docker-compose.prod.yml has no nginx..."
if grep -q "nginx:" docker-compose.prod.yml; then
    echo "⚠️  WARNING: nginx service still found in docker-compose.prod.yml"
    echo "   This shouldn't happen - let me check..."
    grep -n "nginx" docker-compose.prod.yml
else
    echo "✅ No nginx service in docker-compose.prod.yml"
fi

echo ""
echo "=========================================="
echo "✅ Nginx removal complete!"
echo "=========================================="
echo ""
echo "If you still see nginx containers, they might be from:"
echo "  - Old containers not removed"
echo "  - Another docker-compose file"
echo ""
echo "To check all containers: docker ps -a"
echo ""

