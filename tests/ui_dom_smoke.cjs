// Runs UI handlers against a real DeeDee API using jsdom (no visual layout engine).
// Use a fresh temporary database: npm install --no-save jsdom; node tests/ui_dom_smoke.cjs
const {JSDOM} = require('jsdom');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const base=process.env.DEEDEE_TEST_URL||'http://127.0.0.1:8765';
const pause=()=>new Promise(resolve=>setTimeout(resolve,25));
async function wait(test){for(let n=0;n<200;n++){if(test())return;await pause();}throw Error('UI timeout');}

(async()=>{
 const dom=new JSDOM(await (await fetch(base)).text(),{url:base,runScripts:'outside-only'});
 const w=dom.window,d=w.document,errors=[];
 w.fetch=(url,options)=>fetch(new URL(url,base),options);
 w.confirm=()=>true;w.structuredClone=structuredClone;
 w.HTMLDialogElement.prototype.showModal=function(){this.open=true;};
 w.HTMLDialogElement.prototype.close=function(){this.open=false;};
 w.addEventListener('error',e=>errors.push(e.message));
 try{
 w.eval(fs.readFileSync(path.join(__dirname,'../src/deedee/static/app.js'),'utf8'));
 await wait(()=>d.querySelectorAll('#nav button').length===7);
 const nav=name=>[...d.querySelectorAll('#nav button')].find(b=>b.textContent.includes(name)).click();
 const change=(key,value)=>{d.getElementById('field-'+key).value=value;};
 const save=async()=>{d.getElementById('record-form').dispatchEvent(new w.Event('submit',{bubbles:true,cancelable:true}));await wait(()=>!d.getElementById('editor').open);await wait(()=>!d.getElementById('save').disabled);};
 const add=()=>d.getElementById('add').click();
 nav('Companies');add();change('name','DOM Example');await save();
 nav('Contacts');add();change('name','DOM Alex');change('email','dom@example.com');
 const company=[...d.getElementById('field-company_id').options].find(o=>o.textContent==='DOM Example').value;change('company_id',company);await save();
 nav('Sales pipeline');add();change('title','DOM Opportunity');change('amount','123.45');change('company_id',company);await save();
 const stage=d.querySelector('.deal-card select');stage.value='proposal';stage.dispatchEvent(new w.Event('change'));
 await wait(()=>d.getElementById('notice').textContent==='Deal moved to proposal.');
 nav('Follow-ups');add();change('title','DOM next step');change('due_date','2030-12-01');await save();
 nav('Activity timeline');add();change('note','<script>unsafe()</script> A meeting note');change('company_id',company);await save();
 assert(d.getElementById('content').textContent.includes('<script>unsafe()</script>'));
 assert.equal(d.getElementById('content').querySelectorAll('script').length,0);
 nav('AI assistant');const check=[...d.querySelectorAll('.check-row')].find(l=>l.textContent==='DOM Alex').querySelector('input');check.checked=true;check.dispatchEvent(new w.Event('change'));
 const buttons=[...d.querySelectorAll('.ai-controls button')];assert(buttons[1].disabled);buttons[0].click();await wait(()=>!buttons[1].disabled);buttons[1].click();
 await wait(()=>d.getElementById('content').textContent.includes('Local mock summary: contacts: DOM Alex'));
 nav('Overview');const done=[...d.querySelectorAll('#content button')].find(b=>b.textContent==='✓');done.click();await wait(()=>d.getElementById('notice').textContent==='Follow-up marked done.');
 assert(d.getElementById('content').textContent.includes('A clear slate'));
 const snapshot=await(await fetch(base+'/api/v1/backup')).json();
 assert.equal(snapshot.tasks.find(t=>t.title==='DOM next step').status,'done');
 assert.equal(snapshot.deals.find(t=>t.title==='DOM Opportunity').stage,'proposal');
 assert.deepEqual(errors,[]);
 console.log('UI DOM smoke passed: creation across five modules, stage update, safe text rendering, context preview and summary, task completion, and persisted API state. Visual browser layout not tested.');
 }finally{w.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
