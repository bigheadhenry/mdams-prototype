FROM eclipse-temurin:11-jre

RUN set -eux; \
    find /etc/apt -type f \( -name "*.list" -o -name "*.sources" \) -print0 | \
    xargs -0 -r sed -i \
      -e 's|http://archive.ubuntu.com/ubuntu|https://mirrors.tuna.tsinghua.edu.cn/ubuntu|g' \
      -e 's|http://security.ubuntu.com/ubuntu|https://mirrors.tuna.tsinghua.edu.cn/ubuntu|g' \
      -e 's|http://ports.ubuntu.com/ubuntu-ports|https://mirrors.tuna.tsinghua.edu.cn/ubuntu-ports|g'

ENV CANTALOUPE_VERSION=5.0.6
WORKDIR /opt

# Install unzip, download tools, font libraries, and GraphicsMagick/FFmpeg for better format support
RUN apt-get update && apt-get install -y \
    unzip \
    curl \
    fontconfig \
    libfreetype6 \
    graphicsmagick \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Download release zip during build so the repo does not need to carry large binaries
RUN curl -L -o cantaloupe-${CANTALOUPE_VERSION}.zip \
    https://github.com/cantaloupe-project/cantaloupe/releases/download/v${CANTALOUPE_VERSION}/cantaloupe-${CANTALOUPE_VERSION}.zip \
    && unzip cantaloupe-${CANTALOUPE_VERSION}.zip \
    && mv cantaloupe-${CANTALOUPE_VERSION} cantaloupe \
    && rm cantaloupe-${CANTALOUPE_VERSION}.zip

WORKDIR /opt/cantaloupe

# Create default directories
RUN mkdir -p /var/lib/cantaloupe/images \
    && mkdir -p /var/lib/cantaloupe/cache

# Runtime config is mounted by docker-compose to /etc/cantaloupe.properties

# Expose port
EXPOSE 8182

# Start Cantaloupe
CMD ["java", "-Dcantaloupe.config=/etc/cantaloupe.properties", "-jar", "cantaloupe-5.0.6.jar"]
