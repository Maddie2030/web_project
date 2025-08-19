# Stage 1: The Build Stage
FROM node:20-alpine AS builder

WORKDIR /app

# Step 1: Copy only the package files first
COPY package*.json ./

# Step 2: Install dependencies. Docker will cache this step.
# This creates the node_modules folder inside the container
RUN npm install

# Step 3: Copy the rest of the application source code
COPY . .

# Step 4: Run the build command
RUN npm run build

# Stage 2: The Run Stage
FROM node:20-alpine

WORKDIR /app

# Step 5: Copy the compiled build from the builder stage
COPY --from=builder /app/dist ./dist

# Step 6: Install a simple static file server
RUN npm install -g serve

# Step 7: Expose the port
EXPOSE 5173

# Step 8: Command to serve the application
CMD ["serve", "-s", "dist"]