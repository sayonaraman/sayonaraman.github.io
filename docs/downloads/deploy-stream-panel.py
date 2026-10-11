#!/usr/bin/env python3
"""Deploy your app.panel FastAPI project to a dedicated Debian VPS via SSH."""
import argparse
import getpass
import io
import os
from pathlib import Path
import re
import shlex
import subprocess
import tarfile

INSTALL = r'''set -euo pipefail
stage=$1
domain=$2
trap 'rm -rf -- "$stage"' EXIT
. /etc/os-release
test "$ID" = debian || { echo 'Expected Debian.' >&2; exit 1; }
test "$(id -u)" = 0 || { echo 'SSH alias must use root.' >&2; exit 1; }
if test -f /etc/caddy/Caddyfile && ! grep -q '^# STREAM-PANEL-MANAGED$' /etc/caddy/Caddyfile; then
  echo 'Existing Caddy configuration found; no changes made. Use a dedicated VPS.' >&2
  exit 1
fi
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y --no-install-recommends python3-venv ca-certificates curl caddy
id stream-panel >/dev/null 2>&1 || useradd --system --home-dir /var/lib/stream-panel --shell /usr/sbin/nologin stream-panel
install -d -m 755 /opt/stream-panel /opt/stream-panel/releases
install -d -m 700 -o stream-panel -g stream-panel /var/lib/stream-panel
release="/opt/stream-panel/releases/$(date -u +%Y%m%dT%H%M%SZ)-$$"
install -d -m 755 "$release"
cp -a "$stage/app" "$stage/requirements.txt" "$release/"
chmod -R a+rX "$release"
python3 -m venv "$release/.venv"
"$release/.venv/bin/pip" install --disable-pip-version-check -q -r "$release/requirements.txt"
chmod -R a+rX "$release"
if test -f /etc/stream-panel.env; then
  grep -qxF "STREAM_ORIGIN=https://$domain" /etc/stream-panel.env || { echo 'Existing origin differs; configuration preserved.' >&2; exit 1; }
else
  install -m 640 -o root -g stream-panel "$stage/setup.env" /etc/stream-panel.env
fi
STREAM_ORIGIN="https://$domain" "$release/.venv/bin/python" -m compileall -q "$release/app"
previous=$(readlink /opt/stream-panel/current || true)
ln -sfn "$release" /opt/stream-panel/current
cat >/etc/systemd/system/stream-panel.service <<'UNIT'
[Unit]
Description=STREAM panel
Wants=network-online.target
After=network-online.target
[Service]
User=stream-panel
Group=stream-panel
WorkingDirectory=/opt/stream-panel/current
EnvironmentFile=/etc/stream-panel.env
Environment=STREAM_DATA=/var/lib/stream-panel
Environment=PYTHONDONTWRITEBYTECODE=1
ExecStart=/opt/stream-panel/current/.venv/bin/uvicorn app.panel:app --host 127.0.0.1 --port 8080 --workers 1 --no-access-log --no-proxy-headers
Restart=on-failure
RestartSec=5
UMask=0077
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/var/lib/stream-panel
[Install]
WantedBy=multi-user.target
UNIT
cat >"$stage/Caddyfile" <<CADDY
# STREAM-PANEL-MANAGED
$domain {
    reverse_proxy 127.0.0.1:8080 {
        header_up X-Real-IP {remote_host}
    }
}
CADDY
caddy validate --config "$stage/Caddyfile" --adapter caddyfile
systemctl daemon-reload
systemctl enable stream-panel >/dev/null
systemctl restart stream-panel
healthy=0
for attempt in $(seq 1 30); do
  if curl -fsS -H "Host: $domain" http://127.0.0.1:8080/ >/dev/null; then healthy=1; break; fi
  sleep 1
done
if test "$healthy" != 1; then
  if test -n "$previous"; then ln -sfn "$previous" /opt/stream-panel/current; systemctl restart stream-panel; fi
  echo 'Panel readiness failed; previous code restored when available.' >&2
  exit 1
fi
install -m 644 "$stage/Caddyfile" /etc/caddy/Caddyfile
systemctl enable --now caddy >/dev/null
systemctl reload caddy
systemctl is-active --quiet stream-panel caddy
echo "Panel installed: https://$domain"
echo 'DNS and inbound ports 80/443 must point to this VPS for HTTPS.'
echo 'Next: sign in and prepare the streaming worker from the Server section.'
'''


