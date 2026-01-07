# Multi-stage build for production React frontend
FROM node:18-alpine as builder

WORKDIR /app

# Copy package files and install dependencies
COPY package*.json ./
RUN npm ci

# Copy source code and build
COPY . .
RUN npm run build

# ============================================
# Production stage with nginx
FROM nginx:1.25-alpine

# Copy custom nginx configuration
COPY nginx.prod.conf /etc/nginx/conf.d/default.conf

# Copy built assets from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Expose port (internal only)
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost/ || exit 1

# nginx runs as root by default but drops privileges
# No need to change user as nginx handles this internally
CMD ["nginx", "-g", "daemon off;"]
