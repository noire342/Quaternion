#!/usr/bin/env python3
"""Host state/rollback tests against simulated Android settings and ksud APIs."""
import json
import fcntl
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

SOURCE = Path(__file__).resolve().parents[1]
SHELL = os.environ.get('QUATERNION_TEST_SHELL', '/bin/dash')


class ControllerTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.state = self.root / 'state'
        self.database = self.root / 'settings.json'
        self.calls = self.root / 'calls'
        self.database.write_text(json.dumps({'adb_enabled': '1', 'adb_wifi_enabled': '1'}))
        self.env = dict(os.environ, DB=str(self.database), CALLS=str(self.calls))
        self.settings = self.root / 'settings'
        self.settings.write_text('''#!/usr/bin/env python3
import json, os, pathlib, sys
p=pathlib.Path(os.environ['DB']); data=json.loads(p.read_text())
action, namespace, key=sys.argv[1:4]
assert namespace == 'global' and key in ('adb_enabled', 'adb_wifi_enabled')
if action == 'get': print(data.get(key, 'null'))
else:
    with open(os.environ['CALLS'], 'a') as f: f.write(' '.join(sys.argv[1:])+'\\n')
    if os.environ.get('FAIL_KEY') == key: sys.exit(1)
    if action == 'delete': data.pop(key, None)
    else: data[key]=sys.argv[4]
    p.write_text(json.dumps(data))
''')
        self.settings.chmod(0o755)
        self.ksud = self.root / 'ksud'
        self.ksud.write_text('#!/bin/sh\necho "Error: Unknown feature: mount_hide" >&2\nexit 1\n')
        self.ksud.chmod(0o755)
        self.toybox = self.root / 'toybox'
        self.toybox.write_text('#!/bin/sh\nexec "$@"\n')
        self.toybox.chmod(0o755)
        self.script = self.root / 'control.sh'
        self.script.write_text((SOURCE / 'control.sh').read_text()
                               .replace('/data/adb/quaternion_companion', str(self.state))
                               .replace('/system/bin/settings', str(self.settings))
                               .replace('/data/adb/ksud', str(self.ksud))
                               .replace('/system/bin/toybox', str(self.toybox)))

    def tearDown(self):
        self.tmp.cleanup()

    def run_action(self, action, expected=0):
        result = subprocess.run([SHELL, str(self.script), action], env=self.env,
                                capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        return result

    def values(self):
        return json.loads(self.database.read_text())

    def test_status_is_read_only_and_reports_unsupported(self):
        result = self.run_action('status')
        self.assertIn('Unknown feature: mount_hide', result.stdout)
        self.assertFalse(self.state.exists())
        self.assertFalse(self.calls.exists())

    def test_disable_and_restore_exact_original(self):
        self.run_action('disable-adb')
        self.assertEqual(self.values(), {'adb_enabled': '0', 'adb_wifi_enabled': '0'})
        self.assertEqual((self.state / 'adb.backup').read_text(), '1\n1\n')
        self.assertEqual(self.calls.read_text().splitlines()[0], 'put global adb_wifi_enabled 0')
        self.run_action('restore-adb')
        self.assertEqual(self.values(), {'adb_enabled': '1', 'adb_wifi_enabled': '1'})
        self.assertFalse((self.state / 'adb.backup').exists())

    def test_absent_settings_are_deleted_on_restore(self):
        self.database.write_text('{}')
        self.run_action('disable-adb')
        self.run_action('restore-adb')
        self.assertEqual(self.values(), {})

    def test_already_disabled_stays_disabled(self):
        original = {'adb_enabled': '0', 'adb_wifi_enabled': '0'}
        self.database.write_text(json.dumps(original))
        self.run_action('disable-adb')
        self.run_action('restore-adb')
        self.assertEqual(self.values(), original)

    def test_repeated_apply_cannot_overwrite_backup(self):
        self.run_action('disable-adb')
        self.run_action('disable-adb', 1)
        self.assertEqual((self.state / 'adb.backup').read_text(), '1\n1\n')

    def test_usb_failure_rolls_back_wireless(self):
        self.env['FAIL_KEY'] = 'adb_enabled'
        self.run_action('disable-adb', 1)
        self.assertEqual(self.values(), {'adb_enabled': '1', 'adb_wifi_enabled': '1'})
        self.assertFalse((self.state / 'adb.backup').exists())

    def test_wireless_failure_leaves_usb_alone(self):
        self.env['FAIL_KEY'] = 'adb_wifi_enabled'
        self.run_action('disable-adb', 1)
        self.assertEqual(self.values(), {'adb_enabled': '1', 'adb_wifi_enabled': '1'})

    def test_restore_failure_keeps_backup_for_retry(self):
        self.run_action('disable-adb')
        self.env['FAIL_KEY'] = 'adb_wifi_enabled'
        self.run_action('restore-adb', 1)
        self.assertTrue((self.state / 'adb.backup').exists())
        del self.env['FAIL_KEY']
        self.run_action('restore-adb')

    def test_external_change_is_preserved(self):
        self.database.write_text('{"adb_enabled":"0","adb_wifi_enabled":"0"}')
        self.run_action('disable-adb')
        self.database.write_text('{"adb_enabled":"1","adb_wifi_enabled":"0"}')
        self.run_action('restore-adb', 1)
        self.assertEqual(self.values()['adb_enabled'], '1')
        self.assertTrue((self.state / 'adb.backup').exists())

    def test_corrupt_backup_is_never_executed(self):
        self.state.mkdir()
        marker = self.root / 'unexpected'
        (self.state / 'adb.backup').write_text(f'$(touch {marker})\n1\n')
        self.run_action('restore-adb', 1)
        self.assertFalse(marker.exists())
        self.assertFalse(self.calls.exists())

    def test_symlink_state_refused(self):
        target = self.root / 'elsewhere'
        target.mkdir()
        self.state.symlink_to(target, target_is_directory=True)
        self.run_action('disable-adb', 1)
        self.assertEqual(list(target.iterdir()), [])

    def test_unknown_action_cannot_inject_command(self):
        self.run_action('disable-adb; touch unexpected', 1)
        self.assertFalse(self.calls.exists())

    def test_concurrent_operation_is_refused_without_settings_changes(self):
        self.state.mkdir()
        with (self.state / 'lock').open('w') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.run_action('disable-adb', 1)
        self.assertFalse(self.calls.exists())


if __name__ == '__main__':
    unittest.main(verbosity=2)
