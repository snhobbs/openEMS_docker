# Base image
FROM openems_base
ENV DEBIAN_FRONTEND=noninteractive 

## Clone Each Independant Section and Build

## AppCSXCAD is standalone so build this separately
RUN mkdir /root/AppCSXCAD
WORKDIR /root/AppCSXCAD
RUN git clone --recursive https://github.com/thliebig/CSXCAD.git
RUN git clone --recursive https://github.com/thliebig/QCSXCAD.git
RUN git clone --recursive https://github.com/thliebig/fparser.git
RUN git clone --recursive https://github.com/thliebig/AppCSXCAD.git

WORKDIR /root/AppCSXCAD/fparser
RUN cmake ./
RUN make -j4

WORKDIR /root/AppCSXCAD/CSXCAD
RUN cmake ./ -D fparser_INCLUDE_DIR=../fparser -D fparser_LIBRARIES=../fparser/libfparser.so
RUN make -j4

WORKDIR /root/AppCSXCAD/QCSXCAD
RUN cmake ./ -D fparser_INCLUDE_DIR=../fparser -D fparser_LIBRARIES=../fparser/libfparser.so -D CSXCAD_INCLUDE_DIR=../CSXCAD/src/  -D CSXCAD_LIBRARIES=../CSXCAD/src/libCSXCAD.so 
RUN make -j4

WORKDIR /root/AppCSXCAD/AppCSXCAD
RUN cmake ./ -D fparser_INCLUDE_DIR=../fparser -D fparser_LIBRARIES=../fparser/libfparser.so -D QCSXCAD_INCLUDE_DIR=../QCSXCAD/ -D CSXCAD_INCLUDE_DIR=../CSXCAD/src/  -D CSXCAD_LIBRARIES=../CSXCAD/src/libCSXCAD.so -D QCSXCAD_LIBRARIES=../QCSXCAD/libQCSXCAD.so
RUN make -j4

RUN cp /root/AppCSXCAD/AppCSXCAD/AppCSXCAD /bin
RUN cp /root/AppCSXCAD/AppCSXCAD/AppCSXCAD.sh /bin

## Build openEMS
RUN mkdir /root/openems
WORKDIR /root/openems
RUN git clone --recursive https://github.com/thliebig/CSXCAD.git
RUN git clone --recursive https://github.com/thliebig/QCSXCAD.git
RUN git clone --recursive https://github.com/thliebig/fparser.git
RUN git clone --recursive https://github.com/thliebig/openEMS.git

WORKDIR /root/openems/fparser
RUN cmake ./
RUN make -j4
RUN make install
RUN cp *.so* /lib

WORKDIR /root/openems/CSXCAD
RUN cmake ./ -D fparser_INCLUDE_DIR=../fparser -D fparser_LIBRARIES=../fparser/libfparser.so
RUN make -j4
RUN make install
RUN cp src/*.so* /lib
WORKDIR /root/openems/CSXCAD/python
RUN pip install .

WORKDIR /root/openems/openEMS
RUN cmake ./ -D FPARSER_ROOT_DIR=/usr/local/ -D CSXCAD_INCLUDE_DIR=../CSXCAD/src/  -D CSXCAD_LIBRARIES=../CSXCAD/src/libCSXCAD.so -D WITH_MPI=FALSE
RUN make -j4
RUN make install
RUN cp *.so* /lib

WORKDIR /root/openems/openEMS/nf2ff
RUN cp *.so* /lib
RUN cp nf2ff /bin

WORKDIR /root/openems/openEMS/python
RUN python3 setup.py build_ext
RUN python3 setup.py install 

WORKDIR /root/openems/openEMS/matlab
RUN mkoctfile h5readatt_octave.cc -I/usr/include/hdf5 -I/usrlib/x86_64-linux-gnu/hdf5 -I/usr/include/hdf5/serial/ -lhdf5 -L/usr/lib/x86_64-linux-gnu/hdf5/openmpi

# Set user and group
ARG user=appuser
ARG group=appuser
ARG uid=1000
ARG gid=1000
RUN groupadd -g ${gid} ${group}
RUN useradd -u ${uid} -g ${group} -s /bin/bash -m ${user} # <--- the '-m' create a user home directory

# Switch to user
USER ${uid}:${gid}
WORKDIR /home/${user}

# Default command
CMD ["bash"]
