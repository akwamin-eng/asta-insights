# STAGE 1: Build
FROM node:20 AS build
WORKDIR /app

# The path needs to be relative to the context (the folder being sent to Docker)
COPY package*.json ./
RUN npm install

# Copy everything from the current directory (asta-web) to the container
COPY . .
RUN npm run build

# STAGE 2: Serve
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
RUN echo 'server { listen 8080; location / { root /usr/share/nginx/html; index index.html; try_files $uri $uri/ /index.html; } }' > /etc/nginx/conf.d/default.conf
EXPOSE 8080
CMD ["nginx", "-g", "daemon off;"]
