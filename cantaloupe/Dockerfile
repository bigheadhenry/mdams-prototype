FROM ubuntu/jre:11-24.04

# Use Aliyun mirror for Ubuntu APT
# Note: ubuntu/jre images are minimal (distroless-like) and may not have apt or sh in expected paths.
# However, 11-24.04 usually has basic shell. If not, we skip apt config or assume sources.list is in different place.
# Actually, ubuntu/jre is VERY minimal. It might not have 'sed' or 'apt-get' installed.
# But we need 'unzip'. If 'unzip' is not there, we have a problem.
# Let's check if we can copy unzip from a builder stage or use python to unzip if available.
# Or better: Unzip on host machine (Windows/Server) and COPY the folder! This removes ALL build dependencies.

ENV CANTALOUPE_VERSION=5.0.6
WORKDIR /opt

# Optimize: Copy the UNZIPPED folder directly to avoid needing 'unzip' inside the image
# User must unzip cantaloupe-5.0.6.zip locally to cantaloupe-5.0.6 folder before building
COPY cantaloupe-${CANTALOUPE_VERSION} cantaloupe

WORKDIR /opt/cantaloupe

# Create defaultWORKDIR /opt/cantaloupe

# Create default directories (Using array syntax for CMD to avoid shell dependency, but RUN needs shell)
# Since ubuntu/jre is so minimal it might lack 'mkdir' in PATH or shell
# We can try to use java to create dirs? No, that's runtime.
# Let's assume /bin/mkdir exists.
# If shell is missing, we can try COPY-ing empty dirs from host.

# Create dirs on host (via empty placeholder) and COPY them
# Or just use Python/Java one-liner if available? No.
# Let's try to just COPY the properties file which is essential.
# The image/cache dirs can be mounted as volumes at runtime, so we don't STRICTLY need to mkdir them in build
# providing the user mounts volumes (which docker-compose does).
# So we can COMMENT OUT the mkdir commands.

# RUN mkdir -p /var/lib/cantaloupe/images \
#    && mkdir -p /var/lib/cantaloupe/cache

# Copy config
COPY cantaloupe.properties /etc/cantaloupe.properties

# Expose port
EXPOSE 8182

# Start Cantaloupe
CMD ["java", "-Dcantaloupe.config=/etc/cantaloupe.properties", "-jar", "cantaloupe-5.0.6.jar"]
