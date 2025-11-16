#!/bin/bash

# Script to fix port 80 conflict
# This script helps identify and resolve port 80 conflicts

set -e

echo "=========================================="
echo "Port 80 Conflict Resolution"
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
    apt-get update && apt-get install -y net-tools
    netstat -tulpn | grep :80 || echo "No process found"
fi

echo ""
echo "=========================================="
echo "Resolution Options:"
echo "=========================================="
echo ""
echo "Option 1: Stop the conflicting service"
echo "  Common services:"
echo "    - Apache: systemctl stop apache2"
echo "    - Nginx (system): systemctl stop nginx"
echo "    - Other web server: Check the process above"
echo ""
echo "Option 2: Use a different port (e.g., 8080)"
echo "  Edit docker-compose.prod.yml:"
echo "    Change '80:80' to '8080:80'"
echo "  Then access at: http://YOUR_SERVER_IP:8080"
echo ""
echo "Option 3: Disable the conflicting service permanently"
echo "  For Apache: systemctl disable apache2"
echo "  For Nginx: systemctl disable nginx"
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
echo "   Try starting services again: ./start_production.sh"

