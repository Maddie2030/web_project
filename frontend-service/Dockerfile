# Stage 1: The Build Stage
# -------------------------
FROM node:20-alpine AS builder

WORKDIR /app

# Copy and install dependencies in one step to create a single layer.
COPY package*.json ./
RUN npm install

# Copy the rest of the application source code.
COPY . .

# Run the build command to generate the static assets.
RUN npm run build


# Stage 2: The Run Stage (using Nginx)
# -------------------------
FROM nginx:stable-alpine

# Set working directory for Nginx.
WORKDIR /usr/share/nginx/html

# Remove the default Nginx static files.
RUN rm -rf ./*

# Copy the compiled build from the builder stage into the Nginx directory.
COPY --from=builder /app/dist .

# Expose port 80, the standard HTTP port for web servers.
EXPOSE 80

# Command to start Nginx in the foreground.
CMD ["nginx", "-g", "daemon off;"]