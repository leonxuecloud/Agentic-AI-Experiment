##### Multi-stage Dockerfile (Builder + Production) #####
# Purpose: Build TypeScript with dev dependencies, ship minimal production image.

# -------- Builder Stage --------
FROM node:20-alpine AS builder
WORKDIR /app

# Copy manifest & tsconfig first for better layer caching
COPY package*.json tsconfig.json ./
RUN npm ci && npm cache clean --force

# Copy source code
COPY src ./src

# Build TypeScript (produces dist/)
RUN npm run build

# -------- Production Stage --------
FROM node:20-alpine AS production
WORKDIR /app

# Create non-root user
RUN addgroup -g 1001 -S nodejs && adduser -S oncall -u 1001

# Copy only production dependencies (install separate to prune dev deps)
COPY package*.json ./
RUN npm ci --only=production && npm cache clean --force

# Copy build artifacts from builder
COPY --from=builder /app/dist ./dist

# Create writable directories used by the server
RUN mkdir -p /var/oncall-support/files oncall-files .mcp-storage && \
    chown -R oncall:nodejs /var/oncall-support /app

USER oncall
ENV MCP_PORT=3001
EXPOSE 3001

# Healthcheck (optional but helpful for orchestrators)
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD node -e "require('http').get('http://localhost:3001/health', r => process.exit(r.statusCode===200?0:1)).on('error',()=>process.exit(1))"

# Run the MCP Server in DUAL mode (HTTP for external + stdio for webhook processor)
CMD ["node", "dist/mcp-server.js", "--transport=dual", "--port=${MCP_PORT}"]
