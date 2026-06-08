# Custom defined commands to run the rover system more easily. 
# This file creates a more user-friendly way to run the system.
# It also makes it easier to run the system on different machines without having to remember all the different commands.

### MAIN COMMANDS ###

roverpi-manual-mode-build:
	docker compose -f docker-compose.yml up --build nav_thread
	docker compose -f docker-compose.yml run --rm -it manual_command_thread
	
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

# IMU sensor docker targets
imu-sensor-build:
	docker compose -f docker-compose.yml up -d --build imu_sensor_thread
	docker compose -f docker-compose.yml logs -f imu_sensor_thread

imu-sensor-restart:
	docker compose -f docker-compose.yml restart imu_sensor_thread

imu-sensor-stop:
	docker compose -f docker-compose.yml stop imu_sensor_thread

imu-sensor-clean:
	docker compose stop imu_sensor_thread
	docker compose rm -f imu_sensor_thread
	docker rmi imu_sensor_thread

imu-sensor-logs:
	docker compose -f docker-compose.yml logs -f imu_sensor_thread

# Depth camera docker targets
depth-camera-build:
	docker compose -f docker-compose.yml up -d --build realsense_camera_thread depth_camera_thread
	docker compose -f docker-compose.yml logs -f realsense_camera_thread depth_camera_thread

depth-camera-restart:
	docker compose -f docker-compose.yml restart realsense_camera_thread depth_camera_thread

depth-camera-stop:
	docker compose -f docker-compose.yml stop realsense_camera_thread depth_camera_thread

depth-camera-clean:
	docker compose stop realsense_camera_thread depth_camera_thread
	docker compose rm -f realsense_camera_thread depth_camera_thread

depth-camera-logs:
	docker compose -f docker-compose.yml logs -f realsense_camera_thread depth_camera_thread

# PiCam ROS2 hardware targets
picam-build:
	docker compose -f docker-compose.yml up -d --build picam_thread
	docker compose -f docker-compose.yml logs -f picam_thread

picam-restart:
	docker compose -f docker-compose.yml restart picam_thread

picam-stop:
	docker compose -f docker-compose.yml stop picam_thread

picam-logs:
	docker compose -f docker-compose.yml logs -f picam_thread

# PiCam detect server (PC-side) targets
picam-detect-build:
	docker compose -f docker-compose-server.yml up -d --build picam_detect_server
	docker compose -f docker-compose-server.yml logs -f picam_detect_server

picam-detect-restart:
	docker compose -f docker-compose-server.yml restart picam_detect_server

picam-detect-stop:
	docker compose -f docker-compose-server.yml stop picam_detect_server

picam-detect-clean:
	docker compose -f docker-compose-server.yml stop picam_detect_server
	docker compose -f docker-compose-server.yml rm -f picam_detect_server

picam-detect-logs:
	docker compose -f docker-compose-server.yml logs -f picam_detect_server

