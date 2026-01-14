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
    libimage-exiftool-perl \
    && rm -rf /var/lib/apt/lists/*

# Fix: Relax ImageMagick security policy for large images (PSB/TIFF)
# 修复: 放宽 ImageMagick 的安全策略以支持超大图像
# 自动检测并修改 policy.xml，并打印修改后的配置以供调试
RUN export POLICY_PATH=$(find /etc -name "policy.xml" | grep "ImageMagick" | head -n 1) && \
    if [ -z "$POLICY_PATH" ]; then \
        echo "Error: ImageMagick policy.xml not found!"; \
        exit 1; \
    else \
        echo "Found ImageMagick policy at: $POLICY_PATH"; \
        # Backup original policy
        cp "$POLICY_PATH" "$POLICY_PATH.bak"; \
        \
        # Use a more robust sed pattern that handles optional spaces and quotes
        # Increase memory limit to 8GiB (N100 has 16GB)
        sed -i 's/domain="resource" name="memory" value="[^"]*"/domain="resource" name="memory" value="8GiB"/' "$POLICY_PATH" && \
        sed -i 's/domain="resource" name="map" value="[^"]*"/domain="resource" name="map" value="16GiB"/' "$POLICY_PATH" && \
        sed -i 's/domain="resource" name="width" value="[^"]*"/domain="resource" name="width" value="256KP"/' "$POLICY_PATH" && \
        sed -i 's/domain="resource" name="height" value="[^"]*"/domain="resource" name="height" value="256KP"/' "$POLICY_PATH" && \
        sed -i 's/domain="resource" name="area" value="[^"]*"/domain="resource" name="area" value="16GB"/' "$POLICY_PATH" && \
        sed -i 's/domain="resource" name="disk" value="[^"]*"/domain="resource" name="disk" value="32GiB"/' "$POLICY_PATH"; \
        \
        echo "--- Updated Policy Settings ---"; \
        grep -E "memory|map|width|height|area|disk" "$POLICY_PATH"; \
    fi

WORKDIR /app

COPY requirements.txt .
# Use Aliyun mirror for PyPI
RUN pip install --no-cache-dir -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
