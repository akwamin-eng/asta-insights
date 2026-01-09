# STAGE 1: Build
FROM node:20-alpine AS build
WORKDIR /app

# In this context, package.json is in the root of 'asta-web'
COPY package.json package-lock.json* ./

# Install dependencies (Alpine is faster and uses less memory)
RUN npm install --network-timeout=100000 --legacy-peer-deps

COPY . .
RUN npm run build

# STAGE 2: Serve
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
RUN echo 'server { listen 8080; location / { root /usr/share/nginx/html; index index.html; try_files $uri $uri/ /index.html; } }' > /etc/nginx/conf.d/default.conf
EXPOSE 8080
CMD ["nginx", "-g", "daemon off;"]
