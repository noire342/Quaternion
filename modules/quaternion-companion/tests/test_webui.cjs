'use strict';
const vm = require('node:vm');
const fs = require('node:fs');
const assert = require('node:assert/strict');
const path = require('node:path');
const source = fs.readFileSync(path.join(__dirname, '../webroot/app.js'), 'utf8');
const nodes = {state: {textContent: ''}, feedback: {textContent: ''}};
const commands = [];
const context = vm.createContext({console, setTimeout, clearTimeout, Date, Error, Number, Promise,
  document: {getElementById: id => nodes[id], querySelectorAll: () => []}, window: {}});
context.window.ksu = {exec(command, options, name) {
  commands.push(command);
  context.window[name](0, command.endsWith(' status') ? 'Unknown feature: mount_hide\n' : '<untrusted output>', '');
}};
vm.runInContext(source, context);
(async () => {
  await new Promise(resolve => setImmediate(resolve));
  assert.match(nodes.state.textContent, /Unknown feature/);
  assert.equal(commands.length, 1);
  await vm.runInContext('run("disable-adb")', context);
  assert.equal(commands.length, 3);
  assert.equal(nodes.feedback.textContent, '<untrusted output>');
  await assert.rejects(vm.runInContext('exec("status; reboot")', context), /Comando non valido/);
  assert.equal(commands.length, 3);
  context.window.ksu = undefined;
  await vm.runInContext('run("status")', context);
  assert.match(nodes.feedback.textContent, /Apri la WebUI/);
  console.log('WebUI bridge, action allowlist, readback and error handling passed (host simulation).');
})().catch(error => { console.error(error); process.exitCode = 1; });
