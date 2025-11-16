#!/bin/bash

# Fix n8n secure cookie issue for HTTP access

set -e

echo "=========================================="
echo "Fixing n8n Secure Cookie Issue"
echo "=========================================="
echo ""

echo "1. Stopping n8n..."
docker compose -f docker-compose.prod.yml stop n8n

echo ""
echo "2. Restarting n8n with updated configuration..."
docker compose -f docker-compose.prod.yml up -d n8n

echo ""
echo "3. Waiting for n8n to start..."
sleep 10

echo ""
echo "4. Checking n8n status..."
docker ps | grep n8n

echo ""
echo "5. Testing n8n access..."
SERVER_IP=$(hostname -I | awk '{print $1}')
if curl -s http://localhost:5678/healthz > /dev/null 2>&1; then
    echo "✅ n8n is accessible"
else
    echo "⚠️  n8n may still be starting..."
fi

echo ""
echo "=========================================="
echo "✅ Fix complete!"
echo "=========================================="
echo ""
echo "n8n should now be accessible at:"
echo "  http://${SERVER_IP}:5678"
echo ""
echo "The secure cookie error should be resolved."
echo ""

