#!/usr/bin/env python3
"""Read-only ADB snapshot. Never pushes, installs, changes settings, or reboots."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import shlex
import subprocess

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--adb', default='adb')
parser.add_argument('--serial')
parser.add_argument('--output', type=Path, default=Path('artifacts/private-adb'))
args = parser.parse_args()
args.output.mkdir(parents=True, exist_ok=True)
records = []

def capture(name, command, timeout=20):
    try:
        r = subprocess.run(command, capture_output=True, text=True, timeout=timeout,
                           encoding='utf-8', errors='replace')
        data = {'name': name, 'command': command, 'returncode': r.returncode,
                'stdout': r.stdout, 'stderr': r.stderr}
    except subprocess.TimeoutExpired as e:
        data = {'name': name, 'command': command, 'returncode': None,
                'stdout': str(e.stdout or ''), 'stderr': 'TIMED OUT; command not retried'}
    records.append(data)
    (args.output / (name + '.json')).write_text(json.dumps(data, indent=2), encoding='utf-8')
    return data

devices = capture('devices', [args.adb, 'devices', '-l'])
online = [line.split()[0] for line in devices['stdout'].splitlines()
          if re.match(r'^\S+\s+device\s', line)]
serial = args.serial
if serial is None:
    if len(online) != 1:
        (args.output / 'summary.json').write_text(json.dumps({
            'utc': datetime.now(timezone.utc).isoformat(),
            'status': 'no-authorized-device' if not online else 'multiple-devices-select-serial',
            'root_available': None, 'device_mutations': False,
            'install_performed': False, 'soft_reboot_performed': False,
        }, indent=2), encoding='utf-8')
        raise SystemExit('Expected exactly one authorized device; no device modified. See devices.json.')
    serial = online[0]
if serial not in online:
    raise SystemExit('Selected device is not authorized/online. No device modified.')
adb = [args.adb, '-s', serial, 'shell']
def shell(name, command, root=False, timeout=20):
    if root:
        command = 'su -c ' + shlex.quote(command)
    return capture(name, adb + [command], timeout)

model = shell('model', 'getprop ro.product.model')['stdout'].strip()
if model != 'SM-S948B':
    raise SystemExit(f'Unexpected model {model!r}; stopped after model read.')
for name, command in {
    'fingerprint': 'getprop ro.build.fingerprint',
    'android': 'getprop ro.build.version.release; getprop ro.build.version.sdk',
    'selinux': 'getenforce',
    'boot': 'cat /proc/uptime; cat /proc/sys/kernel/random/boot_id; getprop sys.boot_completed; getprop ro.boot.bootreason; getprop sys.boot.reason; getprop ro.boot.verifiedbootstate; getprop ro.boot.vbmeta.device_state',
    'processes': 'ps -A',
    'rescue-properties': 'getprop | grep -iE "rescue|boot_count|reboot|rollback"',
    'rescue-settings': 'settings list global | grep -iE "rescue|boot_count"',
    'extensions': 'pm path android.ext.services; pm path android.ext.shared; getprop init.svc.zygote; getprop init.svc.zygote_secondary',
}.items():
    shell(name, command)
root_id = shell('root-id', 'id', root=True, timeout=12)
root_ok = root_id['returncode'] == 0 and 'uid=0(' in root_id['stdout']
ksud = 'if [ -x /data/adb/ksud ]; then /data/adb/ksud'
if root_ok:
    commands = {
        'ksud-help': ksud + ' --help; else command -v ksud; fi',
        'ksud-version': ksud + ' --version; fi; cat /sys/module/kernelsu/version 2>/dev/null',
        'ksud-module-help': ksud + ' module --help; fi',
        'modules': ksud + ' module list; fi',
        'root-processes': 'ps -A -o USER,PID,PPID,PGID,SID,NAME,ARGS',
        'module-files': 'for d in /data/adb/modules/* /data/adb/modules_update/*; do [ -d "$d" ] || continue; echo "$d"; cat "$d/module.prop"; ls -ld "$d/disable" "$d/remove" "$d/update" "$d/emulated-soft-reboot.sh" "$d/post-fs-data.sh" "$d/service.sh" 2>/dev/null; done',
        'init-mountinfo': 'cat /proc/1/mountinfo',
        'art-process-mounts': 'for p in $(pidof zygote zygote64 system_server artd); do echo "PID=$p"; readlink /proc/$p/ns/mnt; grep -E "dex2oat|com.android.art|com.android.runtime|resource-cache|zygisk_vector" /proc/$p/mountinfo; done',
        'lspd-paths': 'ls -ld /data/adb/lspd* /data/adb/modules/zygisk_vector /data/adb/modules_update/zygisk_vector 2>/dev/null',
        'composer-hooks': 'for p in /data/adb/emulated-soft-reboot.d/00-rmgu-samsung-composer.sh /data/adb/post-mount.d/00-rmgu-samsung-composer.sh /data/adb/rmgu/composer/restart.sh /data/adb/rmgu/composer/transition; do [ -f "$p" ] || continue; echo "$p"; cat "$p"; done',
        'root-kernel-log': 'dmesg | grep -iE "kernelsu|ksu|rescue|avc:.*denied|vector|zygisk" | tail -250',
    }
    for name, command in commands.items():
        result = shell(name, command, root=True)
        if result['returncode'] is None:
            break
shell('logcat', 'logcat -b all -d -t 2500', root=root_ok, timeout=30)
summary = {'utc': datetime.now(timezone.utc).isoformat(), 'model': model,
           'root_available': root_ok, 'device_mutations': False,
           'install_performed': False, 'soft_reboot_performed': False,
           'commands': len(records), 'private_logs': True}
(args.output / 'summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
print(json.dumps(summary, indent=2))
