# KernelSU emulated soft-reboot regression tests

Run from the repository root on Linux:

```sh
python3 tests/soft-reboot/run_tests.py
```

Requires Python 3, GCC, dash, util-linux (`unshare`, `mount`, `umount`), and
user/mount namespace support. If the host restricts unprivileged user namespaces,
use `sudo python3 tests/soft-reboot/run_tests.py`. Set `VECTOR_TEST_SHELL` to an
alternative shell executable to test its parser and execution behavior.

The suite runs the production cleanup script against real child processes and
bind mounts inside private user, network, and mount namespaces. Only Android
filesystem prefixes and the reference init PID are relocated in the temporary
script copy. It does not communicate with an Android device.

Coverage includes daemon identity independent of its name, unrelated processes,
deleted module directories, wrapper replacement, stacked and busy mounts,
preservation of other modules' mounts, Android compiler path variants, repeated
cleanup, first-update ordering, argument forwarding, and refusing startup when
cleanup fails. This is not an Android version/ABI compatibility test.

The S26 experimental branch adds eight regressions to the original 24 tests:
current `.resource-cache` bind mounts on the same device as `/data`, deleted
bind sources across updates, unrelated cache binds, mixed legacy/current
daemons, unmount failure, signal failure, ten repeated bind-cache cycles, and
refusing to launch without the private resource-cache mount. KernelSU startup
also passes zero automatic system-server restart retries to the daemon.
Run the recursion tests separately with
`python3 dex2oat/tests/test_wrapper_recursion.py`.

Use `VECTOR_TEST_SHELL=/bin/mksh` or point it to `tools/busybox-shell.sh` to
exercise the cleanup with alternative shells. The built ZIP is checked using
`python3 tools/verify_module.py PATH_TO_ZIP` on Linux. That check executes the
real installer in four temporary architecture fixtures, verifies all file
hashes and installed lifecycle hooks, and checks competing-module preservation.
Host installer fixtures do not prove Android executable compatibility.
