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
