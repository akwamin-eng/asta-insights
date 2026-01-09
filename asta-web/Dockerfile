# STAGE 1: Build
FROM node:20-alpine AS build
WORKDIR /app

# ARGUMENTS (Secrets passed from GitHub)
ARG VITE_SUPABASE_URL
ARG VITE_SUPABASE_ANON_KEY
ARG VITE_GOOGLE_MAPS_API_KEY

# ENVIRONMENT VARIABLES (Made available to Vite)
# 1. Supabase
ENV VITE_SUPABASE_URL=$VITE_SUPABASE_URL
ENV VITE_SUPABASE_ANON_KEY=$VITE_SUPABASE_ANON_KEY

# 2. Mapbox (Hardcoded Public Token - 100% Reliable)
ENV VITE_MAPBOX_TOKEN="pk.eyJ1IjoiYWt3YW1pbiIsImEiOiJjbWprdXBkZ2kweDQ5M2dweTU2d2plNXcwIn0.1TlZFWJvlEuX8-i3FOdV3g"

# 3. Google Maps
ENV VITE_GOOGLE_MAPS_API_KEY=$VITE_GOOGLE_MAPS_API_KEY

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install --legacy-peer-deps

# Copy source code
COPY . .

# Build
RUN npm run build

# STAGE 2: Serve
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
RUN echo 'server { listen 8080; location / { root /usr/share/nginx/html; index index.html; try_files $uri $uri/ /index.html; } }' > /etc/nginx/conf.d/default.conf
EXPOSE 8080
CMD ["nginx", "-g", "daemon off;"]
