# Post-Deployment Checklist

After running `./deploy-vultr.sh`, follow these steps:

## ✅ Step 1: Configure Environment Variables

The script creates a `.env` file, but you need to add your API keys:

```bash
# Edit the .env file
nano .env
```

**Required settings:**
- `GEMINI_API_KEY` - Your Google Gemini API key (required)
- `OPENAI_API_KEY` - Your OpenAI API key (if using OpenAI models)
- `POSTGRES_PASSWORD` - Change from default to a strong password
- `N8N_PASSWORD` - Change from default to a strong password  
- `GRAFANA_PASSWORD` - Change from default to a strong password

Save and exit (Ctrl+X, then Y, then Enter).

## ✅ Step 2: Restart Services

After updating `.env`, restart services to load the new environment variables:

```bash
# Restart all services
docker compose -f docker-compose.prod.yml restart

# OR use the production start script
./start_production.sh --no-build
```

## ✅ Step 3: Verify Services Are Running

```bash
# Check service status
docker compose -f docker-compose.prod.yml ps

# Check logs for any errors
docker compose -f docker-compose.prod.yml logs -f
```

All services should show as "Up" or "Healthy".

## ✅ Step 4: Test Your Application

Get your server IP:
```bash
hostname -I | awk '{print $1}'
```

Then test these URLs in your browser:
- **Frontend**: `http://YOUR_SERVER_IP` (port 80)
- **API**: `http://YOUR_SERVER_IP:8000`
- **API Health**: `http://YOUR_SERVER_IP:8000/api/v1/health`
- **API Docs**: `http://YOUR_SERVER_IP:8000/docs`
- **n8n**: `http://YOUR_SERVER_IP:5678`
- **Grafana**: `http://YOUR_SERVER_IP:3000`

## ✅ Step 5: Set Up n8n Workflow (If Needed)

1. Access n8n at `http://YOUR_SERVER_IP:5678`
2. Login with credentials from `.env` (N8N_USER / N8N_PASSWORD)
3. Import workflow:
   - Click "Import from File"
   - Select: `n8n_workflows/main_control_loop.json`
   - Activate the workflow

## ✅ Step 6: Set Up SSL (Recommended for Production)

See [DEPLOYMENT.md](DEPLOYMENT.md) Step 9 for SSL setup with Let's Encrypt.

## 🔍 Troubleshooting

### Services not starting?
```bash
# Check logs
docker compose -f docker-compose.prod.yml logs

# Check specific service
docker compose -f docker-compose.prod.yml logs agent-api
```

### API not responding?
- Verify `GEMINI_API_KEY` is set correctly in `.env`
- Check API logs: `docker compose -f docker-compose.prod.yml logs agent-api`
- Restart API: `docker compose -f docker-compose.prod.yml restart agent-api`

### Frontend not loading?
- Check frontend logs: `docker compose -f docker-compose.prod.yml logs frontend`
- Rebuild frontend: `docker compose -f docker-compose.prod.yml build frontend && docker compose -f docker-compose.prod.yml up -d frontend`

## 📝 Quick Reference

```bash
# View all logs
docker compose -f docker-compose.prod.yml logs -f

# Restart all services
docker compose -f docker-compose.prod.yml restart

# Stop all services
docker compose -f docker-compose.prod.yml down

# Start services (after code changes)
./start_production.sh

# Check service health
docker compose -f docker-compose.prod.yml ps
```

## 🎉 You're Done!

Your application should now be accessible at `http://YOUR_SERVER_IP`

For more details, see:
- [DEPLOYMENT.md](DEPLOYMENT.md) - Full deployment guide
- [VULTR_QUICKSTART.md](VULTR_QUICKSTART.md) - Quick reference

