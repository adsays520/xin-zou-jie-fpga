const {chromium}=require('playwright');
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..'),assets=path.join(root,'android/app/src/main/assets');
(async()=>{
 const browser=await chromium.launch({headless:true,...(process.env.CHROME_EXE?{executablePath:process.env.CHROME_EXE}:{})});
 const page=await browser.newPage({viewport:{width:412,height:915},deviceScaleFactor:1});
 const errors=[];page.on('pageerror',e=>errors.push(e.message));page.on('dialog',d=>d.accept());
 await page.route('https://fpga.local/**',route=>{
  const rel=decodeURIComponent(new URL(route.request().url()).pathname).slice(1),file=path.join(assets,rel);
  if(!file.startsWith(assets+path.sep)||!fs.existsSync(file))return route.abort();
  return route.fulfill({contentType:file.endsWith('.js')?'application/javascript':file.endsWith('.json')?'application/json':'text/html',body:fs.readFileSync(file)});
 });
 const samples=Object.fromEntries([['twinkle','Twinkle_Star.mid'],['harbor','04_Star_Harbor.mid'],['retrigger','02_Echo_Retrigger.mid']].map(([key,name])=>[key,fs.readFileSync(path.join(assets,'midi',name)).toString('base64')]));
 await page.addInitScript(samples=>{
  window.sent=[];window.resources=[];window.samples=samples;
  window.Mobile={scan(){},disconnect(){},clearQueue(){},saveTang(){},save(){},
   send(hex,text){sent.push({hex,text});},sendWithDelay(hex,text,delay){sent.push({hex,text,delay});},
   whenIdle(ticket){setTimeout(()=>nativeEvent('idle',ticket),0);},demo(){return '';},
   midiSample(key){return samples[key]||'';},openMidiResource(key){resources.push(key);}};
 },samples);
 await page.goto('https://fpga.local/index.html');
 assert.equal(await page.locator('#nav button').count(),14);
 await page.getByRole('button',{name:'MIDI 导入 / 跟灯',exact:true}).click();
 await page.getByRole('button',{name:'Mutopia · 古典 / 吉他',exact:true}).click();
 assert.equal(await page.evaluate(()=>resources[0]),'mutopia');
 // Select an actual file through the browser's file-input path, the same JS
 // reader used after Android's ACTION_OPEN_DOCUMENT returns a content URI.
 await page.locator('#midiFile').setInputFiles(path.join(assets,'midi','Twinkle_Star.mid'));
 await page.waitForFunction(()=>midiScore?.notes.length===42);
 assert.equal(await page.evaluate(()=>midiScore.bpm),80);
 assert.equal(await page.evaluate(()=>sent.length),0,'Import must not send controls');
 await page.getByRole('button',{name:'开始 / 继续跟灯',exact:true}).click();
 assert((await page.locator('#midiStatus').innerText()).includes('请先连接BLE'));
 await page.evaluate(()=>nativeEvent('state','BLE已连接；FPGA能力由每次指令的板端结果核验'));
 await page.getByRole('button',{name:'开始 / 继续跟灯',exact:true}).click();
 await page.waitForFunction(()=>sent.some(x=>x.text&&new TextDecoder().decode(Uint8Array.from(x.hex.match(/../g),h=>parseInt(h,16)))==='LED,GUIDE,STATUS'));
 assert.equal(await page.evaluate(()=>!!midiGuide),false,'Capability is required');
 await page.evaluate(()=>nativeEvent('rx','LED,GUIDE,CAP,1,TTL_MS,1000'));
 await page.waitForFunction(()=>!!midiGuide);
 let commands=await page.evaluate(()=>sent.filter(x=>x.text).map(x=>new TextDecoder().decode(Uint8Array.from(x.hex.match(/../g),h=>parseInt(h,16)))));
 assert(commands.includes('LED,GUIDE,2,2'));// C4 -> string2 fret1
 await page.getByRole('button',{name:'暂停跟灯',exact:true}).click();
 commands=await page.evaluate(()=>sent.filter(x=>x.text).map(x=>new TextDecoder().decode(Uint8Array.from(x.hex.match(/../g),h=>parseInt(h,16)))));
 assert.equal(commands.at(-1),'LED,GUIDE,0,0');
 await page.locator('#midiSeek').evaluate(el=>{el.value='10';el.dispatchEvent(new Event('change'));});
 assert.equal(await page.evaluate(()=>midiPosition),10);
 await page.getByRole('button',{name:'开始 / 继续跟灯',exact:true}).click();
 await page.waitForFunction(()=>!!midiGuide);
 await page.evaluate(()=>nativeEvent('error','ACK,3,1：板端拒收；蓝牙连接保留'));
 assert.equal(await page.evaluate(()=>midiGuide),null);assert.equal(await page.evaluate(()=>midiConnected),true);
 await page.getByRole('button',{name:'开始 / 继续跟灯',exact:true}).click();await page.waitForFunction(()=>!!midiGuide);
 await page.evaluate(()=>nativeEvent('background',''));assert.equal(await page.evaluate(()=>midiGuide),null);
 await page.getByRole('button',{name:'转入编曲编辑',exact:true}).click();
 assert((await page.locator('#main').innerText()).includes('编曲工程'));
 assert.equal(await page.evaluate(()=>project.tracks[0].clips[0].notes.length),42);
 await page.getByRole('button',{name:'MIDI 导入 / 跟灯',exact:true}).click();
 await page.getByRole('button',{name:'发送到FPGA演奏',exact:true}).click();
 await page.waitForTimeout(140);
 assert(await page.evaluate(()=>sent.some(x=>!x.text&&x.hex.startsWith('a50c'))),'Piano event must reach transport');
 await page.evaluate(()=>stopAll());
 await page.locator('#midiFile').setInputFiles({name:'bad.mid',mimeType:'audio/midi',buffer:Buffer.from('not midi')});
 await page.waitForFunction(()=>midiMessage.includes('导入失败'));assert.equal(await page.evaluate(()=>midiScore.notes.length),42);
 await page.getByRole('button',{name:'原创合奏',exact:true}).click();
 assert.equal(await page.evaluate(()=>midiScore.notes.length),1000);
 assert.equal(await page.locator('#main input[type=checkbox]').count(),5);
 for(const input of await page.locator('#main input[type=checkbox]').all())await input.check();
 const plan=await page.evaluate(()=>{const p=midiProject();const compiled=Tang.compile(p.project);return {tracks:p.project.tracks.length,notes:p.project.tracks.flatMap(t=>t.clips.flatMap(c=>c.notes)).length,events:compiled.events.length};});assert.equal(plan.tracks,5);assert.equal(plan.notes,1000);assert(plan.events>100);
 await page.evaluate(()=>scrollTo(0,0));
 await page.screenshot({path:path.join(root,'audit/mobile_midi.png'),fullPage:true});
 // File-controlled names are shown as text, including after cache restoration.
 await page.evaluate(()=>{const s=structuredClone(midiScore);s.names=s.names.map(()=>'<img src=x onerror=alert(1)>');midiAccept(s);});
 assert.equal(await page.locator('#main img').count(),0);
 await page.reload();await page.getByRole('button',{name:'MIDI 导入 / 跟灯',exact:true}).click();
 assert.equal(await page.evaluate(()=>midiScore.notes.length),1000);
 assert.equal(await page.evaluate(()=>sent.length),0,'Cached import must remain offline');
 const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+2);assert.equal(overflow,false,'Mobile page horizontal overflow');
 assert.deepEqual(errors,[]);
 console.log(JSON.stringify({passed:true,tabs:14,file_input:true,sample_import:true,cached_import:true,resource_bridge:true,capability_gate:true,guide_mask:true,pause_clear:true,seek:true,rejection_stops_guide:true,background_clear:true,editor_conversion:true,FPGA_transport:true,malformed_preserves_score:true,all_track_ensemble:true,escaped_names:true,mobile_width:412,scope:'Chromium + mocked Android bridge; real SAF/BLE pending'}));
 await browser.close();
})().catch(e=>{console.error(e);process.exit(1);});
