from datetime import datetime, timedelta


def _easyrsa_date(dt):
    # easy-rsa's index.txt date format: YYMMDDHHMMSSZ
    return dt.strftime('%y%m%d%H%M%SZ')


def test_parse_index_skips_server_entry_and_malformed_lines(app_module, fake_index):
    future = _easyrsa_date(datetime.now() + timedelta(days=400))
    fake_index([
        f'V\t{future}\t\t01\tunknown\t/CN=server',
        'this line has too few fields',
    ])
    assert app_module.parse_index() == []


def test_parse_index_active_vs_revoked(app_module, fake_index):
    future = _easyrsa_date(datetime.now() + timedelta(days=400))
    fake_index([
        f'V\t{future}\t\t01\tunknown\t/CN=alice',
        f'R\t{future}\t250101000000Z\t02\tunknown\t/CN=bob',
    ])
    clients = {c['name']: c for c in app_module.parse_index()}
    assert clients['alice']['status'] == 'activo'
    assert clients['bob']['status'] == 'revocado'


def test_parse_index_expiry_flags(app_module, fake_index):
    expired_date = _easyrsa_date(datetime.now() - timedelta(days=1))
    soon_date = _easyrsa_date(datetime.now() + timedelta(days=5))
    far_date = _easyrsa_date(datetime.now() + timedelta(days=400))
    fake_index([
        f'V\t{expired_date}\t\t01\tunknown\t/CN=expired-client',
        f'V\t{soon_date}\t\t02\tunknown\t/CN=expiring-client',
        f'V\t{far_date}\t\t03\tunknown\t/CN=healthy-client',
    ])
    clients = {c['name']: c for c in app_module.parse_index()}
    assert clients['expired-client']['expired'] is True
    assert clients['expiring-client']['expiring_soon'] is True
    assert clients['healthy-client']['expired'] is False
    assert clients['healthy-client']['expiring_soon'] is False


def test_parse_index_missing_file_returns_empty_list(app_module, tmp_path, monkeypatch):
    monkeypatch.setattr(app_module, 'INDEX_FILE', str(tmp_path / 'does-not-exist.txt'))
    assert app_module.parse_index() == []


def test_parse_index_cn_can_repeat_across_renewals(app_module, fake_index):
    """A client can appear more than once (revoked + renewed) -- callers
    must filter by status when they want 'the' client by name, never just
    take the first/last match (documented gotcha, see project memory)."""
    future = _easyrsa_date(datetime.now() + timedelta(days=400))
    fake_index([
        f'R\t{future}\t250101000000Z\t01\tunknown\t/CN=juan',
        f'V\t{future}\t\t02\tunknown\t/CN=juan',
    ])
    entries = [c for c in app_module.parse_index() if c['name'] == 'juan']
    assert len(entries) == 2
    assert {e['status'] for e in entries} == {'activo', 'revocado'}
