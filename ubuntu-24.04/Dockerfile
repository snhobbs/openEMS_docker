FROM ubuntu:24.04
ENV DEBIAN_FRONTEND=noninteractive

# Install all required packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    git wget build-essential cmake pkg-config \
    libx11-dev x11-apps paraview \
    libhdf5-dev \
    libboost-all-dev libcgal-dev libtinyxml-dev \
    qtbase5-dev \
    gengetopt help2man groff pod2pdf bison flex libhpdf-dev libtool
   
RUN apt-get install -y --no-install-recommends \
    libvtk9-dev libvtk9-qt-dev

# Clone OpenEMS project
WORKDIR /root/
ARG BRANCH=master
ARG REPO=https://github.com/thliebig/OpenEMS-Project.git

RUN git clone --recursive --branch ${BRANCH} ${REPO}

RUN apt-get install -y --no-install-recommends \
    python3.12 python3-pip python3-dev python3-venv cython3 python3-setuptools

# Upgrade pip and install Python tools
# RUN pip install --upgrade pip wheel setuptools==58.2.0 pyproject-toml

ENV INSTALL_DIR=/usr/local

RUN cd OpenEMS-Project && bash update_openEMS.sh ${INSTALL_DIR} --python 

ARG UID=1000
ARG GID=1000
ARG USER=appuser
ARG GROUP=appuser

RUN rm -rf /var/lib/apt/lists/*

# Setup user

RUN userdel -r ubuntu && \
    groupadd -g ${GID} ${GROUP} \
    && useradd -m -u ${UID} -g ${GROUP} -s /bin/bash ${USER} \
    && chown -R ${UID}:${GID} ${INSTALL_DIR}
USER ${UID}:${GID}
WORKDIR /home/${USER}

CMD ["bash"]
