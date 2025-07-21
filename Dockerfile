# Use a base image with both Python and Node.js
FROM python:3.9-slim as backend

WORKDIR /app/backend

# Install system dependencies for backend
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements and install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ .

# --- Frontend build stage ---
FROM node:16-alpine as frontend
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ .
RUN npm run build

# --- Final stage ---
FROM python:3.9-slim

# Install system dependencies for backend
RUN apt-get update && apt-get install -y \
    ffmpeg \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Install supervisord to run both services
RUN pip install supervisor

WORKDIR /app

# Copy backend from build stage
COPY --from=backend /app/backend /app/backend

# Copy backend requirements and install Python dependencies in final image
COPY backend/requirements.txt /app/backend/
RUN pip install --no-cache-dir -r /app/backend/requirements.txt


# Copy frontend build from build stage
COPY --from=frontend /app/frontend/build /app/frontend/build

# Copy supervisord config
COPY supervisord.conf /etc/supervisord.conf

EXPOSE 8000 3000

CMD ["supervisord", "-c", "/etc/supervisord.conf"] 
