# Quaternion

Experimental fork of [JingMatrix/Vector](https://github.com/JingMatrix/Vector),
maintained at <https://github.com/noire342/Quaternion>.

## Baseline and compatibility

The baseline is Vector **canary 3114**, commit
`eaffc816ee78bb4acd45fc42ed1e07a892e8dc46` (PR #1034).
It fixes rendezvous selection for late root and stops automatically restarting
system_server after an unsuccessful injection handshake. The local lifecycle and
compiler-recursion guards remain included.

Quaternion retains `zygisk_vector`, the existing package names, API contracts,
configuration database and signing identity. It is an in-place Vector update;
renaming the display name does not hide its implementation. Automatic updates
from Vector are removed to avoid replacing Quaternion with another build.

The upstream change clearing Rescue Party boot counters is deliberately excluded.
The launcher also refuses to continue if making its private namespace slave fails.
Neither this fork nor its companion disables SELinux or changes attestation,
Verified Boot, Knox, fingerprints or Play Integrity properties.

## Duck Detector report, 27 October 2026

The supplied report directly exposes the compiler bind mount rooted at
`/adb/modules/zygisk_vector/bin/dex2oat64` through Android 17's native isolated
zygote. This is not evidence of a surviving NeoZygisk daemon: the current provider
is Zygisk Next **1.5.2 (864-a4a72ce-release)**; its runtime probes were clear.

Upstream [#843](https://github.com/JingMatrix/Vector/issues/843) was closed as a
duplicate of [#918](https://github.com/JingMatrix/Vector/issues/918).
The latter explains that ordinary app-namespace unmounting cannot cover a native
isolated child inspecting init's shared namespace. Blindly unmounting there would
remove the compiler wrapper for the whole system. Removing the wrapper also
removes its protection against AOT inlining and can break hooks.

The upstream kernel solution is JingMatrix/KernelSU commit
`80a3ab3` (`mount_hide`). A script module can use that capability only if the loaded
kernel implementation actually supplies it; a version number or a manager update
does not establish support. Quaternion Companion reports unsupported/unknown
capabilities instead of pretending to install a kernel feature.

**Canary 3114 does not fix this mount exposure by itself.** Renaming the module,
changing proc output inside the detector, or disabling the compiler interception
is not offered as a verified solution.

The SELinux card says Enforcing, strong policy, and denied dirty-policy edges. Its
red classification cannot be attributed to Vector from this report. Installed
Xposed modules, the root manager, Termux and HMA are genuine package observations;
HMA-OSS is already installed and should be configured separately for the intended
apps. ADB being enabled is a real setting, not an attestation result.

## Validation and device boundary

Host lifecycle tests, compiler recursion tests, build/package checks and Android
runtime checks are separate evidence. No host result proves Samsung compatibility,
invisibility, or preservation of Strong Integrity. Installation and any reboot are
manual. Do not chain experimental updates and reboots; compare a fresh report
after one change. Retain the previous Vector ZIP for rollback.
