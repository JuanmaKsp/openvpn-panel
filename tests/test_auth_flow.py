from conftest import login


def test_login_success_sets_session_and_redirects(client, app_module, monkeypatch):
    resp = login(client, app_module, pam_ok=True, monkeypatch=monkeypatch)
    assert resp.status_code == 303
    assert resp.headers['Location'].endswith('/')
    with client.session_transaction() as sess:
        assert sess['user'] == 'root'


def test_login_failure_shows_error_no_session(client, app_module, monkeypatch):
    resp = login(client, app_module, pam_ok=False, monkeypatch=monkeypatch)
    assert resp.status_code == 200  # re-renders the login form, no redirect
    with client.session_transaction() as sess:
        assert 'user' not in sess


def test_post_without_csrf_token_is_rejected(client, app_module, monkeypatch):
    monkeypatch.setattr(app_module, 'pam_auth', lambda u, p: True)
    client.get('/login')  # establishes a session, but we won't send its token
    resp = client.post('/login', data={'username': 'root', 'password': 'x'})
    assert resp.status_code == 403


def test_brute_force_lockout_after_max_attempts(client, app_module, monkeypatch):
    monkeypatch.setattr(app_module.time, 'sleep', lambda *_: None)  # skip the anti-brute-force delay in tests
    for _ in range(app_module._MAX_ATTEMPTS):
        login(client, app_module, pam_ok=False, monkeypatch=monkeypatch)
    resp = login(client, app_module, pam_ok=True, monkeypatch=monkeypatch)
    # locked out even with correct credentials now
    with client.session_transaction() as sess:
        assert 'user' not in sess
    assert resp.status_code == 200


def test_protected_route_redirects_to_login_when_unauthenticated(client):
    resp = client.get('/')
    assert resp.status_code == 303
    assert '/login' in resp.headers['Location']


def test_root_required_blocks_non_root_user(client, app_module, monkeypatch):
    login(client, app_module, username='nonroot', pam_ok=True, monkeypatch=monkeypatch)
    resp = client.get('/admin/users')
    assert resp.status_code == 403


def test_logout_revokes_session(client, app_module, monkeypatch):
    login(client, app_module, pam_ok=True, monkeypatch=monkeypatch)
    client.get('/logout')
    with client.session_transaction() as sess:
        assert 'user' not in sess
