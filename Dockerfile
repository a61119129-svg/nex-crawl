FROM python:3.13-slim

WORKDIR /app

# Install system deps for lxml & playwright
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libxml2-dev libxslt1-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY nexcrawl/ nexcrawl/
COPY pyproject.toml .

# Install the package
RUN pip install --no-cache-dir -e .

EXPOSE 8000

CMD ["uvicorn", "nexcrawl.api:app", "--host", "0.0.0.0", "--port", "8000"]
