#!/bin/bash
set -euo pipefail

BRANCH="$(git branch --show-current)"

if [ -z "$BRANCH" ]; then
  echo "Unable to determine current branch"
  exit 1
fi

echo ">>> Current branch: $BRANCH"
echo ">>> Pushing to GitHub (origin)..."
git push origin "$BRANCH"

echo ">>> Pushing to local deploy bare repo (local-bare)..."
git push local-bare "$BRANCH:$BRANCH"

echo ">>> Done"
