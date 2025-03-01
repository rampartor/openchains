# docker/frontend.Dockerfile
FROM node:20-slim

WORKDIR /app

# Copy package.json and yarn.lock
COPY frontend/package.json frontend/yarn.lock* ./

# Install dependencies
RUN yarn install

# Copy frontend code
COPY frontend ./

# Expose port
EXPOSE 5173

# Start development server with host set to 0.0.0.0 to make it accessible outside the container
CMD ["yarn", "dev", "--host", "0.0.0.0"]
