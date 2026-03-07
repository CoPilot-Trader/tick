FROM node:18-alpine

WORKDIR /app

# Copy package files first for Docker layer caching
COPY package.json package-lock.json ./
RUN npm ci

# Copy the rest of the application
COPY . .

# Accept build-time API URL (for production builds)
ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

# Build the Next.js app
RUN npm run build

EXPOSE 3000

# Use Next.js production server
CMD ["npm", "start"]
