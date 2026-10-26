#!/usr/bin/env python3
"""Bootstrap the Linux SDK needed by this checkout, verifying Google's archive digest."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import urllib.request
import xml.etree.ElementTree as ET
import zipfile

root = Path(sys.argv[1] if len(sys.argv) > 1 else '/opt/vector-s26-tools')
root.mkdir(parents=True, exist_ok=True)
sdk = root / 'android-sdk'
sdk.mkdir(exist_ok=True)
base = 'https://dl.google.com/android/repository/'
data = urllib.request.urlopen(base + 'repository2-1.xml', timeout=60).read()
(root / 'repository2-1.xml').write_bytes(data)
tree = ET.fromstring(data)
packages = tree.findall('.//remotePackage')
package = next(p for p in packages if p.attrib['path'] == 'cmdline-tools;latest')
archive = next(a for a in package.findall('./archives/archive')
               if a.findtext('host-os') == 'linux')
complete = archive.find('complete')
url = base + complete.findtext('url')
checksum = complete.find('checksum')
archive_path = root / url.rsplit('/', 1)[1]
if not archive_path.exists():
    urllib.request.urlretrieve(url, archive_path)
algorithm = checksum.attrib.get('type', 'sha1')
actual = hashlib.file_digest(archive_path.open('rb'), algorithm).hexdigest()
assert actual == checksum.text, (actual, checksum.text)
destination = sdk / 'cmdline-tools/latest'
if not destination.exists():
    with zipfile.ZipFile(archive_path) as z:
        z.extractall(root / 'unpacked')
    destination.parent.mkdir(exist_ok=True)
    (root / 'unpacked/cmdline-tools').rename(destination)
for p in (destination / 'bin').iterdir():
    p.chmod(0o755)
manager = destination / 'bin/sdkmanager'
licenses = sdk / 'licenses'
licenses.mkdir(exist_ok=True)
subprocess.run([str(manager), f'--sdk_root={sdk}', '--licenses'],
               input='y\n' * 200, text=True, check=True)
required = ['platforms;android-37.0', 'build-tools;37.0.0', 'ndk;30.0.16248370', 'cmake;4.1.2']
subprocess.run([str(manager), f'--sdk_root={sdk}', *required], check=True)
for package in required:
    assert (sdk / package.replace(';', '/')).is_dir(), f'SDK package missing: {package}'
(root / 'sdk-manifest.json').write_text(json.dumps({
    'commandline_url': url, algorithm: actual, 'packages': required}, indent=2))
