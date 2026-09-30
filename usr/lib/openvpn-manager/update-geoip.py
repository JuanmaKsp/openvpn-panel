#!/usr/bin/env python3
"""
update-geoip — descarga/actualiza la base de datos DB-IP City Lite usada
para geolocalizar la ultima conexion de cada cliente VPN.

Se ejecuta al instalar el paquete (mejor esfuerzo, no bloqueante si no hay
red en ese momento) y despues mensualmente via ovpn-geoip-update.timer.
No requiere cuenta ni API key (a diferencia de MaxMind GeoLite2) y esta
bajo licencia CC BY 4.0, redistribuible: https://github.com/wp-statistics/DbIP-City-lite

Descarga a un fichero temporal y solo reemplaza el .mmdb en uso si la
descarga se completa y el fichero resultante es un .mmdb valido -- una
descarga a medias o corrupta nunca debe dejar el sistema sin base de datos
utilizable.
"""
import gzip
import os
import sys
import tempfile
import urllib.request

URL      = 'https://cdn.jsdelivr.net/npm/dbip-city-lite/dbip-city-lite.mmdb.gz'
DEST_DIR = '/var/lib/openvpn-manager'
DEST     = os.path.join(DEST_DIR, 'dbip-city-lite.mmdb')
TIMEOUT  = 30


def log(msg):
    print(f'update-geoip: {msg}', file=sys.stderr)


def main():
    os.makedirs(DEST_DIR, exist_ok=True)

    try:
        req = urllib.request.Request(URL, headers={'User-Agent': 'openvpn-manager-geoip-updater'})
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            compressed = resp.read()
    except Exception as e:
        log(f'no se pudo descargar {URL}: {e}')
        return 1

    try:
        data = gzip.decompress(compressed)
    except Exception as e:
        log(f'la descarga no es un .gz valido: {e}')
        return 1

    # Comprobacion minima de cordura: un .mmdb real termina con el marcador
    # de metadatos de MaxMind DB. Si no esta, no sobreescribimos el bueno.
    if b'\xab\xcd\xefMaxMind.com' not in data[-40000:]:
        log('el fichero descargado no parece un .mmdb valido, se descarta')
        return 1

    fd, tmp_path = tempfile.mkstemp(dir=DEST_DIR, prefix='.dbip-city-lite-', suffix='.mmdb.tmp')
    try:
        with os.fdopen(fd, 'wb') as f:
            f.write(data)
        os.chmod(tmp_path, 0o644)
        os.replace(tmp_path, DEST)
    except Exception as e:
        log(f'no se pudo escribir {DEST}: {e}')
        try:
            os.remove(tmp_path)
        except OSError:
            pass
        return 1

    log(f'base de datos GeoIP actualizada correctamente ({len(data)} bytes) -> {DEST}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
