# Extract the directory path and change directory 
MODDIR="${0%/*}"
cd "$MODDIR" || exit 1

# KernelSU replays service.sh after an emulated reboot, including updates from
# versions without the pre-stop stage. Never let a replacement cache an old
# compiler wrapper as the stock dex2oat or race a surviving daemon.
if [ "$KSU" = true ]; then
    sh "$MODDIR/emulated-soft-reboot.sh" || exit 1
fi

# A root manager runs this script with its own busybox, but a manual bootstrap has nothing in
# front of it except Android's utilities, so this is written for toybox's unshare: it makes a
# mount namespace with -m and takes no propagation flag. The namespace therefore marks its own
# root slave before handing over. Abort if isolation cannot be established.
# Dex2OatServer separately enters init's namespace for compiler interception;
# this isolation protects the daemon's resource-cache, not those compiler mounts.
unshare -m /system/bin/sh -c '
    mount -o rslave none / || exit 1
    exec "$0" "$@"
' "$MODDIR/daemon" "$@" &
