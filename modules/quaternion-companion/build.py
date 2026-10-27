#!/usr/bin/env python3
"""Build a deterministic script-only module; no installation or device access."""
import hashlib
import json
from pathlib import Path
import stat
import zipfile

SOURCE = Path(__file__).resolve().parent
OUT = SOURCE.parents[1] / 'artifacts/quaternion'
FILES = ('module.prop', 'customize.sh', 'action.sh', 'uninstall.sh', 'control.sh',
         'README.md', 'webroot/index.html', 'webroot/style.css', 'webroot/app.js')

if __name__ == '__main__':
    OUT.mkdir(parents=True, exist_ok=True)
    archive = OUT / 'Quaternion-Companion-v0.1.0-Experimental.zip'
    with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED) as z:
        for name in sorted(FILES):
            data = (SOURCE / name).read_bytes()
            assert b'\r' not in data and not data.startswith(b'\xef\xbb\xbf'), name
            item = zipfile.ZipInfo(name, (2026, 10, 27, 0, 0, 0))
            item.create_system = 3
            item.external_attr = (stat.S_IFREG | (0o755 if name.endswith('.sh') else 0o644)) << 16
            item.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(item, data)
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        assert set(z.namelist()) == set(FILES)
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    archive.with_suffix('.zip.sha256').write_text(f'{digest}  {archive.name}\n')
    (OUT / 'Quaternion-Companion-recovery.sh').write_bytes((SOURCE / 'control.sh').read_bytes())
    print(json.dumps({'zip': str(archive), 'sha256': digest, 'device_tested': False}, indent=2))
