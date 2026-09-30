#!/usr/bin/env python3
import os
import re
import grp
import pwd
import json
import hmac
import time
import secrets
import logging
import tempfile
import ipaddress
import subprocess
import contextlib
from collections import defaultdict
from datetime import datetime, timedelta
from functools import wraps

# PAM: Debian 11/12 usa python3-pam (import PAM), Debian 10 usa pip python-pam (import pam)
try:
    import PAM as _PAM
    _PAM_STYLE = 'debian'
except ImportError:
    try:
        import pam as _PAM
        _PAM_STYLE = 'pip'
    except ImportError as _e:
        raise ImportError(
            "Módulo PAM no encontrado. Instala: apt install python3-pam "
            "o pip3 install python-pam"
        ) from _e

import flask as _flask
_FLASK_V2 = int(_flask.__version__.split('.')[0]) >= 2

from flask import (Flask, render_template, request, redirect,
                   url_for, session, flash, send_file, g, abort, jsonify)

from translations import TRANSLATIONS, DEFAULT_LANG, SUPPORTED_LANGS, get_text

# ---------------------------------------------------------------------------
# Logging / audit
# ---------------------------------------------------------------------------
logging.basicConfig(
    filename='/var/log/openvpn-gui.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
)
logger = logging.getLogger(__name__)

APP_VERSION = '1.7.2'

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
EASY_RSA   = '/etc/openvpn/easy-rsa'
KEY_DIR    = '/etc/openvpn/easy-rsa/keys'
INDEX_FILE = f'{KEY_DIR}/index.txt'
VARS_FILE  = f'{EASY_RSA}/vars'
META_FILE   = '/var/www/openvpn/clients_meta.json'
CCD_DIR     = '/etc/openvpn/server.ccd'
STATUS_FILE = '/var/log/openvpn/server.log'

# ---------------------------------------------------------------------------
# Flask setup
# ---------------------------------------------------------------------------
SECRET_FILE = '/var/www/openvpn/app/.secret'
if os.path.exists(SECRET_FILE):
    with open(SECRET_FILE) as _f:
        _secret = _f.read().strip()
else:
    _secret = secrets.token_hex(32)
    with open(SECRET_FILE, 'w') as _f:
        _f.write(_secret)
    os.chmod(SECRET_FILE, 0o600)

app = Flask(__name__)
app.secret_key = _secret
app.config.update(
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8),
    SESSION_COOKIE_SECURE      = True,
    SESSION_COOKIE_HTTPONLY    = True,
    SESSION_COOKIE_SAMESITE    = 'Lax',
)

# ---------------------------------------------------------------------------
# Revoked session tokens (server-side invalidation on logout)
# ---------------------------------------------------------------------------
_revoked_sessions: set = set()
_REVOKED_MAX = 10000   # cap para evitar crecimiento ilimitado


def _revoke_session(sid: str):
    if len(_revoked_sessions) >= _REVOKED_MAX:
        # Descartamos la mitad más antigua (set no es ordenado, basta limpiar)
        _revoked_sessions.clear()
    _revoked_sessions.add(sid)


def _session_id() -> str:
    """Identificador estable de la sesión actual (token de sesión del usuario)."""
    return session.get('_sid', '')


# ---------------------------------------------------------------------------
# Brute-force protection
# ---------------------------------------------------------------------------
_failed: dict = defaultdict(list)   # ip -> [timestamp, ...]
_MAX_ATTEMPTS = 5
_WINDOW_SECS  = 300   # 5 minutes
_LOCKOUT_SECS = 300


def _client_ip():
    return request.remote_addr or '0.0.0.0'


def _sanitize_log_field(s):
    """Quita CR/LF de un valor no autenticado antes de meterlo en el log,
    para que no pueda forjar líneas de auditoría falsas (log injection)."""
    return s.replace('\r', '').replace('\n', '') if s else s


def _is_locked(ip: str) -> bool:
    now = time.time()
    _failed[ip] = [t for t in _failed[ip] if now - t < _WINDOW_SECS]
    return len(_failed[ip]) >= _MAX_ATTEMPTS


def _record_failure(ip: str):
    _failed[ip].append(time.time())


# ---------------------------------------------------------------------------
# CSRF
# ---------------------------------------------------------------------------
def _csrf_token() -> str:
    if '_csrf' not in session:
        session['_csrf'] = secrets.token_hex(32)
    return session['_csrf']


def _check_csrf():
    if request.method in ('POST', 'PUT', 'PATCH', 'DELETE'):
        token = request.form.get('_csrf_token', '')
        if not hmac.compare_digest(token, session.get('_csrf', '')):
            logger.warning('CSRF check failed from %s %s', _client_ip(), request.path)
            abort(403)


# ---------------------------------------------------------------------------
# Hooks
# ---------------------------------------------------------------------------
@app.before_request
def before():
    request.environ['wsgi.url_scheme'] = 'https'
    session.permanent = True
    # Reject revoked sessions (server-side logout invalidation)
    if 'user' in session and _session_id() in _revoked_sessions:
        session.clear()
        return redirect(url_for('login'), 303)
    _check_csrf()   # applies to all POST requests, including login
    lang = request.cookies.get('lang')
    g.lang = lang if lang in SUPPORTED_LANGS else DEFAULT_LANG


@app.after_request
def security_headers(resp):
    resp.headers['X-Frame-Options']           = 'DENY'
    resp.headers['X-Content-Type-Options']    = 'nosniff'
    resp.headers['X-XSS-Protection']          = '1; mode=block'
    resp.headers['Referrer-Policy']           = 'strict-origin-when-cross-origin'
    resp.headers['Content-Security-Policy']   = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'; "
        # Unico permiso externo de toda la CSP: las teselas del mapa
        # (pestaña "Mapa"). Las pide el navegador del admin directamente a
        # OpenStreetMap -- nunca el servidor, y solo son coordenadas de
        # cuadricula del mapa, ninguna IP de cliente viaja en esa petición.
        "img-src 'self' data: https://*.tile.openstreetmap.org;"
    )
    resp.headers['Strict-Transport-Security'] = 'max-age=63072000; includeSubDomains'
    return resp


# Make csrf_token available in all templates
app.jinja_env.globals['csrf_token'] = _csrf_token
app.jinja_env.globals['app_version'] = APP_VERSION


def t(key, **kwargs):
    """Texto traducido según el idioma activo (g.lang) — usable tanto en
    plantillas Jinja ({{ t('clave') }}) como en Python puro (mensajes
    flash()). Fuera de una request (script, import) g.lang no existe;
    se cae al idioma por defecto en vez de reventar."""
    lang = getattr(g, 'lang', DEFAULT_LANG)
    text = get_text(lang, key)
    return text.format(**kwargs) if kwargs else text


app.jinja_env.globals['t'] = t
app.jinja_env.globals['lang'] = lambda: getattr(g, 'lang', DEFAULT_LANG)


def _safe_next(default_endpoint='login'):
    """Solo redirige a una ruta local (empieza por '/', nunca '//' —
    evita un open-redirect vía el parámetro next)."""
    next_url = request.args.get('next', '')
    if next_url.startswith('/') and not next_url.startswith('//'):
        return next_url
    return url_for(default_endpoint)


@app.route('/lang/<code>')
def set_lang(code):
    """Cambia el idioma del panel — no requiere sesión iniciada (también
    aplica al login) y vuelve a la página desde la que se pidió."""
    resp = redirect(_safe_next(), 303)
    if code in SUPPORTED_LANGS:
        resp.set_cookie('lang', code, max_age=60 * 60 * 24 * 365,
                        secure=True, httponly=False, samesite='Lax')
    return resp

