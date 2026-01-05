FROM eclipse-temurin:11-jre

ENV CANTALOUPE_VERSION=5.0.6
WORKDIR /opt

# Optimize: Copy the UNZIPPED folder directly to avoid needing 'unzip' inside the image
# User must unzip cantaloupe-5.0.6.zip locally to cantaloupe-5.0.6 folder before building
COPY cantaloupe-${CANTALOUPE_VERSION} cantaloupe

WORKDIR /opt/cantaloupe

# Create default directories
RUN mkdir -p /var/lib/cantaloupe/images \
    && mkdir -p /var/lib/cantaloupe/cache

# Copy config
COPY cantaloupe.properties /etc/cantaloupe.properties

# Expose port
EXPOSE 8182

# Start Cantaloupe
CMD ["java", "-Dcantaloupe.config=/etc/cantaloupe.properties", "-jar", "cantaloupe-5.0.6.jar"]
