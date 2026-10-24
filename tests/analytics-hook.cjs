const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync('frontend/js/analytics.js', 'utf8');
function run(code, consent, privacy = {}) {
    const scripts = [];
    const listeners = {};
    const window = {plexudoAnalyticsConsent: consent, addEventListener: (name, fn) => {listeners[name] = fn;}};
    const context = {window, navigator: privacy, document: {createElement: () => ({}), head: {appendChild: s => scripts.push(s)}}};
    vm.runInNewContext(code, context);
    return {scripts, window, listeners};
}
assert.equal(run(source, true).scripts.length, 0, 'placeholder must make zero requests');
const configured = source.replace("const ANALYTICS_ID = 'G-XXXXXXXXXX'", "const ANALYTICS_ID = 'G-FAKE000000'");
assert.equal(run(configured, false).scripts.length, 0, 'consent is required');
assert.equal(run(configured, true, {globalPrivacyControl: true}).scripts.length, 0);
assert.equal(run(configured, true, {doNotTrack: '1'}).scripts.length, 0);
const granted = run(configured, true);
assert.equal(granted.scripts.length, 1);
granted.listeners['plexudo:analytics-consent']();
assert.equal(granted.scripts.length, 1, 'load once');
const delayed = run(configured, false);
delayed.window.plexudoAnalyticsConsent = true;
delayed.listeners['plexudo:analytics-consent']();
assert.equal(delayed.scripts.length, 1);
console.log('PASS: analytics placeholder, consent, privacy signals, delayed consent and deduplication');
