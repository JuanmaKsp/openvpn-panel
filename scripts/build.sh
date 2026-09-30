#!/bin/bash
# Assembles both .deb packages from the shared app/usr/systemd/config
# sources plus each target's packaging/<target>/DEBIAN overlay.
#
# Usage: scripts/build.sh [debian10|debian11-13|all]
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIST_DIR="$REPO_ROOT/dist"
WORK_DIR="$REPO_ROOT/build"

# packaging dir name -> filename suffix used in the .deb artifact name
declare -A TARGET_SUFFIX=(
    [debian10]="debian10"
    [debian11-13]="debian11-12-13"
)

build_target() {
    local target="$1"
    local suffix="${TARGET_SUFFIX[$target]}"
    local pkg_dir="$REPO_ROOT/packaging/$target"
    local tree="$WORK_DIR/$target"

    if [ ! -d "$pkg_dir/DEBIAN" ]; then
        echo "ERROR: no packaging/$target/DEBIAN found" >&2
        exit 1
    fi

    echo "==> Building $target"
    rm -rf "$tree"
    mkdir -p "$tree/var/www/openvpn/app" \
             "$tree/usr/lib/openvpn-manager" \
             "$tree/usr/lib/tmpfiles.d" \
             "$tree/etc/systemd/system" \
             "$tree/etc/stunnel" \
             "$tree/etc/logrotate.d"

    cp -r "$REPO_ROOT/app/"* "$tree/var/www/openvpn/app/"
    cp "$REPO_ROOT/usr/lib/openvpn-manager/"*.py "$tree/usr/lib/openvpn-manager/"
    cp "$REPO_ROOT/systemd/"*.service "$REPO_ROOT/systemd/"*.timer "$tree/etc/systemd/system/"
    cp "$REPO_ROOT/config/stunnel/openvpn-gui.conf" "$tree/etc/stunnel/openvpn-gui.conf"
    cp "$REPO_ROOT/config/logrotate.d/openvpn-gui" "$tree/etc/logrotate.d/openvpn-gui"
    cp "$REPO_ROOT/config/tmpfiles.d/openvpn-manager-acl.conf" "$tree/usr/lib/tmpfiles.d/openvpn-manager-acl.conf"

    cp -r "$pkg_dir/DEBIAN" "$tree/DEBIAN"
    chmod 755 "$tree/DEBIAN/postinst" "$tree/DEBIAN/prerm" "$tree/DEBIAN/postrm"

    local version
    version="$(grep '^Version:' "$tree/DEBIAN/control" | awk '{print $2}')"

    mkdir -p "$DIST_DIR"
    local out="$DIST_DIR/openvpn-manager_${version}_${suffix}_all.deb"
    dpkg-deb --build --root-owner-group "$tree" "$out"
    echo "==> Built $out"
}

case "${1:-all}" in
    all)
        for t in "${!TARGET_SUFFIX[@]}"; do build_target "$t"; done
        ;;
    debian10|debian11-13)
        build_target "$1"
        ;;
    *)
        echo "Usage: $0 [debian10|debian11-13|all]" >&2
        exit 1
        ;;
esac
