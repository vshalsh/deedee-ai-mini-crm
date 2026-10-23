// Start an isolated temporary database/API and run either DOM or browser checks.
const {spawn} = require('node:child_process');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const mode=process.argv[2]||'dom';
if(!['dom','browser'].includes(mode))throw Error('Use dom or browser');
const directory=fs.mkdtempSync(path.join(os.tmpdir(),'deedee-ui-'));
const port=20000+Math.floor(Math.random()*30000);
const url='http://127.0.0.1:'+port;
const root=path.join(__dirname,'..');
const server=spawn(process.env.DEEDEE_TEST_PYTHON||'python',['-m','uvicorn','deedee.api:create_app','--factory','--host','127.0.0.1','--port',String(port)],{
 cwd:root,env:{...process.env,DEEDEE_DB_PATH:path.join(directory,'crm.db')},stdio:['ignore','ignore','inherit']});
let startupError;server.on('error',e=>startupError=e);
(async()=>{
 try{
  let ready=false;
  for(let i=0;i<200;i++){
   if(startupError)throw startupError;
   if(server.exitCode!==null)throw Error('API exited before startup');
   try{ready=(await fetch(url+'/health')).ok;}catch{}
   if(ready)break;await new Promise(r=>setTimeout(r,50));
  }
  if(!ready)throw Error('API startup timeout');
  const test=spawn(process.execPath,[path.join(__dirname,mode==='dom'?'ui_dom_smoke.cjs':'browser_smoke.cjs')],{
   cwd:root,env:{...process.env,DEEDEE_TEST_URL:url},stdio:'inherit'});
  const code=await new Promise((resolve,reject)=>{test.on('exit',resolve);test.on('error',reject);});
  process.exitCode=code||0;
 }finally{
  server.kill('SIGTERM');
  await new Promise(resolve=>{if(server.exitCode!==null)resolve();else server.once('exit',resolve);});
  fs.rmSync(directory,{recursive:true,force:true});
 }
})().catch(e=>{console.error(e);process.exitCode=1;});
