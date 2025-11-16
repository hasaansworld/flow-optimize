#!/bin/bash

# Fix port 80 conflict for frontend

set -e

echo "=========================================="
echo "Port 80 Conflict Resolution for Frontend"
echo "=========================================="
echo ""

# Check what's using port 80
echo "🔍 Checking what's using port 80..."
echo ""

if command -v netstat &> /dev/null; then
    echo "Using netstat:"
    netstat -tulpn | grep :80 || echo "No process found with netstat"
elif command -v ss &> /dev/null; then
    echo "Using ss:"
    ss -tulpn | grep :80 || echo "No process found with ss"
elif command -v lsof &> /dev/null; then
    echo "Using lsof:"
    lsof -i :80 || echo "No process found with lsof"
else
    echo "⚠️  No port checking tools found. Installing..."
    apt-get update && apt-get install -y net-tools 2>/dev/null || true
    netstat -tulpn | grep :80 || echo "No process found"
fi

echo ""
echo "=========================================="
echo "Resolution Options:"
echo "=========================================="
echo ""
echo "Option 1: Stop the conflicting service (Recommended)"
echo "  Common services:"
echo "    - Apache: systemctl stop apache2 && systemctl disable apache2"
echo "    - Nginx (system): systemctl stop nginx && systemctl disable nginx"
echo ""
echo "Option 2: Change frontend to use port 8080"
echo "  Edit docker-compose.prod.yml:"
echo "    Change frontend ports from '80:80' to '8080:80'"
echo "  Then access at: http://YOUR_SERVER_IP:8080"
echo ""

read -p "Would you like to stop Apache? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    systemctl stop apache2 2>/dev/null && echo "✅ Apache stopped" || echo "⚠️  Apache not running or not installed"
    systemctl disable apache2 2>/dev/null && echo "✅ Apache disabled" || echo "⚠️  Could not disable Apache"
fi

read -p "Would you like to stop system Nginx? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    systemctl stop nginx 2>/dev/null && echo "✅ System Nginx stopped" || echo "⚠️  System Nginx not running or not installed"
    systemctl disable nginx 2>/dev/null && echo "✅ System Nginx disabled" || echo "⚠️  Could not disable system Nginx"
fi

echo ""
echo "✅ Port conflict resolution complete!"
echo ""
echo "Now try starting services again:"
echo "  docker compose -f docker-compose.prod.yml up -d"
echo "  OR"
echo "  ./start_production.sh"
echo ""

