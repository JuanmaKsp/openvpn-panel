#!/usr/bin/env python3
"""
acl-poller — mantiene la cadena iptables OVPN_ACL sincronizada con los
clientes VPN actualmente conectados que tienen "Rangos de acceso"
configurados en el panel.

Corre fuera de OpenVPN por completo (no usa client-connect/client-disconnect,
no toca el chroot ni la degradacion a "nobody" del propio proceso OpenVPN):
sondea la interfaz de gestion cada POLL_INTERVAL segundos, exactamente igual
que ya hace app.py para mostrar quien esta conectado, y reconstruye la
cadena OVPN_ACL solo cuando el estado deseado cambia.

Fail-closed: un cliente restringido cuyos rangos resulten invalidos/vacios
tras validar se bloquea por completo (DROP), nunca se deja sin restriccion.
Fail-open a nivel de proceso: cualquier error de una vuelta del bucle
(interfaz de gestion caida, JSON corrupto, etc.) se registra y se reintenta
en el siguiente ciclo — nunca debe morir el servicio por un fallo puntual.
"""
import socket
import json
import os
import subprocess
import ipaddress
import time
import logging
import signal
import sys

try:
    import maxminddb
except ImportError:
    maxminddb = None  # geolocalizacion deshabilitada con gracia (ver geolocate())

MGMT_HOST      = '127.0.0.1'
MGMT_PORT      = 7505
META_FILE      = '/var/www/openvpn/clients_meta.json'
CHAIN_NAME     = 'OVPN_ACL'
IPTABLES_BIN   = '/usr/sbin/iptables-legacy'
POLL_INTERVAL  = 2  # segundos

# Geolocalizacion de la ultima conexion (mapa en el panel). Se resuelve solo
# en el instante en que un cliente pasa de "desconectado" a "conectado" (no
# en cada ciclo de sondeo) usando una base de datos local .mmdb -- ninguna
# IP de cliente sale nunca de este servidor hacia un tercero.
#
# GEO_FILE vive en /var/lib/ovpn-acl/ (StateDirectory=ovpn-acl en el
# .service, systemd lo crea y lo deja propiedad de este mismo usuario) y NO
# en /var/www/openvpn/ (root:root 755) -- este proceso corre como el
# usuario sin privilegios "ovpn-acl" y no podria crear ficheros nuevos ahi.
# app.py si puede leerlo sin mas: corre como root, que no esta sujeto a
# comprobaciones DAC de lectura.
GEO_DB_FILE = '/var/lib/openvpn-manager/dbip-city-lite.mmdb'
GEO_FILE    = '/var/lib/ovpn-acl/clients_geo.json'

# Cache de "quien esta conectado ahora" para que app.py (badge de conexion
# en "Clientes VPN") no tenga que abrir su propia conexion a la interfaz de
# gestion -- eso evitaria del todo el riesgo de contencion del puerto 7505
# (solo admite un cliente a la vez) y no añade NINGUN trafico nuevo hacia
# OpenVPN: el dato ya se consulta aqui, cada POLL_INTERVAL segundos, para
# el propio cortafuegos. El directorio lo crea systemd (RuntimeDirectory=
# en el .service), asi que existe con los permisos correctos antes de que
# este proceso arranque.
CONNECTED_CACHE_FILE = '/run/openvpn-manager/connected.json'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)],  # systemd/journald lo captura
)
log = logging.getLogger('acl-poller')

_running = True


def _handle_sigterm(signum, frame):
    global _running
    _running = False


signal.signal(signal.SIGTERM, _handle_sigterm)
signal.signal(signal.SIGINT, _handle_sigterm)