# ---------------------------------------------------------------------------
# Jinja2 filters for log coloring
# ---------------------------------------------------------------------------
import markupsafe

@app.template_filter('vpn_class')
def vpn_class(line):
    l = line.lower()
    if any(x in l for x in ('sigterm', 'link disconnect', 'connection reset', 'client-instance exiting',
                            'inactivity timeout', 'sigusr1', 'client-instance restarting')):
        return 'log-disconnect'
    if any(x in l for x in ('initialization sequence completed', 'multi: learn', 'ifconfig pool')):
        return 'log-connected'
    if any(x in l for x in ('tls-client', 'tls error', 'tls handshake', 'verify error', 'certificate')):
        return 'log-tls'
    if 'error' in l:
        return 'log-error'
    if 'warn' in l:
        return 'log-warn'
    if any(x in l for x in ('multi: link', 'peer info', 'sent control', 'connection initiated')):
        return 'log-connected'
    if any(x in l for x in ('systemd', 'started', 'stopped', 'starting', 'stopping')):
        return 'log-dim'
    return ''


@app.template_filter('audit_class')
def audit_class(line):
    l = line.lower()
    if 'error' in l:
        return 'log-error'
    if 'warning' in l or 'csrf' in l or 'brute' in l or 'fail' in l:
        return 'log-warn'
    if any(x in l for x in ('login ok', 'logout', 'create ok', 'renew ok', 'download', 'unblock ok')):
        return 'log-ok'
    if any(x in l for x in ('revoke ok', 'block ok', 'disconnect ok', 'maintenance')):
        return 'log-info'
    if 'login' in l:
        return 'log-login'
    return ''


@app.template_filter('highlight')
def highlight(line, term):
    safe_line = markupsafe.escape(line)
    if not term:
        return safe_line
    idx = safe_line.lower().find(term.lower())
    if idx == -1:
        return safe_line
    result = (safe_line[:idx]
              + markupsafe.Markup('<mark>')
              + safe_line[idx:idx + len(term)]
              + markupsafe.Markup('</mark>')
              + safe_line[idx + len(term):])
    return result

# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

def pam_auth(username, password):
    if _PAM_STYLE == 'pip':
        # python-pam (pip): API simple, disponible en Debian 10
        return _PAM.pam().authenticate(username, password, service='sshd')
    else:
        # python3-pam (apt): API de bajo nivel, disponible en Debian 11
        def conv(auth, query_list, userdata):
            resp = []
            for _query, qtype in query_list:
                if qtype in (_PAM.PAM_PROMPT_ECHO_OFF, _PAM.PAM_PROMPT_ECHO_ON):
                    resp.append((password, 0))
                else:
                    resp.append(('', 0))
            return resp
        p = _PAM.pam()
        p.start('login')
        p.set_item(_PAM.PAM_USER, username)
        p.set_item(_PAM.PAM_CONV, conv)
        try:
            p.authenticate()
            p.acct_mgmt()
            return True
        except _PAM.error:
            return False


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'), 303)
        return f(*args, **kwargs)
    return decorated


