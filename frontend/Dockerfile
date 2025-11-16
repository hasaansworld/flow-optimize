# Frontend Dockerfile
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Verify build output exists and show contents
RUN echo "Checking build output..." && \
    (test -d /app/build && echo "Found /app/build" && ls -la /app/build) || \
    (test -d /app/dist && echo "Found /app/dist" && ls -la /app/dist) || \
    (echo "ERROR: Build output not found in /app/build or /app/dist" && exit 1)

# Production stage with nginx
FROM nginx:alpine

# Remove default nginx config to avoid showing default page
RUN rm -f /etc/nginx/conf.d/default.conf

# Copy built files to nginx (vite.config.ts specifies outDir: 'build')
COPY --from=builder /app/build /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]

