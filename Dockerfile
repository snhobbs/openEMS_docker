# Base image
FROM ubuntu:22.04
ENV DEBIAN_FRONTEND=noninteractive 
# Install required packages
RUN apt-get update 
RUN apt-get install -y git
RUN apt-get install -y libx11-dev x11-apps
RUN apt-get install -y python3-tk
RUN apt-get install -qqy x11-apps
RUN apt-get install -qqy paraview

## Install dependancies for openEMS
RUN apt-get install -y build-essential cmake libhdf5-dev libvtk7-dev libboost-all-dev libcgal-dev libtinyxml-dev qtbase5-dev libvtk7-qt-dev
RUN apt-get install -y python3-dev libhdf5-dev
RUN apt-get install -y pkg-config
## Install octave
RUN apt-get install -y octave liboctave-dev
## Install additonal dependencies for hyp2mat
RUN apt-get install -y gengetopt help2man groff pod2pdf bison flex libhpdf-dev libtool vim

## Install python
RUN apt-get install -y python3.11
RUN apt-get install -y python3-pip
RUN pip install numpy matplotlib Cython pyproject-toml
RUN pip install --upgrade pip wheel
RUN pip install setuptools==58.2.0
RUN pip install pyems
RUN pip install h5py

# Set the working directory
WORKDIR /root

## Clone Each Independant Section and Build

## AppCSXCAD is standalone so build this seperately
RUN mkdir AppCSXCAD
WORKDIR /root/AppCSXCAD
RUN git clone --recursive https://github.com/thliebig/CSXCAD.git
RUN git clone --recursive https://github.com/thliebig/QCSXCAD.git
RUN git clone --recursive https://github.com/thliebig/fparser.git
RUN git clone --recursive https://github.com/thliebig/AppCSXCAD.git

WORKDIR /root/AppCSXCAD/fparser
RUN cmake ./
RUN make -j2

WORKDIR /root/AppCSXCAD/CSXCAD
RUN cmake ./ -D fparser_INCLUDE_DIR=../fparser -D fparser_LIBRARIES=../fparser/libfparser.so
RUN make -j2

WORKDIR /root/AppCSXCAD/QCSXCAD
RUN cmake ./ -D fparser_INCLUDE_DIR=../fparser -D fparser_LIBRARIES=../fparser/libfparser.so -D CSXCAD_INCLUDE_DIR=../CSXCAD/src/  -D CSXCAD_LIBRARIES=../CSXCAD/src/libCSXCAD.so 
RUN make -j2

WORKDIR /root/AppCSXCAD/AppCSXCAD
RUN cmake ./ -D fparser_INCLUDE_DIR=../fparser -D fparser_LIBRARIES=../fparser/libfparser.so -D QCSXCAD_INCLUDE_DIR=../QCSXCAD/ -D CSXCAD_INCLUDE_DIR=../CSXCAD/src/  -D CSXCAD_LIBRARIES=../CSXCAD/src/libCSXCAD.so -D QCSXCAD_LIBRARIES=../QCSXCAD/libQCSXCAD.so
RUN make -j2

RUN cp /root/AppCSXCAD/AppCSXCAD/AppCSXCAD /bin
RUN cp /root/AppCSXCAD/AppCSXCAD/AppCSXCAD.sh /bin

## Build openEMS
RUN mkdir openems
WORKDIR /root/openems
RUN git clone --recursive https://github.com/thliebig/CSXCAD.git
RUN git clone --recursive https://github.com/thliebig/QCSXCAD.git
RUN git clone --recursive https://github.com/thliebig/fparser.git
RUN git clone --recursive https://github.com/thliebig/openEMS.git

WORKDIR /root/openems/fparser
RUN cmake ./
RUN make -j2
RUN make install

WORKDIR /root/openems/CSXCAD
RUN cmake ./ -D fparser_INCLUDE_DIR=../fparser -D fparser_LIBRARIES=../fparser/libfparser.so
RUN make -j2
RUN make install
RUN cp src/*.so* /lib
WORKDIR /root/openems/CSXCAD/python
RUN pip install .

WORKDIR /root/openems/openEMS
RUN cmake ./ -D FPARSER_ROOT_DIR=/usr/local/ -D CSXCAD_INCLUDE_DIR=../CSXCAD/src/  -D CSXCAD_LIBRARIES=../CSXCAD/src/libCSXCAD.so -D WITH_MPI=FALSE
RUN make -j2
RUN make install
RUN cp *.so* /lib

WORKDIR /root/openems/openEMS/nf2ff
RUN cp *.so* /lib
RUN cp nf2ff /bin

WORKDIR /root/openems/openEMS/python
RUN python3 setup.py build_ext
RUN python3 setup.py install 

## Setup Octave
WORKDIR /root/openems/
RUN git clone --recursive https://github.com/thliebig/CTB.git

RUN echo "addpath(\"/root/openems/CTB/\");" >> /etc/octaverc
RUN echo "addpath(\"/root/openems/openEMS/matlab/\");" >> /etc/octaverc
RUN echo "addpath(\"/root/openems/CSXCAD/matlab/\");" >> /etc/octaverc
RUN echo "addpath(\"/root/openems/openEMS/matlab/private\");" >> /etc/octaverc

WORKDIR /root/openems/openEMS/matlab
RUN mkoctfile h5readatt_octave.cc -I/usr/include/hdf5 -I/usrlib/x86_64-linux-gnu/hdf5 -I/usr/include/hdf5/serial/ -lhdf5 -L/usr/lib/x86_64-linux-gnu/hdf5/openmpi

WORKDIR /app
# Default command
CMD ["bash"]
