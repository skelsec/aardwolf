#!/bin/sh
set -eu

if test -r /etc/profile; then
    . /etc/profile
fi
if test -r "${HOME}/.profile"; then
    . "${HOME}/.profile"
fi

if test -x /usr/bin/openbox-session; then
    exec /usr/bin/openbox-session
fi
exec /usr/bin/xterm
