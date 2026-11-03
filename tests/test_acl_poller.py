import json
import time


def test_is_public_ip(acl_poller_module):
    m = acl_poller_module
    assert m.is_public_ip('185.44.17.160')
    assert not m.is_public_ip('192.168.1.1')
    assert not m.is_public_ip('10.8.0.2')
    assert not m.is_public_ip('127.0.0.1')
    assert not m.is_public_ip('169.254.1.1')
    assert not m.is_public_ip('not-an-ip')


def test_is_mobile_org_matches_known_mvno_names(acl_poller_module):
    m = acl_poller_module
    assert m.is_mobile_org('XFERA MOVILES S.A.')  # Yoigo's legal name
    assert m.is_mobile_org('ES-AIRENETWORKS-MOBILE')
    assert not m.is_mobile_org(None)
    assert not m.is_mobile_org('')


def test_is_mobile_org_does_not_flag_dual_use_telcos(acl_poller_module):
    """Documented, intentional limitation: large carriers register mobile
    and fixed traffic under the identical company name, so this heuristic
    can't tell them apart -- see help.map.body and the map's own legend.
    This test pins that known gap so a future change doesn't silently
    start over- or under-flagging without anyone noticing."""
    m = acl_poller_module
    assert not m.is_mobile_org('TELEFONICA DE ESPANA S.A.U.')
    assert not m.is_mobile_org('VODAFONE ESPANA S.A.U.')
    assert not m.is_mobile_org('ORANGE ESPAGNE S.A.U.')


def test_update_geo_for_new_connections_dedups_by_ip(acl_poller_module, tmp_path, monkeypatch):
    m = acl_poller_module
    geo_file = tmp_path / 'clients_geo.json'
    monkeypatch.setattr(m, 'GEO_FILE', str(geo_file))
    monkeypatch.setattr(m, 'geolocate', lambda ip: {'lat': 40.0, 'lon': -3.0, 'city': 'Madrid',
                                                      'country': 'Spain', 'country_code': 'ES'})
    monkeypatch.setattr(m, 'asn_lookup', lambda ip: None)

    connected = {'juan': {'vip': '10.8.0.2', 'real_ip': '80.58.0.33'}}
    m.update_geo_for_new_connections({'juan'}, connected)
    m.update_geo_for_new_connections({'juan'}, connected)  # reconnect from the same IP

    geo = json.loads(geo_file.read_text())
    history = geo['juan']['history']
    assert len(history) == 1  # same IP refreshed in place, not duplicated
    assert history[0]['ip'] == '80.58.0.33'


def test_update_geo_for_new_connections_caps_history_at_5_distinct_ips(acl_poller_module, tmp_path, monkeypatch):
    m = acl_poller_module
    geo_file = tmp_path / 'clients_geo.json'
    monkeypatch.setattr(m, 'GEO_FILE', str(geo_file))
    monkeypatch.setattr(m, 'geolocate', lambda ip: None)
    monkeypatch.setattr(m, 'asn_lookup', lambda ip: None)

    for i in range(7):
        connected = {'juan': {'vip': '10.8.0.2', 'real_ip': f'80.58.0.{i}'}}
        m.update_geo_for_new_connections({'juan'}, connected)
        time.sleep(0.01)  # keep timestamps strictly increasing for the ordering check below

    geo = json.loads(geo_file.read_text())
    history = geo['juan']['history']
    assert len(history) == m.GEO_HISTORY_MAX
    # most-recent-first: the last IP connected (80.58.0.6) must be first
    assert history[0]['ip'] == '80.58.0.6'


def test_retry_pending_geolocations_resolves_lat_and_isp_independently(acl_poller_module, tmp_path, monkeypatch):
    """Two separate databases can finish downloading at different times --
    a pending entry must be able to pick up just the piece that's ready,
    not wait for both before updating anything."""
    m = acl_poller_module
    geo_file = tmp_path / 'clients_geo.json'
    geo_file.write_text(json.dumps({
        'juan': {'history': [{'ip': '80.58.0.33', 'ts': 123}]},  # no lat, no isp yet
    }))
    monkeypatch.setattr(m, 'GEO_FILE', str(geo_file))
    monkeypatch.setattr(m, 'geolocate', lambda ip: {'lat': 40.0, 'lon': -3.0, 'city': 'Madrid',
                                                      'country': 'Spain', 'country_code': 'ES'})
    monkeypatch.setattr(m, 'asn_lookup', lambda ip: None)  # ASN db still not available

    m.retry_pending_geolocations()

    geo = json.loads(geo_file.read_text())
    entry = geo['juan']['history'][0]
    assert entry['lat'] == 40.0
    assert 'isp' not in entry  # correctly left pending, will retry again next cycle
