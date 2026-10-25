const assert = require('node:assert/strict');
const fs = require('node:fs'),vm=require('node:vm');
const nodes=new Map();
const context = {
  console,
  document: {
    addEventListener() {},
    querySelectorAll() { return []; },
    getElementById(id) {
      if (!nodes.has(id)) nodes.set(id, {textContent: '', innerHTML: '', style: {}});
      return nodes.get(id);
    },
    createElement() {
      return {set textContent(value) {
        this.innerHTML = String(value).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
      }};
    }
  }
};
vm.createContext(context);vm.runInContext(fs.readFileSync('frontend/js/tools/trend-analyzer.js','utf8'),context);
context.updateKpiBadges('SUCCESS',false);
assert.match(nodes.get('kpiTotalViewsDeltaText').textContent,/freshness unavailable/);
assert(!/live|rss/i.test(nodes.get('kpiTotalViewsDeltaText').textContent));
context.renderKpis({totalViews:0,avgEngagement:null,risingCount:null,totalTracked:2},true);
assert.equal(nodes.get('kpiTotalViewsVal').textContent,'0');
assert.equal(nodes.get('kpiAvgEngVal').textContent,'—');
assert.equal(nodes.get('kpiRisingCountVal').textContent,'—');
assert.match(nodes.get('kpiAvgEngDelta').className,/amber/);
context.renderKpis({totalViews:17,avgEngagement:0,risingCount:0,totalTracked:3},true);
assert.equal(nodes.get('kpiAvgEngVal').textContent,'0.0%');
assert.equal(nodes.get('kpiRisingCountDeltaText').textContent,'of 3 returned');
context.renderKpis(null,false);
assert.equal(nodes.get('kpiTotalViewsVal').textContent,'—');
const html=fs.readFileSync('frontend/tools/trend-analyzer.html','utf8');
for(const sample of ['Shorts 55%','Longform 30%','Live 15%','100 Peak Viral','stitch-sparkline-row'])assert(!html.includes(sample));
const source=fs.readFileSync('frontend/js/tools/trend-analyzer.js','utf8');
assert(!source.includes('buildSpreadLabels'));
console.log('PASS: missing-versus-zero metrics, truthful source labels, real cohort count, no static analytics decoration or invented chart times');