def root_required(f):
    """Restringe una ruta al usuario Linux 'root' — usado para la gestión
    de usuarios del panel (crear/eliminar cuentas sin shell)."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get('user') != 'root':
            abort(403)
        return f(*args, **kwargs)
    return decorated

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def read_var(name):
    try:
        with open(VARS_FILE) as f:
            for line in f:
                line = line.strip()
                if line.startswith(f'set_var {name} '):
                    parts = line.split('"')
                    if len(parts) >= 2:
                        return parts[1]
    except Exception:
        pass
    return None


def get_default_months():
    val  = read_var('EASYRSA_CERT_EXPIRE')
    days = int(val) if val else 730
    return max(1, round(days / 30))


def months_to_days(months):
    return months * 30


_CONNECTED_CACHE_FILE    = '/run/openvpn-manager/connected.json'
_CONNECTED_CACHE_MAX_AGE = 6  # segundos; algo más que el intervalo de sondeo del poller (2s)


def get_connected_clients():
    """Devuelve el conjunto de nombres de clientes conectados ahora mismo.

    Se lee primero de la cache que escribe ovpn-acl-poller (que ya consulta
    la interfaz de gestión cada 2s para el propio cortafuegos) — así el
    panel no necesita abrir su propia conexión al puerto 7505 en el caso
    normal: cero tráfico/ruido adicional hacia OpenVPN, y se evita también
    el riesgo de contención con esa interfaz (solo admite un cliente a la
    vez — bug real encontrado en producción cuando se probó con una
    conexión persistente ahí). Solo si la cache no existe o está
    desactualizada (por ejemplo, el poller no está corriendo) se cae a la
    consulta en vivo de siempre."""
    try:
        st = os.stat(_CONNECTED_CACHE_FILE)
        if time.time() - st.st_mtime <= _CONNECTED_CACHE_MAX_AGE:
            with open(_CONNECTED_CACHE_FILE) as f:
                return set(json.load(f).keys())
    except (OSError, ValueError):
        pass

    import socket as _socket
    connected = set()
    try:
        s = _socket.create_connection(('127.0.0.1', 7505), timeout=3)
        s.recv(1024)
        s.sendall(b'status 2\n')
        data = b''
        while True:
            chunk = s.recv(4096)
            if not chunk:
                break
            data += chunk
            if b'\nEND' in data:
                break
        s.sendall(b'quit\n')
        s.close()
        for line in data.decode(errors='ignore').splitlines():
            if line.startswith('CLIENT_LIST,'):
                parts = line.split(',')
                if len(parts) > 1 and parts[1]:
                    connected.add(parts[1])
        return connected
    except Exception:
        pass
    # Fallback: leer fichero de estado
    try:
        with open(STATUS_FILE) as f:
            in_list = False
            for line in f:
                line = line.strip()
                if line.startswith('Common Name,Real Address,'):
                    in_list = True
                    continue
                if line.startswith('ROUTING TABLE'):
                    break
                if in_list and line:
                    connected.add(line.split(',')[0])
    except FileNotFoundError:
        pass
    return connected


def get_blocked_clients():
    blocked = set()
    if not os.path.isdir(CCD_DIR):
        return blocked
    for fname in os.listdir(CCD_DIR):
        fpath = os.path.join(CCD_DIR, fname)
        if os.path.isfile(fpath):
            try:
                with open(fpath) as f:
                    if any(l.strip() == 'disable' for l in f):
                        blocked.add(fname)
            except Exception:
                pass
    return blocked


def get_maintenance_blocked_clients():
    """Clientes bloqueados específicamente por el modo mantenimiento (no bloqueos manuales)."""
    blocked = set()
    if not os.path.isdir(CCD_DIR):
        return blocked
    for fname in os.listdir(CCD_DIR):
        fpath = os.path.join(CCD_DIR, fname)
        if os.path.isfile(fpath):
            try:
                with open(fpath) as f:
                    marked = {l.strip() for l in f}
                if 'disable' in marked and '# maintenance-blocked' in marked:
                    blocked.add(fname)
            except Exception:
                pass
    return blocked


def block_client(name, via_maintenance=False):
    ccd_path = os.path.join(CCD_DIR, name)
    lines = []
    if os.path.exists(ccd_path):
        with open(ccd_path) as f:
            lines = f.readlines()
    # Si ya estaba bloqueado (manual o de mantenimiento), no tocamos el fichero:
    # así maintenance_on() no "roba" la autoría de un bloqueo manual existente.
    if not any(l.strip() == 'disable' for l in lines):
        lines.append('disable\n')
        if via_maintenance:
            lines.append('# maintenance-blocked\n')
        with open(ccd_path, 'w') as f:
            f.writelines(lines)
    mgmt_kill(name)


def unblock_client(name):
    ccd_path = os.path.join(CCD_DIR, name)
    if not os.path.exists(ccd_path):
        return
    with open(ccd_path) as f:
        lines = f.readlines()
    lines = [l for l in lines if l.strip() not in ('disable', '# maintenance-blocked')]
    if lines:
        with open(ccd_path, 'w') as f:
            f.writelines(lines)
    else:
        os.remove(ccd_path)


def mgmt_kill(name):
    import socket as _socket
    try:
        s = _socket.create_connection(('127.0.0.1', 7505), timeout=3)
        s.recv(1024)

        # Obtener client-id para enviar HALT explícito al cliente
        s.sendall(b'status 2\n')
        data = b''
        while True:
            chunk = s.recv(4096)
            if not chunk:
                break
            data += chunk
            if b'\nEND' in data:
                break

        # Determinar índice de Client ID leyendo el HEADER dinámicamente
        client_id = None
        cid_idx = None
        for line in data.decode(errors='ignore').splitlines():
            if line.startswith('HEADER,CLIENT_LIST,'):
                cols = line.split(',')
                # cols[0]=HEADER, cols[1]=CLIENT_LIST, cols[2]=Common Name...
                # En DATA line no hay HEADER → offset -1
                try:
                    cid_idx = cols.index('Client ID') - 1
                except ValueError:
                    pass
            elif line.startswith('CLIENT_LIST,') and cid_idx is not None:
                parts = line.split(',')
                if len(parts) > cid_idx and parts[1] == name:
                    client_id = parts[cid_idx]
                    break

        if client_id:
            # Envía señal HALT: el cliente recibe aviso y se desconecta limpiamente
            s.sendall(f'client-kill {client_id} HALT\n'.encode())
        else:
            # Fallback: corte abrupto
            s.sendall(f'kill {name}\n'.encode())

        resp = s.recv(1024).decode(errors='ignore')
        s.sendall(b'quit\n')
        s.close()
        if 'SUCCESS' in resp or 'ERROR' not in resp:
            return 'ok'
        return 'not_connected'
    except ConnectionRefusedError:
        return 'no_mgmt'
    except Exception:
        return 'error'


def parse_index():
    clients = []
    try:
        with open(INDEX_FILE) as f:
            for line in f:
                parts = line.strip().split('\t')
                if len(parts) < 6:
                    continue
                status     = parts[0]
                expiry_raw = parts[1]
                serial     = parts[3]
                subject    = parts[5]

                cn = next((p[3:] for p in subject.split('/') if p.startswith('CN=')), '')
                if not cn or cn == 'server':
                    continue

                try:
                    expiry        = datetime.strptime(expiry_raw, '%y%m%d%H%M%SZ')
                    exp_str       = expiry.strftime('%d-%m-%Y')
                    now           = datetime.now()
                    expired       = expiry < now
                    expiring_soon = (not expired) and (expiry - now).days <= 30
                except Exception:
                    exp_str       = expiry_raw
                    expired       = False
                    expiring_soon = False

                clients.append({
                    'name':         cn,
                    'status':       'revocado' if status == 'R' else 'activo',
                    'expiry':       exp_str,
                    'expired':      expired,
                    'expiring_soon': expiring_soon,
                    'serial':       serial,
                })
    except FileNotFoundError:
        pass
    return clients


def load_meta():
    try:
        with open(META_FILE) as f:
            return json.load(f)
    except Exception:
        return {}


def save_meta(meta):
    with open(META_FILE, 'w') as f:
        json.dump(meta, f, indent=2)
    # Contiene emails de clientes: no debe ser legible por cualquier usuario
    # del sistema. Se refuerza en cada guardado (no depende del umask).
    try:
        os.chmod(META_FILE, 0o640)
    except OSError:
        pass
    # ovpn-acl-poller (usuario dedicado, ver postinst) necesita leer los
    # rangos de acceso de aqui para mantener sincronizada la cadena
    # OVPN_ACL. Se refuerza en cada guardado por si el fichero llegara a
    # recrearse alguna vez con el grupo por defecto.
    try:
        os.chown(META_FILE, -1, grp.getgrnam('ovpn-acl').gr_gid)
    except (OSError, KeyError):
        pass


def run_cmd(cmd, extra_env=None):
    env = os.environ.copy()
    if extra_env:
        env.update(extra_env)
    return subprocess.run(cmd, capture_output=True, text=True, env=env)


def _send_attachment(path, filename):
    """send_file wrapper compatible con Flask 1.x (Debian 10/11) y Flask 2.x (Debian 12)."""
    if _FLASK_V2:
        return send_file(path, as_attachment=True, download_name=filename)
    return send_file(path, as_attachment=True, attachment_filename=filename)


def valid_name(name):
    return bool(name and re.match(r'^[a-zA-Z0-9_-]+$', name))


def valid_email(email):
    # Sin espacios, comillas ni < > — evita que el email rompa el contexto
    # JS/HTML donde se interpola (ver onclick de Renovar en index.html)
    return bool(email and re.match(r'^[^\s<>\'"]+@[^\s<>\'"]+\.[^\s<>\'"]+$', email))


# ---------------------------------------------------------------------------
# Usuarios del panel (cuentas Linux sin shell, solo para entrar al manager)
# ---------------------------------------------------------------------------
PANEL_GROUP = 'ovpn-panel'
_PANEL_USERNAME_RE = re.compile(r'^[a-z][a-z0-9_-]{2,31}$')


def valid_panel_username(name):
    return bool(name and _PANEL_USERNAME_RE.match(name))


def ensure_panel_group():
    if run_cmd(['getent', 'group', PANEL_GROUP]).returncode != 0:
        run_cmd(['groupadd', PANEL_GROUP])


def list_panel_users():
    try:
        return sorted(grp.getgrnam(PANEL_GROUP).gr_mem)
    except KeyError:
        return []


def create_panel_user(username, password):
    ensure_panel_group()
    result = run_cmd(['adduser', '--disabled-password', '--gecos', '',
                      '--shell', '/usr/sbin/nologin', '--no-create-home', username])
    if result.returncode != 0:
        return False, result.stderr
    run_cmd(['usermod', '-aG', PANEL_GROUP, username])
    proc = subprocess.run(['chpasswd'], input=f'{username}:{password}',
                          text=True, capture_output=True)
    if proc.returncode != 0:
        return False, proc.stderr
    return True, ''


def delete_panel_user(username):
    # Solo se pueden borrar por aquí cuentas creadas como usuarios de panel
    # (miembros de PANEL_GROUP) — nunca cuentas normales del sistema.
    if username not in list_panel_users():
        return False, t('flash.not_panel_user')
    result = run_cmd(['deluser', username])
    if result.returncode != 0:
        return False, result.stderr
    return True, ''


def reset_panel_user_password(username, password):
    # Igual que al borrar: solo se puede tocar por aquí una cuenta que sea
    # de verdad un usuario de panel (miembro de PANEL_GROUP), nunca una
    # cuenta normal del sistema — no es una ruta genérica de "passwd".
    if username not in list_panel_users():
        return False, t('flash.not_panel_user')
    proc = subprocess.run(['chpasswd'], input=f'{username}:{password}',
                          text=True, capture_output=True)
    if proc.returncode != 0:
        return False, proc.stderr
    return True, ''


def clean_easyrsa_artifacts(name):
    for path in [f'{KEY_DIR}/private/{name}.key',
                 f'{KEY_DIR}/reqs/{name}.req',
                 f'{KEY_DIR}/issued/{name}.crt',
                 f'{KEY_DIR}/{name}.ovpn']:
        try:
            os.remove(path)
        except FileNotFoundError:
            pass


def parse_cidrs(raw):
    cidrs = []
    for token in re.split(r'[\s,;]+', raw or ''):
        token = token.strip()
        if not token:
            continue
        try:
            net = ipaddress.ip_network(token, strict=False)
            cidrs.append(str(net))
        except ValueError:
            pass
    return cidrs


SERVER_CONF_FILE = '/etc/openvpn/server.conf'
IPP_FILE = '/var/lib/openvpn/server.ipp'


def get_dynamic_pool_network():
    """Parsea la linea 'server x.x.x.x m.m.m.m' de server.conf."""
    try:
        with open(SERVER_CONF_FILE) as f:
            conf = f.read()
    except FileNotFoundError:
        return None
    m = re.search(r'^server\s+(\S+)\s+(\S+)', conf, re.M)
    if not m:
        return None
    try:
        return ipaddress.ip_network(f'{m.group(1)}/{m.group(2)}', strict=False)
    except ValueError:
        return None


def get_static_pool_network():
    """Rango contiguo al pool dinamico, reservado para IP fija (un bloque
    /30 por cliente, misma convencion net30 que ya usa el pool dinamico).
    Se calcula a partir del "server" real de esta maquina, nunca a ciegas,
    para que cada instalacion use el rango que de verdad le corresponde."""
    dyn = get_dynamic_pool_network()
    if dyn is None:
        return None
    try:
        return ipaddress.ip_network(
            (int(dyn.network_address) + dyn.num_addresses, dyn.prefixlen), strict=False)
    except ValueError:
        return None


def _used_static_blocks(meta):
    static_net = get_static_pool_network()
    used = set()
    if static_net is None:
        return used
    for data in meta.values():
        ip = data.get('static_ip')
        if not ip:
            continue
        try:
            addr = ipaddress.ip_address(ip)
        except ValueError:
            continue
        if addr in static_net:
            used.add((int(addr) - int(static_net.network_address)) // 4)
    return used


def allocate_static_ip(name, meta):
    """Asigna un bloque /30 libre del rango de IP fija a 'name'. Devuelve
    (client_ip, peer_ip) o None si no hay rango calculable o esta agotado.
    No modifica meta ni el CCD — eso lo hace el llamador."""
    static_net = get_static_pool_network()
    if static_net is None:
        return None
    used = _used_static_blocks(meta)
    total_blocks = static_net.num_addresses // 4
    # El primer bloque se deja libre, igual que el pool dinamico reserva
    # el suyo para el propio extremo del servidor.
    for block in range(1, total_blocks):
        if block in used:
            continue
        base = int(static_net.network_address) + block * 4
        peer_ip = str(ipaddress.ip_address(base + 1))
        client_ip = str(ipaddress.ip_address(base + 2))
        return client_ip, peer_ip
    return None


def resolve_manual_static_ip(ip_str, meta):
    """Valida una IP fija elegida a mano por el admin dentro del rango de
    IP fija de este servidor. Devuelve ((client_ip, peer_ip), None) si es
    valida y esta libre, o (None, mensaje_error) en caso contrario."""
    static_net = get_static_pool_network()
    if static_net is None:
        return None, t('flash.staticip_no_range')
    try:
        addr = ipaddress.ip_address((ip_str or '').strip())
    except ValueError:
        return None, t('flash.staticip_invalid_ip', ip=ip_str)
    if addr not in static_net:
        return None, t('flash.staticip_out_of_range', ip=addr, net=static_net)
    offset = int(addr) - int(static_net.network_address)
    block = offset // 4
    if block == 0:
        return None, t('flash.staticip_reserved_block')
    if offset % 4 != 2:
        suggested = ipaddress.ip_address(int(static_net.network_address) + block * 4 + 2)
        return None, t('flash.staticip_invalid_offset', ip=addr, suggested=suggested)
    if block in _used_static_blocks(meta):
        return None, t('flash.staticip_ip_taken', ip=addr)
    peer_ip = str(ipaddress.ip_address(int(addr) - 1))
    return (str(addr), peer_ip), None


def clean_ipp_entry(name):
    """Borra la entrada persistida del pool dinamico para 'name' (si la
    hay) al pasarlo a IP fija — si no, esa direccion del pool dinamico
    queda reservada para siempre a un nombre que ya no la va a usar via
    pool. No hace falta reiniciar OpenVPN: se recoge en el siguiente
    arranque natural del servicio (ifconfig-push ya tiene prioridad sobre
    el pool para ese cliente mientras tanto)."""
    try:
        with open(IPP_FILE) as f:
            lines = f.readlines()
    except FileNotFoundError:
        return
    kept = [l for l in lines if not l.startswith(f'{name},')]
    if len(kept) != len(lines):
        with open(IPP_FILE, 'w') as f:
            f.writelines(kept)


_CCD_PRESERVE_STATIC_IP = object()  # centinela: no tocar la IP fija existente


def apply_ccd(name, cidrs, static_ip=_CCD_PRESERVE_STATIC_IP):
    """static_ip:
      - omitido (por defecto): preserva cualquier "ifconfig-push" ya
        presente en el CCD — para que renovar un cliente o cambiarle el
        rango no le borre la IP fija sin querer.
      - None explicito: quita la IP fija (no preserva, no escribe nada).
      - (client_ip, peer_ip): fija esa IP, sustituyendo cualquier otra
        que hubiera antes."""
    ccd_path = os.path.join(CCD_DIR, name)
    # Preservar un bloqueo existente (manual o de mantenimiento) y, salvo
    # que se pida explicitamente lo contrario, la asignacion de IP fija
    # que ya hubiera: renovar o recrear un cliente no debe desbloquearlo
    # ni quitarle la IP fija en silencio.
    preserved = []
    if os.path.exists(ccd_path):
        with open(ccd_path) as f:
            for l in f:
                s = l.rstrip('\n')
                if s.strip() in ('disable', '# maintenance-blocked'):
                    preserved.append(s)
                elif static_ip is _CCD_PRESERVE_STATIC_IP and s.strip().startswith('ifconfig-push '):
                    preserved.append(s)
    lines = list(preserved)
    if static_ip and static_ip is not _CCD_PRESERVE_STATIC_IP:
        client_ip, peer_ip = static_ip
        lines.append(f'ifconfig-push {client_ip} {peer_ip}')
    if cidrs:
        # Cancelar la ruta general que el servidor empuja a todos los
        # clientes (server.conf) y dejar solo los rangos autorizados para
        # este cliente. Nota: esto es una restricción a nivel de rutas del
        # sistema operativo del cliente, no un cortafuegos — un cliente que
        # añada rutas manuales igualmente sería reenviado por el servidor.
        lines.append('push-remove "route"')
        for cidr in cidrs:
            net = ipaddress.ip_network(cidr, strict=False)
            lines.append(f'push "route {net.network_address} {net.netmask}"')
    if lines:
        with open(ccd_path, 'w') as f:
            f.write('\n'.join(lines) + '\n')
    else:
        try:
            os.remove(ccd_path)
        except FileNotFoundError:
            pass


@contextlib.contextmanager
def _temp_passfile(password: str):
    """Write password to a temp file and delete it on exit."""
    fd, path = tempfile.mkstemp(prefix='.ovpnpass-', dir='/tmp')
    try:
        os.write(fd, password.encode())
        os.close(fd)
        os.chmod(path, 0o600)
        yield path
    finally:
        try:
            os.remove(path)
        except FileNotFoundError:
            pass


def build_create_cmd(name, email, password):
    cmd = ['/usr/local/bin/openvpn-addclient', name, email]
    extra_env = {}
    if password:
        cmd.append('--pass')
        # password written to temp file — never exposed in env listing
        # caller must use _temp_passfile context and call this inside it
        extra_env['_PASSFILE_PENDING'] = password   # marker; replaced below
    return cmd, extra_env

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user' in session:
        return redirect(url_for('index'), 303)
    error = None
    if request.method == 'POST':
        ip   = _client_ip()
        user = _sanitize_log_field(request.form.get('username', '').strip())
        pwd  = request.form.get('password', '')

        if _is_locked(ip):
            logger.warning('Login blocked (brute-force) ip=%s user=%s', ip, user)
            error = t('login.locked')
        elif user and pam_auth(user, pwd):
            session.clear()
            session['user'] = user
            session['_sid'] = secrets.token_hex(16)   # server-side revocation token
            logger.info('Login OK user=%s ip=%s', user, ip)
            return redirect(url_for('index'), 303)
        else:
            _record_failure(ip)
            time.sleep(2)   # slow down brute force
            logger.warning('Login FAIL user=%s ip=%s', user, ip)
            error = t('login.fail')
    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    user = session.get('user', '?')
    sid  = _session_id()
    if sid:
        _revoke_session(sid)   # invalidar server-side antes de limpiar
    session.clear()
    logger.info('Logout user=%s ip=%s', user, _client_ip())
    return redirect(url_for('login'), 303)


@app.route('/')
@login_required
def index():
    clients        = parse_index()
    meta           = load_meta()
    default_months = get_default_months()
    connected      = get_connected_clients()
    blocked        = get_blocked_clients()
    for c in clients:
        m = meta.get(c['name'], {})
        c['email']              = m.get('email', '')
        c['password_protected'] = m.get('password_protected', False)
        c['ip_ranges']          = m.get('ip_ranges', [])
        c['static_ip']          = m.get('static_ip', '')
        c['connected']          = c['name'] in connected
        c['blocked']            = c['name'] in blocked
    # Activos primero, expirados después, revocados al final
    order = {'activo': 0, 'revocado': 2}
    clients.sort(key=lambda c: (order.get(c['status'], 1), c['expired'], c['name']))
    maintenance_blocked_count = len(get_maintenance_blocked_clients())
    maintenance = bool(maintenance_blocked_count)
    return render_template('index.html',
                           clients=clients,
                           default_months=default_months,
                           maintenance=maintenance,
                           maintenance_blocked_count=maintenance_blocked_count,
                           user=session['user'])


@app.route('/api/connected')
@login_required
def api_connected():
    """Lista de clientes conectados ahora mismo, en JSON — para que
    "Clientes VPN" refresque solo la columna de conexión por JS (sin
    recargar la página entera). Reutiliza get_connected_clients(), que ya
    lee de la cache del poller antes que abrir su propia conexión a
    OpenVPN, así que sondear este endpoint a menudo no añade tráfico
    nuevo hacia la interfaz de gestión."""
    return jsonify({'connected': sorted(get_connected_clients())})


GEO_FILE = '/var/lib/ovpn-acl/clients_geo.json'


def load_geo():
    """{name: {'history': [{'ip','ts','lat'?,'lon'?,'city'?,'country'?,
    'country_code'?}, ...]}}, más reciente primero, como mucho 5 IPs
    *distintas* por cliente (se deduplica y refresca en el poller, no
    aquí) — lo escribe ovpn-acl-poller.service en el instante en que cada
    cliente pasa a "conectado"; el panel solo lee. Una entrada sin lat/lon
    = ip privada, o la base de datos GeoIP aún no se ha descargado, o esa
    IP no tiene registro en ella."""
    try:
        with open(GEO_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


@app.route('/map')
@login_required
def map_page():
    clients = parse_index()
    geo = load_geo()
    clients = [c for c in clients if c['status'] != 'revocado']

    history_by_client = []
    for c in clients:
        hist = geo.get(c['name'], {}).get('history', [])
        if hist:
            history_by_client.append({'name': c['name'], 'history': hist})
        # El mapa solo pinta la ubicación MÁS RECIENTE de cada cliente — el
        # historial completo (hasta 5 IPs distintas) se muestra aparte, en
        # su propia tabla, no como varios pines por cliente.
        if hist:
            c.update(hist[0])

    history_by_client.sort(key=lambda h: h['history'][0].get('ts', 0), reverse=True)

    with_location = [c for c in clients if 'lat' in c]
    without_location = [c for c in clients if 'lat' not in c]
    with_location.sort(key=lambda c: c.get('ts', 0), reverse=True)
    without_location.sort(key=lambda c: c['name'])
    geoip_db_available = os.path.exists('/var/lib/openvpn-manager/dbip-city-lite.mmdb')
    return render_template('map.html',
                           with_location=with_location,
                           without_location=without_location,
                           history_by_client=history_by_client,
                           geoip_db_available=geoip_db_available,
                           user=session.get('user'))


@app.route('/create', methods=['POST'])
@login_required
def create():
    name      = request.form.get('name', '').strip()
    email     = request.form.get('email', '').strip()
    months    = request.form.get('months', '').strip()
    password  = request.form.get('key_password', '').strip()
    raw_cidrs = request.form.get('ip_ranges', '').strip()

    if not valid_name(name):
        flash(t('flash.invalid_name'), 'error')
        return redirect(url_for('index'), 303)
    if not valid_email(email):
        flash(t('flash.invalid_email'), 'error')
        return redirect(url_for('index'), 303)
    try:
        months = int(months)
        assert 1 <= months <= 1200
    except Exception:
        flash(t('flash.invalid_months'), 'error')
        return redirect(url_for('index'), 303)

    cidrs = parse_cidrs(raw_cidrs)
    days  = months_to_days(months)

    cmd, extra_env = build_create_cmd(name, email, password)
    extra_env['EASYRSA_CERT_EXPIRE'] = str(days)

    if password:
        with _temp_passfile(password) as pfile:
            extra_env['EASYRSA_PASSOUT'] = f'file:{pfile}'
            extra_env['EASYRSA_PASSIN']  = f'file:{pfile}'
            extra_env.pop('_PASSFILE_PENDING', None)
            result = run_cmd(cmd, extra_env=extra_env)
    else:
        result = run_cmd(cmd, extra_env=extra_env)

    if result.returncode != 0:
        logger.error('create failed name=%s stderr=%s', name, result.stderr)
        flash(t('flash.create_failed'), 'error')
        return redirect(url_for('index'), 303)

    apply_ccd(name, cidrs)

    meta = load_meta()
    meta[name] = {
        'email':              email,
        'password_protected': bool(password),
        'ip_ranges':          cidrs,
    }
    save_meta(meta)

    logger.info('create OK name=%s user=%s ip=%s months=%d', name, session['user'], _client_ip(), months)
    msg = t('flash.create_ok', name=name, months=months, plural=('' if months == 1 else 's' if g.lang == 'en' else 'es'))
    if password:
        msg += t('flash.create_ok_pass')
    if cidrs:
        msg += t('flash.create_ok_ranges', ranges=', '.join(cidrs))
    flash(msg + '.', 'success')
    return redirect(url_for('index'), 303)


@app.route('/block/<name>', methods=['POST'])
@login_required
def block(name):
    if not valid_name(name):
        flash(t('flash.invalid_client_name'), 'error')
        return redirect(url_for('index'), 303)
    block_client(name)
    logger.info('block OK name=%s user=%s ip=%s', name, session['user'], _client_ip())
    flash(t('flash.block_ok', name=name), 'success')
    return redirect(url_for('index'), 303)


@app.route('/unblock/<name>', methods=['POST'])
@login_required
def unblock(name):
    if not valid_name(name):
        flash(t('flash.invalid_client_name'), 'error')
        return redirect(url_for('index'), 303)
    unblock_client(name)
    logger.info('unblock OK name=%s user=%s ip=%s', name, session['user'], _client_ip())
    flash(t('flash.unblock_ok', name=name), 'success')
    return redirect(url_for('index'), 303)


@app.route('/staticip')
@login_required
def staticip_page():
    clients = parse_index()
    meta = load_meta()
    static_net = get_static_pool_network()
    for c in clients:
        m = meta.get(c['name'], {})
        c['static_ip']        = m.get('static_ip', '')
        c['static_ip_reason'] = m.get('static_ip_reason', '')
    # Solo clientes activos tiene sentido que aparezcan aquí (uno revocado
    # no va a volver a conectarse con ninguna IP).
    clients = [c for c in clients if c['status'] == 'activo']
    clients.sort(key=lambda c: (not c['static_ip'], c['name']))
    assigned_count = sum(1 for c in clients if c['static_ip'])
    return render_template('staticip.html',
                           clients=clients,
                           static_net=str(static_net) if static_net else None,
                           assigned_count=assigned_count,
                           user=session.get('user'))


@app.route('/staticip/assign/<name>', methods=['POST'])
@login_required
def staticip_assign(name):
    if not valid_name(name):
        flash(t('flash.invalid_client_name'), 'error')
        return redirect(url_for('staticip_page'), 303)

    reason = request.form.get('reason', '').strip()
    mode   = request.form.get('mode', 'auto')
    if not reason:
        flash(t('flash.staticip_reason_required'), 'error')
        return redirect(url_for('staticip_page'), 303)
    if len(reason) > 200:
        reason = reason[:200]

    meta = load_meta()
    current = meta.get(name, {})
    if current.get('static_ip'):
        flash(t('flash.staticip_already_assigned', name=name), 'error')
        return redirect(url_for('staticip_page'), 303)

    if mode == 'manual':
        result, err = resolve_manual_static_ip(request.form.get('manual_ip', ''), meta)
        if err:
            flash(err, 'error')
            return redirect(url_for('staticip_page'), 303)
    else:
        result = allocate_static_ip(name, meta)
        if result is None:
            flash(t('flash.staticip_auto_failed'), 'error')
            return redirect(url_for('staticip_page'), 303)
    client_ip, peer_ip = result

    meta.setdefault(name, {})
    meta[name]['static_ip']        = client_ip
    meta[name]['static_ip_reason'] = reason
    save_meta(meta)
    clean_ipp_entry(name)
    apply_ccd(name, meta[name].get('ip_ranges', []), static_ip=(client_ip, peer_ip))

    logger.info('staticip assign OK name=%s ip=%s mode=%s reason=%s user=%s ip_addr=%s',
                name, client_ip, mode, _sanitize_log_field(reason), session['user'], _client_ip())
    flash(t('flash.staticip_assigned', name=name, ip=client_ip), 'success')
    return redirect(url_for('staticip_page'), 303)


@app.route('/staticip/release/<name>', methods=['POST'])
@login_required
def staticip_release(name):
    if not valid_name(name):
        flash(t('flash.invalid_client_name'), 'error')
        return redirect(url_for('staticip_page'), 303)

    meta = load_meta()
    if not meta.get(name, {}).get('static_ip'):
        flash(t('flash.staticip_not_assigned', name=name), 'error')
        return redirect(url_for('staticip_page'), 303)

    meta[name].pop('static_ip', None)
    meta[name].pop('static_ip_reason', None)
    save_meta(meta)
    apply_ccd(name, meta[name].get('ip_ranges', []), static_ip=None)

    logger.info('staticip release OK name=%s user=%s ip=%s', name, session['user'], _client_ip())
    flash(t('flash.staticip_released', name=name), 'success')
    return redirect(url_for('staticip_page'), 303)


@app.route('/maintenance/on', methods=['POST'])
@login_required
def maintenance_on():
    protected = set(request.form.getlist('protected'))
    clients   = parse_index()
    blocked   = 0
    for c in clients:
        if c['status'] == 'revocado':
            continue
        if c['name'] not in protected:
            block_client(c['name'], via_maintenance=True)
            blocked += 1
    logger.info('maintenance ON protected=%s blocked=%d user=%s ip=%s',
                list(protected), blocked, session['user'], _client_ip())
    flash(t('flash.maintenance_on_ok', n=blocked), 'success')
    return redirect(url_for('index'), 303)


@app.route('/maintenance/off', methods=['POST'])
@login_required
def maintenance_off():
    # Solo desbloquea lo que bloqueó el propio modo mantenimiento — los
    # bloqueos manuales (/block/<name>) se quedan como estaban.
    blocked = get_maintenance_blocked_clients()
    for name in blocked:
        unblock_client(name)
    logger.info('maintenance OFF unblocked=%d user=%s ip=%s',
                len(blocked), session['user'], _client_ip())
    flash(t('flash.maintenance_off_ok', n=len(blocked)), 'success')
    return redirect(url_for('index'), 303)


@app.route('/disconnect/<name>', methods=['POST'])
@login_required
def disconnect(name):
    if not valid_name(name):
        flash(t('flash.invalid_client_name'), 'error')
        return redirect(url_for('index'), 303)
    result = mgmt_kill(name)
    if result == 'ok':
        logger.info('disconnect OK name=%s user=%s ip=%s', name, session['user'], _client_ip())
        flash(t('flash.disconnect_ok', name=name), 'success')
    elif result == 'not_connected':
        flash(t('flash.not_connected', name=name), 'info')
    elif result == 'no_mgmt':
        flash(t('flash.mgmt_unavailable'), 'error')
    else:
        flash(t('flash.disconnect_error', name=name), 'error')
    return redirect(url_for('index'), 303)


@app.route('/revoke/<name>', methods=['POST'])
@login_required
def revoke(name):
    if not valid_name(name):
        flash(t('flash.invalid_client_name'), 'error')
        return redirect(url_for('index'), 303)

    result = run_cmd(['/usr/local/bin/openvpn-revoke', name],
                     extra_env={'EASYRSA_BATCH': '1'})
    if result.returncode != 0:
        logger.error('revoke failed name=%s stderr=%s', name, result.stderr)
        flash(t('flash.revoke_failed', name=name), 'error')
    else:
        logger.info('revoke OK name=%s user=%s ip=%s', name, session['user'], _client_ip())
        flash(t('flash.revoke_ok', name=name), 'success')
    return redirect(url_for('index'), 303)


@app.route('/renew/<name>', methods=['POST'])
@login_required
def renew(name):
    if not valid_name(name):
        flash(t('flash.invalid_client_name'), 'error')
        return redirect(url_for('index'), 303)

    months    = request.form.get('months', '').strip()
    password  = request.form.get('key_password', '').strip()
    raw_cidrs = request.form.get('ip_ranges', '').strip()

    try:
        months = int(months)
        assert 1 <= months <= 1200
    except Exception:
        flash(t('flash.invalid_months'), 'error')
        return redirect(url_for('index'), 303)

    meta  = load_meta()
    email = meta.get(name, {}).get('email', '') or request.form.get('email', '').strip()
    if not valid_email(email):
        flash(t('flash.renew_email_required', name=name), 'error')
        return redirect(url_for('index'), 303)

    cidrs = parse_cidrs(raw_cidrs) if raw_cidrs else meta.get(name, {}).get('ip_ranges', [])
    days  = months_to_days(months)

    # Revocar solo si está activo. Un CN puede aparecer varias veces en
    # index.txt (revocaciones/renovaciones anteriores) — hay que buscar
    # específicamente la entrada activa, no la primera del archivo (que
    # bien podría ser una ya revocada), o se salta la revocación y queda
    # un certificado activo duplicado.
    clients = parse_index()
    current = next((c for c in clients if c['name'] == name and c['status'] == 'activo'), None)
    if current:
        result = run_cmd(['/usr/local/bin/openvpn-revoke', name],
                         extra_env={'EASYRSA_BATCH': '1'})
        if result.returncode != 0:
            logger.error('renew/revoke failed name=%s stderr=%s', name, result.stderr)
            flash(t('flash.renew_revoke_failed'), 'error')
            return redirect(url_for('index'), 303)

    clean_easyrsa_artifacts(name)

    cmd, extra_env = build_create_cmd(name, email, password)
    extra_env['EASYRSA_CERT_EXPIRE'] = str(days)

    if password:
        with _temp_passfile(password) as pfile:
            extra_env['EASYRSA_PASSOUT'] = f'file:{pfile}'
            extra_env['EASYRSA_PASSIN']  = f'file:{pfile}'
            extra_env.pop('_PASSFILE_PENDING', None)
            result = run_cmd(cmd, extra_env=extra_env)
    else:
        result = run_cmd(cmd, extra_env=extra_env)

    if result.returncode != 0:
        logger.error('renew/reissue failed name=%s stderr=%s', name, result.stderr)
        flash(t('flash.renew_reissue_failed'), 'error')
        return redirect(url_for('index'), 303)

    apply_ccd(name, cidrs)

    # Renovar no debe borrar en silencio la IP fija que ya tuviera el
    # cliente: apply_ccd() de arriba ya preserva el "ifconfig-push" en el
    # CCD (sin pasarle static_ip usa el centinela por defecto), pero
    # reconstruir meta[name] desde cero SIN copiar estos campos hacia el
    # nuevo dict los perdía igualmente en clients_meta.json — desajuste
    # real encontrado en producción: el CCD seguía con la IP fija pero el
    # panel la mostraba como "sin asignar", y el asignador de bloques
    # habría dado ese bloque como libre para otro cliente.
    old_static_ip     = meta.get(name, {}).get('static_ip')
    old_static_reason = meta.get(name, {}).get('static_ip_reason')

    meta[name] = {
        'email':              email,
        'password_protected': bool(password),
        'ip_ranges':          cidrs,
    }
    if old_static_ip:
        meta[name]['static_ip'] = old_static_ip
        if old_static_reason:
            meta[name]['static_ip_reason'] = old_static_reason
    save_meta(meta)

    logger.info('renew OK name=%s user=%s ip=%s months=%d', name, session['user'], _client_ip(), months)
    flash(t('flash.renew_ok', name=name, months=months, plural=('' if months == 1 else 's' if g.lang == 'en' else 'es')), 'success')
    return redirect(url_for('index'), 303)


@app.route('/access-ranges')
@login_required
def access_ranges_page():
    clients = parse_index()
    meta = load_meta()
    for c in clients:
        m = meta.get(c['name'], {})
        c['ip_ranges'] = m.get('ip_ranges', [])
        c['static_ip'] = m.get('static_ip', '')
    # Solo clientes activos tiene sentido que aparezcan aquí (uno revocado
    # no va a volver a conectarse, así que no hay nada que restringir).
    clients = [c for c in clients if c['status'] == 'activo']
    clients.sort(key=lambda c: (not c['ip_ranges'], c['name']))
    restricted_count = sum(1 for c in clients if c['ip_ranges'])
    return render_template('access_ranges.html',
                           clients=clients,
                           restricted_count=restricted_count,
                           user=session.get('user'))


@app.route('/access-ranges/update/<name>', methods=['POST'])
@login_required
def access_ranges_update(name):
    """Cambia los "Rangos de acceso" de un cliente SIN tocar su certificado
    ni su .ovpn: el certificado responde a "quien eres" (autenticacion), el
    rango a "a que puedes llegar" (autorizacion) — son cosas independientes
    y no hace falta revocar/reemitir solo por cambiar la segunda. Como el
    cortafuegos (OVPN_ACL) se construye siempre desde clients_meta.json y
    la IP real de la sesion, nunca desde el .ovpn, el cliente no necesita
    un .ovpn nuevo para que el cambio se aplique — solo reconectar."""
    if not valid_name(name):
        flash(t('flash.invalid_client_name'), 'error')
        return redirect(url_for('access_ranges_page'), 303)

    meta = load_meta()
    if name not in meta:
        flash(t('flash.client_not_found', name=name), 'error')
        return redirect(url_for('access_ranges_page'), 303)

    raw_cidrs = request.form.get('ip_ranges', '').strip()
    cidrs = parse_cidrs(raw_cidrs)

    meta[name]['ip_ranges'] = cidrs
    save_meta(meta)
    apply_ccd(name, cidrs)  # sin static_ip -> preserva la IP fija si la tuviera

    logger.info('access-ranges update OK name=%s ranges=%s user=%s ip=%s',
                name, ','.join(cidrs) if cidrs else '(sin restricción)', session['user'], _client_ip())
    if cidrs:
        flash(t('flash.ranges_updated', name=name, ranges=', '.join(cidrs)), 'success')
    else:
        flash(t('flash.ranges_removed', name=name), 'success')
    return redirect(url_for('access_ranges_page'), 303)


@app.route('/download/<name>')
@login_required
def download(name):
    if not valid_name(name):
        flash(t('flash.invalid_client_name'), 'error')
        return redirect(url_for('index'), 303)

    ovpn = f'{KEY_DIR}/{name}.ovpn'
    if not os.path.exists(ovpn):
        flash(t('flash.ovpn_not_found', name=name), 'error')
        return redirect(url_for('index'), 303)

    logger.info('download name=%s user=%s ip=%s', name, session['user'], _client_ip())
    return _send_attachment(ovpn, f'{name}.ovpn')


@app.route('/profiles/<path:subpath>')
@login_required
def serve_profile(subpath):
    base = '/var/www/openvpn/htdocs/profiles'
    full = os.path.realpath(os.path.join(base, subpath))
    # Comparación de límite real, no un simple prefijo de string (un directorio
    # hermano como "profiles-otra-cosa" también empezaría por "profiles").
    if full != base and not full.startswith(base + os.sep):
        return 'Acceso denegado', 403
    if not os.path.isfile(full):
        abort(404)
    return send_file(full)


LOG_GUI_FILE    = '/var/log/openvpn-gui.log'
LOG_OVPN_UNIT   = 'openvpn@server'
_LOG_LINE_LIMIT = 1000

_VPN_QUICK_FILTERS = {
    'events': lambda l: any(x in l for x in (
                  'Peer Connection Initiated', 'MULTI: LINK UP',
                  'peer connection initiated', 'multi: link up',
                  'SIGTERM', 'sigterm', 'Connection reset',
                  'client-instance exiting', 'connection reset',
                  'Inactivity timeout', 'inactivity timeout',
                  'SIGUSR1', 'sigusr1',
                  'client-instance restarting')),
}

_AUDIT_QUICK_FILTERS = {
    'events': lambda l: any(x in l for x in (
                  'Login', 'Logout', 'login', 'logout',
                  'create OK', 'revoke OK', 'renew OK', 'download',
                  'block OK', 'unblock OK', 'maintenance', 'disconnect OK',
                  'ERROR', 'WARNING')),
}


_JOURNAL_SCAN_MAX     = 500_000  # límite de líneas crudas a inspeccionar, por seguridad
_JOURNAL_SCAN_TIMEOUT = 8        # segundos, límite de tiempo total del escaneo


def _read_journal(n):
    """Lee las últimas n líneas REALES (no ruido "MANAGEMENT: ...") del
    journal de OpenVPN. La interfaz de gestión se consulta constantemente
    (el poller de rangos de acceso cada 2s, entre otros) y cada consulta
    genera varias líneas "MANAGEMENT: ..." en el journal del propio
    openvpn@server. Si se tomaran solo las últimas N líneas en crudo y se
    filtrara DESPUES, ese ruido puede dejar fuera los eventos reales
    (conexión/desconexión de un cliente) casi por completo — bug real
    encontrado: en la práctica más del 98% de las líneas del journal eran
    ruido de MANAGEMENT, así que las últimas N líneas en crudo podían no
    contener NINGÚN evento real. Por eso journalctl se lee en orden inverso
    (más reciente primero) y nos detenemos en cuanto reunimos N líneas
    reales, con un límite de líneas y de tiempo por seguridad para no
    escanear el journal entero si de verdad no hay tantos eventos.
    """
    collected = []
    start = time.monotonic()
    proc = None
    try:
        proc = subprocess.Popen(
            ['journalctl', '-u', LOG_OVPN_UNIT, '--no-pager', '-r', '--output=short'],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True,
        )
        scanned = 0
        for line in proc.stdout:
            scanned += 1
            if 'MANAGEMENT:' not in line:
                collected.append(line.rstrip('\n'))
                if len(collected) >= n:
                    break
            if scanned >= _JOURNAL_SCAN_MAX or (time.monotonic() - start) > _JOURNAL_SCAN_TIMEOUT:
                break
    except Exception:
        return []
    finally:
        if proc is not None:
            try:
                proc.stdout.close()
            except Exception:
                pass
            proc.terminate()
            try:
                proc.wait(timeout=2)
            except Exception:
                proc.kill()
    collected.reverse()
    return collected


def _read_gui_log(n):
    """Lee las últimas n líneas del log de auditoría del manager."""
    try:
        with open(LOG_GUI_FILE) as f:
            return [l.rstrip() for l in f.readlines()[-n:]]
    except Exception:
        return []


@app.route('/logs')
@login_required
def logs():
    try:
        n = min(max(int(request.args.get('n', 200)), 50), _LOG_LINE_LIMIT)
    except (ValueError, TypeError):
        n = 200
    tab         = request.args.get('tab', 'vpn')
    search      = request.args.get('q', '').strip().lower()
    quick_filter = request.args.get('f', '')

    # Leemos más líneas de las que mostramos cuando hay quick_filter o búsqueda
    # de texto activos, para tener suficiente material tras el filtrado
    fetch_n = min(n * 5, _LOG_LINE_LIMIT) if (quick_filter or search) else n

    vpn_lines   = _read_journal(fetch_n)
    audit_lines = _read_gui_log(fetch_n)

    # Aplicar quick filter
    if quick_filter and quick_filter in _VPN_QUICK_FILTERS:
        vpn_lines = [l for l in vpn_lines if _VPN_QUICK_FILTERS[quick_filter](l)]
    if quick_filter and quick_filter in _AUDIT_QUICK_FILTERS:
        audit_lines = [l for l in audit_lines if _AUDIT_QUICK_FILTERS[quick_filter](l)]

    # Aplicar búsqueda de texto libre
    if search:
        vpn_lines   = [l for l in vpn_lines   if search in l.lower()]
        audit_lines = [l for l in audit_lines if search in l.lower()]

    # Limitar al número pedido tras el filtrado
    vpn_lines   = vpn_lines[-n:]
    audit_lines = audit_lines[-n:]

    return render_template('logs.html',
                           vpn_lines=vpn_lines,
                           audit_lines=audit_lines,
                           n=n, tab=tab, search=search,
                           quick_filter=quick_filter,
                           user=session['user'])


@app.route('/help')
@login_required
def help_page():
    return render_template('help.html', user=session['user'])


@app.route('/admin/users')
@login_required
@root_required
def admin_users():
    return render_template('admin_users.html', users=list_panel_users(), user=session['user'])


@app.route('/admin/users/create', methods=['POST'])
@login_required
@root_required
def admin_users_create():
    username  = request.form.get('username', '').strip()
    password  = request.form.get('password', '')
    password2 = request.form.get('password2', '')

    if not valid_panel_username(username):
        flash(t('flash.invalid_panel_username'), 'error')
        return redirect(url_for('admin_users'), 303)

    try:
        pwd.getpwnam(username)
        flash(t('flash.panel_user_exists', name=username), 'error')
        return redirect(url_for('admin_users'), 303)
    except KeyError:
        pass

    if '\n' in password or '\r' in password:
        flash(t('flash.password_no_newlines'), 'error')
        return redirect(url_for('admin_users'), 303)
    if len(password) < 8:
        flash(t('flash.password_too_short'), 'error')
        return redirect(url_for('admin_users'), 303)
    if password != password2:
        flash(t('flash.passwords_mismatch'), 'error')
        return redirect(url_for('admin_users'), 303)

    ok, err = create_panel_user(username, password)
    if not ok:
        logger.error('admin create-user failed name=%s err=%s', username, err)
        flash(t('flash.panel_user_create_failed'), 'error')
        return redirect(url_for('admin_users'), 303)

    logger.info('admin create-user OK name=%s by=%s ip=%s', username, session['user'], _client_ip())
    flash(t('flash.panel_user_created', name=username), 'success')
    return redirect(url_for('admin_users'), 303)


@app.route('/admin/users/reset-password/<name>', methods=['POST'])
@login_required
@root_required
def admin_users_reset_password(name):
    """No existe forma segura de "ver" la contraseña de un usuario ya
    creado (se guarda como hash de un solo sentido en /etc/shadow, ni el
    propio sistema puede recuperarla) — esta es la alternativa estándar:
    asignarle una nueva."""
    if not valid_panel_username(name):
        flash(t('flash.invalid_panel_username_simple'), 'error')
        return redirect(url_for('admin_users'), 303)

    password  = request.form.get('password', '')
    password2 = request.form.get('password2', '')

    if '\n' in password or '\r' in password:
        flash(t('flash.password_no_newlines'), 'error')
        return redirect(url_for('admin_users'), 303)
    if len(password) < 8:
        flash(t('flash.password_too_short'), 'error')
        return redirect(url_for('admin_users'), 303)
    if password != password2:
        flash(t('flash.passwords_mismatch'), 'error')
        return redirect(url_for('admin_users'), 303)

    ok, err = reset_panel_user_password(name, password)
    if not ok:
        logger.error('admin reset-password failed name=%s err=%s', name, err)
        flash(t('flash.reset_password_failed', name=name, err=err or t('flash.check_logs')), 'error')
        return redirect(url_for('admin_users'), 303)

    logger.info('admin reset-password OK name=%s by=%s ip=%s', name, session['user'], _client_ip())
    flash(t('flash.reset_password_ok', name=name), 'success')
    return redirect(url_for('admin_users'), 303)


@app.route('/admin/users/delete/<name>', methods=['POST'])
@login_required
@root_required
def admin_users_delete(name):
    if not valid_panel_username(name):
        flash(t('flash.invalid_panel_username_simple'), 'error')
        return redirect(url_for('admin_users'), 303)

    ok, err = delete_panel_user(name)
    if not ok:
        logger.error('admin delete-user failed name=%s err=%s', name, err)
        flash(t('flash.delete_user_failed', name=name, err=err or t('flash.check_logs')), 'error')
        return redirect(url_for('admin_users'), 303)

    logger.info('admin delete-user OK name=%s by=%s ip=%s', name, session['user'], _client_ip())
    flash(t('flash.delete_user_ok', name=name), 'success')
    return redirect(url_for('admin_users'), 303)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=False)
