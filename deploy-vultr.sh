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

# Create nginx ssl directory
echo -e "${GREEN}📁 Creating nginx SSL directory...${NC}"
mkdir -p nginx/ssl

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
echo "  API:       http://$(hostname -I | awk '{print $1}')/api/v1/health"
echo "  n8n:       http://$(hostname -I | awk '{print $1}')/n8n/"
echo "  Grafana:   http://$(hostname -I | awk '{print $1}')/grafana/"
echo ""
echo -e "${YELLOW}Useful commands:${NC}"
echo "  View logs:     docker compose -f docker-compose.prod.yml logs -f"
echo "  Restart:       docker compose -f docker-compose.prod.yml restart"
echo "  Stop:          docker compose -f docker-compose.prod.yml down"
echo "  Status:        docker compose -f docker-compose.prod.yml ps"
echo ""
echo -e "${RED}⚠️  Don't forget to:${NC}"
echo "  1. Set up SSL certificates (see DEPLOYMENT.md)"
echo "  2. Change default passwords in .env"
echo "  3. Configure your domain DNS (if using custom domain)"
echo ""

