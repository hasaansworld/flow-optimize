#!/bin/bash

# Production start script for Vultr deployment
# Uses docker-compose.prod.yml with nginx reverse proxy
#
# Usage:
#   ./start_production.sh           # Normal start with rebuild
#   ./start_production.sh --no-build # Skip rebuild (faster restart)

set -e

echo "=========================================="
echo "Multi-Agent Wastewater Control System"
echo "Production Deployment (Vultr)"
echo "=========================================="
echo ""

# Parse arguments
SKIP_BUILD=false
if [ "$1" = "--no-build" ]; then
    SKIP_BUILD=true
    echo "⚡ Fast mode: Skipping rebuild"
    echo ""
fi

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found"
    echo "📝 Creating .env from example..."
    if [ -f env.example ]; then
        cp env.example .env
        echo "✅ Created .env file"
        echo "⚠️  Please edit .env and add your API keys and passwords"
        exit 1
    else
        echo "❌ env.example not found. Please create .env manually"
        exit 1
    fi
fi

# Check for Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker first."
    exit 1
fi

if ! command -v docker compose &> /dev/null; then
    echo "❌ docker compose not found. Please install docker compose first."
    exit 1
fi

echo "🐳 Starting Docker services (Production)..."
echo ""

# Rebuild if not skipped
if [ "$SKIP_BUILD" = false ]; then
    echo "🔍 Checking if rebuild is needed..."
    if [ -f "requirements.txt" ] || [ -f "requirements-api.txt" ]; then
        echo "📦 Rebuilding services with latest dependencies..."
        docker compose -f docker-compose.prod.yml build
        echo "✅ Build complete"
        echo ""
    fi
else
    echo "⏭️  Skipping rebuild (use without --no-build to rebuild)"
    echo ""
fi

# Start services
echo "🚀 Starting all services..."
docker compose -f docker-compose.prod.yml up -d

echo ""
echo "⏳ Waiting for services to be healthy..."
sleep 15

# Get server IP
SERVER_IP=$(hostname -I | awk '{print $1}')

# Check service health
echo ""
echo "📊 Service Status:"
echo ""

# Get frontend port from env or default to 80
FRONTEND_PORT=${FRONTEND_PORT:-80}

# Check frontend
if curl -s http://localhost:${FRONTEND_PORT}/health > /dev/null 2>&1; then
    echo "✅ Frontend: http://${SERVER_IP}:${FRONTEND_PORT}"
else
    echo "⚠️  Frontend: Starting..."
fi

# Check agent API
if curl -s http://localhost:8000/api/v1/health > /dev/null 2>&1; then
    echo "✅ Agent API Server: http://${SERVER_IP}:8000"
    echo "   📚 API Docs: http://${SERVER_IP}:8000/docs"
    echo "   Health: http://${SERVER_IP}:8000/api/v1/health"
else
    echo "⚠️  Agent API Server: Starting..."
fi

# Check n8n
if curl -s http://localhost:5678/healthz > /dev/null 2>&1; then
    echo "✅ n8n Workflow UI: http://${SERVER_IP}:5678"
    echo "   👤 Login: Check .env for N8N_USER and N8N_PASSWORD"
else
    echo "⚠️  n8n: Starting..."
fi

# Check Grafana
if curl -s http://localhost:3000/api/health > /dev/null 2>&1; then
    echo "✅ Grafana Dashboard: http://${SERVER_IP}:3000"
    echo "   👤 Login: Check .env for GRAFANA_USER and GRAFANA_PASSWORD"
else
    echo "⚠️  Grafana: Starting..."
fi

# Check PostgreSQL
if docker exec wastewater-postgres pg_isready -U ${POSTGRES_USER:-wastewater} > /dev/null 2>&1; then
    echo "✅ PostgreSQL Database: Running (internal)"
else
    echo "⚠️  PostgreSQL: Starting..."
fi

echo ""
echo "=========================================="
echo "🎉 Production System Started Successfully!"
echo "=========================================="
echo ""
echo "📖 Access Your Services:"
echo ""
echo "  Frontend:  http://${SERVER_IP}:${FRONTEND_PORT:-80}"
echo "  API:       http://${SERVER_IP}:8000"
echo "  API Docs:  http://${SERVER_IP}:8000/docs"
echo "  n8n:       http://${SERVER_IP}:5678"
echo "  Grafana:   http://${SERVER_IP}:3000"
echo ""
echo "📖 Next Steps:"
echo ""
echo "1. Access n8n UI:"
echo "   http://${SERVER_IP}:5678"
echo "   Login: Check .env file for credentials"
echo ""
echo "2. Import workflow:"
echo "   - Click 'Import from File'"
echo "   - Select: n8n_workflows/main_control_loop.json"
echo "   - Activate the workflow"
echo ""
echo "3. Test the API:"
echo "   curl http://${SERVER_IP}/api/v1/health"
echo ""
echo "4. View logs:"
echo "   docker compose -f docker-compose.prod.yml logs -f"
echo ""
echo "5. Stop services:"
echo "   docker compose -f docker-compose.prod.yml down"
echo ""
echo "💡 Tips:"
echo "   - Fast restart (skip rebuild): ./start_production.sh --no-build"
echo "   - View logs: docker compose -f docker-compose.prod.yml logs -f [service]"
echo "   - Restart specific service: docker compose -f docker-compose.prod.yml restart [service]"
echo ""
echo "📚 Full documentation: DEPLOYMENT.md"
echo ""