def get_connected_clients():
    """Devuelve {common_name: {'vip': virtual_ip, 'real_ip': real_ip}} de
    los clientes conectados ahora mismo, consultando la interfaz de
    gestion (igual que app.py).

    Se abre y cierra una conexion nueva en cada sondeo (en vez de mantener
    una persistente) A PROPOSITO: la interfaz de gestion de OpenVPN solo
    admite UN cliente conectado a la vez. Una version anterior de este
    fichero mantenia la conexion abierta permanentemente para reducir el
    ruido "MANAGEMENT: ..." en el journal -- pero eso ocupaba el unico
    hueco disponible todo el tiempo, y bloqueaba durante 3s (timeout) cada
    consulta que el propio panel (app.py) hace al cargar "Clientes VPN" o
    al bloquear/desconectar un cliente -- regresion real encontrada en
    produccion. El ruido en el journal ya se mitiga de otras dos formas
    (el panel filtra y busca sobre el journal en vez de leer las ultimas N
    lineas en crudo, y el journal ahora es persistente en disco en vez de
    un tmpfs pequeño), asi que se prioriza no monopolizar la interfaz de
    gestion sobre reducir aun mas ese ruido."""
    result = {}
    try:
        s = socket.create_connection((MGMT_HOST, MGMT_PORT), timeout=3)
        s.recv(1024)
        s.sendall(b'status 2\n')
        data = b''
        while b'\nEND' not in data:
            chunk = s.recv(4096)
            if not chunk:
                break
            data += chunk
        s.sendall(b'quit\n')
        s.close()
        for line in data.decode(errors='ignore').splitlines():
            if line.startswith('CLIENT_LIST,'):
                parts = line.split(',')
                # CLIENT_LIST,Common Name,Real Address,Virtual Address,...
                if len(parts) > 3 and parts[1] and parts[3]:
                    real_addr = parts[2].rsplit(':', 1)[0] if parts[2] else ''  # quitar ":puerto"
                    result[parts[1]] = {'vip': parts[3], 'real_ip': real_addr}
    except (ConnectionRefusedError, OSError, socket.timeout) as e:
        log.warning('no se pudo consultar la interfaz de gestion: %s', e)
    return result


def load_ranges():
    """Devuelve {name: [cidrs]} para clientes con ip_ranges no vacio."""
    try:
        with open(META_FILE) as f:
            meta = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        log.warning('no se pudo leer %s: %s', META_FILE, e)
        return {}
    ranges = {}
    for name, data in meta.items():
        cidrs = data.get('ip_ranges') or []
        if cidrs:
            ranges[name] = cidrs
    return ranges


def valid_cidr(cidr):
    try:
        net = ipaddress.ip_network(cidr, strict=False)
        if net.version != 4:
            return None
        return str(net)
    except ValueError:
        return None


def write_connected_cache(connected):
    """Escribe {name: virtual_ip} para que app.py lo lea sin tener que
    consultar la interfaz de gestion por su cuenta. Escritura atomica
    (fichero temporal + rename) para que una lectura a medio escribir
    nunca vea JSON incompleto."""
    try:
        tmp = CONNECTED_CACHE_FILE + '.tmp'
        with open(tmp, 'w') as f:
            json.dump(connected, f)
        os.chmod(tmp, 0o640)
        os.replace(tmp, CONNECTED_CACHE_FILE)
    except OSError as e:
        log.warning('no se pudo escribir la cache de conectados: %s', e)


class _GeoReader:
    """Envoltorio perezoso sobre el lector .mmdb. Vuelve a abrir el fichero
    si cambia su mtime (el timer mensual lo reemplaza atomicamente) o si
    aparece por primera vez (aun no se habia descargado al arrancar este
    servicio). Si falta la libreria maxminddb o el fichero, todo lookup
    devuelve None sin error -- el mapa simplemente no tendra datos hasta
    que la base de datos este disponible."""

    def __init__(self):
        self._reader = None
        self._mtime = None

    def _ensure_open(self):
        if maxminddb is None:
            return False
        try:
            mtime = os.path.getmtime(GEO_DB_FILE)
        except OSError:
            return False
        if self._reader is None or mtime != self._mtime:
            try:
                if self._reader is not None:
                    self._reader.close()
                self._reader = maxminddb.open_database(GEO_DB_FILE)
                self._mtime = mtime
                log.info('base de datos GeoIP (re)cargada: %s', GEO_DB_FILE)
            except Exception as e:
                log.warning('no se pudo abrir la base de datos GeoIP %s: %s', GEO_DB_FILE, e)
                self._reader = None
                return False
        return True

    def lookup(self, ip):
        if not self._ensure_open():
            return None
        try:
            rec = self._reader.get(ip)
        except (ValueError, OSError):
            return None
        if not rec:
            return None
        loc = rec.get('location') or {}
        lat, lon = loc.get('latitude'), loc.get('longitude')
        if lat is None or lon is None:
            return None
        city = (rec.get('city') or {}).get('names', {}).get('en', '')
        country = rec.get('country') or {}
        return {
            'lat': lat,
            'lon': lon,
            'city': city,
            'country': country.get('names', {}).get('en', ''),
            'country_code': country.get('iso_code', ''),
        }


