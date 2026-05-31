# Custom defined commands to run the rover system more easily. 
# This file creates a more user-friendly way to run the system.
# It also makes it easier to run the system on different machines without having to remember all the different commands.

# Build the docker image for roverPi and run the container. Also shows the logs of the container.
roverpi-build:
	docker compose -f docker-compose.yml build
	docker compose -f docker-compose.yml run --rm nav_thread 
	docker compose -f docker-compose.yml logs -f

roverpi-rebuild:
	docker compose down
	docker compose build --no-cache nav_thread
	docker compose run --rm nav_thread

# Rebuild the docker image for roverPi and run the container.
roverpi-restart:
	docker compose -f docker-compose.yml restart nav_thread

# Stops and removes conainers + orphans.
roverpi-stop: 
	docker compose -f docker-compose.yml down --remove-orphans

# Stops and removes conainers, volumes and orphans.
roverpi-clean:
	docker compose -f docker-compose.yml down -v --remove-orphans



# Completely resets the system by stopping and removing all containers, volumes and orphans. 
nuclear-reset:
	docker compose -f docker-compose.yml down -v --remove-orphans

# Builds the docker image for roverPi without using cache and run the container. Also shows the logs of the container.
build-from-scratch:
	docker compose -f docker-compose.yml build --no-cache
	docker compose -f docker-compose.yml up -d
	docker compose -f docker-compose.yml logs -f


# Metal sensor docker targets
metal-sensor-build:
	docker compose -f docker-compose.yml up -d --build metal_sensor_thread
	docker compose -f docker-compose.yml logs -f metal_sensor_thread

metal-sensor-install-host:
	sudo apt update
	sudo apt install -y python3-gpiozero

metal-sensor-restart:
	docker compose -f docker-compose.yml restart metal_sensor_thread

metal-sensor-stop:
	docker compose -f docker-compose.yml stop metal_sensor_thread

metal-sensor-clean:
	docker compose -f docker-compose.yml down -v --remove-orphans

metal-sensor-logs:
	docker compose -f docker-compose.yml logs -f metal_sensor_thread