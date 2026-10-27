#!/bin/bash
# Local build only. No device, GitHub publish, install or reboot tasks.
set -uo pipefail
export JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64
export ANDROID_HOME=/opt/vector-s26-tools/android-sdk
export GRADLE_USER_HOME=/opt/vector-s26-tools/gradle-home
export PATH="$ANDROID_HOME/cmake/4.1.2/bin:$JAVA_HOME/bin:/usr/local/bin:/usr/bin:/bin"
cd /opt/vector-s26-build || exit 1
logs=/mnt/c/Users/loren/Documents/ChatGPT/VECTOR/artifacts/logs
./gradlew :zygisk:zipDebug --no-daemon --max-workers=4 --console=plain > "$logs/build-quaternion.log" 2>&1
code=$?
printf '%s\n' "$code" > "$logs/build-quaternion.exit"
tail -45 "$logs/build-quaternion.log"
exit "$code"
