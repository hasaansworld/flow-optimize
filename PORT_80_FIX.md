# Port 80 Conflict - Quick Fix

If you get an error: `failed to bind host port 0.0.0.0:80/tcp: address already in use`

## Quick Solutions

### Option 1: Stop Conflicting Service (Recommended)

```bash
# Run the automated fix script
./fix-port-80-frontend.sh

# Or manually stop common services:
sudo systemctl stop apache2
sudo systemctl disable apache2
sudo systemctl stop nginx
sudo systemctl disable nginx
```

### Option 2: Use Port 8080 Instead

If you can't stop the service using port 80, use port 8080:

```bash
# Add to your .env file
echo "FRONTEND_PORT=8080" >> .env

# Restart services
docker compose -f docker-compose.prod.yml restart frontend
```

Then access frontend at: `http://YOUR_SERVER_IP:8080`

### Option 3: Find and Stop the Specific Process

```bash
# Find what's using port 80
sudo netstat -tulpn | grep :80
# OR
sudo ss -tulpn | grep :80
# OR
sudo lsof -i :80

# Stop the process (replace PID with actual process ID)
sudo kill -9 PID
```

## Verify Fix

After fixing, restart services:

```bash
docker compose -f docker-compose.prod.yml up -d
```

Check if frontend is running:

```bash
docker ps | grep frontend
curl http://localhost:${FRONTEND_PORT:-80}/health
```

