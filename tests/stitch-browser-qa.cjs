/* Interactive QA against local Flask only. QA dependencies are installed separately. */
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const {execFileSync} = require('node:child_process');
const modules = process.env.STITCH_QA_MODULES;
if (!modules) throw new Error('Set STITCH_QA_MODULES to the isolated QA node_modules directory');
const {chromium} = require(path.join(modules, 'playwright'));
const argv = process.argv.slice(2);
const before = argv.includes('--before');
const screensOnly = argv.includes('--screens-only');
const output = argv.includes('--output') ? path.resolve(argv[argv.indexOf('--output') + 1]) : path.resolve('qa-output');
const base = 'http://127.0.0.1:5067';
const repo = path.resolve(__dirname, '..');
const longText = "QA creator's strategy: " + 'UnbrokenCreatorToken'.repeat(7);
const seo = {score:72, breakdown:[{id:'title',label:'Title quality',points:18,max:25,status:'pass',evidence:'QA fixture metadata'}],suggestions:[{priority:2,component:'description',message:'Add context',fix:'Use a clear description'}],unavailable:{vph:{reason:'Not observable from this snapshot'}}};
const video = {success:true,title:longText,description:'QA description. '.repeat(30),views:340000,engagement_rate:null,virality_score:62,channel_title:'QA channel',published_at:'2026-10-24',thumbnail:base+'/__qa/image',tags:['QA tag',longText],comments:["QA creator's comment"],sentiment:{positive_score:60,neutral_score:30,negative_score:10,sample_comment:'QA sample'},seo_quality:seo};
const channel = {title:longText,custom_url:'@qa_channel',channel_age_years:4,subscribers:12345,total_views:456789,video_count:42,est_monthly_earnings_min:12,est_monthly_earnings_max:48,avatar_url:base+'/__qa/image',top_videos:[{title:longText,views:1234,likes:null,published_at:'2026-10-24'}]};
const yt = {keyword:'QA fixture',trend_id:4242,engagement_rate:5.4,virality_score:62,seo_title_ideas:['QA title'],youtube_tags:['QA tag'],sentiment:{positive_score:60,negative_score:10,neutral_score:30,dominant_sentiment:'positive',sample_comment:'QA comment'},trend_intelligence:{status:'baseline',forecast:{available:false,reason:'QA: more comparable observations required'},historical_context:{},timeline:[{date:'2026-10-25 10:00',views:72500000}],current_direction:'BASELINE'}};
const trend = {videos:[{id:'abcdefghijk',rank:1,title:longText,channel:'QA channel',category:'Gaming',views:72500000,likes:3900000,comments:15000,engagement:5.4,momentumScore:75,hoursAgo:48}],kpis:{totalViews:72500000,avgEngagement:5.4,fastestCategory:'Gaming',topCategoryViews:72500000,risingCount:1,totalTracked:1},timeSeries:[{label:'0–1d old',views:1000000},{label:'1–2d old',views:71500000}],catBreakdown:[{name:'Gaming',value:72500000,hue:'#8B5CF6'}],results:{YouTube:yt}};
function asset(name) { return path.join(modules,name); }
const fonts = {jakarta:'@fontsource-variable/plus-jakarta-sans/files/plus-jakarta-sans-latin-wght-normal.woff2',inter:'@fontsource-variable/inter/files/inter-latin-wght-normal.woff2',icons:'@fontsource/material-symbols-outlined/files/material-symbols-outlined-latin-400-normal.woff2'};
const fontCss = `@font-face{font-family:'Plus Jakarta Sans';src:url('${base}/__qa/font/jakarta');font-weight:100 900}@font-face{font-family:Inter;src:url('${base}/__qa/font/inter');font-weight:100 900}@font-face{font-family:'Material Symbols Outlined';src:url('${base}/__qa/font/icons');font-weight:400}.material-symbols-outlined{font-family:'Material Symbols Outlined';font-weight:normal;font-style:normal;font-size:24px;line-height:1;letter-spacing:normal;text-transform:none;display:inline-block;white-space:nowrap;word-wrap:normal;direction:ltr;font-feature-settings:'liga'}`;

