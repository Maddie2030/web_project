# Use a recent Node.js image
FROM node:20-alpine

# Set the working directory for the container
WORKDIR /app

# Copy the package.json and package-lock.json to install dependencies
COPY package*.json ./

# Install project dependencies
RUN npm install

# Expose the port that the Vite dev server runs on
EXPOSE 5173

# The `command` in your docker-compose.yml will override this
CMD ["npm", "run", "dev"]