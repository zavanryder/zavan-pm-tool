#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/.."
sudo docker compose down
echo "App stopped."
