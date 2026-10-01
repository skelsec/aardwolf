#!/bin/sh
set -eu

username="${AARDWOLF_VNC_USERNAME:-aardwolftest}"
password="${AARDWOLF_VNC_PASSWORD:-Aardwolf-Test-Only-1!}"

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

install -d -m 0700 -o "$username" -g "$username" "/home/${username}/.vnc"
printf '%s\n' "$password" | vncpasswd -f > "/home/${username}/.vnc/passwd"
chmod 0600 "/home/${username}/.vnc/passwd"
chown "$username:$username" "/home/${username}/.vnc/passwd"

runuser -u "$username" -- env HOME="/home/${username}" \
    Xvnc :1 \
    -geometry 1024x768 \
    -depth 24 \
    -rfbport 5900 \
    -rfbauth "/home/${username}/.vnc/passwd" \
    -localhost no \
    -SecurityTypes VncAuth \
    -AlwaysShared \
    -desktop aardwolf-vnc &
vnc_pid=$!

sleep 1
runuser -u "$username" -- env DISPLAY=:1 HOME="/home/${username}" \
    openbox-session &

wait "$vnc_pid"