def entries(source):
    if not (source / 'app/panel.py').is_file() or not (source / 'requirements.txt').is_file():
        raise ValueError('Source must contain app/panel.py and requirements.txt.')
    allow = {'.py', '.html', '.js', '.css', '.svg', '.png', '.jpg', '.jpeg', '.woff', '.woff2'}
    paths = [source / 'requirements.txt']
    for path in sorted((source / 'app').rglob('*')):
        if path.is_symlink():
            raise ValueError('Symlinks in app/ are not supported.')
        if path.is_file() and path.suffix in allow and not any(part.startswith('.') or part == '__pycache__' for part in path.relative_to(source).parts):
            paths.append(path)
    return paths


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host', required=True, help='SSH config alias using root and key authentication')
    parser.add_argument('--source', type=Path, required=True, help='Local panel source folder')
    parser.add_argument('--domain', required=True, help='Domain without scheme or path; DNS must point to VPS')
    parser.add_argument('--config', type=Path, help='Private env file with TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID')
    parser.add_argument('--plan', action='store_true', help='Validate source only; no SSH, no secrets requested')
    args = parser.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,252}', args.host):
        parser.error('Use a valid SSH alias.')
    if not re.fullmatch(r'(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}', args.domain):
        parser.error('Use a DNS hostname without https:// or a path.')
    source = args.source.resolve()
    files = entries(source)
    print(f'Panel source: {len(files)} public application files; data and local secrets excluded.')
    if args.plan:
        print('Plan OK. No connection to VPS was made.')
        return
    secret = {}
    if args.config:
        for line in args.config.read_text().splitlines():
            key, sep, value = line.partition('=')
            if sep and key in ('TELEGRAM_BOT_TOKEN', 'TELEGRAM_CHAT_ID'):
                secret[key] = value.strip().strip('\"\'')
    token = secret.get('TELEGRAM_BOT_TOKEN') or getpass.getpass('Telegram bot token (hidden): ')
    chat = secret.get('TELEGRAM_CHAT_ID') or input('Your Telegram chat ID for login codes: ').strip()
    if not re.fullmatch(r'\d{5,15}:[A-Za-z0-9_-]{20,100}', token) or not re.fullmatch(r'-?\d{1,20}', chat):
        parser.error('Invalid Telegram login settings.')
    env = f'TELEGRAM_BOT_TOKEN={token}\nTELEGRAM_CHAT_ID={chat}\nSTREAM_ORIGIN=https://{args.domain}\nSTREAM_TRUSTED_PROXIES=127.0.0.1/32\n'
    archive = io.BytesIO()
    with tarfile.open(fileobj=archive, mode='w:gz') as tar:
        for path in files:
            tar.add(path, arcname=str(path.relative_to(source)), recursive=False)
        for name, data in [('setup.env', env.encode()), ('install.sh', INSTALL.encode())]:
            info = tarfile.TarInfo(name); info.size = len(data); info.mode = 0o600
            tar.addfile(info, io.BytesIO(data))
    ssh = ['ssh', '-o', 'StrictHostKeyChecking=yes', '-o', 'BatchMode=yes', args.host]
    subprocess.run(ssh + ['true'], check=True)
    stage = subprocess.check_output(ssh + ['umask 077; mktemp -d /tmp/stream-panel-deploy.XXXXXXXX'], text=True).strip()
    if not re.fullmatch(r'/tmp/stream-panel-deploy\.[A-Za-z0-9]+', stage):
        raise RuntimeError('Unexpected remote staging path.')
    try:
        subprocess.run(ssh + ['tar -xz -C ' + shlex.quote(stage)], input=archive.getvalue(), check=True)
        command = 'bash ' + shlex.quote(stage+'/install.sh') + ' ' + shlex.quote(stage) + ' ' + shlex.quote(args.domain)
        subprocess.run(ssh + [command], check=True)
    finally:
        subprocess.run(ssh + ['rm -rf -- ' + shlex.quote(stage)], check=False, stdout=subprocess.DEVNULL)


if __name__ == '__main__':
    main()
