#!/bin/bash
# Build locally without invoking any Gradle push/install/reboot task.
set -uo pipefail
export JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64
export ANDROID_HOME=/opt/vector-s26-tools/android-sdk
export GRADLE_USER_HOME=/opt/vector-s26-tools/gradle-home
export PATH="$ANDROID_HOME/cmake/4.1.2/bin:$JAVA_HOME/bin:/usr/local/bin:/usr/bin:/bin"
cd /opt/vector-s26-build || exit 1
logs=/mnt/c/Users/loren/Documents/ChatGPT/VECTOR/artifacts/logs
./gradlew :zygisk:zipDebug testDebugUnitTest lintDebug \
    --no-daemon --max-workers=4 --console=plain > "$logs/build-debug.log" 2>&1
code=$?
printf '%s\n' "$code" > "$logs/build-debug.exit"
tail -55 "$logs/build-debug.log"
exit "$code"
