# Multi-stage build for React frontend
# Stage 1: Build
FROM node:20-alpine as builder

# Set working directory
WORKDIR /app

# Copy package files
COPY webui/package.json webui/package-lock.json* /app/

# Install dependencies
RUN npm ci

# Copy source code
COPY webui/ /app/

# Build arguments for API URL
ARG VITE_API_URL=http://backend:8000
ENV VITE_API_URL=$VITE_API_URL

# Build production bundle
RUN npm run build

# Stage 2: Serve with nginx
FROM nginx:alpine

# Copy nginx configuration
COPY webui/nginx.conf /etc/nginx/conf.d/default.conf

# Copy built files from builder
COPY --from=builder /app/dist /usr/share/nginx/html

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost/health || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
