# Scripts

Linux start/stop scripts for the Docker container.

- `start.sh` -- Builds and starts the container via `sudo docker compose up --build -d`
- `stop.sh` -- Stops the container via `sudo docker compose down`

Both scripts `cd` to the project root before running.
