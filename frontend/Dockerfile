# Stage 1: Build
FROM node:18-alpine as builder
WORKDIR /app

# Use Aliyun mirror for Alpine APK
RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.aliyun.com/g' /etc/apk/repositories

COPY package.json .
# Use --legacy-peer-deps to resolve Mirador 3 / React 18 conflict
# Use Aliyun mirror for NPM
RUN npm config set registry https://registry.npmmirror.com && \
    npm install --legacy-peer-deps

COPY . .
# Increase memory limit for Node build to prevent OOM on N100
# Also skip type checking to save memory if needed (add tsc --skipLibCheck in package.json)
ENV NODE_OPTIONS="--max-old-space-size=2048"
RUN npm run build

FROM nginx:alpine

# Use Aliyun mirror for Alpine APK
RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.aliyun.com/g' /etc/apk/repositories
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
