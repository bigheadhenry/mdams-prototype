FROM eclipse-temurin:11-jre



ENV CANTALOUPE_VERSION=5.0.6
WORKDIR /opt

# Install unzip, font libraries, and GraphicsMagick/FFmpeg for better format support
RUN apt-get update && apt-get install -y \
    unzip \
    fontconfig \
    libfreetype6 \
    graphicsmagick \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy zip and unzip
COPY cantaloupe-${CANTALOUPE_VERSION}.zip .
RUN unzip cantaloupe-${CANTALOUPE_VERSION}.zip && \
    mv cantaloupe-${CANTALOUPE_VERSION} cantaloupe && \
    rm cantaloupe-${CANTALOUPE_VERSION}.zip

WORKDIR /opt/cantaloupe

# Create default directories
RUN mkdir -p /var/lib/cantaloupe/images \
    && mkdir -p /var/lib/cantaloupe/cache

# Copy config
# Force rebuild 2026-01-05
COPY cantaloupe.properties /etc/cantaloupe.properties

# Expose port
EXPOSE 8182

# Start Cantaloupe
CMD ["java", "-Dcantaloupe.config=/etc/cantaloupe.properties", "-jar", "cantaloupe-5.0.6.jar"]
