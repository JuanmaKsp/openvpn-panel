# OpenVPN Manager

Panel web (GUI) para gestionar clientes OpenVPN sobre **TurnKey Linux OpenVPN**. Interfaz **Flask** servida por HTTPS en el puerto **12322**, con autenticación de usuarios del sistema (PAM). Disponible en **español e inglés** (selector de idioma en la propia interfaz).

Permite crear, revocar, renovar y descargar perfiles `.ovpn`, además de gestionar IPs estáticas, rangos de acceso por cliente, bloqueos, modo mantenimiento, un mapa de geolocalización de conexiones y visor de logs — todo desde el navegador.

## Compatibilidad — elige el `.deb` correcto

Hay dos paquetes según la versión de Debian de tu TurnKey. El contenido de la app es el mismo; cambia cómo se resuelven las dependencias de Python.

| Fichero | Debian | Dependencias de Python |
|---|---|---|
| `openvpn-manager_<version>_debian10_all.deb` | 10 (Buster) | `gunicorn`, `python-pam` y `maxminddb` se instalan vía `pip3` en la instalación (no están en los repos de Buster). |
| `openvpn-manager_<version>_debian11-12-13_all.deb` | 11 (Bullseye), 12 (Bookworm), 13 (Trixie) | Todo desde APT (`gunicorn`, `python3-pam`, `python3-maxminddb`). |

Descarga la última versión desde la pestaña **[Releases](../../releases)**.

## Funcionalidades

- Crear clientes y generar/descargar perfiles `.ovpn`
- Revocar certificados (CRL) y renovar perfiles
- Validez configurable por meses al crear/renovar
- Asignación de **IP estática** por cliente
- **Rangos de acceso** por cliente (rutas push vía CCD), editables sin necesidad de reemitir el `.ovpn`
- Bloquear / desbloquear clientes
- Desconectar clientes conectados (interfaz de gestión de OpenVPN)
- **Modo mantenimiento** (bloqueo temporal global)
- **Mapa de geolocalización**: ubicación aproximada de la última conexión de cada cliente (hasta 5 IPs distintas de historial), resuelta localmente contra una base de datos GeoIP (DB-IP City Lite) — ninguna IP de cliente se envía nunca a un tercero; solo el navegador del administrador carga las teselas del mapa desde OpenStreetMap
- Visor de logs de OpenVPN y de auditoría
- Gestión de usuarios del panel (cuentas del sistema sin shell)
- Interfaz bilingüe español/inglés

## Arquitectura

- **stunnel4** termina TLS y escucha en `:::12322` (proxy protocol).
- **gunicorn** ejecuta la app Flask en `127.0.0.1:5000` (solo localhost).
- Un poller (`ovpn-acl-poller`) sincroniza las ACL de los clientes restringidos que están conectados y resuelve la geolocalización de nuevas conexiones.
- Un timer mensual (`ovpn-geoip-update`) refresca la base de datos GeoIP local.

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
apt install -y ./openvpn-manager_<version>_debian11-12-13_all.deb
```

En Debian 10 (Buster):

```bash
apt update
apt install -y ./openvpn-manager_<version>_debian10_all.deb
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
- `ovpn-acl-poller.service` — sincronización de ACL de clientes restringidos y geolocalización
- `ovpn-geoip-update.timer` / `.service` — refresco mensual de la base de datos GeoIP

```bash
systemctl status openvpn-gui stunnel4@openvpn-gui ovpn-acl-poller
journalctl -u openvpn-gui -f
```

## Rutas de instalación

- App: `/var/www/openvpn/app/`
- Metadatos de clientes: `/var/www/openvpn/clients_meta.json`
- Historial de geolocalización: `/var/lib/ovpn-acl/clients_geo.json`
- Base de datos GeoIP: `/var/lib/openvpn-manager/dbip-city-lite.mmdb`
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

## Estructura del repositorio

```
app/                  Aplicación Flask (código fuente, plantillas, estáticos)
usr/lib/openvpn-manager/   Scripts del poller de ACL/geolocalización y del refresco GeoIP
systemd/              Unidades systemd (.service / .timer)
config/               Config de stunnel, logrotate y tmpfiles.d
packaging/debian10/DEBIAN/       Scripts de control específicos de Debian 10
packaging/debian11-13/DEBIAN/    Scripts de control específicos de Debian 11/12/13
scripts/build.sh      Ensambla ambos árboles de paquete y construye los .deb
```

El código de la app, los scripts y las unidades systemd son **compartidos** entre ambos paquetes; solo cambian los scripts de control (`postinst`/`prerm`/`postrm`/`control`) bajo `packaging/`, que resuelven las dependencias de Python de forma distinta según el Debian objetivo.

## Build del `.deb`

Requiere `dpkg-deb` (paquete `dpkg-dev`, normalmente ya presente en Debian).

```bash
./scripts/build.sh          # construye ambos paquetes en dist/
./scripts/build.sh debian10       # solo Debian 10
./scripts/build.sh debian11-13    # solo Debian 11/12/13
```

Los `.deb` resultantes se generan en `dist/openvpn-manager_<version>_<target>_all.deb`, con la versión leída del `Version:` de cada `packaging/<target>/DEBIAN/control`.

## Licencia

Distribuido bajo licencia **GPL-3.0**. Ver [LICENSE](LICENSE).