_geo_reader = _GeoReader()


def is_public_ip(ip_str):
    """False para privadas/loopback/enlace-local/reservadas/multicast --
    esas nunca son geolocalizables y no tiene sentido intentarlo (ademas de
    ser habitual verlas en pruebas locales, cliente y servidor en la misma
    LAN, etc.)."""
    try:
        addr = ipaddress.ip_address(ip_str)
    except ValueError:
        return False
    return not (addr.is_private or addr.is_loopback or addr.is_link_local
                or addr.is_reserved or addr.is_multicast or addr.is_unspecified)


def geolocate(ip_str):
    """{'lat', 'lon', 'city', 'country', 'country_code'} o None si la IP
    no es publica, la base de datos no esta disponible, o no hay registro
    para esa IP (comun con IPs muy nuevas o rangos no asignados)."""
    if not is_public_ip(ip_str):
        return None
    return _geo_reader.lookup(ip_str)


GEO_HISTORY_MAX = 5  # IPs *distintas* como mucho por cliente, no conexiones


def update_geo_for_new_connections(newly_connected_names, connected):
    """Para cada cliente que acaba de pasar a "conectado" en este ciclo,
    geolocaliza su IP real y actualiza su historial en clients_geo.json:
    {name: {'history': [{'ip','ts','lat'?,'lon'?,'city'?,'country'?,
    'country_code'?}, ...]}}, mas reciente primero, como mucho
    GEO_HISTORY_MAX entradas -- pero de IPs *distintas*, no de conexiones.
    Si el cliente se reconecta desde una IP que ya estaba en su historial,
    esa entrada se refresca (nueva hora) y sube a la primera posicion, sin
    crear una duplicada -- si siempre se conecta desde el mismo sitio, la
    lista nunca crece de una entrada. Si la geolocalizacion falla (IP
    privada, o la base de datos GeoIP aun no disponible en ese instante) se
    guarda igualmente la IP y la hora, para que el panel pueda mostrar "sin
    datos de ubicacion" en vez de nada -- y si fue por falta de base de
    datos (no por ser privada), retry_pending_geolocations() la completara
    sola en un ciclo posterior en cuanto la base de datos este lista."""
    if not newly_connected_names:
        return
    try:
        with open(GEO_FILE) as f:
            geo = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        geo = {}

    changed = False
    for name in newly_connected_names:
        real_ip = connected.get(name, {}).get('real_ip')
        if not real_ip:
            continue
        entry = {'ip': real_ip, 'ts': int(time.time())}
        loc = geolocate(real_ip)
        if loc:
            entry.update(loc)

        history = geo.get(name, {}).get('history', [])
        history = [h for h in history if h.get('ip') != real_ip]  # quitar duplicado, si lo hay
        history.insert(0, entry)
        history = history[:GEO_HISTORY_MAX]
        geo[name] = {'history': history}

        changed = True
        log.info('nueva conexion geolocalizada: name=%s ip=%s city=%s country=%s ips_distintas=%d',
                  name, real_ip, entry.get('city', ''), entry.get('country_code', ''), len(history))

    if not changed:
        return
    _save_geo(geo)


def _save_geo(geo):
    try:
        tmp = GEO_FILE + '.tmp'
        with open(tmp, 'w') as f:
            json.dump(geo, f, indent=2)
        os.replace(tmp, GEO_FILE)
    except OSError as e:
        log.warning('no se pudo escribir %s: %s', GEO_FILE, e)


