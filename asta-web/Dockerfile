# STAGE 1: Build
FROM node:20-alpine AS build
WORKDIR /app

# COPY using a wildcard (*)
# This is the magic fix: It copies package.json AND package-lock.json if it exists,
# but it won't crash if the lockfile is missing.
COPY package*.json ./

# Switch back to 'npm install' because 'npm ci' requires a lockfile
RUN npm install --legacy-peer-deps

# Copy the rest of the web folder
COPY . .

# Build
RUN npm run build

# STAGE 2: Serve
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
RUN echo 'server { listen 8080; location / { root /usr/share/nginx/html; index index.html; try_files $uri $uri/ /index.html; } }' > /etc/nginx/conf.d/default.conf
EXPOSE 8080
CMD ["nginx", "-g", "daemon off;"]
