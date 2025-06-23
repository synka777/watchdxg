# Use the official Playwright Python image (includes Python, Playwright, and browsers)
FROM mcr.microsoft.com/playwright/python:v1.52.0-noble

# Set work directory
WORKDIR /app

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Real-time output, useful for logging
ENV PYTHONUNBUFFERED=1

# Then run the project
CMD ["python", "runner.py", "--setup"]