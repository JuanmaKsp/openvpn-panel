from conftest import login


def _fake_journal(n_total, event_positions):
    """n_total lineas 'reales' (ya sin MANAGEMENT:, como devuelve
    _read_journal), con eventos 'Peer Connection Initiated' solo en las
    posiciones indicadas (de mas antigua a mas reciente)."""
    lines = []
    for i in range(n_total):
        if i in event_positions:
            lines.append(f'Nov 04 12:00:{i:02d} ovpn-server[1]: Peer Connection Initiated with [AF_INET]1.2.3.{i}:1194')
        else:
            lines.append(f'Nov 04 12:00:{i:02d} ovpn-server[1]: VERIFY OK: depth=0, CN=cliente{i}')
    return lines


def test_quick_filter_finds_events_beyond_display_limit(client, app_module, monkeypatch):
    """Bug real reportado: con el filtro rapido 'eventos' puesto, subir n
    hacia _LOG_LINE_LIMIT no sacaba mas resultados, porque fetch_n (cuantas
    lineas reales se leen antes de filtrar) colapsaba a fetch_n == n en vez
    de mantener el margen n*5. Aqui los 3 eventos reales estan mas alla de
    las primeras 1000 lineas leidas con el bug, pero dentro de las 5000 que
    debe leer el fix."""
    fake_lines = _fake_journal(4000, event_positions={3990, 3995, 3999})
    monkeypatch.setattr(app_module, '_read_journal', lambda n: fake_lines[-n:])
    login(client, app_module, pam_ok=True, monkeypatch=monkeypatch)

    resp = client.get('/logs?tab=vpn&f=events&n=1000')
    html = resp.get_data(as_text=True)

    assert 'Peer Connection Initiated' in html


def test_fetch_margin_scales_past_display_limit(app_module):
    """La formula de fetch_n debe seguir dando margen (n*5) incluso cuando
    n se acerca al tope de visualizacion -- antes de la correccion,
    min(n*5, _LOG_LINE_LIMIT) colapsaba a fetch_n == n justo ahi."""
    n = app_module._LOG_LINE_LIMIT
    fetch_n = min(n * 5, app_module._LOG_FETCH_LIMIT)
    assert fetch_n > n


def test_raw_journal_mode_shows_management_noise(client, app_module, monkeypatch):
    """El boton 'Journal completo (sin filtrar)' debe mostrar las lineas
    MANAGEMENT: tal cual -- la vista normal (_read_journal) las descarta a
    proposito, pero para depurar un problema de conexion concreto ese
    ruido (hora exacta de cada sondeo) es justo lo que hace falta ver."""
    fake_raw = [
        'Nov 04 12:00:00 ovpn-server[1]: MANAGEMENT: Client connected from [AF_INET]127.0.0.1:7505',
        'Nov 04 12:00:00 ovpn-server[1]: MANAGEMENT: CMD \'status 2\'',
        'Nov 04 12:00:01 ovpn-server[1]: alfonso/1.2.3.4 VERIFY OK: depth=0, CN=alfonso',
    ]
    monkeypatch.setattr(app_module, '_read_journal_raw', lambda n: fake_raw)
    login(client, app_module, pam_ok=True, monkeypatch=monkeypatch)

    resp = client.get('/logs?tab=vpn&raw=1&n=200')
    html = resp.get_data(as_text=True)

    assert 'MANAGEMENT: Client connected' in html
    assert "CMD &#39;status 2&#39;" in html or "CMD 'status 2'" in html


def test_raw_journal_mode_only_applies_to_vpn_tab(client, app_module, monkeypatch):
    """raw=1 en la pestaña de auditoria no debe activar el modo crudo (no
    tiene sentido ahi: el log de auditoria del manager no tiene ruido
    MANAGEMENT que mostrar)."""
    called = []
    monkeypatch.setattr(app_module, '_read_journal_raw', lambda n: called.append(n) or [])
    login(client, app_module, pam_ok=True, monkeypatch=monkeypatch)

    client.get('/logs?tab=audit&raw=1&n=200')

    assert called == []


def test_history_tab_shows_permanent_connection_log(client, app_module, monkeypatch):
    """Bug real reportado: la pestaña 'Historial de conexiones' (el fichero
    permanente que escribe acl-poller.py, independiente de journald) nunca
    se conecto a ningun sitio del panel -- se construyo el backend
    (CONN_LOG_FILE) en acl-poller.py pero nadie en app.py lo leia."""
    fake_history = [
        '2026-11-04 20:04:16 CONNECT name=juan real_ip=80.58.0.33 vip=10.8.0.2',
        '2026-11-04 20:05:01 DISCONNECT name=juan real_ip=80.58.0.33 vip=10.8.0.2',
    ]
    monkeypatch.setattr(app_module, '_read_conn_log', lambda n: fake_history)
    login(client, app_module, pam_ok=True, monkeypatch=monkeypatch)

    resp = client.get('/logs?tab=history&n=200')
    html = resp.get_data(as_text=True)

    assert 'CONNECT name=juan' in html
    assert 'DISCONNECT name=juan' in html


def test_app_and_acl_poller_agree_on_the_connections_log_path(app_module, acl_poller_module):
    """app.py lee de LOG_CONN_FILE, acl-poller.py escribe en CONN_LOG_FILE --
    si alguna vez se desincronizan, la pestaña 'Historial de conexiones'
    se queda vacia en silencio (sin error visible) mientras el fichero
    real crece en otra ruta."""
    assert app_module.LOG_CONN_FILE == acl_poller_module.CONN_LOG_FILE
