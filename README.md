# OpenVPN Manager

Panel web (GUI) para gestionar clientes OpenVPN sobre **TurnKey Linux OpenVPN**. Interfaz **Flask** servida por HTTPS en el puerto **12322**, con autenticación de usuarios del sistema (PAM).

Permite crear, revocar, renovar y descargar perfiles `.ovpn`, además de gestionar IPs estáticas, rangos de acceso por cliente, bloqueos, modo mantenimiento y visor de logs — todo desde el navegador.

## Compatibilidad — elige el `.deb` correcto

Hay dos paquetes según la versión de Debian de tu TurnKey. El contenido de la app es el mismo; cambia cómo se resuelven las dependencias de Python.

| Fichero | Debian | Dependencias de Python |
|---|---|---|
| `openvpn-manager_1_5_5_debian10_all.deb` | 10 (Buster) | `gunicorn` y `python-pam` se instalan vía `pip3` en la instalación (no están en los repos de Buster). |
| `openvpn-manager_1_5_5_debian11-12-13_all.deb` | 11 (Bullseye), 12 (Bookworm), 13 (Trixie) | Todo desde APT (`gunicorn`, `python3-pam`). |

## Funcionalidades

- Crear clientes y generar/descargar perfiles `.ovpn`
- Revocar certificados (CRL) y renovar perfiles
- Validez configurable por meses al crear/renovar
- Asignación de **IP estática** por cliente
- **Rangos de acceso** por cliente (rutas push vía CCD)
- Bloquear / desbloquear clientes
- Desconectar clientes conectados (interfaz de gestión de OpenVPN)
- **Modo mantenimiento** (bloqueo temporal global)
- Visor de logs de OpenVPN y de auditoría
- Gestión de usuarios del panel (cuentas del sistema sin shell)

## Arquitectura

- **stunnel4** termina TLS y escucha en `:::12322` (proxy protocol).
- **gunicorn** ejecuta la app Flask en `127.0.0.1:5000` (solo localhost).
- Un poller (`ovpn-acl-poller`) sincroniza las ACL de los clientes restringidos que están conectados.

```
Navegador  ──HTTPS 12322──►  stunnel4  ──proxy──►  gunicorn 127.0.0.1:5000  (Flask)
```

La app llama a las herramientas de easy-rsa / OpenVPN de TurnKey; no expone la lógica de certificados a Internet.

## Requisitos previos

- TurnKey Linux **OpenVPN** ya configurado (easy-rsa en `/etc/openvpn/easy-rsa`).
- Certificado TLS en `/etc/ssl/private/cert.pem` (la instalación falla si no existe).
- Acceso de red al puerto **12322/tcp** (la instalación intenta abrirlo en el firewall automáticamente).

## Instalación

Descarga el `.deb` correspondiente a tu Debian desde la pestaña **[Releases](../../releases)** e instálalo con APT para que resuelva dependencias:

```bash
apt update
apt install -y ./openvpn-manager_1_5_5_debian11-12-13_all.deb
```

En Debian 10 (Buster):

```bash
apt update
apt install -y ./openvpn-manager_1_5_5_debian10_all.deb
```

> Si instalas con `dpkg -i`, ejecuta después `apt -f install -y` para completar las dependencias.

Al terminar, la instalación habilita y arranca los servicios y muestra la URL de acceso.

## Primer acceso

- URL: `https://<IP-del-servidor>:12322/`
- **Credenciales:** un usuario Linux del sistema (por ejemplo `root`), autenticado vía **PAM**. No hay un usuario/contraseña por defecto propio del panel.

Desde **Administración** puedes crear usuarios adicionales del panel; se crean como cuentas del sistema sin shell y en el grupo `ovpn-panel`, al que se le deniega el acceso SSH.

> El certificado por defecto es autofirmado, así que el navegador avisará la primera vez.

## Puertos

| Puerto | Uso |
|---|---|
| `12322/tcp` | Panel HTTPS (stunnel), acceso externo |
| `127.0.0.1:5000` | gunicorn / Flask (solo interno) |

## Servicios systemd

- `openvpn-gui.service` — la app Flask (gunicorn)
- `stunnel4@openvpn-gui` — terminación TLS del panel
- `ovpn-acl-poller.service` — sincronización de ACL de clientes restringidos

```bash
systemctl status openvpn-gui stunnel4@openvpn-gui ovpn-acl-poller
journalctl -u openvpn-gui -f
```

## Rutas de instalación

- App: `/var/www/openvpn/app/`
- Metadatos de clientes: `/var/www/openvpn/clients_meta.json`
- Config de easy-rsa / OpenVPN: `/etc/openvpn/easy-rsa`, `/etc/openvpn/server.ccd`
- Config de stunnel: `/etc/stunnel/openvpn-gui.conf`
- Logs: `/var/log/openvpn-gui.log` (auditoría) y `/var/log/openvpn-gui-access.log` (accesos), con rotación semanal (12 semanas)

## Seguridad

- Autenticación por PAM contra usuarios del sistema.
- Protección CSRF, cabeceras de seguridad y expiración de sesión.
- Bloqueo por fuerza bruta (lockout por IP).
- Registro de auditoría de acciones.
- La app solo escucha en `localhost`; el acceso externo pasa siempre por stunnel (TLS).

## Desinstalación

```bash
apt remove openvpn-manager        # conserva ficheros de configuración
apt purge openvpn-manager         # elimina también la configuración
```

## Build del `.deb` (opcional)

El paquete se construye con las herramientas estándar de Debian (`dpkg-deb --build` / `dpkg-buildpackage`) a partir del árbol del paquete. Consulta la carpeta de empaquetado del repositorio.

## Licencia

Distribuido bajo licencia **GPL-3.0**. Ver [LICENSE](LICENSE).
