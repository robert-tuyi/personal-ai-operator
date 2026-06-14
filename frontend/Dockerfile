# Dev-oriented frontend image: Next.js dev server with hot reload.
FROM node:22-slim

WORKDIR /app

# Install deps first (cached unless package.json changes). Source is bind-mounted at runtime.
COPY package.json package-lock.json* ./
RUN npm install

COPY . .

EXPOSE 3000
CMD ["npm", "run", "dev"]
