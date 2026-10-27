'use strict';
let sequence = 0;
let busy = false;
const actions = ['status', 'disable-adb', 'restore-adb', 'hma'];
function exec(action) {
  if (!actions.includes(action)) return Promise.reject(new Error('Comando non valido.'));
  if (!window.ksu || typeof window.ksu.exec !== 'function') return Promise.reject(new Error('Apri la WebUI del modulo da KernelSU.'));
  return new Promise((resolve, reject) => {
    const name = `quaternion_${Date.now()}_${sequence++}`;
    const timer = setTimeout(() => { delete window[name]; reject(new Error('Tempo scaduto: aggiorna lo stato prima di riprovare.')); }, 30000);
    window[name] = (code, stdout, stderr) => {
      clearTimeout(timer); delete window[name];
      if (Number(code) !== 0) reject(new Error(stderr || stdout || 'Operazione fallita.'));
      else resolve(stdout);
    };
    try { window.ksu.exec(`/system/bin/sh /data/adb/modules/quaternion_companion/control.sh ${action}`, '{}', name); }
    catch (error) { clearTimeout(timer); delete window[name]; reject(error); }
  });
}
async function run(action) {
  if (busy) return;
  busy = true;
  document.querySelectorAll('button').forEach(button => { button.disabled = true; });
  const feedback = document.getElementById('feedback');
  feedback.textContent = '';
  try {
    const output = await exec(action);
    if (action !== 'status') feedback.textContent = output;
    document.getElementById('state').textContent = action === 'status' ? output : await exec('status');
  } catch (error) { feedback.textContent = error.message; }
  finally { busy = false; document.querySelectorAll('button').forEach(button => { button.disabled = false; }); }
}
document.querySelectorAll('[data-action]').forEach(button => button.addEventListener('click', () => run(button.dataset.action)));
run('status');
