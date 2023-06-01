ARG BASE_IMAGE=senzing/senzingapi-runtime:3.5.2
FROM ${BASE_IMAGE}

ENV REFRESHED_AT=2023-05-10

LABEL Name="senzing/SzFileLoader" \
      Maintainer="support@senzing.com" \
      Version="0.0.2"

# Run as "root" for system installation.

USER root

# Install packages via apt.

RUN apt update \
      && apt -y install \
      curl \
      python3 \
      python3-pip \
      && apt clean \
      && rm -rf /var/lib/apt/lists/*

# Install packages via pip.

COPY requirements.txt .
RUN pip3 install --upgrade pip \
      && pip3 install -r requirements.txt \
      && rm requirements.txt

# Install senzing_governor.py.

RUN curl -X GET \
      --output /opt/senzing/g2/sdk/python/senzing_governor.py \
      https://raw.githubusercontent.com/Senzing/governor-postgresql-transaction-id/main/senzing_governor.py

# Copy files from repository.

COPY ./file-loader.py /

# Copy files from repository.

COPY ./rootfs /

# Create path to mount to for input data and output data to persist

RUN mkdir /input /output

# Make non-root container.

USER 1001

# Runtime environment variables.

ENV LD_LIBRARY_PATH=/opt/senzing/g2/lib:/opt/senzing/g2/lib/debian
ENV PATH=${PATH}:/opt/senzing/g2/python
ENV PYTHONPATH=/opt/senzing/g2/sdk/python
ENV PYTHONUNBUFFERED=1
ENV SENZING_DOCKER_LAUNCHED=true

WORKDIR /
ENTRYPOINT ["/file-loader.py"]
