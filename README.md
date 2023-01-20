![Supported Python versions](https://img.shields.io/badge/python-3.7+-blue.svg) [![Twitter](https://img.shields.io/twitter/follow/skelsec?label=skelsec&style=social)](https://twitter.com/intent/follow?screen_name=skelsec)

:triangular_flag_on_post: This is the public repository of aardwolf, for latest version and updates please consider supporting us through https://porchetta.industries/

# AARDWOLF - Asynchronous RDP/VNC client in Python (headless)
This project is aimed to play around the RDP and VNC protocols.  
Project contains no GUI, for a GUI client please check out [`aardwolfgui`](https://github.com/skelsec/aardwolfgui)

## :triangular_flag_on_post: Sponsors

If you want to sponsors this project and have the latest updates on this project, latest issues fixed, latest features, please support us on https://porchetta.industries/

## Official Discord Channel

Come hang out on Discord!

[![Porchetta Industries](https://discordapp.com/api/guilds/736724457258745996/widget.png?style=banner3)](https://discord.gg/ycGXUxy)

# Important
This is a headless client, for GUI functionality use the `aardwolfgui` package.

# Features
 - Supports credssp auth via NTLM/Kerberos.
 - Built-in proxy client allows SOCKS/HTTP proxy tunneling without 3rd part software  
 - PtH via CredSSP+Restricted admin mode
 - Scriptable Keyboard, Mouse input and Clipboard input/output
 - Can run in headless mode, no GUI required (read: no need for Qt)
 - Support for Duckyscript files to emulate keystrokes 

# Example scripts
 - `ardpscan` Multi-purpose scanner for RDP and VNC protocols. (screenshot/capabilities/login scanner)

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
 - Sylvain Peyrefitte ([@citronneur](https://twitter.com/citronneur)) [`rdpy`](https://github.com/citronneur/rdpy). The decompression code and the QT image magic was really valuable.
 - Marc-André Moreau ([@awakecoding](https://twitter.com/awakecoding)) for providing suggestions on fixes



