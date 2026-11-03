def test_valid_name_accepts_alnum_dash_underscore(app_module):
    assert app_module.valid_name('juan-perez_01')
    assert not app_module.valid_name('')
    assert not app_module.valid_name(None)
    assert not app_module.valid_name('nombre con espacios')
    assert not app_module.valid_name('../etc/passwd')


def test_valid_email(app_module):
    assert app_module.valid_email('a@b.com')
    assert not app_module.valid_email('not-an-email')
    # these characters would break the JS onclick context the email is
    # interpolated into (see Renovar button in index.html) -- must be rejected
    assert not app_module.valid_email('a"<script>@b.com')
    assert not app_module.valid_email('a b@c.com')


def test_valid_panel_username(app_module):
    assert app_module.valid_panel_username('operador1')
    assert not app_module.valid_panel_username('Operador1')  # must be lowercase
    assert not app_module.valid_panel_username('ab')  # too short (min 3)
    assert not app_module.valid_panel_username('a' * 33)  # too long (max 32)


def test_months_to_days(app_module):
    assert app_module.months_to_days(1) == 30
    assert app_module.months_to_days(24) == 720


def test_sanitize_log_field_strips_crlf(app_module):
    # prevents forging fake audit-log lines via a crafted username
    assert app_module._sanitize_log_field('ok') == 'ok'
    assert app_module._sanitize_log_field('user\r\nFAKE LOG LINE') == 'userFAKE LOG LINE'
    assert app_module._sanitize_log_field(None) is None


def test_safe_next_rejects_open_redirect(app_module):
    with app_module.app.test_request_context('/login?next=//evil.com'):
        assert app_module._safe_next() == app_module.url_for('login')
    with app_module.app.test_request_context('/login?next=http://evil.com'):
        assert app_module._safe_next() == app_module.url_for('login')


def test_safe_next_allows_local_path(app_module):
    with app_module.app.test_request_context('/login?next=/map'):
        assert app_module._safe_next() == '/map'
