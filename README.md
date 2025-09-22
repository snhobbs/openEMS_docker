# Docker Image for openEMS

## Building 
```sh 
docker build --build-arg UID=$(id -u) --build-arg GID=$(id -g) --build-arg USER=$(whoami) -t openems-ubuntu-24 -f Dockerfile .
```

## Running 
```sh
docker run -it --rm  -e DISPLAY=:0 \
  --device /dev/dri --group-add video \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  -v $(pwd):$(pwd) \
  --workdir "$(pwd)" \
  --name [CONTAINER TAG] [IMAGE TAG] [COMMAND]
```

## Building AppCSXCAD AppImage
```bash
cd builder
docker build --rm -f Dockerfile-AppCSXCAD-AppImage -t appcsxcad-appimage --output type=local,dest=./ .
```
This creates a stand-alone AppImage in ./output/AppCSXCAD-x86_64.AppImage
