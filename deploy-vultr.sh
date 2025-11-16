#!/bin/bash

# Vultr Deployment Script
# This script automates the deployment process on a Vultr VPS

set -e

echo "🚀 Starting Vultr Deployment Script..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Please run as root${NC}"
    exit 1
fi

# Update system
echo -e "${GREEN}📦 Updating system packages...${NC}"
apt-get update && apt-get upgrade -y

# Install required packages
echo -e "${GREEN}📦 Installing required packages...${NC}"
apt-get install -y \
    curl \
    git \
    ufw \
    certbot \
    python3-certbot-nginx

# Install Docker
if ! command -v docker &> /dev/null; then
    echo -e "${GREEN}🐳 Installing Docker...${NC}"
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
else
    echo -e "${YELLOW}Docker already installed${NC}"
fi

# Install Docker Compose plugin
if ! docker compose version &> /dev/null; then
    echo -e "${GREEN}🐳 Installing Docker Compose...${NC}"
    apt-get install -y docker-compose-plugin
else
    echo -e "${YELLOW}Docker Compose already installed${NC}"
fi

# Verify Docker installation
echo -e "${GREEN}✅ Verifying Docker installation...${NC}"
docker --version
docker compose version

# Configure firewall
echo -e "${GREEN}🔥 Configuring firewall...${NC}"
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  .env file not found. Creating from .env.example...${NC}"
    if [ -f .env.example ]; then
        cp .env.example .env
        echo -e "${RED}⚠️  IMPORTANT: Please edit .env file and set your API keys and passwords!${NC}"
        echo -e "${YELLOW}Press Enter to continue after editing .env file...${NC}"
        read
    else
        echo -e "${RED}❌ .env.example not found. Please create .env manually.${NC}"
        exit 1
    fi
fi

# Check for port conflicts
echo -e "${GREEN}🔍 Checking for port conflicts...${NC}"
PORTS_IN_USE=""
if command -v netstat &> /dev/null; then
    for port in 80 8000 5678 3000; do
        if netstat -tuln | grep -q ":${port} "; then
            PORTS_IN_USE="${PORTS_IN_USE} ${port}"
        fi
    done
fi
if [ -n "$PORTS_IN_USE" ]; then
    echo -e "${YELLOW}⚠️  Ports in use:${PORTS_IN_USE}${NC}"
    if echo "$PORTS_IN_USE" | grep -q " 80 "; then
        echo -e "${YELLOW}   Port 80 is in use!${NC}"
        echo -e "${YELLOW}   Run ./fix-port-80-frontend.sh to resolve${NC}"
        echo -e "${YELLOW}   Or set FRONTEND_PORT=8080 in .env to use port 8080${NC}"
    fi
    echo -e "${YELLOW}   You may need to stop conflicting services${NC}"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Build and start services
echo -e "${GREEN}🏗️  Building and starting Docker services...${NC}"
docker compose -f docker-compose.prod.yml up -d --build

# Note: You can also use ./start_production.sh for future restarts

# Wait for services to be healthy
echo -e "${GREEN}⏳ Waiting for services to start...${NC}"
sleep 10

# Check service status
echo -e "${GREEN}📊 Service Status:${NC}"
docker compose -f docker-compose.prod.yml ps

# Display access information
echo ""
echo -e "${GREEN}✅ Deployment Complete!${NC}"
echo ""
echo -e "${YELLOW}Access your services at:${NC}"
echo "  Frontend:  http://$(hostname -I | awk '{print $1}')"
echo "  API:       http://$(hostname -I | awk '{print $1}'):8000"
echo "  API Docs:  http://$(hostname -I | awk '{print $1}'):8000/docs"
echo "  n8n:       http://$(hostname -I | awk '{print $1}'):5678"
echo "  Grafana:   http://$(hostname -I | awk '{print $1}'):3000"
echo ""
echo -e "${YELLOW}Useful commands:${NC}"
echo "  View logs:     docker compose -f docker-compose.prod.yml logs -f"
echo "  Restart:       docker compose -f docker-compose.prod.yml restart"
echo "  Stop:          docker compose -f docker-compose.prod.yml down"
echo "  Status:        docker compose -f docker-compose.prod.yml ps"
echo ""
echo -e "${RED}⚠️  IMPORTANT: Next Steps${NC}"
echo ""
echo "1. Configure .env file with your API keys:"
echo "   nano .env"
echo "   (Set GEMINI_API_KEY, OPENAI_API_KEY, and change passwords)"
echo ""
echo "2. Restart services to load new environment:"
echo "   docker compose -f docker-compose.prod.yml restart"
echo "   OR: ./start_production.sh --no-build"
echo ""
echo "3. Verify services are running:"
echo "   docker compose -f docker-compose.prod.yml ps"
echo ""
echo "4. Test your application:"
echo "   http://$(hostname -I | awk '{print $1}')"
echo ""
echo "📚 See POST_DEPLOYMENT.md for detailed next steps"
echo ""
echo -e "${YELLOW}Optional:${NC}"
echo "  - Set up SSL certificates (see DEPLOYMENT.md)"
echo "  - Configure your domain DNS (if using custom domain)"
echo ""

