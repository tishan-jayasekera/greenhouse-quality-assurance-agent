FROM python:3.11-slim

# Install Python dependencies first so Playwright is available
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers and dependencies
RUN playwright install chromium
RUN playwright install-deps chromium

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
