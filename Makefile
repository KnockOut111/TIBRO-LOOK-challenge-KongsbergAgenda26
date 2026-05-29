# Custom defined commands to run the rover system more easily. 
# This file creates a more user-friendly way to run the system.
# It also makes it easier to run the system on different machines without having to remember all the different commands.

# Build the docker image for roverPi and run the container. Also shows the logs of the container.
build-roverpi:
	docker compose -f docker-compose.yml build
	docker compose -f docker-compose.yml run --rm nav_thread 
	docker compose -f docker-compose.yml logs -f

# Rebuild the docker image for roverPi and run the container.
restart-roverpi:
	docker compose -f docker-compose.yml restart nav_thread

# Stops and removes conainers + orphans.
stop-roverpi: 
	docker compose -f docker-compose.yml down --remove-orphans

# Stops and removes conainers, volumes and orphans.
clean-roverpi:
	docker compose -f docker-compose.yml down -v --remove-orphans



# Completely resets the system by stopping and removing all containers, volumes and orphans. 
nuclear-reset:
	docker compose -f docker-compose.yml down -v --remove-orphans

# Builds the docker image for roverPi without using cache and run the container. Also shows the logs of the container.
build-from-scratch:
	docker compose -f docker-compose.yml build --no-cache
	docker compose -f docker-compose.yml up -d
	docker compose -f docker-compose.yml logs -f