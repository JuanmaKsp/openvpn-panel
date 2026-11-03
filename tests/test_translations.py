import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'app'))
from translations import TRANSLATIONS, DEFAULT_LANG, SUPPORTED_LANGS, get_text  # noqa: E402


def test_es_en_key_parity():
    """Every key must exist in both languages -- a key present in one but
    not the other silently falls back to English (or to the raw key) for
    whoever is missing it, which is easy to not notice without this check."""
    es_keys = set(TRANSLATIONS['es'].keys())
    en_keys = set(TRANSLATIONS['en'].keys())
    assert es_keys == en_keys, f'ES/EN key mismatch: {es_keys ^ en_keys}'


def test_default_lang_is_english():
    assert DEFAULT_LANG == 'en'


def test_supported_langs():
    assert set(SUPPORTED_LANGS) == {'en', 'es'}


def test_get_text_known_key():
    assert get_text('es', 'nav.logout') != get_text('es', 'does.not.exist')


def test_get_text_falls_back_to_english_for_unsupported_lang():
    # get_text() must never crash on a language it doesn't recognize
    assert get_text('fr', 'nav.logout') == get_text('en', 'nav.logout')


def test_get_text_falls_back_to_key_itself_when_missing_everywhere():
    missing_key = 'this.key.does.not.exist.anywhere'
    assert get_text('en', missing_key) == missing_key
