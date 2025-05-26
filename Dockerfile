# ---------- Stage 1: Build ----------
FROM openems_base AS builder
ENV DEBIAN_FRONTEND=noninteractive

ARG BRANCH=v0.0.36.alpha2

WORKDIR /root/
RUN git clone --recursive --branch ${BRANCH} https://github.com/snhobbs/OpenEMS-Project.git

# Build all components
WORKDIR /root/OpenEMS-Project/fparser
RUN cmake . && make -j$(nproc) && make install

WORKDIR /root/OpenEMS-Project/CSXCAD
RUN cmake . && make -j$(nproc) && make install

WORKDIR /root/OpenEMS-Project/QCSXCAD
RUN cmake . && make -j$(nproc) && make install

WORKDIR /root/OpenEMS-Project/AppCSXCAD
RUN cmake . && make -j$(nproc) && make install

WORKDIR /root/OpenEMS-Project/CSXCAD/python
RUN pip install .

WORKDIR /root/OpenEMS-Project/openEMS
RUN cmake . -D WITH_MPI=FALSE && make -j$(nproc) && make install

WORKDIR /root/OpenEMS-Project/openEMS/nf2ff
RUN install -m 755 nf2ff /usr/local/bin/

WORKDIR /root/OpenEMS-Project/openEMS/python
RUN pip install numpy==1.26.2 pkgconfig h5py==3.13.0 && python3 setup.py install

# ---------- Stage 2: Runtime ----------
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ARG UID=1000
ARG GID=1000
ARG USER=appuser
ARG GROUP=appuser

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libqt5widgets5 \
    libqt5gui5 \
    libqt5core5a \
    libhdf5-103-1 \
    libomp5 \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Copy binaries and libraries from builder
COPY --from=builder /usr/local /usr/local
COPY --from=builder /usr/lib/x86_64-linux-gnu /usr/lib/x86_64-linux-gnu
COPY --from=builder /usr/lib /usr/lib
COPY --from=builder /usr/share /usr/share

# Ensure Python packages work
COPY --from=builder /usr/lib/python3*/site-packages /usr/lib/python3*/site-packages

RUN apt-get install -y \
    python3-matplotlib \
    python3-numpy


# Setup user
RUN groupadd -g ${GID} ${GROUP} \
    && useradd -m -u ${UID} -g ${GROUP} -s /bin/bash ${USER}
USER ${UID}:${GID}
WORKDIR /home/${USER}

CMD ["AppCSXCAD"]
