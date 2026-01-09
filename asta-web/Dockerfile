# STAGE 1: Build
FROM node:20-alpine AS build
WORKDIR /app

# COPY from the root context (asta-web/package.json) to the container
COPY asta-web/package.json asta-web/package-lock.json ./

# Install dependencies (Clean Install)
RUN npm ci --legacy-peer-deps

# Copy the rest of the web folder
COPY asta-web/ .

# Build
RUN npm run build

# STAGE 2: Serve
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
RUN echo 'server { listen 8080; location / { root /usr/share/nginx/html; index index.html; try_files $uri $uri/ /index.html; } }' > /etc/nginx/conf.d/default.conf
EXPOSE 8080
CMD ["nginx", "-g", "daemon off;"]
