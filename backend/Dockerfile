FROM python:3.12-slim

# Use Aliyun mirror for Debian APT
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources

# Install system dependencies for libvips and other tools
RUN apt-get update && apt-get install -y \
    libvips \
    libvips-dev \
    libvips-tools \
    build-essential \
    imagemagick \
    && rm -rf /var/lib/apt/lists/*

# Fix: Relax ImageMagick security policy for large images (PSB/TIFF)
# 修复: 放宽 ImageMagick 的安全策略以支持超大图像
RUN sed -i 's/policy domain="resource" name="memory" value="256MiB"/policy domain="resource" name="memory" value="4GiB"/' /etc/ImageMagick-6/policy.xml && \
    sed -i 's/policy domain="resource" name="map" value="512MiB"/policy domain="resource" name="map" value="8GiB"/' /etc/ImageMagick-6/policy.xml && \
    sed -i 's/policy domain="resource" name="width" value="16KP"/policy domain="resource" name="width" value="128KP"/' /etc/ImageMagick-6/policy.xml && \
    sed -i 's/policy domain="resource" name="height" value="16KP"/policy domain="resource" name="height" value="128KP"/' /etc/ImageMagick-6/policy.xml && \
    sed -i 's/policy domain="resource" name="area" value="128MB"/policy domain="resource" name="area" value="8GB"/' /etc/ImageMagick-6/policy.xml && \
    sed -i 's/policy domain="resource" name="disk" value="1GiB"/policy domain="resource" name="disk" value="16GiB"/' /etc/ImageMagick-6/policy.xml

WORKDIR /app

COPY requirements.txt .
# Use Aliyun mirror for PyPI
RUN pip install --no-cache-dir -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
