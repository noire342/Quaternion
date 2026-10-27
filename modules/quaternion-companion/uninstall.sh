#!/system/bin/sh
# Retain the backup outside the module if restoration fails.
/system/bin/sh "${0%/*}/control.sh" restore-adb || echo 'Quaternion: ripristino ADB incompleto; backup conservato.' >&2
