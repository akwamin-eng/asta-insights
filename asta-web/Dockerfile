# STAGE 1: Build the React App
FROM node:20-slim AS build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# STAGE 2: Serve with Nginx
FROM nginx:alpine
# Copy the built files from Stage 1 to the Nginx folder
COPY --from=build /app/dist /usr/share/nginx/html
# Custom config to allow React Router to work and listen on 8080
RUN echo 'server { listen 8080; location / { root /usr/share/nginx/html; index index.html; try_files $uri $uri/ /index.html; } }' > /etc/nginx/conf.d/default.conf
EXPOSE 8080
CMD ["nginx", "-g", "daemon off;"]
