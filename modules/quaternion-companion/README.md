# Quaternion Companion 0.1.0 — sperimentale

Modulo KernelSU di supporto. Si installa senza modificare impostazioni e non
richiede riavvio. Azione mostra uno stato in sola lettura; la WebUI offre:

- Stato di SELinux, debug USB/wireless e disponibilita di `mount_hide`.
- Disattivazione reale del debug USB e wireless, con backup e ripristino.
- Apertura di HMA-OSS gia installato e indicazioni per configurarlo.

Non e un modulo "fix tutto". Su questo telefono `ksud` risponde **Unknown
feature: mount_hide**: la correzione kernel descritta nella issue Vector #918
non si puo attivare tramite questa interfaccia. Il modulo non cambia kernel,
non nasconde mount e non sostituisce il root attuale.

## Pacchetti nel report

In HMA-OSS crea una configurazione per l'app dalla quale vuoi limitare la
visibilita dei pacchetti (per questo confronto: `com.eltavine.duckdetector`).
Aggiungi i soli pacchetti che vuoi escludere, inclusi il manager KSU Next,
HMA e i moduli Xposed rilevati. Riavvia soltanto l'app per ripetere il test.
Non aggiungere l'app detector allo scope degli altri moduli. La riuscita dei
singoli metodi di rilevamento va verificata con un nuovo report; questa guida
non prova che HMA li copra tutti su Android 17.

Il report cita anche Termux: e la presenza di un'app installata, non una prova
di root. La sezione SELinux riporta Enforcing e controlli coerenti; il solo
colore rosso non autorizza a disattivare o riscrivere la policy.

## ADB e ripristino

Disattiva il debug dalla WebUI sul telefono, consapevole che USB e ADB wireless
possono disconnettersi. Developer Options, autorizzazioni ADB, servizi, porte TCP,
SystemUI e app root non vengono modificati. Nessun intervento su `adbd` o
`persist.*`: la gestione del trasporto resta ad Android/OEM, e il nuovo report
deve confermare il risultato effettivo. Un riavvio completo non serve.

Per ripristinare dalla WebUI usa **Ripristina ADB**. Oppure in Termux root:

```sh
sh /data/adb/modules/quaternion_companion/control.sh restore-adb
```

Ripristina prima di disabilitare il modulo o perdere il root temporaneo.
Disabilitare il modulo non ripristina le impostazioni Android. La disinstallazione
tenta il ripristino; il backup in `/data/adb/quaternion_companion/adb.backup`
resta disponibile se fallisce. Il controller non riattiva ADB contro una modifica
successiva rilevabile. Nessun polling, servizio in background o applicazione
automatica all'avvio.

Non tocca fingerprint, TEE, attestation, Play Integrity, Verified Boot, Knox,
Rescue Party o impostazioni SELinux. Questo non garantisce Strong Integrity.
I test host simulano le API settings e ksud: serve verifica sul telefono.
