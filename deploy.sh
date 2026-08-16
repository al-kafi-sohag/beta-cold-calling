#!/usr/bin/env bash
set -euo pipefail

cd /opt/beta-cold-calling

# Make sure persistent paths exist BEFORE compose runs,
# otherwise Docker may create them as root-owned dirs on first boot
# and a missing leads.csv would get created as a directory instead of a file.
mkdir -p transcripts tmp_audio
touch leads.csv

echo "==> Pulling latest code..."
git pull origin main

echo "==> Rebuilding image and restarting container..."
docker compose up -d --build

echo "==> Pruning old dangling images..."
docker image prune -f

echo "==> Done. Tailing logs (Ctrl+C to stop tailing, container keeps running)..."
docker compose logs -f cold-call-app