FROM debian:12.11-slim@sha256:b1a741487078b369e78119849663d7f1a5341ef2768798f7b7406c4240f86aef

ARG DEBIAN_SNAPSHOT=20250811T000000Z
ARG XRDP_PACKAGE_VERSION=0.9.21.1-1
ARG XORGXRDP_PACKAGE_VERSION=0.9.19-1

LABEL org.opencontainers.image.title="aardwolf xrdp interoperability lab" \
      org.opencontainers.image.description="Disposable, test-only xrdp target" \
      org.opencontainers.image.version="${XRDP_PACKAGE_VERSION}"

RUN printf '%s\n' \
      "deb [check-valid-until=no] http://snapshot.debian.org/archive/debian/${DEBIAN_SNAPSHOT} bookworm main" \
      "deb [check-valid-until=no] http://snapshot.debian.org/archive/debian-security/${DEBIAN_SNAPSHOT} bookworm-security main" \
      "deb [check-valid-until=no] http://snapshot.debian.org/archive/debian/${DEBIAN_SNAPSHOT} bookworm-updates main" \
      > /etc/apt/sources.list \
    && rm -f /etc/apt/sources.list.d/debian.sources \
    && apt-get -o Acquire::Check-Valid-Until=false update \
    && DEBIAN_FRONTEND=noninteractive apt-get install --yes --no-install-recommends \
      "xrdp=${XRDP_PACKAGE_VERSION}" \
      "xorgxrdp=${XORGXRDP_PACKAGE_VERSION}" \
      xserver-xorg-core \
      xserver-xorg-input-libinput \
      openbox \
      dbus-x11 \
      xauth \
      procps \
      netcat-openbsd \
      adduser \
      passwd \
    && rm -rf /var/lib/apt/lists/*

COPY xrdp.ini /etc/xrdp/xrdp.ini
COPY sesman.ini /etc/xrdp/sesman.ini
COPY startwm.sh /etc/xrdp/startwm.sh
COPY entrypoint.sh /usr/local/bin/aardwolf-xrdp-entrypoint

RUN chmod 0755 /usr/local/bin/aardwolf-xrdp-entrypoint /etc/xrdp/startwm.sh \
    && printf '%s\n' 'allowed_users=anybody' > /etc/X11/Xwrapper.config \
    && mkdir -p /var/run/xrdp /run/dbus

EXPOSE 3389

HEALTHCHECK --interval=2s --timeout=2s --start-period=15s --retries=30 \
    CMD ["nc", "-z", "127.0.0.1", "3389"]

ENTRYPOINT ["/usr/local/bin/aardwolf-xrdp-entrypoint"]
