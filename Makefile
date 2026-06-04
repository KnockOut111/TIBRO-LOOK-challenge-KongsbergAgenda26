# Custom defined commands to run the rover system more easily. 
# This file creates a more user-friendly way to run the system.
# It also makes it easier to run the system on different machines without having to remember all the different commands.

### MAIN COMMANDS ###
roverpi-startsys:
	docker compose -f docker-compose.yml build
	docker compose -f docker-compose.yml up -d
	docker compose -f docker-compose.yml logs -f


roverpi-build:
	docker compose -f docker-compose.yml build

roverpi-start:
	docker compose -f docker-compose.yml up -d

roverpi-logs:
	docker compose -f docker-compose.yml logs -f

roverpi-stopsys:
	docker compose -f docker-compose.yml down

# Rebuild the docker image for roverPi and run the container.
roverpi-restart:
	docker compose -f docker-compose.yml restart 

# Stops and removes conainers + volumes + orphans.
roverpi-stopclean: 
	docker compose -f docker-compose.yml down -v --remove-orphans

	

# More clean and easy way to run the system locally, without downloading new content/updates.
roverpi-localstart:
	docker compose up
	docker compose -f docker-compose.yml logs -f

roverpi-localstop:
	docker compose down



# Build the docker image. Also shows the logs of the container.
roverpi-buildandlog:
	docker compose -f docker-compose.yml build
	docker compose -f docker-compose.yml logs -f

#Restarting the system
roverpi-rebuild:
	docker compose down
	docker compose build --no-cache 
	docker compose run --rm 



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
	docker compose stop metal_sensor_thread
	docker compose rm -f metal_sensor_thread
	docker rmi metal_sensor_thread

#docker compose -f docker-compose.yml down -v --remove-orphans


metal-sensor-logs:
	docker compose -f docker-compose.yml logs -f metal_sensor_thread
