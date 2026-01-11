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
# 注意：在 ImageMagick 6 中，路径是 /etc/ImageMagick-6/policy.xml
# 在 ImageMagick 7 (Debian Bookworm) 中，路径可能是 /etc/ImageMagick-6/policy.xml 或其他
# 这里的 sed 命令会尝试查找文件，如果找不到会报错。
# 更好的做法是先检查文件是否存在，或者直接写入新文件。
RUN if [ -f /etc/ImageMagick-6/policy.xml ]; then \
        sed -i 's/policy domain="resource" name="memory" value="256MiB"/policy domain="resource" name="memory" value="4GiB"/' /etc/ImageMagick-6/policy.xml && \
        sed -i 's/policy domain="resource" name="map" value="512MiB"/policy domain="resource" name="map" value="8GiB"/' /etc/ImageMagick-6/policy.xml && \
        sed -i 's/policy domain="resource" name="width" value="16KP"/policy domain="resource" name="width" value="128KP"/' /etc/ImageMagick-6/policy.xml && \
        sed -i 's/policy domain="resource" name="height" value="16KP"/policy domain="resource" name="height" value="128KP"/' /etc/ImageMagick-6/policy.xml && \
        sed -i 's/policy domain="resource" name="area" value="128MB"/policy domain="resource" name="area" value="8GB"/' /etc/ImageMagick-6/policy.xml && \
        sed -i 's/policy domain="resource" name="disk" value="1GiB"/policy domain="resource" name="disk" value="16GiB"/' /etc/ImageMagick-6/policy.xml; \
    else \
        echo "ImageMagick policy file not found at /etc/ImageMagick-6/policy.xml, checking other locations..."; \
        find /etc -name "policy.xml"; \
    fi

WORKDIR /app

COPY requirements.txt .
# Use Aliyun mirror for PyPI
RUN pip install --no-cache-dir -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
