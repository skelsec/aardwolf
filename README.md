![Supported Python versions](https://img.shields.io/badge/python-3.7+-blue.svg) [![Twitter](https://img.shields.io/twitter/follow/skelsec?label=skelsec&style=social)](https://twitter.com/intent/follow?screen_name=skelsec)

:triangular_flag_on_post: This is the public repository of aardwolf, for latest version and updates please consider supporting us through https://porchetta.industries/

# AARDWOLF - Asynchronous RDP client in Python
This project is aimed to play around the RDP protocol.

## :triangular_flag_on_post: Sponsors

If you want to sponsors this project and have the latest updates on this project, latest issues fixed, latest features, please support us on https://porchetta.industries/

## Official Discord Channel

Come hang out on Discord!

[![Porchetta Industries](https://discordapp.com/api/guilds/736724457258745996/widget.png?style=banner3)](https://discord.gg/ycGXUxy)

# Features
 - Supports credssp auth via NTLM/Kerberos.
 - Built-in proxy client allows SOCKS/HTTP proxy tunneling without 3rd part software  
 - PtH via CredSSP+Restricted admin mode
 - Scriptable Keyboard, Mouse input and Clipboard input/output
 - Can run in headless mode, no GUI required (read: no need for Qt)
 - Support for Duckyscript files to emulate keystrokes 

# Example scripts
 - `aardpclient` Basic RDP client running on top of Qt5. Can copy-paste text, handles keyboard and mouse.  
 - `aardpscreenshot` RDP ?screenshotter? scans the given target/s or network ranges for open RDP clients, tries to log in either with or without credentials and takes a screemshot  
 - `aardpcapscan` RDP login capability scanner identifies the supported login protocols on a target or network ranges.  

# URL format
As usual the scripts take the target/scredentials in URL format. Below some examples
 - `rdp+kerberos-password://TEST\Administrator:Passw0rd!1@win2016ad.test.corp/?dc=10.10.10.2&proxytype=socks5&proxyhost=127.0.0.1&proxyport=1080`  
 CredSSP (aka `HYBRID`) auth using Kerberos auth + password via `socks5` to `win2016ad.test.corp`, the domain controller (kerberos service) is at `10.10.10.2`. The socks proxy is on `127.0.0.1:1080`
 - `rdp+ntlm-password://TEST\Administrator:Passw0rd!1@10.10.10.103`  
 CredSSP (aka `HYBRID`) auth using NTLM auth + password connecting to RDP server `10.10.10.103`
 - `rdp+ntlm-password://TEST\Administrator:<NThash>@10.10.10.103`  
 CredSSP (aka `HYBRID`) auth using Pass-the-Hash (NTLM) auth connecting to RDP server `10.10.10.103`
 - `rdp+plain://Administrator:Passw0rd!1@10.10.10.103`  
 Plain authentication (No SSL, encryption is RC4) using password connecting to RDP server `10.10.10.103`
 - `vnc+plain://Passw0rd!1@10.10.10.103`  
 VNC client with VNC authentication using password connecting to RDP server `10.10.10.103`
 - `vnc+plain://Passw0rd!1@10.10.10.103`  
 VNC client with VNC authentication using password connecting to RDP server `10.10.10.103`
 - `vnc+plain://:admin:aaa@10.10.10.103`  
 VNC client with VNC authentication using password `admin:aa` connecting to RDP server `10.10.10.103`. Note that if the password contains `:` char you will have to prepend the password with `:`

# Kudos
 - Citronneur's `rdpy`. The decompression code and the QT image magic was really valuable.
 - Marc-André Moreau (@awakecoding) for providing suggestions on fixes


# Additional info for Qt install.
 - installing in venv will require installing Qt5 outside of venv, then installing 'wheel' and 'vext.pyqt5' in the venv via pip first. then install pyqt5 in the venv
 - installing Qt5 can be a nightmare
 - generally on ubuntu you can use `apt install python3-pyqt5` before installing `aardwolf` and it will (should) work
