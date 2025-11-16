#!/bin/bash

# Fix frontend port - change from 8080 to 80

set -e

echo "=========================================="
echo "Fixing Frontend Port (8080 -> 80)"
echo "=========================================="
echo ""

echo "1. Checking current FRONTEND_PORT setting..."
if grep -q "FRONTEND_PORT=8080" .env 2>/dev/null; then
    echo "⚠️  FRONTEND_PORT is set to 8080 in .env"
    echo "   Changing to 80..."
    sed -i 's/FRONTEND_PORT=8080/FRONTEND_PORT=80/' .env
    echo "✅ Updated .env"
elif ! grep -q "FRONTEND_PORT" .env 2>/dev/null; then
    echo "⚠️  FRONTEND_PORT not set, adding FRONTEND_PORT=80..."
    echo "FRONTEND_PORT=80" >> .env
    echo "✅ Added FRONTEND_PORT=80 to .env"
else
    echo "✅ FRONTEND_PORT already set correctly"
fi
echo ""

echo "2. Stopping frontend..."
docker compose -f docker-compose.prod.yml stop frontend
docker compose -f docker-compose.prod.yml rm -f frontend

echo ""
echo "3. Starting frontend on port 80..."
docker compose -f docker-compose.prod.yml up -d frontend

echo ""
echo "4. Waiting for frontend to start..."
sleep 10

echo ""
echo "5. Checking port binding..."
docker port wastewater-frontend

echo ""
echo "6. Testing access..."
SERVER_IP=$(hostname -I | awk '{print $1}')
if curl -s http://localhost > /dev/null 2>&1; then
    echo "✅ Frontend accessible on localhost:80"
else
    echo "❌ Frontend NOT accessible on localhost:80"
fi

echo ""
echo "=========================================="
echo "✅ Port fix complete!"
echo "=========================================="
echo ""
echo "Frontend should now be accessible at:"
echo "  http://${SERVER_IP}"
echo ""
echo "If you still need port 8080, access at:"
echo "  http://${SERVER_IP}:8080"
echo ""

