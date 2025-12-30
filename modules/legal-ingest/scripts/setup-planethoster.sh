#!/bin/bash

# Setup script for PlanetHoster deployment
# Deploys API, cache database, and nginx with SSL

set -e

echo "=== Legal Ingest - PlanetHoster Setup ==="

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "ERROR: This script must be run as root (use sudo)"
    exit 1
fi

# Update system
echo -e "\nUpdating system..."
apt-get update
apt-get upgrade -y

# Install Docker if not present
echo -e "\nChecking Docker installation..."
if ! command -v docker &> /dev/null; then
    echo "Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
    
    # Install Docker Compose
    echo "Installing Docker Compose..."
    curl -L "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
else
    echo "Docker already installed: $(docker --version)"
fi

# Create application directory
echo -e "\nCreating application directory..."
APP_DIR="/opt/legal-ingest"
mkdir -p $APP_DIR
cd $APP_DIR

# Copy files (assumes files are in current directory or uploaded separately)
echo -e "\nSetting up application files..."
# This would typically involve git clone or file transfer
# For now, assume files are already in place

# Create required directories
mkdir -p $APP_DIR/logs
mkdir -p $APP_DIR/nginx/conf.d
mkdir -p $APP_DIR/data

# Create nginx configuration
echo -e "\nCreating nginx configuration..."
cat > $APP_DIR/nginx/nginx.conf << 'EOF'
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;

    sendfile on;
    tcp_nopush on;
    keepalive_timeout 65;
    gzip on;

    include /etc/nginx/conf.d/*.conf;
}
EOF

cat > $APP_DIR/nginx/conf.d/api.conf << 'EOF'
# HTTP redirect to HTTPS
server {
    listen 80;
    server_name api.zeroobstacle.ca;

    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }

    location / {
        return 301 https://$server_name$request_uri;
    }
}

# HTTPS server
server {
    listen 443 ssl http2;
    server_name api.zeroobstacle.ca;

    ssl_certificate /etc/letsencrypt/live/api.zeroobstacle.ca/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.zeroobstacle.ca/privkey.pem;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # API proxy
    location / {
        proxy_pass http://api:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Health check
    location /health {
        proxy_pass http://api:8000/health;
        access_log off;
    }
}
EOF

# Create environment file if it doesn't exist
if [ ! -f "$APP_DIR/.env" ]; then
    echo -e "\nCreating .env file..."
    cp $APP_DIR/.env.example $APP_DIR/.env || echo "Warning: .env.example not found"
    echo "Please edit $APP_DIR/.env with your configuration"
fi

# Configure firewall
echo -e "\nConfiguring firewall..."
if command -v ufw &> /dev/null; then
    ufw allow 22/tcp
    ufw allow 80/tcp
    ufw allow 443/tcp
    ufw --force enable
    echo "Firewall configured"
else
    echo "ufw not found, skipping firewall configuration"
fi

# Build and start services
echo -e "\nBuilding Docker images..."
cd $APP_DIR
docker-compose -f docker-compose-planethoster.yml build

echo -e "\nStarting services..."
docker-compose -f docker-compose-planethoster.yml up -d

# Wait for services to start
echo -e "\nWaiting for services to start..."
sleep 20

# Obtain SSL certificate
echo -e "\nObtaining SSL certificate..."
echo "Note: Make sure DNS is configured to point to this server before proceeding"
read -p "Press Enter to continue with SSL certificate generation, or Ctrl+C to abort..."

docker-compose -f docker-compose-planethoster.yml run --rm certbot certonly \
    --webroot \
    --webroot-path=/var/www/html \
    --email admin@zeroobstacle.ca \
    --agree-tos \
    --no-eff-email \
    -d api.zeroobstacle.ca

# Reload nginx with SSL
echo -e "\nReloading nginx..."
docker-compose -f docker-compose-planethoster.yml restart nginx

# Setup SSL renewal cron job
echo -e "\nSetting up SSL auto-renewal..."
cat > /etc/cron.daily/certbot-renewal << 'EOF'
#!/bin/bash
cd /opt/legal-ingest
docker-compose -f docker-compose-planethoster.yml run --rm certbot renew
docker-compose -f docker-compose-planethoster.yml restart nginx
EOF
chmod +x /etc/cron.daily/certbot-renewal

# Check service status
echo -e "\nChecking service status..."
docker-compose -f docker-compose-planethoster.yml ps

# Display results
echo -e "\n=== PlanetHoster Setup Complete ==="
echo -e "\nServices running:"
echo "  API: https://api.zeroobstacle.ca"
echo "  Health check: https://api.zeroobstacle.ca/health"
echo -e "\nTo view logs:"
echo "  docker-compose -f docker-compose-planethoster.yml logs -f"
echo -e "\nTo stop services:"
echo "  docker-compose -f docker-compose-planethoster.yml down"
echo -e "\nSSL certificate will auto-renew daily"
echo -e "\nNext steps:"
echo "  1. Verify API is accessible at https://api.zeroobstacle.ca"
echo "  2. Configure tunnel from local servers"
echo "  3. Test end-to-end data sync"
