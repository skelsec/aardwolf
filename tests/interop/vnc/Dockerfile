FROM debian:12.11-slim@sha256:b1a741487078b369e78119849663d7f1a5341ef2768798f7b7406c4240f86aef

ARG DEBIAN_SNAPSHOT=20250811T000000Z
ARG TIGERVNC_PACKAGE_VERSION=1.12.0+dfsg-8

LABEL org.opencontainers.image.title="aardwolf TigerVNC interoperability lab" \
      org.opencontainers.image.description="Disposable, test-only TigerVNC target" \
      org.opencontainers.image.version="${TIGERVNC_PACKAGE_VERSION}"

RUN printf '%s\n' \
      "deb [check-valid-until=no] http://snapshot.debian.org/archive/debian/${DEBIAN_SNAPSHOT} bookworm main" \
      "deb [check-valid-until=no] http://snapshot.debian.org/archive/debian-security/${DEBIAN_SNAPSHOT} bookworm-security main" \
      "deb [check-valid-until=no] http://snapshot.debian.org/archive/debian/${DEBIAN_SNAPSHOT} bookworm-updates main" \
      > /etc/apt/sources.list \
    && rm -f /etc/apt/sources.list.d/debian.sources \
    && apt-get -o Acquire::Check-Valid-Until=false update \
    && DEBIAN_FRONTEND=noninteractive apt-get install --yes --no-install-recommends \
      "tigervnc-standalone-server=${TIGERVNC_PACKAGE_VERSION}" \
      "tigervnc-common=${TIGERVNC_PACKAGE_VERSION}" \
      openbox \
      xauth \
      procps \
      netcat-openbsd \
      adduser \
      passwd \
    && rm -rf /var/lib/apt/lists/*

COPY entrypoint.sh /usr/local/bin/aardwolf-vnc-entrypoint
RUN chmod 0755 /usr/local/bin/aardwolf-vnc-entrypoint

EXPOSE 5900

HEALTHCHECK --interval=2s --timeout=2s --start-period=10s --retries=30 \
    CMD ["nc", "-z", "127.0.0.1", "5900"]

ENTRYPOINT ["/usr/local/bin/aardwolf-vnc-entrypoint"]
