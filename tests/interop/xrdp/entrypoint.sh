#!/bin/sh
set -eu

username="${AARDWOLF_XRDP_USERNAME:-aardwolftest}"
password="${AARDWOLF_XRDP_PASSWORD:-Aardwolf-Test-Only-1!}"

case "$username" in
    *[!A-Za-z0-9_.-]* | "") echo "invalid test username" >&2; exit 2 ;;
esac
if [ -z "$password" ]; then
    echo "test password must not be empty" >&2
    exit 2
fi

if ! id "$username" >/dev/null 2>&1; then
    adduser \
        --disabled-password \
        --gecos "" \
        --shell /bin/bash \
        "$username" >/dev/null
fi

printf '%s:%s\n' "$username" "$password" | chpasswd

install -d -m 0755 -o "$username" -g "$username" "/home/${username}"
printf '%s\n' '#!/bin/sh' 'exec /usr/bin/openbox-session' \
    > "/home/${username}/.xsession"
chmod 0755 "/home/${username}/.xsession"
chown "$username:$username" "/home/${username}/.xsession"

mkdir -p /run/dbus /var/run/xrdp /var/log
if [ ! -S /run/dbus/system_bus_socket ]; then
    dbus-daemon --system --fork
fi

rm -f /var/run/xrdp/xrdp.pid /var/run/xrdp/xrdp-sesman.pid
xrdp-sesman
exec xrdp --nodaemon
