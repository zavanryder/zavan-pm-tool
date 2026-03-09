#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/.."
sudo docker compose up --build -d
echo "App running at http://localhost:8000"
