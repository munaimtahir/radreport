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

# Note: In the official nginx image, the master process starts as root and drops
# privileges for worker processes to the nginx user. For stricter least-privilege
# isolation, consider running this container as a non-root user at deployment time.
CMD ["nginx", "-g", "daemon off;"]
