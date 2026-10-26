/* Behavioral data provenance regressions, including the actual chart configuration. */
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const nodes=new Map(),charts=[];
function node(){return {textContent:'',innerHTML:'',style:{},className:'',attrs:{},classList:{add(){},remove(){}},setAttribute(k,v){this.attrs[k]=v},getAttribute(k){return this.attrs[k]},replaceChildren(){this.innerHTML=''},getContext(){return {createLinearGradient(){return {addColorStop(){}}}}}};}
const c={console,window:{Chart:true},Chart:function(ctx,config){charts.push(config);this.destroy=()=>{}},document:{
  addEventListener(){},querySelectorAll(){return []},
  getElementById(id){if(!nodes.has(id))nodes.set(id,node());return nodes.get(id)},
  createElement(){return {set textContent(v){this.innerHTML=String(v).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')}}}
}};
vm.createContext(c);vm.runInContext(fs.readFileSync('frontend/js/tools/trend-analyzer.js','utf8'),c);
let count=0;function test(name,fn){fn();count++;console.log('PASS: '+name)}
const text=id=>c.document.getElementById(id).textContent;
const setVideos=v=>vm.runInContext('currentVideos='+JSON.stringify(v),c);
test('missing growth never creates 38.4',()=>{setVideos([{views:10}]);c.renderKpis({totalViews:10},true);assert.equal(text('kpiTopTopicVelocity'),'Unavailable')});
test('observed zero growth preserved with explicit compatibility evidence',()=>{c.renderKpis({totalViews:0,growthRate:0,growthComparable:true},true);assert.equal(text('kpiTopTopicVelocity'),'0.0% observed change')});
test('unproven growth suppressed even if numeric',()=>{c.renderKpis({totalViews:10,growthRate:99},true);assert.equal(text('kpiTopTopicVelocity'),'Unavailable')});
test('missing engagement vs actual zero',()=>{c.renderKpis({totalViews:10,avgEngagement:null},true);assert.equal(text('kpiEngagementRatioDisplay'),'—');c.renderKpis({totalViews:10,avgEngagement:0},true);assert.equal(text('kpiEngagementRatioDisplay'),'0.0%')});
test('median is median of lifetime counters, not mean or a 24h measurement',()=>{setVideos([{views:0},{views:10},{views:1000}]);c.renderKpis({totalViews:1010},true);assert.equal(text('kpiMedianViewsVal'),'10')});
test('missing format is not longform or live',()=>{assert.equal(c.computeFormatBreakdown([{title:'#shorts'}]),null);c.updateFormatBreakdownCard([]);assert.equal(text('formatShortsStat'),'Unavailable')});
test('duration shares in both cards use same sample; not a Shorts classification',()=>{const v=[{duration_sec:30},{duration_sec:600}];c.updateFormatBreakdownCard(v);assert.equal(text('formatShortsStat'),'50%');assert.equal(text('formatLongStat'),'50%');assert.match(text('kpiFormatLegend'),/Not observed YouTube formats/)});
test('no historical data cannot fall back to daily_metrics',()=>{c.renderDeepIntelligence({daily_metrics:[{date:'2026-10-25',views:100}],trend_intelligence:{}});assert.equal(vm.runInContext('currentTimelineRaw.length',c),0)});
test('baseline uses actual persisted counter and timestamp',()=>{vm.runInContext('currentKpis={totalViews:999999}',c);c.renderLowerChart([{date:'2026-10-20 12:00',views:0}]);const q=charts.at(-1);assert.deepEqual(Array.from(q.data.labels),['2026-10-20 12:00 UTC']);assert.equal(q.data.datasets[0].data[0],0);assert.equal(q.data.datasets[0].showLine,false)});
test('multiple observations use raw values, not synthetic smoothed measurements',()=>{c.renderLowerChart([{date:'2026-10-20',views:10},{date:'2026-10-21',views:30,smoothed_views:999}]);const q=charts.at(-1);assert.deepEqual(Array.from(q.data.datasets[0].data),[10,30]);assert.equal(q.data.datasets[0].tension,0)});
test('changed cohort suppresses history',()=>{c.renderDeepIntelligence({trend_intelligence:{cohort_comparable:false,timeline:[{date:'2026-10-20',views:10}]}});assert.equal(vm.runInContext('currentTimelineRaw.length',c),0)});
test('invalid timestamps and hidden counters rejected',()=>{c.renderDeepIntelligence({trend_intelligence:{timeline:[{date:'invalid',views:1},{date:'2026-10-20',views:null}]}});assert.equal(vm.runInContext('currentTimelineRaw.length',c),0)});
test('all success metrics clear in unavailable state',()=>{setVideos([{views:100,momentumScore:90,duration_sec:30}]);c.renderKpis({totalViews:100,avgEngagement:5},true);c.renderKpis(null,false);for(const id of ['kpiMedianViewsVal','kpiMomentumScoreVal','kpiEngagementRatioDisplay'])assert.equal(text(id),'—');assert.equal(text('formatShortsStat'),'Unavailable');assert.equal(nodes.get('kpiGaugeArc').attrs.d,'')});
test('age buckets retain labels and zero values with XSS-safe table output',()=>{c.renderViewsChart([{label:'<img src=x onerror=1>',views:0}],'All');const q=charts.at(-1);assert.equal(q.config?.type||q.type,'bar');assert.equal(q.data.datasets[0].data[0],0);assert(!nodes.get('viewsChartA11y').innerHTML.includes('<img'));assert(nodes.get('viewsChartA11y').innerHTML.includes('&lt;img'))});
test('confidence/retention/surge numeric placeholders absent',()=>{const h=fs.readFileSync('frontend/tools/trend-analyzer.html','utf8');for(const bad of ['94.2%','64.5%','52%','34%','14%','Updated just now','+148% Surge','+42.8%'])assert(!h.includes(bad),bad);assert(!fs.readFileSync('frontend/js/tools/trend-analyzer.js','utf8').includes('"38.4"'))});
test('partial sentiment is unavailable rather than filling missing classes with zero',()=>{c.renderDeepIntelligence({sentiment:{positive_score:10}});assert.match(text('sentimentBreakdown'),/Unavailable/)});
test('legacy multi-point timeline without cohort evidence is unavailable',()=>{c.renderDeepIntelligence({trend_intelligence:{timeline:[{date:'2026-10-20',views:1},{date:'2026-10-21',views:2}]}});assert.equal(vm.runInContext('currentTimelineRaw.length',c),0)});
test('generic counter formatter distinguishes zero from missing',()=>{assert.equal(c.formatCompact(0),'0');assert.equal(c.formatCompact(null),'Unavailable')});
test('negative observed changes retain their sign and count',()=>{c.renderLowerChart([{date:'2026-10-20',views:30},{date:'2026-10-21',views:10}]);assert.match(nodes.get('chartBaselineNote').innerHTML,/-20/)});
console.log(`${count} data truth behavior tests passed`);
