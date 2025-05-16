# 1. Base image
FROM python:3.11-slim

# 2. Install Chromium & matching chromedriver
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       chromium \
       chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# 3. Set working directory
WORKDIR /app

# 4. Cache and install Python dependencies
#    Copy only requirements first to leverage Docker layer caching
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# 5. Copy rest of the application code
COPY . .

# 6. Expose the port your app runs on
EXPOSE 8000

# 7. (Optional) Set environment variables
ENV PYTHONUNBUFFERED=1

# 8. Default command to run the ASGI app
CMD ["uvicorn", "main:socketio_app", "--host", "0.0.0.0", "--port", "8000"]
