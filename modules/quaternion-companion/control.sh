#!/system/bin/sh
STATE_DIR=/data/adb/quaternion_companion
SETTINGS=/system/bin/settings
KSUD=/data/adb/ksud
TOYBOX=/system/bin/toybox
umask 077

fail() { printf '%s\n' "$*" >&2; exit 1; }
read_setting() {
  value=$("$SETTINGS" get global "$1") || return 1
  case "$value" in 0|1|null) printf '%s\n' "$value" ;; *) return 1 ;; esac
}
write_setting() {
  case "$2" in
    null) "$SETTINGS" delete global "$1" >/dev/null ;;
    0|1) "$SETTINGS" put global "$1" "$2" ;;
    *) return 1 ;;
  esac || return 1
  [ "$(read_setting "$1")" = "$2" ]
}

status() {
  printf 'Quaternion Companion 0.1.0\n'
  printf 'SELinux: %s\n' "$(getenforce 2>/dev/null || printf unknown)"
  printf 'Debug USB: %s\n' "$(read_setting adb_enabled || printf unknown)"
  printf 'Debug wireless: %s\n' "$(read_setting adb_wifi_enabled || printf unknown)"
  if [ -f "$STATE_DIR/adb.backup" ]; then
    printf 'Backup ADB: presente (ripristinabile)\n'
  else
    printf 'Backup ADB: nessuno\n'
  fi
  printf '\nCapacita mount_hide (sola lettura):\n'
  "$KSUD" feature get mount_hide 2>&1 || printf 'Non disponibile tramite questo ksud.\n'
  printf '\nIl modulo non filtra mount, pacchetti o risultati del detector.\n'
  printf 'Per i pacchetti, configura HMA-OSS per le app desiderate.\n'
}

restore_adb() {
  [ -f "$STATE_DIR/adb.backup" ] || return 0
  # Never source shell code from a state file. Require exactly the two saved settings.
  lines=$(wc -l < "$STATE_DIR/adb.backup") || fail 'Backup non leggibile.'
  [ "$lines" -eq 2 ] || fail 'Backup non valido; conservato.'
  {
    IFS= read -r usb
    IFS= read -r wifi
  } < "$STATE_DIR/adb.backup"
  case "$usb:$wifi" in
    0:0|0:1|0:null|1:0|1:1|1:null|null:0|null:1|null:null) ;;
    *) fail 'Backup non valido; conservato.' ;;
  esac
  # Preserve subsequent user changes. Settings still at our applied value (0)
  # can be restored; values already equal to the original need no mutation.
  current_usb=$(read_setting adb_enabled) || fail 'Lettura ADB fallita.'
  current_wifi=$(read_setting adb_wifi_enabled) || fail 'Lettura wireless fallita.'
  [ "$current_usb" = 0 ] || [ "$current_usb" = "$usb" ] || fail 'Debug USB modificato altrove; backup conservato.'
  [ "$current_wifi" = 0 ] || [ "$current_wifi" = "$wifi" ] || fail 'Debug wireless modificato altrove; backup conservato.'
  [ "$current_wifi" = "$wifi" ] || write_setting adb_wifi_enabled "$wifi" || fail 'Ripristino wireless fallito; backup conservato.'
  [ "$current_usb" = "$usb" ] || write_setting adb_enabled "$usb" || fail 'Ripristino USB fallito; backup conservato.'
  rm -f "$STATE_DIR/adb.backup" || fail 'Impossibile chiudere il backup.'
  printf 'Impostazioni ADB ripristinate.\n'
}

disable_adb() {
  [ ! -e "$STATE_DIR/adb.backup" ] || fail 'Backup gia presente: ripristina prima di una nuova applicazione.'
  usb=$(read_setting adb_enabled) || fail 'Impossibile leggere Debug USB.'
  wifi=$(read_setting adb_wifi_enabled) || fail 'Impossibile leggere Debug wireless.'
  printf '%s\n%s\n' "$usb" "$wifi" > "$STATE_DIR/adb.backup.tmp" || fail 'Backup fallito.'
  mv "$STATE_DIR/adb.backup.tmp" "$STATE_DIR/adb.backup" || fail 'Backup non salvato.'
  if ! write_setting adb_wifi_enabled 0; then
    restore_adb
    fail 'Disattivazione wireless fallita; ripristino tentato.'
  fi
  # USB last: switching it off may disconnect the very ADB session invoking us.
  if ! write_setting adb_enabled 0; then
    restore_adb
    fail 'Disattivazione USB fallita; ripristino tentato.'
  fi
  printf 'Debug USB e wireless disattivati. Le connessioni ADB possono interrompersi.\n'
}

[ "$(id -u)" = 0 ] || fail 'Serve root.'
case "${1:-status}" in
  status) status; exit 0 ;;
  hma) exec /system/bin/am start -a android.intent.action.MAIN -c android.intent.category.LAUNCHER -p org.frknkrc44.hma_oss ;;
  disable-adb|restore-adb) action=$1 ;;
  *) fail 'Azioni: status, disable-adb, restore-adb, hma' ;;
esac
[ ! -L "$STATE_DIR" ] || fail 'Directory di stato non valida.'
mkdir -p "$STATE_DIR" || fail 'Directory di stato non disponibile.'
chmod 0700 "$STATE_DIR" || fail 'Permessi dello stato non applicati.'
[ ! -L "$STATE_DIR/lock" ] || fail 'File lock non valido.'
exec 9>"$STATE_DIR/lock" || fail 'Lock non disponibile.'
# mksh marks persistent extra descriptors close-on-exec. Export the same open
# file description explicitly; the shell then retains ownership of the lock.
"$TOYBOX" flock -n 9 9>&9 || fail 'Altra operazione in corso; riprova.'
case "$action" in disable-adb) disable_adb ;; restore-adb) restore_adb ;; esac
