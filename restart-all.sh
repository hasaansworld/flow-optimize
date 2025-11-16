#!/bin/bash

# Remove all containers and restart them

set -e

echo "=========================================="
echo "Restart All Containers"
echo "=========================================="
echo ""

echo "1. Stopping all containers..."
docker compose -f docker-compose.prod.yml down

echo ""
echo "2. Removing all containers..."
docker compose -f docker-compose.prod.yml rm -f

echo ""
echo "3. (Optional) Remove volumes? This will delete all data!"
read -p "Remove volumes (database, n8n data, etc.)? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "⚠️  Removing volumes..."
    docker compose -f docker-compose.prod.yml down -v
    echo "✅ Volumes removed"
else
    echo "✅ Keeping volumes (data preserved)"
fi

echo ""
echo "4. Rebuilding containers..."
docker compose -f docker-compose.prod.yml build

echo ""
echo "5. Starting all containers..."
docker compose -f docker-compose.prod.yml up -d

echo ""
echo "6. Waiting for services to start..."
sleep 10

echo ""
echo "7. Checking service status..."
docker compose -f docker-compose.prod.yml ps

echo ""
echo "=========================================="
echo "✅ Restart complete!"
echo "=========================================="
echo ""
echo "View logs: docker compose -f docker-compose.prod.yml logs -f"
echo ""

