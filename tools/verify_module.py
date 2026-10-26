#!/usr/bin/env python3
"""Validate a built ZIP and run its actual installer in temporary Linux fixtures."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile

archive = Path(sys.argv[1]).resolve()
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None, 'ZIP CRC error'
    names = set(z.namelist())
    required = ['module.prop', 'customize.sh', 'service.sh', 'daemon', 'daemon.apk',
                'emulated-soft-reboot.sh', 'post-fs-data.sh', 'manager.apk',
                'framework/vector.dex', 'sepolicy.rule']
    for name in required:
        assert name in names, name
    verified = 0
    for name in names:
        if name.endswith('/') or name.endswith('.sha256'):
            continue
        assert name + '.sha256' in names, f'Missing hash: {name}'
        assert hashlib.sha256(z.read(name)).hexdigest() == z.read(name + '.sha256').decode().strip(), name
        verified += 1
    for abi in ['armeabi-v7a', 'arm64-v8a', 'x86', 'x86_64']:
        for name in [f'bin/{abi}/dex2oat', f'bin/{abi}/liboat_hook.so', f'lib/{abi}/libzygisk.so']:
            assert z.read(name).startswith(b'\x7fELF'), name
    for script in ['emulated-soft-reboot.sh', 'post-fs-data.sh', 'service.sh']:
        assert b'\r' not in z.read(script), f'CRLF in {script}'
        subprocess.run(['/bin/dash', '-n'], input=z.read(script), check=True)
    results = []
    with tempfile.TemporaryDirectory(prefix='vector-installer-') as tmp:
        root = Path(tmp)
        # The KernelSU installer uses BusyBox sha256sum's -s option. GNU
        # coreutils does not implement that option; use the real target applet.
        applets = root / 'applets'
        applets.mkdir()
        (applets / 'sha256sum').symlink_to('/bin/busybox')
        for arch, abi32, abi64, is64 in [('arm', 'armeabi-v7a', 'arm64-v8a', False),
                                       ('arm64', 'armeabi-v7a', 'arm64-v8a', True),
                                       ('x86', 'x86', 'x86_64', False),
                                       ('x64', 'x86', 'x86_64', True)]:
            case = root / arch
            case.mkdir()
            module = case / 'module'
            module.mkdir()
            installer_tmp = case / 'tmp'
            installer_tmp.mkdir()
            (installer_tmp / 'module.prop').write_bytes(z.read('module.prop'))
            foreign = case / 'zygisk_lsposed'
            source = z.read('customize.sh').decode().replace('/data/adb/modules/zygisk_lsposed', str(foreign))
            script = case / 'install.sh'
            script.write_text('''#!/bin/sh
ui_print() { echo "$*"; }
abort() { echo "$*" >&2; exit 1; }
grep_prop() { if [ "$1" = version ]; then echo test; else echo 0; fi; }
set_perm_recursive() {
    find "$1" -type d -exec chmod "$4" {} +
    find "$1" -type f -exec chmod "$5" {} +
}
set_perm() { chmod "$4" "$1"; }
''' + source)
            env = dict(os.environ, ARCH=arch, API='37', IS64BIT=str(is64).lower(),
                       MODPATH=str(module), TMPDIR=str(installer_tmp), ZIPFILE=str(archive),
                       PATH=str(applets) + ':' + os.environ['PATH'])
            result = subprocess.run(['/bin/dash', str(script)], env=env, capture_output=True, text=True, timeout=30)
            assert result.returncode == 0, result.stdout + result.stderr
            for name in required:
                if name == 'customize.sh':
                    continue  # KernelSU sources the installer; the installer does not copy itself.
                assert (module / name).is_file(), name
            for name in ['emulated-soft-reboot.sh', 'post-fs-data.sh', 'service.sh']:
                assert (module / name).read_bytes() == z.read(name), name
            assert (module / 'bin/dex2oat32').is_file()
            assert (module / 'zygisk' / (abi32 + '.so')).is_file()
            if is64:
                assert (module / 'bin/dex2oat64').is_file()
                assert (module / 'zygisk' / (abi64 + '.so')).is_file()
            foreign.mkdir()
            blocked = subprocess.run(['/bin/dash', str(script)], env=env, capture_output=True, text=True, timeout=30)
            assert blocked.returncode != 0
            assert 'Active LSPosed' in blocked.stderr
            assert not (foreign / 'disable').exists(), 'Installer changed another module'
            results.append({'arch': arch, 'installed_hooks': True, 'competing_module_preserved': True})
    print(json.dumps({'zip': archive.name, 'sha256': hashlib.sha256(archive.read_bytes()).hexdigest(),
                      'verified_files': verified, 'installer_fixtures': results}, indent=2))
