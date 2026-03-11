#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/.."
echo "Building and starting container..."
sudo docker compose up --build -d 2>&1 | tail -5
echo "Waiting for app to be ready..."
for i in $(seq 1 30); do
  if curl -sf http://localhost:8000/ > /dev/null 2>&1; then
    echo "App running at http://localhost:8000"
    exit 0
  fi
  sleep 1
done
echo "Warning: app did not respond within 30s. Check logs with: sudo docker compose logs"
exit 1
