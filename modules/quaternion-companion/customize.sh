#!/system/bin/sh
[ "$KSU" = true ] || abort 'Questo modulo richiede KernelSU.'
[ -x /system/bin/toybox ] || abort 'Toybox non disponibile.'
/system/bin/toybox flock --help >/dev/null 2>&1 || abort 'Toybox flock non disponibile.'
for script in control.sh action.sh uninstall.sh; do
  set_perm "$MODPATH/$script" 0 0 0755
done
export MODULE_HOT_INSTALL_REQUEST=true
ui_print 'Quaternion Companion - sperimentale'
ui_print 'Installazione senza modifiche al telefono. Non serve riavviare.'
ui_print 'Apri WebUI per i controlli e le azioni manuali.'
