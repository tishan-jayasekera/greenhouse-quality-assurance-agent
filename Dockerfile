FROM python:3.11-slim

# Install Playwright system dependencies
RUN apt-get update && apt-get install -y \
    libnss3 libatk-bridge2.0-0 libdrm2 libxcomposite1 \
    libxdamage1 libxrandr2 libgbm1 libpango-1.0-0 \
    libcairo2 libasound2 libatspi2.0-0 libxshmfence1 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN playwright install chromium

# Copy agent code
COPY qa_agent/ /app/qa_agent/
COPY tests/ /app/tests/
COPY app.py /app/
WORKDIR /app

# Expose Render's default expected port
EXPOSE 10000

# Entry point for the Streamlit Web UI
# We tell Streamlit to run headlessly, bind to all interfaces (0.0.0.0), and listen on $PORT
CMD sh -c "streamlit run app.py --server.port=${PORT:-10000} --server.address=0.0.0.0 --server.headless=true"
