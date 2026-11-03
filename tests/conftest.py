"""
Shared pytest fixtures.

app.py hardcodes absolute production paths (/var/www/openvpn/..., /var/log/
openvpn-gui.log) and touches some of them at import time (it writes its
Flask secret key to /var/www/openvpn/app/.secret the first time it's
imported). Rather than editing app.py to make those paths configurable --
extra complexity the production code doesn't need -- these fixtures create
the same real paths a `.deb` install would, exactly as every manual test
during this project's development has (see project memory), so the app
imports and runs unmodified.
"""
import importlib.util
import os
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
APP_DIR = REPO_ROOT / 'app'


def _prepare_real_paths():
    os.makedirs('/var/www/openvpn/app', exist_ok=True)
    os.makedirs('/var/log', exist_ok=True)
    Path('/var/log/openvpn-gui.log').touch(exist_ok=True)


@pytest.fixture(scope='session')
def app_module():
    """Import app.py once per test session, the same way gunicorn does
    (cwd = app/, so its `from translations import ...` resolves)."""
    _prepare_real_paths()
    sys.path.insert(0, str(APP_DIR))
    import app as app_module  # noqa: PLC0415
    return app_module


@pytest.fixture(scope='session')
def acl_poller_module():
    """acl-poller.py has a hyphen in its filename, so it can't be
    `import`-ed normally -- load it the same way as everywhere else in
    this project's manual tests."""
    spec = importlib.util.spec_from_file_location(
        'acl_poller', REPO_ROOT / 'usr' / 'lib' / 'openvpn-manager' / 'acl-poller.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(autouse=True)
def _reset_module_state(app_module):
    """app.py keeps some state (failed-login counters, revoked session
    ids) in module-level dicts/sets so it survives across requests within
    one gunicorn worker. Tests share that same imported module (see
    app_module's session scope), so without resetting it here, a test
    that triggers the brute-force lockout would leave the next test's
    identical client IP (127.0.0.1) looking locked out too."""
    app_module._failed.clear()
    app_module._revoked_sessions.clear()
    yield


@pytest.fixture
def client(app_module):
    app_module.app.config['TESTING'] = True
    with app_module.app.test_client() as c:
        yield c


@pytest.fixture
def fake_index(app_module, tmp_path, monkeypatch):
    """Points INDEX_FILE at a throwaway file so tests never touch a real
    easy-rsa install; returns a helper to write index.txt contents."""
    index_file = tmp_path / 'index.txt'
    monkeypatch.setattr(app_module, 'INDEX_FILE', str(index_file))

    def _write(lines):
        index_file.write_text('\n'.join(lines) + '\n')

    return _write


@pytest.fixture
def fake_meta(app_module, tmp_path, monkeypatch):
    meta_file = tmp_path / 'clients_meta.json'
    monkeypatch.setattr(app_module, 'META_FILE', str(meta_file))
    return meta_file


def login(client, app_module, username='root', password='whatever', pam_ok=True, monkeypatch=None):
    """Full real login flow: GET to pick up the session + CSRF cookie,
    extract the token from the rendered form, then POST it back -- the
    exact double-submit pattern app.py's CSRF check requires (see
    before_request -> _check_csrf()). Mocks pam_auth so no real system
    user/PAM setup is needed."""
    if monkeypatch is not None:
        monkeypatch.setattr(app_module, 'pam_auth', lambda u, p: pam_ok)
    get_resp = client.get('/login')
    html = get_resp.get_data(as_text=True)
    token = html.split('name="_csrf_token" value="')[1].split('"')[0]
    return client.post('/login', data={
        'username': username,
        'password': password,
        '_csrf_token': token,
    })