// Measure text fragments as well as boxes against every visible clipping ancestor.
function auditGeometry() {
  const label = e => e.tagName.toLowerCase()+(e.id?'#'+e.id:'.'+[...e.classList].slice(0,3).join('.'));
  const rect = r => ({left:r.left,right:r.right,top:r.top,bottom:r.bottom,width:r.width,height:r.height});
  const visible = e => e.getClientRects().length && getComputedStyle(e).visibility!=='hidden' && !e.closest('[aria-hidden="true"],[inert]');
  const selectors='h1,h2,h3,p,input,textarea,button,a,summary,.stitch-page-header,.stitch-faq-item,.stitch-kpi-card,.stitch-kpi-badge,.stitch-card,.chat-bubble,.chat-chips-wrap';
  const elements=[];const failures=[];const scrollRegions=[];
  const assistiveOnly=[];
  function screenReaderOnly(e){
    for(let a=e;a;a=a.parentElement){
      const c=getComputedStyle(a),r=a.getBoundingClientRect();
      if(c.position==='absolute'&&r.width<=1&&r.height<=1&&c.overflow==='hidden'&&/^rect\(0px[, ]+0px[, ]+0px[, ]+0px\)$/.test(c.clip)){
        assistiveOnly.push({element:label(e),ancestor:label(a),clip:c.clip,rect:rect(r)});return true;
      }
    }
    return false;
  }
  function check(e,r,kind){
    // Vertical clipping must be checked too; page length itself is not a failure.
    for(let a=e;a;a=a.parentElement){
      const cs=getComputedStyle(a),ar=a.getBoundingClientRect();
      if(/hidden|clip|auto|scroll/.test(cs.overflowY)){
        const top=ar.top+a.clientTop,bottom=top+a.clientHeight;
        if(r.top<top-2||r.bottom>bottom+2){
          const ancestor={selector:label(a),rect:rect(ar),overflowY:cs.overflowY,scrollHeight:a.scrollHeight,clientHeight:a.clientHeight};
          if(/auto|scroll/.test(cs.overflowY)&&a.scrollHeight>a.clientHeight+2){scrollRegions.push({element:label(e),ancestor,kind,axis:'y'});break;}
          failures.push({element:label(e),text:e.textContent.trim().slice(0,100),kind,axis:'y',rect:rect(r),ancestor});break;
        }
      }
    }
    let a=e, nearest=null, recoverable=false;
    while(a){const cs=getComputedStyle(a), ar=a.getBoundingClientRect();
      if(/hidden|clip|auto|scroll/.test(cs.overflowX)){
        const left=ar.left+a.clientLeft,right=left+a.clientWidth;
        if(r.left<left-2||r.right>right+2){
          const scroller=/auto|scroll/.test(cs.overflowX)&&a.scrollWidth>a.clientWidth+2;
          nearest={selector:label(a),rect:rect(ar),overflowX:cs.overflowX,scrollWidth:a.scrollWidth,clientWidth:a.clientWidth};
          if(scroller && ar.left>=-2 && ar.right<=innerWidth+2){recoverable=true;scrollRegions.push({element:label(e),ancestor:nearest,kind});break;}
          failures.push({element:label(e),text:e.textContent.trim().slice(0,100),kind,rect:rect(r),ancestor:nearest});return;
        }
      }a=a.parentElement;
    }
    if(!recoverable&&(r.left< -2||r.right>innerWidth+2))failures.push({element:label(e),kind,text:e.textContent.trim().slice(0,100),rect:rect(r),ancestor:{selector:'viewport',width:innerWidth}});
  }
  for(const e of document.querySelectorAll(selectors)){
    if(!visible(e)||screenReaderOnly(e))continue;const r=e.getBoundingClientRect(),c=getComputedStyle(e);
    elements.push({selector:label(e),rect:rect(r),style:{overflowX:c.overflowX,overflowY:c.overflowY,width:c.width,minWidth:c.minWidth,maxWidth:c.maxWidth,whiteSpace:c.whiteSpace,transform:c.transform,display:c.display,flex:c.flex,gridTemplateColumns:c.gridTemplateColumns,padding:c.padding}});
    check(e,r,'box');
  }
  const walker=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);
  while(walker.nextNode()){
    const n=walker.currentNode,e=n.parentElement;
    if(!n.textContent.trim()||!e||!visible(e)||screenReaderOnly(e)||e.closest('script,style,.material-symbols-outlined,[data-qa-label],input,textarea'))continue;
    const range=document.createRange();range.selectNodeContents(n);
    for(const r of range.getClientRects())if(r.width&&r.height)check(e,r,'text');
  }
  return {viewport:innerWidth,documentWidth:document.documentElement.scrollWidth,elements,failures,scrollRegions,assistiveOnly};
}

