'use strict';
const $ = id => document.getElementById(id);
const state = {page:'dashboard', records:{companies:[],contacts:[],deals:[],tasks:[],activities:[]}, query:'', filter:'', offset:0, editing:null, aiPreview:null};
const stages = ['lead','qualified','proposal','won','lost'];
const labels = {dashboard:'Overview',contacts:'Contacts',companies:'Companies',deals:'Sales pipeline',tasks:'Follow-ups',activities:'Activity timeline',ai:'AI assistant'};
const singular = {companies:'company',contacts:'contact',deals:'deal',tasks:'task',activities:'activity'};
const subtitles = {dashboard:'A clear view of your relationships and next steps.',contacts:'Keep the people behind every opportunity in view.',companies:'Build a useful picture of each customer.',deals:'Move opportunities forward, one conversation at a time.',tasks:'Make the next step clear. Keep your promises.',activities:'The conversations and notes that keep work moving.',ai:'Select context, inspect it, and request a suggestion.'};
const icons = {dashboard:'◫',contacts:'♙',companies:'▤',deals:'▥',tasks:'✓',activities:'◷',ai:'✧'};
function el(tag, attrs={}, ...children) {
  const node = document.createElement(tag);
  for (const [key,value] of Object.entries(attrs)) {
    if (key==='class') node.className=value;
    else if (key==='text') node.textContent=value;
    else if (key.startsWith('on')) node.addEventListener(key.slice(2),value);
    else if (value!==null && value!==undefined) node.setAttribute(key,value);
  }
  for (const child of children.flat()) if (child!==null && child!==undefined) node.append(child instanceof Node ? child : document.createTextNode(String(child)));
  return node;
}
function button(text, action, cls='secondary'){return el('button',{type:'button',class:cls,onclick:action},text);}
function notice(message, error=false){$('notice').textContent=message;$('notice').className=error?'error':'';$('notice').hidden=false;}
async function api(path, options={}) {
  const response = await fetch('/api/v1/'+path,{...options,headers:{'Content-Type':'application/json',...options.headers}});
  if (!response.ok) {
    const data=await response.json().catch(()=>({}));
    const error=data.error;
    throw new Error(error?.details?.map(d=>d.location.slice(1).join('.')+': '+d.message).join('\n') || error?.message || 'Request failed ('+response.status+').');
  }
  return response.status===204 ? null : response.json();
}
async function all(kind){let items=[],offset=0;while(true){const data=await api(kind+'?limit=100&offset='+offset);items.push(...data.items);offset+=data.items.length;if(offset>=data.total||!data.items.length)break;}return items;}
async function reload(){
  const kinds=Object.keys(state.records);
  const results=await Promise.all(kinds.map(all));
  kinds.forEach((kind,i)=>state.records[kind]=results[i]);
  state.aiPreview=null;
}
function nameOf(kind,id){return state.records[kind].find(r=>r.id===id)?.name || state.records[kind].find(r=>r.id===id)?.title || '—';}
function badge(value){return el('span',{class:'badge '+value},value.replaceAll('_',' '));}
function empty(text='No records yet.',hint='Add your first record to get started.'){return el('div',{class:'empty'},el('strong',{},text),hint);}
function localDate(){const d=new Date();return [d.getFullYear(),String(d.getMonth()+1).padStart(2,'0'),String(d.getDate()).padStart(2,'0')].join('-');}
function money(amount,currency){return currency+' '+Number(amount).toLocaleString(undefined,{minimumFractionDigits:2,maximumFractionDigits:2});}
function readable(date){return date?new Date(date).toLocaleString():'—';}
function recordActions(kind,record){return el('div',{class:'row-actions'},button('View',()=>details(kind,record)),button('Edit',()=>edit(kind,record)),button('Delete',()=>remove(kind,record),'danger'));}
async function remove(kind,record){if(!confirm('Delete '+(record.name||record.title||'this activity')+'? Linked records may need to be removed first.'))return;try{await api(kind+'/'+record.id,{method:'DELETE'});await reload();render();notice('Record deleted.');}catch(e){notice(e.message,true);}}
function navigate(page){state.page=page;state.query='';state.filter='';state.offset=0;$('notice').hidden=true;render();}
function render(){
  $('page-title').textContent=labels[state.page];$('page-subtitle').textContent=subtitles[state.page];
  $('nav').replaceChildren(...Object.keys(labels).map(navButton));
  const kind=state.page==='dashboard'?'contacts':state.page;
  $('add').hidden=state.page==='ai';$('add').textContent='+ Add '+(singular[kind]||'contact');$('add').onclick=()=>edit(kind);
  const content=$('content');content.replaceChildren();
  if(state.page==='dashboard')dashboard(content);
  else if(state.page==='ai')aiPage(content);
  else recordsPage(content);
}
function navButton(page){const b=button('',()=>navigate(page),'nav-item'+(state.page===page?' active':''));b.setAttribute('aria-current',state.page===page?'page':'false');b.append(el('span',{class:'nav-icon'},icons[page]),labels[page]);return b;}
function dashboard(root){
  const r=state.records, openDeals=r.deals.filter(d=>!['won','lost'].includes(d.stage)), tasks=r.tasks.filter(t=>t.status!=='done');
  const overdue=tasks.filter(t=>t.due_date&&t.due_date<localDate());
  const stats=el('div',{class:'stats'});
  for(const [label,value,hint,warn] of [['Contacts',r.contacts.length,r.companies.length+' companies'],['Active opportunities',openDeals.length,'Lead, qualified & proposal'],['Open follow-ups',tasks.length,'Your next customer actions'],['Overdue',overdue.length,'Based on this device’s date',true]])stats.append(el('div',{class:'stat'+(warn?' warn':'')},el('div',{class:'stat-label'},label),el('div',{class:'stat-value'},value),el('div',{class:'stat-hint'},hint)));
  root.append(stats);
  const grid=el('div',{class:'grid-two'}), work=el('section',{class:'panel'},el('div',{class:'panel-head'},el('div',{},el('h2',{},'Next up'),el('p',{},'Small steps that keep relationships moving.')),button('All tasks →',()=>navigate('tasks'),'link')));
  const next=tasks.sort((a,b)=>(a.due_date||'9999').localeCompare(b.due_date||'9999')).slice(0,5);
  if(!next.length)work.append(empty('A clear slate','Add a follow-up to plan your next step.'));
  for(const task of next)work.append(el('div',{class:'list-row'},button('✓',()=>complete(task),'secondary'),el('div',{class:'grow'},el('div',{class:'record-name'},task.title),el('p',{},task.due_date?'Due '+task.due_date:'No due date')),button('Open',()=>details('tasks',task),'link')));
  const pipeline=el('section',{class:'panel'},el('div',{class:'panel-head'},el('h2',{},'Pipeline value'),button('View board →',()=>navigate('deals'),'link')));
  const currencies=[...new Set(r.deals.map(d=>d.currency))];
  if(!currencies.length)pipeline.append(empty('Your pipeline starts here','Add an opportunity with a value and stage.'));
  for(const currency of currencies){pipeline.append(el('h3',{},currency));const ds=r.deals.filter(d=>d.currency===currency);const total=ds.reduce((n,d)=>n+Number(d.amount),0);for(const stage of stages){const value=ds.filter(d=>d.stage===stage).reduce((n,d)=>n+Number(d.amount),0);const fill=el('span');fill.style.width=(total?value/total*100:0)+'%';pipeline.append(el('div',{class:'money-line'},badge(stage),money(value,currency)),el('div',{class:'bar'},fill));}}
  grid.append(work,pipeline);root.append(grid);
  const timeline=el('section',{class:'panel'},el('div',{class:'panel-head'},el('h2',{},'Recent conversations'),button('All activity →',()=>navigate('activities'),'link')));
  const recent=[...r.activities].sort((a,b)=>b.occurred_at.localeCompare(a.occurred_at)).slice(0,4);
  if(!recent.length)timeline.append(empty('Every relationship has a story','Log a note, call, or meeting.'));
  recent.forEach(a=>timeline.append(activityRow(a)));root.append(timeline);
}
async function complete(task){try{await api('tasks/'+task.id,{method:'PUT',body:JSON.stringify(payload('tasks',task,{status:'done'}))});await reload();render();notice('Follow-up marked done.');}catch(e){notice(e.message,true);}}
const fieldSpec={
 companies:[['name','Company name','text',true],['industry','Industry'],['website','Website','url'],['notes','Notes','textarea']],
 contacts:[['name','Full name','text',true],['email','Email','email'],['phone','Phone'],['title','Job title'],['company_id','Company','companies'],['tags','Tags (comma separated)']],
 deals:[['title','Opportunity title','text',true],['amount','Amount','number',true],['currency','Currency (3 letters)','text',true],['stage','Stage','stage',true],['expected_close_date','Expected close','date'],['company_id','Company','companies'],['contact_id','Contact','contacts'],['notes','Notes','textarea']],
 tasks:[['title','Follow-up title','text',true],['due_date','Due date','date'],['status','Status','status',true],['company_id','Company','companies'],['contact_id','Contact','contacts'],['deal_id','Deal','deals'],['notes','Notes','textarea']],
 activities:[['type','Activity type','activityType',true],['occurred_at','When','datetime-local',true],['company_id','Company','companies'],['contact_id','Contact','contacts'],['deal_id','Deal','deals'],['note','Conversation / note','textarea',true]]
};
function payload(kind,record,overrides={}){return Object.fromEntries(fieldSpec[kind].map(([key])=>[key,overrides[key]!==undefined?overrides[key]:record[key]??(key==='tags'?[]:null)]));}
function recordsPage(root){
 const kind=state.page;
 const toolbar=el('div',{class:'toolbar'}),search=el('input',{type:'search',placeholder:'Search '+kind+'…','aria-label':'Search '+kind,value:state.query});
 search.addEventListener('input',()=>{state.query=search.value;state.offset=0;draw();});toolbar.append(search);
 if(kind==='deals'||kind==='tasks'){const select=el('select',{'aria-label':'Filter '+kind});select.append(el('option',{value:''},'All '+(kind==='deals'?'stages':'statuses')));for(const value of(kind==='deals'?stages:['open','in_progress','done','overdue']))select.append(el('option',{value},value.replaceAll('_',' ')));select.value=state.filter;select.onchange=()=>{state.filter=select.value;state.offset=0;draw();};toolbar.append(select);}
 const count=el('span',{class:'count'});toolbar.append(count);root.append(toolbar);const body=el('div');root.append(body);
 function draw(){
   let rows=state.records[kind].filter(r=>{const text=[r.name,r.title,r.email,r.industry,r.note,r.notes,...(r.tags||[]),nameOf('companies',r.company_id)].join(' ').toLowerCase();return text.includes(state.query.toLowerCase());});
   if(state.filter)rows=rows.filter(r=>state.filter==='overdue'?r.status!=='done'&&r.due_date&&r.due_date<localDate():(r.stage||r.status)===state.filter);
   count.textContent=rows.length+' '+kind;body.replaceChildren();
   if(!rows.length){body.append(el('div',{class:'panel'},empty(state.query||state.filter?'No matching records':'No '+kind+' yet','Use the add button to create a record.')));return;}
   if(kind==='deals'){const board=el('div',{class:'board'});for(const stage of stages){const group=rows.filter(d=>d.stage===stage),column=el('section',{class:'column'},el('div',{class:'column-title'},stage,el('span',{},group.length)));for(const deal of group){const select=el('select',{'aria-label':'Stage for '+deal.title});stages.forEach(s=>select.append(el('option',{value:s},s)));select.value=deal.stage;select.onchange=()=>changeStage(deal,select.value);column.append(el('article',{class:'deal-card'},el('div',{class:'record-name'},deal.title),el('span',{class:'sub'},nameOf('companies',deal.company_id)),el('div',{class:'amount'},money(deal.amount,deal.currency)),el('span',{class:'sub'},deal.expected_close_date?'Close '+deal.expected_close_date:'No close date'),select,recordActions(kind,deal)));}board.append(column);}body.append(board);return;}
   const pageRows=rows.slice(state.offset,state.offset+25),panel=el('section',{class:'panel'});
   if(kind==='activities')pageRows.forEach(a=>panel.append(activityRow(a,true)));
   else {const heads=kind==='companies'?['Company','Industry','Website','Actions']:kind==='contacts'?['Contact','Company','Email','Actions']:['Follow-up','Linked record','Due date','Status','Actions'];const table=el('table',{},el('thead',{},el('tr',{},heads.map(h=>el('th',{scope:'col'},h))))),tbody=el('tbody');for(const record of pageRows){const title=button(record.name||record.title,()=>details(kind,record),'link record-name');let cells;if(kind==='companies')cells=[title,record.industry||'—',record.website||'—'];else if(kind==='contacts')cells=[el('div',{},title,el('span',{class:'sub'},record.title||'')),nameOf('companies',record.company_id),record.email||'—'];else cells=[title,nameOf(record.deal_id?'deals':'contacts',record.deal_id||record.contact_id),record.due_date||'—',badge(record.status)];tbody.append(el('tr',{},cells.map(c=>el('td',{},c)),el('td',{},recordActions(kind,record))));}table.append(tbody);panel.append(el('div',{class:'table-wrap'},table));}
   const prev=button('← Previous',()=>{state.offset=Math.max(0,state.offset-25);draw();}),next=button('Next →',()=>{state.offset+=25;draw();});prev.disabled=state.offset===0;next.disabled=state.offset+25>=rows.length;panel.append(el('div',{class:'pager'},prev,(state.offset+1)+'–'+Math.min(state.offset+25,rows.length)+' of '+rows.length,next));body.append(panel);
 }
 draw();
}
function activityRow(a,actions=false){return el('article',{class:'list-row'},el('div',{class:'avatar'},a.type.slice(0,1).toUpperCase()),el('div',{class:'grow'},el('div',{class:'record-name'},a.type+' · '+nameOf(a.deal_id?'deals':a.contact_id?'contacts':'companies',a.deal_id||a.contact_id||a.company_id)),el('p',{},a.note),el('span',{class:'sub'},readable(a.occurred_at))),actions?recordActions('activities',a):null);}
async function changeStage(deal,stage){try{await api('deals/'+deal.id,{method:'PUT',body:JSON.stringify(payload('deals',deal,{stage}))});await reload();render();notice('Deal moved to '+stage+'.');}catch(e){notice(e.message,true);render();}}
function edit(kind,record=null){
 state.editing={kind,record};$('editor-title').textContent=(record?'Edit ':'New ')+singular[kind];$('fields').replaceChildren();$('form-error').textContent='';
 for(const [key,label,type='text',required=false] of fieldSpec[kind]){
   let input;const choices={stage:stages,status:['open','in_progress','done'],activityType:['note','call','meeting','email']}[type];
   if(choices||['companies','contacts','deals'].includes(type)){input=el('select',{name:key,id:'field-'+key});if(!required)input.append(el('option',{value:''},'None'));for(const choice of choices||state.records[type])input.append(el('option',{value:typeof choice==='string'?choice:choice.id},typeof choice==='string'?choice:choice.name||choice.title));}
   else input=el(type==='textarea'?'textarea':'input',{name:key,id:'field-'+key,type:type==='textarea'?null:type});
   let value=record?.[key]??({amount:'0',currency:'USD',stage:'lead',status:'open',type:'note'}[key]||'');
   if(key==='tags')value=(record?.tags||[]).join(', ');
   if(key==='occurred_at'){const d=record?new Date(record.occurred_at):new Date();value=new Date(d.getTime()-d.getTimezoneOffset()*60000).toISOString().slice(0,16);}
   input.value=value;input.required=required;if(type==='number'){input.min='0';input.max='999999999999.99';input.step='0.01';}
   if(type==='text'||type==='email'||type==='url')input.maxLength=key==='email'?254:key==='website'?500:key==='phone'?60:200;
   if(type==='textarea')input.maxLength=5000;
   if(key==='currency'){input.maxLength=3;input.pattern='[A-Z]{3}';}
   $('fields').append(el('label',{for:input.id,class:type==='textarea'?'wide':''},label+(required?' *':''),input));
 }
 $('editor').showModal();
}
$('record-form').onsubmit=async event=>{
 event.preventDefault();const {kind,record}=state.editing,data={};
 for(const [key] of fieldSpec[kind]){const value=$('record-form').elements.namedItem(key).value.trim();data[key]=key==='tags'?value.split(',').map(t=>t.trim()).filter(Boolean):key==='occurred_at'?new Date(value).toISOString():value||null;}
 $('save').disabled=true;
 try{await api(kind+(record?'/'+record.id:''),{method:record?'PUT':'POST',body:JSON.stringify(data)});$('editor').close();await reload();render();notice('Record saved.');}catch(e){$('form-error').textContent=e.message;}finally{$('save').disabled=false;}
};
async function details(kind,record){
 $('detail-title').textContent=record.name||record.title||'Activity';const body=$('detail-body');body.replaceChildren();
 for(const [key,label] of fieldSpec[kind]){let value=record[key];if(key.endsWith('_id'))value=nameOf(key==='company_id'?'companies':key==='contact_id'?'contacts':'deals',value);if(Array.isArray(value))value=value.join(', ');body.append(el('div',{class:'detail-pair'},el('strong',{},label),value||'—'));}
 body.append(button('Edit record',()=>{$('detail').close();edit(kind,record);},'primary'));
 const related=(r)=>r[(kind==='companies'?'company':kind==='contacts'?'contact':'deal')+'_id']===record.id;
 if(['companies','contacts','deals'].includes(kind)){
   for(const rel of ['contacts','deals','tasks','activities']){if(rel===kind)continue;const records=state.records[rel].filter(related);if(!records.length)continue;const section=el('section',{class:'detail-section'},el('h3',{},rel));for(const r of records)section.append(el('div',{class:'list-row'},el('div',{class:'grow'},r.name||r.title||r.note),button('View',()=>details(rel,r),'link')));body.append(section);}
 }
 if(!$('detail').open)$('detail').showModal();
 if(kind==='deals')try{const data=await api('deals/'+record.id+'/history');const section=el('section',{class:'detail-section'},el('h3',{},'Stage history'));data.items.forEach(h=>section.append(el('p',{class:'sub'},(h.from_stage||'Created')+' → '+h.to_stage+' · '+readable(h.changed_at))));if($('detail-title').textContent===record.title)body.append(section);}catch(e){notice(e.message,true);}
}
function aiPage(root){
 const intro=el('div',{class:'intro'},el('strong',{},'Local mock · No API key needed'),el('p',{},'This deterministic demo formats selected names into a suggestion. It does not call an AI model or change records.'));
 const panel=el('section',{class:'panel'},el('h2',{},'Choose customer context'),el('p',{class:'sub'},'Select up to 20 contacts and companies. Email, phone, and notes are excluded.'));
 const selection={contact_ids:[],company_ids:[]};
 for(const kind of ['contacts','companies']){panel.append(el('h3',{},kind));if(!state.records[kind].length)panel.append(el('p',{class:'sub'},'Add '+kind+' first.'));for(const r of state.records[kind]){const check=el('input',{type:'checkbox',value:r.id});check.onchange=()=>{const key=kind==='contacts'?'contact_ids':'company_ids';selection[key]=check.checked?[...selection[key],r.id]:selection[key].filter(id=>id!==r.id);state.aiPreview=null;confirmButton.disabled=true;output.textContent='Selection changed. Preview context again.';};panel.append(el('label',{class:'check-row'},check,r.name));}}
 const output=el('pre',{class:'context'},'Your context preview will appear here.'),result=el('div',{class:'context'},'Your suggestion will appear here.');
 const preview=button('1. Preview selected context',async()=>{preview.disabled=true;try{const data=await api('ai/context',{method:'POST',body:JSON.stringify(selection)});state.aiPreview=structuredClone(selection);output.textContent=JSON.stringify(data,null,2);confirmButton.disabled=false;result.textContent='Review the context, then confirm below.';}catch(e){notice(e.message,true);}finally{preview.disabled=false;}},'secondary');
 const confirmButton=button('2. Confirm & generate mock summary',async()=>{confirmButton.disabled=true;try{const data=await api('ai/summarize',{method:'POST',body:JSON.stringify({...state.aiPreview,confirm:true})});result.textContent=data.summary+'\n\nProvider: '+data.provider+' · Model: '+data.model+'\nSources: '+data.source_ids.join(', ');}catch(e){notice(e.message,true);}finally{confirmButton.disabled=!state.aiPreview;}},'primary');confirmButton.disabled=true;
 panel.append(el('div',{class:'ai-controls'},preview,confirmButton),el('h3',{},'Context preview'),output,el('h3',{},'Suggestion for review'),result);root.append(intro,panel);
}
for(const id of ['close-editor','cancel-editor'])$(id).onclick=()=>$('editor').close();
$('close-detail').onclick=()=>$('detail').close();
$('refresh').onclick=async()=>{try{await reload();render();notice('Workspace refreshed.');}catch(e){notice(e.message,true);}};
$('backup').onclick=async()=>{try{const data=await api('backup');const blob=new Blob([JSON.stringify(data,null,2)],{type:'application/json'});const url=URL.createObjectURL(blob);const a=el('a',{href:url,download:'deedee-backup-'+localDate()+'.json'});a.click();URL.revokeObjectURL(url);notice('Backup downloaded. Store it securely; it contains CRM data.');}catch(e){notice(e.message,true);}};
reload().then(render).catch(e=>{$('content').replaceChildren(empty('Unable to load workspace','Start the DeeDee API and try Refresh.'));notice(e.message,true);});
