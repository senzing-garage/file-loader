ARG BASE_IMAGE=senzing/senzingapi-runtime:3.13.0@sha256:edca155d3601238fab622a7dd86471046832328d21f71f7bb2ae5463157f6e10

ARG IMAGE_NAME="senzing/file-loader"
ARG IMAGE_MAINTAINER="support@senzing.com"
ARG IMAGE_VERSION="1.3.7"

# -----------------------------------------------------------------------------
# Stage: builder
# -----------------------------------------------------------------------------

FROM ${BASE_IMAGE} AS builder

# Set Shell to use for RUN commands in builder step.

ENV REFRESHED_AT=2026-01-15

# Run as "root" for system installation.

USER root

# Install packages via apt.

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
 && apt-get -y --no-install-recommends install \
      python3 \
      python3-dev \
      python3-pip \
      python3-venv \
 && rm -rf /var/lib/apt/lists/*

# Activate virtual environment.

RUN python3 -m venv /app/venv
ENV PATH="/app/venv/bin:$PATH"

COPY . /git-repository
WORKDIR /git-repository

# Install packages via PIP.

RUN python3 -m pip install --upgrade pip \
 && python3 -m pip install .

# -----------------------------------------------------------------------------
# Stage: Final
# -----------------------------------------------------------------------------

# Create the runtime image.

FROM ${BASE_IMAGE} AS runner

ARG IMAGE_NAME
ARG IMAGE_MAINTAINER
ARG IMAGE_VERSION

ENV REFRESHED_AT=2026-01-15

LABEL Name=${IMAGE_NAME} \
      Maintainer=${IMAGE_MAINTAINER} \
      Version=${IMAGE_VERSION}

# Run as "root" for system installation.

USER root

# Install packages via apt.

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
 && apt-get -y --no-install-recommends install \
      curl \
      postgresql-common \
      python3 \
      python3-pip \
 && /usr/share/postgresql-common/pgdg/apt.postgresql.org.sh -y \
 && apt-get -y install postgresql-client-14 \
 && rm -rf /var/lib/apt/lists/*

# Copy python virtual environment from the builder image.

COPY --from=builder /app/venv /app/venv

# Activate virtual environment.

ENV VIRTUAL_ENV=/app/venv
ENV PATH="/app/venv/bin:${PATH}"

# Install senzing_governor.py.

RUN curl -X GET \
      --output /opt/senzing/g2/sdk/python/senzing_governor.py \
      https://raw.githubusercontent.com/Senzing/governor-postgresql-transaction-id/main/src/senzing_governor.py

# Copy files from repository.

COPY ./file-loader.py /

# Copy files from repository.

COPY ./rootfs /

# Create path to mount to for input and output data

RUN mkdir /data

HEALTHCHECK CMD ["/app/healthcheck.sh"]

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
