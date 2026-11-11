
# Stage 1: Build the React application
FROM node:24-alpine AS builder

WORKDIR /app

COPY frontend/package*.json ./

RUN npm ci

COPY frontend/ .

RUN npm run build

# Stage 2: Serve the production build
FROM nginx:alpine

ENV NGINX_ENVSUBST_FILTER="^BACKEND_URL$"

COPY --from=builder /app/dist /usr/share/nginx/html

COPY frontend/nginx.conf /etc/nginx/templates/default.conf.template

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]