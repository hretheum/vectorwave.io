FROM python:3.11-slim

WORKDIR /app

# Copy only what we need
COPY minimal_server.py .

# Expose port 8040 
EXPOSE 8040

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8040/health', timeout=5)" || exit 1

# Run the minimal server (no dependencies needed)
CMD ["python3", "minimal_server.py"]