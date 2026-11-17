"""
Regression tests for the session idle/absolute timeout (see before()).

Real bug this covers: index.html polls /api/connected every 4s via JS.
Before this fix, that background poll kept renewing the session forever
(Flask's default sliding cookie expiry), so a user who left the dashboard
tab open was never logged out by idle time, no matter how long they were
actually away from the keyboard.
"""
import time

from conftest import login


def test_idle_timeout_logs_out_after_inactivity(client, app_module, monkeypatch):
    login(client, app_module, monkeypatch=monkeypatch)
    assert client.get('/').status_code == 200

    with client.session_transaction() as sess:
        sess['_last_seen'] = time.time() - (app_module._IDLE_TIMEOUT_SECS + 1)

    resp = client.get('/')
    assert resp.status_code == 303
    assert '/login' in resp.headers['Location']


def test_absolute_session_lifetime_logs_out_even_if_active(client, app_module, monkeypatch):
    login(client, app_module, monkeypatch=monkeypatch)

    max_secs = app_module.app.config['PERMANENT_SESSION_LIFETIME'].total_seconds()
    with client.session_transaction() as sess:
        sess['_login_at'] = time.time() - (max_secs + 1)
        sess['_last_seen'] = time.time()   # activity right up to the end

    resp = client.get('/')
    assert resp.status_code == 303
    assert '/login' in resp.headers['Location']


def test_background_polling_endpoint_does_not_reset_idle_clock(client, app_module, monkeypatch):
    login(client, app_module, monkeypatch=monkeypatch)

    stale = time.time() - (app_module._IDLE_TIMEOUT_SECS - 5)   # almost idle
    with client.session_transaction() as sess:
        sess['_last_seen'] = stale

    assert client.get('/api/connected').status_code == 200

    with client.session_transaction() as sess:
        assert sess['_last_seen'] == stale


def test_real_page_view_resets_idle_clock(client, app_module, monkeypatch):
    login(client, app_module, monkeypatch=monkeypatch)

    stale = time.time() - (app_module._IDLE_TIMEOUT_SECS - 5)
    with client.session_transaction() as sess:
        sess['_last_seen'] = stale

    assert client.get('/').status_code == 200

    with client.session_transaction() as sess:
        assert sess['_last_seen'] > stale
