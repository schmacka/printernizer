# Printernizer Slicer Service — OrcaSlicer (glibc >= 2.38 required, so Ubuntu 24.04)
FROM ubuntu:24.04

ARG TARGETARCH
ARG ORCA_VERSION=2.4.0
ENV DEBIAN_FRONTEND=noninteractive ORCA_VERSION=${ORCA_VERSION}

RUN apt-get update && apt-get install -y --no-install-recommends \
      python3 python3-pip curl ca-certificates squashfs-tools \
      xvfb libopengl0 libglu1-mesa libgl1-mesa-dri libgl1 libegl1 \
      libgtk-3-0t64 libwebkit2gtk-4.1-0 libgstreamer1.0-0 \
      libgstreamer-plugins-base1.0-0 libfontconfig1 libsm6 libdbus-1-3 \
      libnss3 libxss1 libosmesa6 \
    && rm -rf /var/lib/apt/lists/*

# Download + FUSE-free extraction of the arch-specific AppImage.
# The AppImage wrapper won't exec (its EI_ABIVERSION byte is overwritten by the
# AppImage magic) and there is no FUSE in-container, so we locate the appended
# squashfs (magic "hsqs") and unsquashfs it, then run the inner AppRun.
RUN set -eux; \
    case "${TARGETARCH}" in \
      amd64) A="OrcaSlicer_Linux_AppImage_Ubuntu2404_V${ORCA_VERSION}.AppImage" ;; \
      arm64) A="OrcaSlicer_Linux_AppImage_Ubuntu2404_aarch64_V${ORCA_VERSION}.AppImage" ;; \
      *) echo "unsupported arch ${TARGETARCH}"; exit 1 ;; \
    esac; \
    curl -fSL -o /tmp/orca.AppImage \
      "https://github.com/SoftFever/OrcaSlicer/releases/download/v${ORCA_VERSION}/${A}"; \
    mkdir -p /opt/orca; \
    EXTRACTED=""; \
    for OFF in $(grep -abo hsqs /tmp/orca.AppImage | cut -d: -f1); do \
      if unsquashfs -s -o "${OFF}" /tmp/orca.AppImage >/dev/null 2>&1; then \
        unsquashfs -o "${OFF}" -d /opt/orca/squashfs-root /tmp/orca.AppImage; \
        EXTRACTED=1; break; \
      fi; \
    done; \
    [ -n "${EXTRACTED}" ] || { echo "no valid squashfs superblock found in AppImage"; exit 1; }; \
    test -x /opt/orca/squashfs-root/AppRun; \
    rm /tmp/orca.AppImage

ENV EMBEDDED_SLICER_PATH=/opt/orca/squashfs-root/AppRun \
    ORCA_PROFILES_ROOT=/opt/orca/squashfs-root/resources/profiles \
    PYTHONPATH=/app

WORKDIR /app
COPY requirements.txt .
RUN pip3 install --break-system-packages --no-cache-dir -r requirements.txt
COPY app/ ./app/
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8001
ENTRYPOINT ["/entrypoint.sh"]
