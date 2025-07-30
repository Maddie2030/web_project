# Dockerfile for Frontend Service (React/Vite - Development)
FROM node:18-alpine

WORKDIR /app

# Copy package.json and lock file to leverage Docker layer caching
# Use yarn.lock if you use yarn, package-lock.json if you use npm
COPY package.json yarn.lock ./ # If using npm: COPY package.json package-lock.json ./

# Install dependencies
RUN yarn install --frozen-lockfile # If using npm: RUN npm install

# Copy the rest of the application code
COPY . .

# Expose the port Vite's dev server runs on
EXPOSE 3000

# Command to start the development server
# This is overridden by docker-compose for convenience, but serves as default
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]