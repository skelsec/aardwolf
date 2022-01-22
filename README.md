# AARDWOLF - Asynchronous RDP client in Python (and a bit of Qt5)
This project is aimed to play around the RDP protocol and not for business use.

# Features
 - Supports credssp auth via NTLM/Kerberos.
 - Built-in proxy client allows SOCKS/HTTP proxy tunneling without 3rd part software  
 - PtH via CredSSP+Restricted admin mode
 - Scriptable Keyboard, Mouse input and CLIPBOARD input/output
 - Can run in headless mode, no GUI required

# Example scripts
 - `aardpclient` Basic RDP client running on top of QT5. Can copy-paste text, handles keyboard and mouse.  
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

# Kudos
 - Citronneur's `rdpy`. The decompression code and the QT image magic was really valuable.

# Additional info for Qt install.
 - installing in venv will require installing Qt5 outside of venv, then installing 'wheel' and 'vext.pyqt5' in the venv via pip first. then install pyqt5 in the venv
 - installing Qt5 can be a nightmare
 - generally on ubuntu you can use `apt install python3-pyqt5` before installing `aardwolf` and it will (should) work