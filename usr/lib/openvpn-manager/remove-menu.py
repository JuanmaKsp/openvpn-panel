#!/usr/bin/env python3
"""Removes the OpenVPN Manager link from the TurnKey landing page."""
import sys

INDEX = '/var/www/openvpn/htdocs/index.html'

try:
    with open(INDEX) as f:
        content = f.read()
except FileNotFoundError:
    sys.exit(0)

if 'ovpngui' not in content:
    sys.exit(0)

content = content.replace(
    'webmin="https://"+window.location.hostname+":12321";\n'
    '              ovpngui="https://"+window.location.hostname+":12322";\n'
    '              document.getElementById("ovpngui").href = ovpngui;',
    'webmin="https://"+window.location.hostname+":12321";'
)

OLD_ANCHOR = (
    '<a id="webmin" href="">\n'
    '                        <img src="/images/webmin.png"/>Webmin</a>\n'
    '                    </div>\n'
    '                    <div>\n'
    '                        <a id="ovpngui" href="">\n'
    '                        <img src="/images/webmin.png"/>OpenVPN Manager</a>\n'
    '                    </div>\n'
    '                    <div></div>'
)
NEW_ANCHOR = (
    '<a id="webmin" href="">\n'
    '                        <img src="/images/webmin.png"/>Webmin</a>\n'
    '                    </div>\n'
    '                    <div></div>'
)
content = content.replace(OLD_ANCHOR, NEW_ANCHOR)

with open(INDEX, 'w') as f:
    f.write(content)

print("TurnKey menu: reverted OK")
