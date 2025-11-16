#!/bin/bash

# Debug why frontend is not accessible from outside

set -e

echo "=========================================="
echo "Frontend Access Debug"
echo "=========================================="
echo ""

echo "1. Checking frontend container status..."
docker ps | grep frontend || echo "Frontend container not running"
echo ""

echo "2. Checking frontend port binding..."
docker port wastewater-frontend 2>/dev/null || echo "Cannot get port info"
echo ""

echo "3. Checking what's listening on port 80..."
if command -v netstat &> /dev/null; then
    netstat -tuln | grep :80 || echo "Nothing listening on port 80"
elif command -v ss &> /dev/null; then
    ss -tuln | grep :80 || echo "Nothing listening on port 80"
fi
echo ""

echo "4. Testing localhost access..."
if curl -s http://localhost > /dev/null 2>&1; then
    echo "✅ Frontend accessible on localhost"
else
    echo "❌ Frontend NOT accessible on localhost"
fi
echo ""

echo "5. Checking firewall status..."
if command -v ufw &> /dev/null; then
    echo "UFW status:"
    ufw status | head -10
else
    echo "UFW not installed"
fi
echo ""

echo "6. Getting server IP..."
SERVER_IP=$(hostname -I | awk '{print $1}')
echo "Server IP: ${SERVER_IP}"
echo ""

echo "7. Testing server IP access from inside..."
if curl -s http://${SERVER_IP} > /dev/null 2>&1; then
    echo "✅ Frontend accessible via server IP from inside"
else
    echo "❌ Frontend NOT accessible via server IP from inside"
fi
echo ""

echo "8. Checking frontend container logs..."
docker logs wastewater-frontend 2>&1 | tail -5
echo ""

echo "9. Checking docker-compose port mapping..."
grep -A 5 "frontend:" docker-compose.prod.yml | grep ports
echo ""

echo "10. Checking if serve is binding to 0.0.0.0..."
docker exec wastewater-frontend netstat -tuln 2>/dev/null | grep :80 || \
docker exec wastewater-frontend ss -tuln 2>/dev/null | grep :80 || \
echo "Cannot check inside container"
echo ""

echo "=========================================="
echo "Common Issues & Fixes:"
echo "=========================================="
echo ""
echo "If localhost works but SERVER_IP doesn't:"
echo "  1. Check firewall: ufw allow 80/tcp"
echo "  2. Check if serve is binding to 0.0.0.0 (should be)"
echo ""
echo "If nothing works:"
echo "  1. Check container: docker ps | grep frontend"
echo "  2. Check logs: docker logs wastewater-frontend"
echo "  3. Restart: docker compose -f docker-compose.prod.yml restart frontend"
echo ""