(async()=>{
  fs.mkdirSync(output,{recursive:true});
  const browser=await chromium.launch({executablePath:process.env.STITCH_QA_BROWSER||'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',headless:true});
  const report={baseline:'45d16454741384e15c17044774ff4b7346b3871a',mode:before?'before':'after',mocked:true,apiRequests:[],cases:[],checks:[],errors:[]};
  async function makePage(width){
    const context=await browser.newContext({viewport:{width,height:900},deviceScaleFactor:1,permissions:['clipboard-read','clipboard-write'],reducedMotion:'reduce'});
    const page=await context.newPage();page.setDefaultTimeout(10000);
    page.on('pageerror',e=>report.errors.push(e.message));
    await page.route('**/*',async route=>{
      const req=route.request(),u=new URL(req.url());
      if(u.pathname.startsWith('/__qa/font/'))return route.fulfill({path:asset(fonts[u.pathname.split('/').pop()]),contentType:'font/woff2'});
      if(u.hostname==='fonts.googleapis.com')return route.fulfill({body:fontCss,contentType:'text/css'});
      if(u.hostname==='cdn.jsdelivr.net')return route.fulfill({path:asset('chart.js/dist/chart.umd.js'),contentType:'text/javascript'});
      if(u.pathname==='/__qa/image'||u.hostname==='i.ytimg.com')return route.fulfill({contentType:'image/svg+xml',body:'<svg xmlns="http://www.w3.org/2000/svg" width="640" height="360"><rect width="640" height="360" fill="#eef2ff"/><text x="30" y="180" fill="#334155">QA fixture thumbnail</text></svg>'});
      if(u.origin!==base)return route.abort();
      if(u.pathname.startsWith('/api/')){
        report.apiRequests.push({path:u.pathname,method:req.method()});
        const body=req.postDataJSON?.()||{}, mode=u.searchParams.get('q')||body.url||body.identifier||body.message||'';
        if(u.pathname.includes('suggest'))return route.fulfill({json:{suggestions:[]}});
        if(u.pathname.includes('/report/')||u.pathname.includes('/export-csv/'))return route.fulfill({body:'QA fixture export',headers:{'Content-Disposition':'attachment; filename="qa-fixture.txt"','Content-Type':'text/plain'}});
        if(mode==='error')return route.fulfill({status:503,json:{error:'QA fixture upstream unavailable'}});
        if(mode==='quota')return route.fulfill({status:429,json:{error:'QA fixture quota reached'}});
        let data;
        if(u.pathname.includes('trending')){
          data=structuredClone(trend);
          if(mode==='empty'){data.videos=[];data.results={};data.kpis={};data.timeSeries=[];data.catBreakdown=[];}
          if(mode==='stale'){data.cached=true;data.is_stale=true;}
          if(mode==='missing')data.kpis={totalViews:0,avgEngagement:null,fastestCategory:null,risingCount:null};
          if(mode==='changed'){data.kpis.totalViews=2000000;data.timeSeries=[{label:'unavailable age',views:2000000},{label:'unavailable age',views:0}];}
          if(mode==='history')data.results.YouTube.trend_intelligence.timeline=[{date:'2026-10-24 10:00',views:100},{date:'2026-10-25 10:00',views:150,smoothed_views:140}];
          if(mode==='nohistory')data.results.YouTube.trend_intelligence.timeline=[];
        }else if(u.pathname.includes('video-analysis')){
          data=structuredClone(video);if(mode==='empty'){data.description='';data.tags=[];data.comments=[];}
        }else if(u.pathname.includes('audit-channel')){
          data=structuredClone(channel);if(mode==='empty')data.top_videos=[];
        }else if(u.pathname.includes('/seo/analyze'))data=seo;
        else if(u.pathname==='/api/chat')data={reply:'## QA fixture response\n'+longText+'\n- A repeatable recommendation, not measured YouTube analytics.'};
        else data={error:'QA unexpected endpoint'};
        return route.fulfill({json:data});
      }
      if(before){
        let file;
        if(u.pathname==='/tools'||u.pathname==='/tools/')file='frontend/tools/index.html';
        else if(/^\/tools\/[^/]+\/?$/.test(u.pathname))file='frontend'+u.pathname.replace(/\/$/,'')+'.html';
        else if(/^\/(css|js)\//.test(u.pathname))file='frontend'+u.pathname;
        if(file){const content=execFileSync('git',['show','45d1645:'+file],{cwd:repo});return route.fulfill({body:content,contentType:file.endsWith('.html')?'text/html':file.endsWith('.css')?'text/css':'text/javascript'});}
      }
      return route.continue();
    });return {page,context};
  }
  async function record(page,tool,width,state){
    await page.evaluate(()=>document.fonts.ready);await page.waitForTimeout(100);
    await page.evaluate(()=>{if(!document.querySelector('[data-qa-label]')){const e=document.createElement('div');e.dataset.qaLabel='true';e.textContent='QA FIXTURE — no live YouTube/Groq calls';e.style.cssText='position:fixed;bottom:0;left:0;right:0;z-index:2000;background:#0f172a;color:#fff;font:11px sans-serif;text-align:center;padding:3px;pointer-events:none';document.body.appendChild(e);}});
    const geometry=await page.evaluate(auditGeometry);
    const item={tool,width,state,...geometry};
    {
      await page.addScriptTag({path:asset('axe-core/axe.min.js')});
      item.accessibility=(await page.evaluate(async()=>await axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21a','wcag21aa']}}))).violations.map(v=>({id:v.id,impact:v.impact,nodes:v.nodes.map(n=>({target:n.target,summary:n.failureSummary}))}));
    }
    // Keep the fixture notice at the end of full-page evidence, not over product text.
    await page.screenshot({path:path.join(output,`${tool}-${width}-${state}.png`),fullPage:true,style:'[data-qa-label] { position: static !important; }'});
    if(state==='success'){await page.evaluate(()=>window.scrollTo(0,0));await page.screenshot({path:path.join(output,`${tool}-${width}-viewport.png`)});}
    report.cases.push(item);fs.writeFileSync(path.join(output,'measurements.json'),JSON.stringify(report,null,2));
  }
  async function check(name,fn){try{await fn();report.checks.push({name,passed:true});}catch(e){report.checks.push({name,passed:false,error:e.message.slice(0,300)});}}
  for(const width of (screensOnly?[320,390]:[320,390,1440]))for(const tool of ['trend-analyzer','video-analyzer','competitor-audit','ai-strategist','tools-hub']){
    const {page,context}=await makePage(width);await page.goto(base+'/tools'+(tool==='tools-hub'?'':'/'+tool),{waitUntil:'networkidle'});
    if(screensOnly){
      if(tool==='trend-analyzer')await page.waitForFunction(()=>document.getElementById('kpiTotalViewsVal').textContent!=='—');
      if(tool==='video-analyzer'||tool==='competitor-audit'){
        await page.locator(tool==='video-analyzer'?'#videoUrlInput':'#channelInput').fill('QA fixture');
        await page.locator(tool==='video-analyzer'?'#analyzeVideoBtn':'#auditBtn').click();
        await page.locator('#resultsArea').waitFor({state:'visible'});
      }
      if(tool==='ai-strategist'){await page.locator('#chatInput').fill(longText);await page.locator('#chatSendBtn').click();await page.waitForTimeout(100);}
      await record(page,tool,width,'success');await context.close();continue;
    }
    if(width<1024){await check(`${tool}/${width} drawer keyboard`,async()=>{
      await page.locator('.stitch-hamburger-btn').click();await page.waitForTimeout(50);
      const drawer=page.locator('#stitchMobileDrawer');const count=await drawer.locator('button,a[href]').count();
      for(let i=0;i<count+2;i++){await page.keyboard.press('Tab');assert(await drawer.evaluate(e=>e.contains(document.activeElement)));}
      for(let i=0;i<count+2;i++){await page.keyboard.press('Shift+Tab');assert(await drawer.evaluate(e=>e.contains(document.activeElement)));}
      await page.keyboard.press('Escape');assert.equal(await drawer.getAttribute('aria-hidden'),'true');assert(await page.locator('.stitch-hamburger-btn').evaluate(e=>e===document.activeElement));
      await page.locator('.stitch-hamburger-btn').click();await page.locator('.stitch-drawer-close-btn').click();
    });await page.evaluate(()=>{if(document.getElementById('stitchMobileDrawer')?.classList.contains('active'))closeSidebarDrawer();});}
    if(tool==='trend-analyzer'){
      await page.waitForFunction(()=>document.getElementById('kpiTotalViewsVal').textContent!=='—');
      await record(page,tool,width,'success');
      for(const mode of ['empty','error','quota','stale','missing','changed','history','nohistory']){
        await page.locator('#pulseSearchInput').fill(mode);await page.locator('#pulseSearchInput').press('Enter');await page.waitForTimeout(120);
        await record(page,tool,width,mode);
        await check(`${tool}/${width} ${mode}`,async()=>{
          const text=await page.locator('#kpiTotalViewsVal').innerText();
          if(['empty','error','quota'].includes(mode)){assert.equal(text,'—');assert(!await page.locator('#resultsArea').isVisible());}
          if(mode==='missing')assert.equal(await page.locator('#kpiAvgEngVal').innerText(),'—');
          if(mode==='stale')assert.match(await page.locator('#kpiTotalViewsDeltaText').innerText(),/stale/i);
          if(mode==='changed'){assert.equal(text,'2M');const chart=await page.evaluate(()=>{const c=Chart.getChart('pulseViewsChart');return {type:c.config.type,labels:c.data.labels,values:c.data.datasets[0].data};});assert.deepEqual(chart.labels,['unavailable age','unavailable age']);assert.deepEqual(chart.values,[2000000,0]);assert.equal(chart.type,'bar');}
          if(mode==='history'){const c=await page.evaluate(()=>{const c=Chart.getChart('viewsChart');return {labels:c.data.labels,datasets:c.data.datasets.map(d=>d.data)};});assert.deepEqual(c.labels,['2026-10-24 10:00','2026-10-25 10:00']);assert.deepEqual(c.datasets,[[100,140],[100,150]]);}
          if(mode==='nohistory')assert(await page.locator('#viewsChartEmpty').isVisible());
        });
      }
      await check(`${tool}/${width} controls and exports`,async()=>{
        await page.locator('#pulseSearchInput').fill('QA fixture');await page.locator('#analyzeBtn').click();await page.waitForTimeout(120);
        for(const chip of await page.locator('[data-copy]').all()){
          await chip.focus();await page.keyboard.press('Enter');
          await page.waitForFunction(()=>[...document.querySelectorAll('[data-copy]')].some(e=>e.textContent.includes('Copied')));
        }
        await page.selectOption('#pulseRegionSelect','United States');
        for(const button of await page.locator('[data-timeframe]').all())await button.click();
        for(const button of await page.locator('#pulseCatScroller button').all())await button.click();
        for(const button of await page.locator('[data-range]').all())if(await button.isVisible())await button.click();
        const forecast=page.locator('#forecastPanel');if(await forecast.isVisible()){await forecast.locator('summary').click();await forecast.locator('summary').click();}
        for(const [id,target] of [['ctaStrategistBtn','/tools/ai-strategist'],['ctaCompetitorBtn','/tools/competitor-audit']]){
          if(await page.locator('#'+id).isVisible()){await page.locator('#'+id).click();await page.waitForURL(u=>u.pathname===target);await page.goBack({waitUntil:'networkidle'});await page.waitForTimeout(120);}
        }
        for(const id of ['exportPdfBtn','exportCsvBtn'])if(await page.locator('#'+id).count()){await Promise.all([page.waitForEvent('download'),page.locator('#'+id).click()]);}
      });
    } else if(tool==='video-analyzer'||tool==='competitor-audit'){
      const input=tool==='video-analyzer'?'#videoUrlInput':'#channelInput',button=tool==='video-analyzer'?'#analyzeVideoBtn':'#auditBtn';
      await page.locator(button).click();await check(`${tool}/${width} empty submission`,async()=>assert(await page.locator('#statusLine').isVisible()));
      await page.locator(input).fill('QA fixture');await page.locator(input).press('Enter');await page.locator('#resultsArea').waitFor({state:'visible'});await record(page,tool,width,'success');
      if(tool==='video-analyzer')await check(`${tool}/${width} copy and draft actions`,async()=>{
        const tag=page.locator('#tagsContainer button').first();await tag.focus();await page.keyboard.press('Enter');
        await page.waitForFunction(()=>document.querySelector('#tagsContainer button')?.textContent.includes('Copied'));
        for(const id of ['copyTitleBtn','copyDescBtn','copyTagsBtn']){await page.locator('#'+id).click();await page.waitForFunction(id=>document.getElementById(id).textContent.includes('Copied'),id);}
        await page.locator('#toggleDraftBtn').click();await page.locator('#seoDraftTitleInput').fill('');await page.locator('#reanalyzeSeoBtn').click();assert.match(await page.locator('#seoDraftStatus').innerText(),/required/i);
        await page.locator('#seoDraftTitleInput').fill(longText);await page.locator('#reanalyzeSeoBtn').click();await page.waitForTimeout(100);assert.match(await page.locator('#seoDraftStatus').innerText(),/successfully/);await record(page,tool,width,'draft');await page.locator('#toggleDraftBtn').click();
      });
      await check(`${tool}/${width} sample button`,async()=>{await page.getByRole('button',{name:/Sample$/}).click();await page.locator('#resultsArea').waitFor({state:'visible'});});
      for(const mode of ['empty','error']){await page.locator(input).fill(mode);await page.locator(button).click();await page.waitForTimeout(100);await record(page,tool,width,mode);}
    } else if(tool==='ai-strategist'){
      await check(`${tool}/${width} empty composer`,async()=>{const n=report.apiRequests.length;await page.locator('#chatSendBtn').click();assert.equal(report.apiRequests.length,n);});
      await page.locator('#chatInput').fill(longText);await page.locator('#chatInput').press('Enter');await page.waitForTimeout(100);await record(page,tool,width,'success');
      await check(`${tool}/${width} response actions and chips`,async()=>{
        for(const button of await page.locator('#chatChips button').all()){await button.click();await page.waitForTimeout(80);}
        await page.locator('#chatInput').fill("A creator's QA response");await page.locator('#chatSendBtn').click();await page.waitForTimeout(80);
        const actions=page.locator('.chat-bubble-action-wrap').last();
        await actions.getByRole('button',{name:/Copy Advice/}).click();await page.waitForFunction(()=>[...document.querySelectorAll('.chat-bubble-action-wrap button')].some(e=>e.textContent.includes('Copied')));
        for(const name of [/Shorts Script/,/Tags.*SEO/]){await page.locator('.chat-bubble-action-wrap').last().getByRole('button',{name}).click();await page.waitForTimeout(80);}
      });
      await page.locator('#chatInput').fill('error');await page.locator('#chatSendBtn').click();await page.waitForTimeout(80);await record(page,tool,width,'error');
      await page.getByRole('button',{name:/Clear/,exact:false}).click();await record(page,tool,width,'cleared');
    } else {await record(page,tool,width,'success');await check(`${tool}/${width} launch links`,async()=>{
      const targets=await page.locator('.stitch-kpi-grid a').evaluateAll(es=>es.map(e=>e.getAttribute('href')));
      for(const target of targets){await page.locator('.stitch-kpi-grid a[href="'+target+'"]').click();await page.waitForURL(u=>u.pathname===target);await page.goBack({waitUntil:'networkidle'});}

    });}
    if(width===1440)await check(`${tool}/${width} input focus action`,async()=>{
      await page.keyboard.press('Control+k');
      if(tool==='tools-hub'){await page.waitForURL(u=>u.pathname==='/tools/trend-analyzer');await page.goBack({waitUntil:'networkidle'});}
      else assert(await page.locator('#pulseSearchInput,#videoUrlInput,#channelInput,#chatInput').evaluate(e=>e===document.activeElement));
    });
    // Each visible navigation/CTA target must resolve through the local Flask router.
    await check(`${tool}/${width} navigation and CTA destinations`,async()=>{
      const links=await page.locator('a[href^="/"]').evaluateAll(es=>[...new Set(es.map(e=>e.getAttribute('href')))]);
      for(const link of links){const u=new URL(link,base);const res=await page.request.get(u.origin+u.pathname,{failOnStatusCode:false});assert(res.status()<400,link+' returned '+res.status());}
    });
    await check(`${tool}/${width} keyboard reachability`,async()=>{
      await page.evaluate(()=>{document.activeElement?.blur();window.scrollTo(0,0);});
      const count=await page.evaluate(()=>{let i=0;for(const e of document.querySelectorAll('a[href],button,input,select,textarea,[tabindex]')){if(e.getClientRects().length&&!e.disabled&&e.tabIndex>=0&&!e.closest('[inert],[aria-hidden="true"]'))e.dataset.qaFocusId=String(++i);}return i;});
      for(const key of ['Tab','Shift+Tab']){
        const reached=new Set();
        for(let i=0;i<count+3;i++){await page.keyboard.press(key);const active=await page.evaluate(()=>({hidden:!!document.activeElement?.closest('[inert],[aria-hidden="true"]'),id:document.activeElement?.dataset.qaFocusId}));assert(!active.hidden);if(active.id)reached.add(active.id);}
        assert.equal(reached.size,count,'Every enabled visible control must be keyboard reachable in '+key+' order');
      }
    });
    await context.close();
  }
  await browser.close();fs.writeFileSync(path.join(output,'measurements.json'),JSON.stringify(report,null,2));
  const summary={mode:report.mode,cases:report.cases.length,geometryFailures:report.cases.reduce((n,c)=>n+c.failures.length,0),failedChecks:report.checks.filter(c=>!c.passed),accessibility:report.cases.filter(c=>c.accessibility?.length).map(c=>({tool:c.tool,width:c.width,violations:c.accessibility.map(v=>v.id)})),pageErrors:report.errors};
  fs.writeFileSync(path.join(output,'summary.json'),JSON.stringify(summary,null,2));console.log(JSON.stringify(summary,null,2));
  if(!before&&(summary.geometryFailures||summary.failedChecks.length||summary.pageErrors.length||summary.accessibility.length))process.exitCode=1;
})().catch(e=>{console.error(e.stack);process.exit(1)});
