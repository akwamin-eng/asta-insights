# STAGE 1: Build
FROM node:20-alpine AS build
WORKDIR /app

# 1. Declare that we expect these arguments from GitHub Actions
ARG VITE_SUPABASE_URL
ARG VITE_SUPABASE_ANON_KEY

# 2. Set them as Environment Variables so Vite can see them during build
ENV VITE_SUPABASE_URL=$VITE_SUPABASE_URL
ENV VITE_SUPABASE_ANON_KEY=$VITE_SUPABASE_ANON_KEY

# Copy package files (Using wildcard for safety)
COPY package*.json ./

# Install dependencies
RUN npm install --legacy-peer-deps

# Copy source code
COPY . .

# Build (Vite will now bake the keys into the JS)
RUN npm run build

# STAGE 2: Serve
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
RUN echo 'server { listen 8080; location / { root /usr/share/nginx/html; index index.html; try_files $uri $uri/ /index.html; } }' > /etc/nginx/conf.d/default.conf
EXPOSE 8080
CMD ["nginx", "-g", "daemon off;"]
