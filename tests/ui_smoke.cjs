// Desktop Chromium smoke test with an Android-Java bridge mock; no hardware IO.
const {chromium}=require('playwright');
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..'),assets=path.join(root,'android/app/src/main/assets');
(async()=>{
 const browser=await chromium.launch({headless:true,...(process.env.CHROME_EXE?{executablePath:process.env.CHROME_EXE}:{})});
 const page=await browser.newPage({viewport:{width:412,height:915},deviceScaleFactor:1});
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.route('https://fpga.local/**',async route=>{
  const rel=decodeURIComponent(new URL(route.request().url()).pathname).slice(1),file=path.join(assets,rel);
  if(!file.startsWith(assets+path.sep)||!fs.existsSync(file))return route.abort();
  const mime=file.endsWith('.js')?'application/javascript':file.endsWith('.json')?'application/json':'text/html';
  await route.fulfill({contentType:mime,body:fs.readFileSync(file)});
 });
 await page.addInitScript(()=>{
  window.sent=[];window.Mobile={scan(){},disconnect(){},clearQueue(){},saveTang(){},save(){},
   send(hex,text){sent.push({hex,text});},sendWithDelay(hex,text,delay){sent.push({hex,text,delay});},
   whenIdle(ticket){setTimeout(()=>nativeEvent('idle',ticket),0);},demo(){return '';}};
 });
 await page.goto('https://fpga.local/index.html');
 const count=await page.locator('#nav button').count();assert.equal(count,14);
 for(let i=0;i<count;i++){
  await page.locator('#nav button').nth(i).click();
  assert((await page.locator('#main').innerText()).length>20,'Empty tab '+i);
 }
 await page.getByRole('button',{name:'灯效 / 展示',exact:true}).click();
 await page.getByRole('button',{name:'常态炫彩展示',exact:true}).click();
 let last=await page.evaluate(()=>sent.at(-1));
 assert.equal(Buffer.from(last.hex,'hex').toString(),'LED,MODE,DEMO');assert(last.text);
 await page.locator('#ledPin').selectOption('7');
 await page.locator('#ledColor').fill('#ff0000');
 await page.getByRole('button',{name:'应用颜色',exact:true}).click();
 last=await page.evaluate(()=>sent.at(-1));
 assert.equal(Buffer.from(last.hex,'hex').toString(),'LED,OUTPUT,7,255,0,0,1000,500');
 await page.screenshot({path:path.join(root,'audit/mobile_led.png'),fullPage:true});
 await page.evaluate(()=>{song={events:[{at:0,hex:'a550007f008a'}],preparation:[{hex:'a503010000a7',delay:0}]};playSong();});
 await page.waitForTimeout(100);
 assert(await page.evaluate(()=>sent.some(x=>x.hex==='a550007f008a')),'Prepared song did not start after idle acknowledgement');
 await page.evaluate(()=>{
  nativeEvent('state','BLE已连接');
  nativeEvent('error','ACK,3,1：板端拒收，连接保留');
  nativeEvent('queue','0');
 });
 assert.equal(await page.locator('#state').innerText(),'BLE已连接');
 assert.equal(await page.locator('#queueState').innerText(),'待发送包 0');
 assert((await page.locator('#log').innerText()).includes('ACK,3,1'));
 assert.equal(await page.evaluate(()=>playing),false);
 const before=await page.evaluate(()=>{startPitch();return sent.length;});
 await page.evaluate(()=>nativeEvent('error','rejected pitch control'));
 await page.waitForTimeout(120);
 assert.equal(await page.evaluate(()=>sent.length),before,'Rejected pitch stream must stop');
 assert.equal(await page.evaluate(()=>pitchTimer),null);
 assert.deepEqual(errors,[]);
 console.log(JSON.stringify({tabs:count,errors,led_command:true,preparation_idle:true,rejection_preserves_connection_status:true,rejection_stops_pitch_stream:true,viewport:'412x915',scope:'Chromium with Java bridge mock; not Android BLE hardware'}));
 await browser.close();
})().catch(e=>{console.error(e);process.exit(1);});
