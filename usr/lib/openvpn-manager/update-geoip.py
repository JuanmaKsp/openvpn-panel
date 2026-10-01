#!/usr/bin/env python3
"""
update-geoip — descarga/actualiza las bases de datos DB-IP usadas para
geolocalizar la ultima conexion de cada cliente VPN y mostrar su operador:

- dbip-city-lite: ciudad/pais aproximados a partir de la IP.
- dbip-asn-lite: nombre del operador (ASN), usado solo para mostrar el ISP
  y marcar como "posible conexion movil" las IPs cuyo operador lo deja claro
  en su propio nombre (vease is_mobile_org() en acl-poller.py).

Se ejecuta al instalar el paquete (mejor esfuerzo, no bloqueante si no hay
red en ese momento) y despues mensualmente via ovpn-geoip-update.timer.
Ninguna de las dos requiere cuenta ni API key (a diferencia de MaxMind
GeoLite2) y estan bajo licencia CC BY 4.0, redistribuibles:
https://github.com/wp-statistics/DbIP-City-lite
https://db-ip.com/db/download/ip-to-asn-lite

Cada descarga va a un fichero temporal y solo reemplaza el .mmdb en uso si
se completa y el resultado es un .mmdb valido -- una descarga a medias o
corrupta nunca debe dejar el sistema sin base de datos utilizable. La
ciudad es la base de datos principal (si falla, se devuelve error); el ASN
es best-effort (si falla, solo se avisa, porque solo afecta al nombre del
operador mostrado, no a la ubicacion en el mapa).
"""
import gzip
import os
import sys
import tempfile
import urllib.request
from datetime import date, timedelta

DEST_DIR = '/var/lib/openvpn-manager'
TIMEOUT  = 30

CITY_URLS = ['https://cdn.jsdelivr.net/npm/dbip-city-lite/dbip-city-lite.mmdb.gz']
CITY_DEST = os.path.join(DEST_DIR, 'dbip-city-lite.mmdb')


def _asn_urls():
    # dbip-asn-lite no tiene mirror "siempre la ultima" como dbip-city-lite
    # en jsdelivr -- el nombre del fichero lleva el mes. Se prueba el mes en
    # curso y, por si aun no se ha publicado justo al cambiar de mes, el
    # anterior.
    today = date.today()
    prev_month_last_day = today.replace(day=1) - timedelta(days=1)
    return [
        f'https://download.db-ip.com/free/dbip-asn-lite-{today:%Y-%m}.mmdb.gz',
        f'https://download.db-ip.com/free/dbip-asn-lite-{prev_month_last_day:%Y-%m}.mmdb.gz',
    ]


ASN_DEST = os.path.join(DEST_DIR, 'dbip-asn-lite.mmdb')


def log(msg):
    print(f'update-geoip: {msg}', file=sys.stderr)


def _download_mmdb(urls, dest, label):
    """Prueba cada URL de `urls` en orden; con la primera que descargue y
    valide correctamente, reemplaza `dest` de forma atomica y devuelve True.
    Si ninguna funciona, deja `dest` tal cual estaba y devuelve False."""
    for url in urls:
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'openvpn-manager-geoip-updater'})
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                compressed = resp.read()
        except Exception as e:
            log(f'{label}: no se pudo descargar {url}: {e}')
            continue

        try:
            data = gzip.decompress(compressed)
        except Exception as e:
            log(f'{label}: la descarga de {url} no es un .gz valido: {e}')
            continue

        # Comprobacion minima de cordura: un .mmdb real termina con el
        # marcador de metadatos de MaxMind DB.
        if b'\xab\xcd\xefMaxMind.com' not in data[-40000:]:
            log(f'{label}: el fichero descargado de {url} no parece un .mmdb valido, se descarta')
            continue

        fd, tmp_path = tempfile.mkstemp(dir=DEST_DIR, prefix=f'.{label}-', suffix='.mmdb.tmp')
        try:
            with os.fdopen(fd, 'wb') as f:
                f.write(data)
            os.chmod(tmp_path, 0o644)
            os.replace(tmp_path, dest)
        except Exception as e:
            log(f'{label}: no se pudo escribir {dest}: {e}')
            try:
                os.remove(tmp_path)
            except OSError:
                pass
            continue

        log(f'{label} actualizada correctamente ({len(data)} bytes) -> {dest}')
        return True

    return False


def main():
    os.makedirs(DEST_DIR, exist_ok=True)

    city_ok = _download_mmdb(CITY_URLS, CITY_DEST, 'dbip-city-lite')
    asn_ok = _download_mmdb(_asn_urls(), ASN_DEST, 'dbip-asn-lite')

    if not asn_ok:
        log('no se pudo actualizar dbip-asn-lite -- el mapa seguira funcionando, '
            'solo faltara el nombre del operador hasta el proximo intento')

    return 0 if city_ok else 1


if __name__ == '__main__':
    sys.exit(main())
