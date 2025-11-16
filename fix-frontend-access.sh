#!/bin/bash

# Fix frontend not accessible from outside

set -e

echo "=========================================="
echo "Fixing Frontend External Access"
echo "=========================================="
echo ""

echo "1. Checking firewall..."
if command -v ufw &> /dev/null; then
    echo "Allowing port 80 in firewall..."
    ufw allow 80/tcp
    echo "✅ Firewall updated"
else
    echo "⚠️  UFW not found, check your firewall manually"
fi
echo ""

echo "2. Stopping frontend..."
docker compose -f docker-compose.prod.yml stop frontend
docker compose -f docker-compose.prod.yml rm -f frontend

echo ""
echo "3. Rebuilding frontend with updated Dockerfile..."
docker compose -f docker-compose.prod.yml build --no-cache frontend

echo ""
echo "4. Starting frontend..."
docker compose -f docker-compose.prod.yml up -d frontend

echo ""
echo "5. Waiting for frontend to start..."
sleep 10

echo ""
echo "6. Checking frontend logs..."
docker logs wastewater-frontend 2>&1 | tail -10

echo ""
echo "7. Testing access..."
SERVER_IP=$(hostname -I | awk '{print $1}')
if curl -s http://localhost > /dev/null 2>&1; then
    echo "✅ Frontend accessible on localhost"
else
    echo "❌ Frontend NOT accessible on localhost"
fi

echo ""
echo "8. Checking port binding..."
docker port wastewater-frontend

echo ""
echo "=========================================="
echo "✅ Fix complete!"
echo "=========================================="
echo ""
echo "Test from your browser:"
echo "  http://${SERVER_IP}"
echo ""
echo "If still not accessible:"
echo "  1. Check firewall: ufw status"
echo "  2. Check Vultr firewall rules in control panel"
echo "  3. Run: ./debug-frontend-access.sh"
echo ""

