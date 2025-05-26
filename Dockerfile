# Base image
FROM openems_base
ENV DEBIAN_FRONTEND=noninteractive

## Clone Each Independant Section and Build

## AppCSXCAD is standalone so build this separately
WORKDIR /root/
RUN git clone --recursive --branch v0.0.36.alpha2 https://github.com/snhobbs/OpenEMS-Project.git


WORKDIR /root/OpenEMS-Project/fparser
RUN cmake ./
RUN make -j4 && make install
RUN cp *.so* /lib

WORKDIR /root/OpenEMS-Project/CSXCAD
RUN cmake ./
RUN make -j4 && make install
RUN cp src/*.so* /lib

WORKDIR /root/OpenEMS-Project/QCSXCAD
RUN cmake ./
RUN make -j4 && make install
RUN cp *.so* /lib

WORKDIR /root/OpenEMS-Project/AppCSXCAD
RUN cmake ./
RUN make -j4
RUN cp AppCSXCAD /bin && cp AppCSXCAD.sh /bin

WORKDIR /root/OpenEMS-Project/CSXCAD/python
RUN pip install .

WORKDIR /root/OpenEMS-Project/openEMS
RUN cmake ./ -D WITH_MPI=FALSE
RUN make -j4 && make install
RUN cp *.so* /lib && cp openEMS /bin && cp openEMS.sh /bin

WORKDIR /root/OpenEMS-Project/openEMS/nf2ff
RUN cp *.so* /lib
RUN cp nf2ff /bin

WORKDIR /root/OpenEMS-Project/openEMS/python
RUN python3 setup.py build_ext
RUN pip install pkgconfig h5py==3.13.0 numpy==1.26.2
RUN python3 setup.py install

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
