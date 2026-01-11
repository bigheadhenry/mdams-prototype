FROM python:3.12-slim

# Use Aliyun mirror for Debian APT
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources

# Install system dependencies for libvips and other tools
RUN apt-get update && apt-get install -y \
    libvips \
    libvips-dev \
    libvips-tools \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
# Use Aliyun mirror for PyPI
RUN pip install --no-cache-dir -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
