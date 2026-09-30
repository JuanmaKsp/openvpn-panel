# OpenVPN Manager

A web GUI for managing OpenVPN clients on **TurnKey Linux OpenVPN**. **Flask**-based interface served over HTTPS on port **12322**, with system-user authentication (PAM). Available in **English and Spanish** (language switcher built into the UI).

Create, revoke, renew and download `.ovpn` profiles, plus manage static IPs, per-client access ranges, blocking, maintenance mode, a connection geolocation map and a log viewer — all from the browser.

## Compatibility — pick the right `.deb`

There are two packages depending on your TurnKey's Debian version. The app itself is the same; what differs is how Python dependencies are resolved.

| File | Debian | Python dependencies |
|---|---|---|
| `openvpn-manager_<version>_debian10_all.deb` | 10 (Buster) | `gunicorn`, `python-pam` and `maxminddb` are installed via `pip3` at install time (not available in Buster's repos). |
| `openvpn-manager_<version>_debian11-12-13_all.deb` | 11 (Bullseye), 12 (Bookworm), 13 (Trixie) | Everything from APT (`gunicorn`, `python3-pam`, `python3-maxminddb`). |

Download the latest version from the **[Releases](../../releases)** tab.

## Features

- Create clients and generate/download `.ovpn` profiles
- Revoke certificates (CRL) and renew profiles
- Configurable validity in months on create/renew
- Per-client **static IP** assignment
- **Access ranges** per client (pushed routes via CCD), editable without reissuing the `.ovpn`
- Block / unblock clients
- Disconnect connected clients (OpenVPN management interface)
- **Maintenance mode** (temporary global lockout)
- **Geolocation map**: approximate location of each client's most recent connection (up to 5 distinct IPs of history), resolved locally against a GeoIP database (DB-IP City Lite) — no client IP is ever sent to a third party; only the admin's own browser loads map tiles from OpenStreetMap
- OpenVPN and audit log viewer
- Panel-user management (system accounts without shell)
- Bilingual English/Spanish UI

## Architecture

- **stunnel4** terminates TLS and listens on `:::12322` (proxy protocol).
- **gunicorn** runs the Flask app on `127.0.0.1:5000` (localhost only).
- A poller (`ovpn-acl-poller`) syncs the ACLs of connected restricted clients and resolves geolocation for new connections.
- A monthly timer (`ovpn-geoip-update`) refreshes the local GeoIP database.

```
Browser  ──HTTPS 12322──►  stunnel4  ──proxy──►  gunicorn 127.0.0.1:5000  (Flask)
```

The app calls TurnKey's easy-rsa / OpenVPN tooling directly; it doesn't expose certificate logic to the Internet.

## Prerequisites

- A configured TurnKey Linux **OpenVPN** appliance (easy-rsa at `/etc/openvpn/easy-rsa`).
- A TLS certificate at `/etc/ssl/private/cert.pem` (install fails if missing).
- Network access to port **12322/tcp** (install attempts to open it in the firewall automatically).

## Installation

Download the `.deb` matching your Debian version from the **[Releases](../../releases)** tab and install it with APT so dependencies resolve:

```bash
apt update
apt install -y ./openvpn-manager_<version>_debian11-12-13_all.deb
```

On Debian 10 (Buster):

```bash
apt update
apt install -y ./openvpn-manager_<version>_debian10_all.deb
```

> If you install with `dpkg -i`, run `apt -f install -y` afterwards to complete the dependencies.

On completion, the install enables and starts the services and prints the access URL.

## First access

- URL: `https://<server-IP>:12322/`
- **Credentials:** a system Linux user (e.g. `root`), authenticated via **PAM**. There's no panel-specific default user/password.

From **Administration** you can create additional panel users; they're created as shell-less system accounts in the `ovpn-panel` group, which is denied SSH access.

> The default certificate is self-signed, so the browser will warn the first time.

## Ports

| Port | Use |
|---|---|
| `12322/tcp` | Panel HTTPS (stunnel), external access |
| `127.0.0.1:5000` | gunicorn / Flask (internal only) |

## systemd services

- `openvpn-gui.service` — the Flask app (gunicorn)
- `stunnel4@openvpn-gui` — panel TLS termination
- `ovpn-acl-poller.service` — restricted-client ACL sync and geolocation
- `ovpn-geoip-update.timer` / `.service` — monthly GeoIP database refresh

```bash
systemctl status openvpn-gui stunnel4@openvpn-gui ovpn-acl-poller
journalctl -u openvpn-gui -f
```

## Installation paths

- App: `/var/www/openvpn/app/`
- Client metadata: `/var/www/openvpn/clients_meta.json`
- Geolocation history: `/var/lib/ovpn-acl/clients_geo.json`
- GeoIP database: `/var/lib/openvpn-manager/dbip-city-lite.mmdb`
- easy-rsa / OpenVPN config: `/etc/openvpn/easy-rsa`, `/etc/openvpn/server.ccd`
- stunnel config: `/etc/stunnel/openvpn-gui.conf`
- Logs: `/var/log/openvpn-gui.log` (audit) and `/var/log/openvpn-gui-access.log` (access), weekly rotation (12 weeks)

## Security

- PAM authentication against system users.
- CSRF protection, security headers and session expiry.
- Brute-force lockout (per-IP).
- Audit logging of actions.
- The app only listens on `localhost`; external access always goes through stunnel (TLS).

## Uninstall

```bash
apt remove openvpn-manager        # keeps configuration files
apt purge openvpn-manager         # also removes configuration
```

## Repository structure

```
app/                  Flask application (source, templates, static assets)
usr/lib/openvpn-manager/   ACL/geolocation poller and GeoIP refresh scripts
systemd/              systemd units (.service / .timer)
config/               stunnel, logrotate and tmpfiles.d config
packaging/debian10/DEBIAN/       Debian 10-specific control scripts
packaging/debian11-13/DEBIAN/    Debian 11/12/13-specific control scripts
scripts/build.sh      Assembles both package trees and builds the .deb files
```

The app code, scripts and systemd units are **shared** between both packages; only the control scripts (`postinst`/`prerm`/`postrm`/`control`) under `packaging/` differ, resolving Python dependencies differently depending on the target Debian version.

## Building the `.deb`

Requires `dpkg-deb` (package `dpkg-dev`, usually already present on Debian).

```bash
./scripts/build.sh          # builds both packages into dist/
./scripts/build.sh debian10       # Debian 10 only
./scripts/build.sh debian11-13    # Debian 11/12/13 only
```

The resulting `.deb` files are generated at `dist/openvpn-manager_<version>_<target>_all.deb`, with the version read from each target's `packaging/<target>/DEBIAN/control`.

## License

Distributed under the **GPL-3.0** license. See [LICENSE](LICENSE).
