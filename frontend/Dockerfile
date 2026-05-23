# ─────────────────────────────────────────────────────────────────────────────
# Frontend Dockerfile — multi-stage build
# Stage 1 (builder): npm install + vite build → produces /dist
# Stage 2 (runtime): Nginx serves the static /dist bundle
# ─────────────────────────────────────────────────────────────────────────────

# ── Stage 1: Build React app ──────────────────────────────────────────────────
FROM node:22-alpine AS builder

WORKDIR /app

# Copy package manifests first — Docker caches this layer
# node_modules only gets reinstalled if package.json or package-lock.json changes
COPY package.json package-lock.json* ./

# ci (clean install) is stricter than install — fails on lockfile mismatch
# --legacy-peer-deps is sometimes needed for React @latest ecosystem
RUN npm ci

# Copy source after installing deps to maximise layer cache hits
COPY . .

# Build the production bundle — Vite outputs to /app/dist
# VITE_ prefixed env vars are inlined at build time by Vite
ARG VITE_API_BASE_URL=http://localhost:8000
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

RUN npm run build


# ── Stage 2: Serve with Nginx ─────────────────────────────────────────────────
FROM nginx:1.27-alpine AS runtime

# Remove the default Nginx placeholder page
RUN rm /etc/nginx/conf.d/default.conf

# Our custom Nginx config handles SPA routing + API proxying
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy the Vite production build from Stage 1
COPY --from=builder /app/dist /usr/share/nginx/html

# Nginx runs as root by default inside Docker; acceptable for this setup
# In hardened deployments, configure Nginx to run as non-root

EXPOSE 80

# Healthcheck — verifies Nginx is serving the app
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD wget -qO- http://127.0.0.1/health || exit 1

CMD ["nginx", "-g", "daemon off;"]
