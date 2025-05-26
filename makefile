# Define the image name and container name
IMAGE_NAME = openems
CONTAINER_NAME = openems-container
LOCAL_DIR=$(shell pwd)# Current directory (where the Makefile is located)
CONTAINER_WORKDIR = /app
COMMAND=python3 /app/examples/python/Simple_Patch_Antenna/Simple_Patch_Antenna.py
# Default target: Build and run the Docker container
#all: build run

# Build the Docker image
build:
	docker build -t $(IMAGE_NAME) .

# Run the Docker container with volume mounts for local development

#-e DISPLAY=host.docker.internal:0 \

run:
	docker run \
		-v $(LOCAL_DIR):/home/appuser \
		-it --rm \
		--name $(CONTAINER_NAME) \
		$(IMAGE_NAME) \
	  ${COMMAND}	

run_visual:
	docker run \
		-v $(LOCAL_DIR):/home/appuser \
		-v /tmp/.X11-unix:/tmp/.X11-unix \
		-it --rm \
		-e DISPLAY=${DISPLAY} \
		--name $(CONTAINER_NAME) \
		$(IMAGE_NAME) \
	  ${COMMAND}	


# Start the Docker container (if it's stopped)
start:
	@echo "Starting Docker container..."
	docker start $(CONTAINER_NAME)

# Stop the Docker container
stop:
	@echo "Stopping Docker container..."
	docker stop $(CONTAINER_NAME)

# Remove the Docker container
rm:
	@echo "Removing Docker container..."
	docker rm $(CONTAINER_NAME)

# Remove the Docker image
rmi:
	@echo "Removing Docker image..."
	docker rmi $(IMAGE_NAME)

# Clean up: Stop and remove the container, then remove the image
clean: stop rm rmi
