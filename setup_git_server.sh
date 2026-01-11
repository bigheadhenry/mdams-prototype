#!/bin/bash

# Configuration
REPO_DIR="/home/bigheadhenry/repos/meam.git"
WORK_DIR="/home/bigheadhenry/meam-prototype"

echo ">>> Setting up Git Push-to-Deploy on Server..."

# 1. Create Bare Repository
if [ ! -d "$REPO_DIR" ]; then
    echo "Creating bare repository at $REPO_DIR..."
    mkdir -p "$REPO_DIR"
    cd "$REPO_DIR"
    git init --bare
else
    echo "Repository already exists at $REPO_DIR"
fi

# 2. Create Post-Receive Hook
HOOK_FILE="$REPO_DIR/hooks/post-receive"
echo "Creating post-receive hook at $HOOK_FILE..."

cat > "$HOOK_FILE" << 'EOF'
#!/bin/bash

WORK_DIR="/home/bigheadhenry/meam-prototype"
LOG_FILE="/home/bigheadhenry/deploy.log"

echo "==============================================="
echo "   MEAM Prototype Deployment Triggered"
echo "   Date: $(date)"
echo "==============================================="

# Redirect output to log file and stdout
exec > >(tee -a "$LOG_FILE") 2>&1

# 1. Check out code
echo ">>> Checking out code to $WORK_DIR..."
mkdir -p "$WORK_DIR"
git --work-tree="$WORK_DIR" --git-dir="$GIT_DIR" checkout -f master

# 2. Fix permissions if needed
chmod +x "$WORK_DIR/deploy.sh"

# 3. Rebuild and Restart Services
echo ">>> Rebuilding Docker containers..."
cd "$WORK_DIR"

# Ensure Environment Variables are set (if needed for deployment)
export API_PUBLIC_URL="http://192.168.5.13:3000/api"
export CANTALOUPE_PUBLIC_URL="http://192.168.5.13:8182/iiif/2"

# Run Docker Compose
docker compose up -d --build

# 4. Cleanup
echo ">>> Pruning old images..."
docker image prune -f

echo "==============================================="
echo "   DEPLOYMENT SUCCESSFUL!"
echo "==============================================="
EOF

# 3. Make hook executable
chmod +x "$HOOK_FILE"

echo ">>> Server setup complete!"
echo "    Remote URL: ssh://bigheadhenry@192.168.5.13$REPO_DIR"
