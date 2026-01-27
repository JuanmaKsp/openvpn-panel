# OpenVPN TurnKey VPN Panel (Laravel + vpn-manager)

Panel web interno para gestionar clientes OpenVPN en **TurnKey OpenVPN (Debian 11)** con una interfaz gráfica.

## Funcionalidades

- Crear clientes y generar perfiles `.ovpn`
- Descargar perfiles `.ovpn`
- Revocar acceso (CRL)
- Renovar perfiles (revoca + emite uno nuevo)
- Control de validez por meses (6 / 24 / 48) aplicada al crear o renovar
- Gestión de usuarios del panel (admin/activo) con login

## Arquitectura

- **lighttpd** (TurnKey) mantiene **80/443**.
- **nginx** sirve Laravel en **127.0.0.1:8080**.
- lighttpd hace **reverse proxy** hacia nginx para mostrar el panel en `/`.
- **vpn-manager** (Python) corre en **127.0.0.1:9187** con token y expone una API local:
  - `POST /add` → llama `openvpn-addclient` con `EASYRSA_CERT_EXPIRE` por llamada (validez variable)
  - `POST /revoke` → llama `openvpn-revoke` en modo no interactivo
  - `GET /profile/<cn>` → descarga `.ovpn`
  - `GET /status/<cn>` → información del certificado/perfil

Laravel **no ejecuta comandos del sistema** ni usa sudoers: solo llama a `vpn-manager` por HTTP local.

## Instalación (recomendada)

Instalar el `.deb` con APT para que resuelva dependencias automáticamente:

```bash
apt update
apt install -y ./openvpn-vpnpanel_<version>_all.deb
```
Si se instala con dpkg -i, después ejecutar:
```bash
apt -f install -y
```
Durante la instalación se solicita APP_URL (debconf).

## Usuario admin inicial (por defecto):

 - usuario: admin@local

 - contraseña: admin

Cambia la contraseña tras el primer login.

## Puertos

 - Panel externo: https://<APP_URL>/ (lighttpd)

 - Nginx interno: 127.0.0.1:8080

 - vpn-manager interno: 127.0.0.1:9187

## Validez de certificados

La fecha “Not After” de un certificado X.509 no se puede editar.
Por eso la validez se aplica solo al crear o renovar un perfil (nuevo .ovpn).

La UI permite introducir la validez como un número (meses) y ofrece accesos rápidos:

 - 6 meses

 - 24 meses (2 años) (por defecto)

 - 48 meses (4 años)

## Seguridad

 - vpn-manager solo escucha en localhost y requiere token (/etc/vpn-manager/env).

 - nginx solo escucha en localhost (8080).

 - lighttpd actúa como proxy (80/443).

 - Revocación real vía CRL (server-side).

## Estructura de instalación (paths)

Puede variar según build (por ejemplo /var/www/vpnpanel o /opt/vpnpanel).

 - App Laravel: /var/www/vpnpanel

 - Env persistente: /etc/vpnpanel/vpnpanel.env

 - DB persistente (SQLite): /var/lib/vpnpanel/database/database.sqlite

 - vpn-manager: /usr/sbin/vpn-manager

 - systemd unit: /lib/systemd/system/vpn-manager.service

## Build del .deb (resumen)

El .deb incluye la app Laravel “release” ya construida (vendor + assets).
Se usa debuild/dpkg-buildpackage para generar el paquete.
```bash
::contentReference[oaicite:0]{index=0}
```
