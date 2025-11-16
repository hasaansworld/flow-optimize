#!/bin/bash

# Start script for n8n-integrated multi-agent system
# Junction 2025 Hackathon - Valmet x HSY Challenge
#
# Usage:
#   ./start_n8n_system.sh           # Normal start with rebuild
#   ./start_n8n_system.sh --no-build # Skip rebuild (faster restart)

set -e

echo "=========================================="
echo "Multi-Agent Wastewater Control System"
echo "with n8n Workflow Integration"
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
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "✅ Created .env file"
        echo "⚠️  Please edit .env and add your GEMINI_API_KEY"
        exit 1
    else
        echo "❌ .env.example not found. Please create .env manually"
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

echo "🐳 Starting Docker services..."
echo ""

# Rebuild if not skipped
if [ "$SKIP_BUILD" = false ]; then
    echo "🔍 Checking if rebuild is needed..."
    if [ -f "requirements.txt" ] || [ -f "requirements-api.txt" ]; then
        echo "📦 Rebuilding agent-api with latest dependencies..."
        docker compose build agent-api
        echo "✅ Build complete"
        echo ""
    fi
else
    echo "⏭️  Skipping rebuild (use without --no-build to rebuild)"
    echo ""
fi

# Start services
echo "🚀 Starting all services..."
docker compose up -d

echo ""
echo "⏳ Waiting for services to be healthy..."
sleep 10

# Check service health
echo ""
echo "📊 Service Status:"
echo ""

# Check agent API
if curl -s http://localhost:8000/api/v1/health > /dev/null 2>&1; then
    echo "✅ Agent API Server: http://localhost:8000"
    echo "   📚 API Docs: http://localhost:8000/docs"
else
    echo "⚠️  Agent API Server: Starting..."
fi

# Check n8n
if curl -s http://localhost:5678/healthz > /dev/null 2>&1; then
    echo "✅ n8n Workflow UI: http://localhost:5678"
    echo "   👤 Login: admin / hackathon2025"
else
    echo "⚠️  n8n: Starting..."
fi

# Check Grafana
if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ Grafana Dashboard: http://localhost:3000"
    echo "   👤 Login: admin / hackathon2025"
else
    echo "⚠️  Grafana: Starting..."
fi

# Check PostgreSQL
if docker exec wastewater-postgres pg_isready -U wastewater > /dev/null 2>&1; then
    echo "✅ PostgreSQL Database: localhost:5432"
else
    echo "⚠️  PostgreSQL: Starting..."
fi

echo ""
echo "=========================================="
echo "🎉 System Started Successfully!"
echo "=========================================="
echo ""
echo "📖 Next Steps:"
echo ""
echo "1. Access n8n UI:"
echo "   http://localhost:5678"
echo "   Login: admin / hackathon2025"
echo ""
echo "2. Import workflow:"
echo "   - Click 'Import from File'"
echo "   - Select: n8n_workflows/main_control_loop.json"
echo "   - Activate the workflow"
echo ""
echo "3. Test the API:"
echo "   curl http://localhost:8000/api/v1/health"
echo ""
echo "4. View logs:"
echo "   docker compose logs -f agent-api"
echo ""
echo "5. Stop services:"
echo "   docker compose down"
echo ""
echo "💡 Tips:"
echo "   - Fast restart (skip rebuild): ./start_n8n_system.sh --no-build"
echo "   - View logs: docker compose logs -f agent-api"
echo "   - Restart API only: docker compose restart agent-api"
echo ""
echo "📚 Full documentation: N8N_INTEGRATION.md"
echo ""
