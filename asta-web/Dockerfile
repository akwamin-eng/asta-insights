# STAGE 1: Build
FROM node:20-alpine AS build
WORKDIR /app

# Copy the package files first (better for caching)
COPY package.json package-lock.json ./

# FIXED: Use 'npm ci' for faster, more reliable builds (fixes exit code 254)
RUN npm ci --legacy-peer-deps

# Copy everything else
COPY . .

# Run build
RUN npm run build

# STAGE 2: Serve
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
# Custom Nginx config to support React Router (prevents 404s on refresh)
RUN echo 'server { listen 8080; location / { root /usr/share/nginx/html; index index.html; try_files $uri $uri/ /index.html; } }' > /etc/nginx/conf.d/default.conf
EXPOSE 8080
CMD ["nginx", "-g", "daemon off;"]