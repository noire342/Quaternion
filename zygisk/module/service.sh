# Extract the directory path and change directory 
MODDIR="${0%/*}"
cd "$MODDIR" || exit 1
system_server_max_retry=3

# KernelSU replays service.sh after an emulated reboot, including updates from
# versions without the pre-stop stage. Never let a replacement cache an old
# compiler wrapper as the stock dex2oat or race a surviving daemon.
if [ "$KSU" = true ]; then
    sh "$MODDIR/emulated-soft-reboot.sh" || exit 1
    # Temporary-root Samsung experiments must not trigger extra framework
    # restarts when bridge registration fails. Leave recovery to the operator.
    system_server_max_retry=0
fi

# Start the daemon directly in the background within a private mount namespace
unshare --propagation slave -m "$MODDIR/daemon" --system-server-max-retry="$system_server_max_retry" "$@" &
