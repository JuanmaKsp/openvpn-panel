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