def retry_pending_geolocations():
    """Reintenta geolocalizar entradas del historial que quedaron sin
    ubicacion (sin 'lat') pero con una IP publica -- bug real encontrado en
    produccion: un cliente que se conecta en los primeros segundos tras
    instalar el paquete (mientras la base de datos GeoIP aun se esta
    descargando en segundo plano) se geolocaliza en el instante exacto de
    esa conexion, UNA sola vez; si en ese momento la base de datos todavia
    no existia, antes se quedaba sin ubicacion para siempre, aunque la
    descarga terminara un segundo despues. Aqui se revisa cada ciclo (barato:
    normalmente no hay ninguna entrada pendiente, y si la hubiera pero la
    base de datos sigue sin estar disponible, geolocate() devuelve None de
    inmediato sin tocar el fichero .mmdb)."""
    try:
        with open(GEO_FILE) as f:
            geo = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return

    changed = False
    for name, data in geo.items():
        for entry in data.get('history', []):
            if 'lat' in entry:
                continue  # ya tiene ubicacion
            ip = entry.get('ip')
            if not ip or not is_public_ip(ip):
                continue  # privada/invalida: nunca va a resolver, no reintentar
            loc = geolocate(ip)
            if loc:
                entry.update(loc)
                changed = True
                log.info('ubicacion pendiente resuelta en reintento: name=%s ip=%s city=%s country=%s',
                          name, ip, loc.get('city', ''), loc.get('country_code', ''))

    if changed:
        _save_geo(geo)


def build_desired_state(connected):
    """{virtual_ip: [cidrs_validos]} solo para clientes conectados Y con
    rango configurado. Un cliente con rango pero SIN ningun CIDR valido
    tras validar aparece con lista vacia -> se traduce en DROP total
    (fail-closed), nunca en ausencia de reglas."""
    ranges = load_ranges()
    state = {}
    for name, cidrs in ranges.items():
        vip = connected.get(name, {}).get('vip')
        if not vip:
            continue  # no conectado ahora mismo, no necesita reglas
        valid = [c for c in (valid_cidr(c) for c in cidrs) if c]
        state[vip] = sorted(valid)
    return state


def run_iptables(args):
    try:
        r = subprocess.run([IPTABLES_BIN] + args, capture_output=True, text=True, timeout=5)
        if r.returncode != 0:
            log.warning('iptables-legacy %s fallo: %s', args, r.stderr.strip())
        return r.returncode == 0
    except (subprocess.TimeoutExpired, OSError) as e:
        log.error('no se pudo ejecutar iptables-legacy %s: %s', args, e)
        return False


def apply_state(state):
    """Devuelve True solo si TODAS las operaciones de iptables-legacy
    tuvieron exito. Si algo falla (p.ej. permiso), el estado no debe darse
    por aplicado, para que el siguiente ciclo lo reintente en vez de
    quedarse "atascado" pensando que ya esta correcto."""
    ok = run_iptables(['-F', CHAIN_NAME])
    for vip, cidrs in state.items():
        src = f'{vip}/32'
        for cidr in cidrs:
            ok = run_iptables(['-A', CHAIN_NAME, '-s', src, '-d', cidr, '-j', 'RETURN']) and ok
        ok = run_iptables(['-A', CHAIN_NAME, '-s', src, '-j', 'DROP']) and ok
        if not cidrs:
            log.warning('cliente en %s sin ningun CIDR valido: bloqueado por completo', vip)
    return ok


def main():
    log.info('acl-poller arrancando, intervalo=%ss', POLL_INTERVAL)
    last_state = None
    last_connected_names = set()
    while _running:
        try:
            connected = get_connected_clients()
            write_connected_cache(connected)

            newly_connected = set(connected) - last_connected_names
            update_geo_for_new_connections(newly_connected, connected)
            retry_pending_geolocations()
            last_connected_names = set(connected)

            state = build_desired_state(connected)
            if state != last_state:
                log.info('cambio de estado detectado, reconstruyendo %s: %s',
                          CHAIN_NAME, {k: len(v) for k, v in state.items()})
                if apply_state(state):
                    last_state = state
                else:
                    log.warning('la reconstruccion de %s fallo parcial o totalmente, se reintentara', CHAIN_NAME)
        except Exception:
            log.exception('error inesperado en el ciclo de sondeo, se reintenta')
        for _ in range(POLL_INTERVAL * 10):
            if not _running:
                break
            time.sleep(0.1)
    log.info('acl-poller detenido')


if __name__ == '__main__':
    main()
