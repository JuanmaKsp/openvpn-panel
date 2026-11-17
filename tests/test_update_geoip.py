"""
Regression test for the security fix to update-geoip.py: downloading and
decompressing the GeoIP .mmdb update used to have no size cap at all, so a
compromised CDN (or a corrupted/huge response) could exhaust memory on this
service, which runs as root via ovpn-geoip-update.timer.
"""
import gzip

import pytest


def test_legit_small_payload_round_trips(update_geoip_module):
    m = update_geoip_module
    payload = b'hello mmdb' * 100
    compressed = gzip.compress(payload)
    assert m._gzip_decompress_capped(compressed, m.MAX_DECOMPRESSED_BYTES) == payload


def test_decompression_bomb_is_rejected(update_geoip_module):
    m = update_geoip_module
    bomb = gzip.compress(b'\x00' * (50 * 1024 * 1024))   # 50MB of zeros -> a few KB compressed
    with pytest.raises(ValueError):
        m._gzip_decompress_capped(bomb, 1024 * 1024)   # cap at 1MB


def test_oversized_download_is_rejected_before_full_buffering(update_geoip_module):
    m = update_geoip_module

    class FakeResp:
        def __init__(self, total):
            self.total = total

        def read(self, n):
            chunk = min(n, self.total)
            self.total -= chunk
            return b'x' * chunk

    with pytest.raises(ValueError):
        m._read_capped(FakeResp(10 * 1024 * 1024), 1024)


def test_download_within_cap_is_accepted(update_geoip_module):
    m = update_geoip_module

    class FakeResp:
        def __init__(self, data):
            self.data = data

        def read(self, n):
            chunk, self.data = self.data[:n], self.data[n:]
            return chunk

    data = b'y' * 500
    assert m._read_capped(FakeResp(data), 1024) == data
