// Optional browser check: start DeeDee against a fresh disposable database first.
// npm install --no-save playwright; node tests/browser_smoke.cjs
const {chromium} = require('playwright');
const assert = require('node:assert/strict');

(async()=>{
 const packaged=process.env.DEEDEE_PACKAGED_CHROMIUM?require('@sparticuz/chromium'):null;
 const bundled=packaged?.default||packaged;
 const browser=await chromium.launch({headless:true,...(bundled?{
  executablePath:await bundled.executablePath(),args:bundled.args}: {})});
 try {
  const page=await browser.newPage({viewport:{width:1440,height:1000}});
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto(process.env.DEEDEE_TEST_URL||'http://127.0.0.1:8765');
  await page.waitForSelector('#nav button');
  const nav=async(name)=>{await page.locator('#nav button').filter({hasText:name}).click();};
  const save=async()=>{await page.locator('#save').click();await page.locator('#editor').waitFor({state:'hidden'});};
  const add=async()=>{await page.locator('#add').click();};
  await nav('Companies');await add();
  await page.locator('#field-name').fill('Browser Example Co');
  await page.locator('#field-industry').fill('Software');await save();
  await page.getByRole('button',{name:'Browser Example Co',exact:true}).waitFor();
  await nav('Contacts');await add();
  await page.locator('#field-name').fill('Browser Alex');await page.locator('#field-email').fill('alex@example.com');
  await page.locator('#field-company_id').selectOption({label:'Browser Example Co'});await save();
  await nav('Sales pipeline');await add();
  await page.locator('#field-title').fill('Browser Pilot');await page.locator('#field-amount').fill('12000.50');
  await page.locator('#field-company_id').selectOption({label:'Browser Example Co'});
  await page.locator('#field-contact_id').selectOption({label:'Browser Alex'});await save();
  await page.getByLabel('Stage for Browser Pilot').selectOption('proposal');
  await page.locator('.column').filter({has:page.locator('.deal-card', {hasText:'Browser Pilot'})}).waitFor();
  await nav('Follow-ups');await add();
  await page.locator('#field-title').fill('Send browser proposal');await page.locator('#field-due_date').fill('2030-10-01');
  await page.locator('#field-deal_id').selectOption({label:'Browser Pilot'});await save();
  await nav('Activity timeline');await add();
  await page.locator('#field-note').fill('Browser meeting notes <script>alert(1)</script>');
  await page.locator('#field-deal_id').selectOption({label:'Browser Pilot'});await save();
  await page.getByText('Browser meeting notes <script>alert(1)</script>',{exact:true}).waitFor();
  await nav('AI assistant');await page.getByLabel('Browser Alex',{exact:true}).check();
  await page.getByRole('button',{name:'1. Preview selected context'}).click();
  await page.getByRole('button',{name:'2. Confirm & generate mock summary'}).click();
  await page.getByText(/Local mock summary: contacts: Browser Alex/).waitFor();
  await nav('Overview');
  await page.screenshot({path:process.env.DEEDEE_SCREENSHOT||'/tmp/deedee-desktop.png',fullPage:true});
  await page.getByRole('button',{name:'✓',exact:true}).click();
  await page.getByText('Follow-up marked done.',{exact:true}).waitFor();
  await page.reload();await page.getByText('A clear slate',{exact:true}).waitFor();
  await nav('Sales pipeline');assert.equal(await page.getByLabel('Stage for Browser Pilot').inputValue(),'proposal');
  await page.locator('.deal-card').getByRole('button',{name:'View',exact:true}).click();
  await page.getByRole('heading',{name:'Stage history',exact:true}).waitFor();
  assert.match(await page.locator('#detail-body').innerText(),/lead → proposal/);
  await page.locator('#close-detail').click();
  const download=page.waitForEvent('download');await page.locator('#backup').click();
  assert.match((await download).suggestedFilename(),/deedee-backup/);
  await page.setViewportSize({width:390,height:844});await nav('Contacts');
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>window.innerWidth),false);
  await page.screenshot({path:'/tmp/deedee-mobile.png',fullPage:true});
  assert.deepEqual(errors,[]);
  console.log('Browser smoke passed: company/contact/deal/task/activity creation, pipeline change, safe text rendering, AI preview/confirmation, task completion, reload persistence, history, backup, and mobile layout.');
 } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
