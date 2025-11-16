# Frontend Dockerfile - No nginx, using simple HTTP server
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

# Verify build output exists
RUN echo "Checking build output..." && \
    (test -d /app/build && echo "Found /app/build" && ls -la /app/build) || \
    (test -d /app/dist && echo "Found /app/dist" && ls -la /app/dist) || \
    (echo "ERROR: Build output not found in /app/build or /app/dist" && exit 1)

# Production stage - use serve to serve static files (no nginx)
FROM node:20-alpine

# Install serve globally (lightweight static file server)
RUN npm install -g serve

# Copy built files (vite.config.ts specifies outDir: 'build')
COPY --from=builder /app/build /app/build

WORKDIR /app

# Verify build directory has files
RUN if [ ! -d "build" ] || [ -z "$(ls -A build)" ]; then \
        echo "ERROR: Build directory is empty or missing" && exit 1; \
    fi && \
    echo "Build files:" && ls -la build/

EXPOSE 80

# Serve on port 80 with SPA routing support (-s for single-page app)
# Health check endpoint will be handled by the app itself
CMD ["serve", "-s", "build", "-l", "80"]

