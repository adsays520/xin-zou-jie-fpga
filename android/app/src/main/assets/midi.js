'use strict';
const midiPage=tabs.length;tabs.push('MIDI 导入 / 跟灯');
let midiScore=null,midiTracks={},midiGuideKey='',midiRate=1,midiTranspose=0,midiConnected=false,midiCap=false;
let midiGuide=null,midiPosition=0,midiGuidePending=false,midiGuideRequest=0,midiImportRevision=0;
let midiOwnPlayback=false;
let midiMessage='手机浏览器下载.mid → 选择下载文件 → 选轨、播放或跟灯。';
try{const stored=localStorage.getItem('fpga_midi_last_v1');if(stored){midiScore=MidiFile.validate(JSON.parse(stored));midiDefaults();}}catch(e){localStorage.removeItem('fpga_midi_last_v1');}
function midiDefaults(){const groups=MidiFile.groups(midiScore);midiGuideKey=(groups.find(g=>g.channel!==9)||groups[0]).key;midiTracks={};for(const g of groups)midiTracks[g.key]={enabled:g.key===midiGuideKey,instrument:MidiFile.instrument(g)};midiPosition=0;}
const beforeMidiScreen=screen;
screen=function(){
 if(page!==midiPage){if(midiGuide||midiGuidePending)midiStopGuide();beforeMidiScreen();return;}
 $('nav').innerHTML=tabs.map((s,i)=>`<button onclick="page=${i};screen()" class="${page===i?'primary':''}">${escapeHtml(s)}</button>`).join('');
 const groups=midiScore?MidiFile.groups(midiScore):[];
 $('main').innerHTML=`<section><h2>MIDI 文件导入</h2><label class="field">选择手机“下载”里的 .mid / .midi<input id="midiFile" type="file" accept=".mid,.midi,audio/midi,audio/x-midi,application/octet-stream" onchange="importMidi(this.files[0])"></label><div class="row">${btn('小星星',"midiSample('twinkle')")}${btn('原创合奏',"midiSample('harbor')")}${btn('1号板连击练习',"midiSample('retrigger')")}</div><p class="notice">支持标准MIDI 0/1、变速、音符和延音踏板，最多4MB／20000音符。导入不自动发送；其他控制器及效果可在编曲中设置。上次导入会缓存在本机。</p></section>
 <section><h2>下载 MIDI 资源</h2><div class="row">${btn('Mutopia · 古典 / 吉他',"Mobile.openMidiResource('mutopia')")}${btn('Wikimedia · 共享曲库',"Mobile.openMidiResource('commons')")}${btn('BitMidi · 搜索曲目',"Mobile.openMidiResource('bitmidi')")}</div><p class="notice">用系统浏览器打开曲目，下载 MIDI（不是PDF或MP3），然后返回此页选择“下载”中的文件。Mutopia和Commons标有曲目授权；其他曲库请查看单曲使用条件。</p></section>
 <section><h2>${midiScore?escapeHtml(midiScore.name):'尚未导入'}</h2><p>${midiScore?`${midiScore.notes.length}音符 · ${midiScore.duration.toFixed(1)}秒 · 起始${midiScore.bpm} BPM`:''}</p><div class="row"><label>速度% <input id="midiSpeed" type="number" min="25" max="150" value="${Math.round(midiRate*100)}" onchange="midiSettings()" style="width:85px"></label><label>移调 <input id="midiTranspose" type="number" min="-36" max="36" value="${midiTranspose}" onchange="midiSettings()" style="width:80px"></label></div>
 ${groups.map(g=>`<div style="padding:10px 0;border-bottom:1px solid #39536b"><label><input type="checkbox" ${midiTracks[g.key]?.enabled?'checked':''} onchange="midiTracks['${g.key}'].enabled=this.checked"> 演奏 ${escapeHtml(g.name)} / CH${g.channel+1} · ${g.count}音符</label><div class="row"><label>映射<select onchange="midiTracks['${g.key}'].instrument=this.value">${Object.entries(names).map(([key,label])=>`<option value="${key}" ${midiTracks[g.key]?.instrument===key?'selected':''}>${label}</option>`).join('')}</select></label>${g.channel!==9?`<label><input type="radio" name="guideTrack" ${midiGuideKey===g.key?'checked':''} onchange="midiStopGuide();midiGuideKey='${g.key}'">跟灯旋律</label>`:''}</div></div>`).join('')}
 <p class="notice">默认选第一条旋律轨。可勾选伴奏组成合奏；小提琴仅支持单声部，多音弦乐轨可映射为钢琴。</p><div class="row">${btn('发送到FPGA演奏','midiPlay()','primary')}${btn('转入编曲编辑','midiEdit()')}${btn('停止演奏','stopAll()')}</div></section>
 <section><h2>实体跟灯练习</h2><p class="notice">本区只亮灯，由你手动演奏。蓝色提示弦与品位，绿色显示实按。音域E2–C6；多音显示弦与品位的集合，无法区分每个交叉点。需要S3实时引导能力。</p><div class="row">${btn('开始 / 继续跟灯','midiStartGuide()','primary')}${btn('暂停跟灯','midiPauseGuide()')}${btn('停止跟灯','midiStopGuide();midiPosition=0;midiRefreshPosition()')}${btn('恢复炫彩展示',"midiStopGuide();text('LED,MODE,DEMO')")}</div><label class="field">位置 <output id="midiPosition">${midiPosition.toFixed(1)}秒</output><input id="midiSeek" type="range" min="0" max="${midiScore?.duration||1}" step="0.1" value="${midiPosition}" onchange="const at=+this.value;midiPauseGuide();midiPosition=at;midiRefreshPosition()"></label><p id="midiActive"></p></section><section><p id="midiStatus" role="status">${escapeHtml(midiMessage)}</p></section>`;
};
function midiStatus(s){midiMessage=s;if($('midiStatus'))$('midiStatus').textContent=s;log(s);}
function midiSettings(){midiPauseGuide();const rate=Number($('midiSpeed').value)/100,shift=Number($('midiTranspose').value);if(!Number.isFinite(rate)||rate<.25||rate>1.5||!Number.isInteger(shift)||Math.abs(shift)>36)throw Error('速度25%–150%，移调±36半音');midiRate=rate;midiTranspose=shift;}
async function importMidi(file){
 if(!file)return;const revision=++midiImportRevision;
 try{if(file.size>4000000)throw Error('MIDI超过4MB');const data=await file.arrayBuffer();if(revision!==midiImportRevision)return;const score=MidiFile.parse(data,file.name);midiAccept(score);}
 catch(e){if(revision===midiImportRevision)midiStatus('导入失败：'+e.message);}
}
function midiAccept(score){
 if(midiGuide||midiGuidePending)midiStopGuide();midiScore=score;midiDefaults();midiRate=1;midiTranspose=0;
 let cached=true;try{localStorage.setItem('fpga_midi_last_v1',JSON.stringify(score));}catch(e){cached=false;}
 midiMessage=`已导入 ${score.notes.length}音符；${cached?'已缓存，下次打开可继续使用':'本机缓存空间不足，本次仍可使用'}。请选择轨道。`;screen();
}
function midiSample(key){++midiImportRevision;const encoded=Mobile.midiSample(key);if(!encoded)throw Error('未找到内置MIDI');const data=Uint8Array.from(atob(encoded),c=>c.charCodeAt(0));midiAccept(MidiFile.parse(data,{twinkle:'小星星.mid',harbor:'星港合奏.mid',retrigger:'1号板连击练习.mid'}[key]));}
function midiProject(){if(!midiScore)throw Error('请先导入MIDI');midiSettings();const converted=MidiFile.toTang(midiScore,{tracks:midiTracks,rate:midiRate,transpose:midiTranspose},Tang);return converted;}
function midiPlay(){if(!midiConnected)throw Error('请先连接BLE');midiStopGuide();const c=midiProject();song=Tang.compile(c.project);midiStatus(`已编译 ${c.project.tracks.length}轨；未映射鼓音跳过${c.skipped}，重叠同音整理${c.trimmed}。`);playSong();midiOwnPlayback=true;}
function midiEdit(){const c=midiProject();if(!confirm('用MIDI替换当前编曲？请先导出需要保留的编辑。'))return;if(playing&&midiConnected)stopAll();project=c.project;trackIndex=clipIndex=0;noteIndex=-1;undoStack=[];redoStack=[];page=9;screen();log('MIDI已转为编曲；速度变化已保留为音符的实际时刻，可继续编辑和导出。');}
function midiGuideNotes(){const g=MidiFile.groups(midiScore).find(g=>g.key===midiGuideKey);if(!g||g.channel===9)throw Error('请选择一条非鼓旋律轨跟灯');return midiScore.notes.filter(n=>n.track===g.track&&n.channel===g.channel&&n.program===g.program);}
function midiStopGuide(clear=true){
 ++midiGuideRequest;midiGuidePending=false;
 const old=midiGuide;if(old){midiPosition=Math.min(midiScore.duration,Math.max(0,(performance.now()-old.anchor)/1000*midiRate));clearInterval(old.timer);}midiGuide=null;
 if(clear&&midiConnected&&old)text('LED,GUIDE,0,0');midiRefreshPosition();
}
function midiPauseGuide(){midiStopGuide();}
function midiRefreshPosition(){if($('midiPosition'))$('midiPosition').textContent=midiPosition.toFixed(1)+'秒';if($('midiSeek'))$('midiSeek').value=midiPosition;}
function midiStartGuide(){return midiStartGuideAsync().catch(e=>midiStatus(e.message));}
async function midiStartGuideAsync(){
 if(!midiScore)throw Error('请先导入MIDI');if(!midiConnected)throw Error('请先连接BLE');
 midiSettings();const selected=midiGuideNotes(),missed=selected.filter(n=>!MidiFile.fingering(n.pitch+midiTranspose)).length;
 if(missed===selected.length)throw Error('此轨全部超出E2–C6，请移调或选择其他旋律');
 if(playing)stopAll();midiStopGuide();const revision=++midiGuideRequest;midiGuidePending=true;
 try{
  if(!midiCap){text('LED,GUIDE,STATUS');const until=performance.now()+2500;while(!midiCap){await new Promise(r=>setTimeout(r,40));if(revision!==midiGuideRequest||!midiConnected)return;if(performance.now()>until)throw Error('S3未报告实时引导能力，请使用v3.4.27或配套新版固件');}}
  if(revision!==midiGuideRequest||!midiConnected)return;midiGuidePending=false;
  if(midiPosition>=midiScore.duration)midiPosition=0;
  text('LED,CLEAR');text('LED,MODE,BOTH');
  const state={anchor:performance.now()-midiPosition/midiRate*1000,timer:null,last:'',sent:0,blocked:null};midiGuide=state;
  midiStatus(`跟灯开始；${missed}个超音域音符跳过。BLE灯光时延随连接变化。`);
  const tick=()=>{if(midiGuide!==state)return;try{
   const now=performance.now();midiPosition=(now-state.anchor)/1000*midiRate;
   if(midiPosition>=midiScore.duration){midiStopGuide();midiPosition=0;midiRefreshPosition();midiStatus('跟灯练习完成，提示已清除');return;}
   const m=MidiFile.masks(selected,midiPosition,midiTranspose),cmd=`LED,GUIDE,${m.frets.toString(16)},${m.strings.toString(16)}`;
   if(queue>=4){if(state.blocked===null)state.blocked=now;if(now-state.blocked>1000)throw Error('BLE灯光队列持续积压，练习已停止');}
   else{state.blocked=null;if(cmd!==state.last||now-state.sent>=300){text(cmd);state.last=cmd;state.sent=now;}}
   midiRefreshPosition();if($('midiActive'))$('midiActive').textContent=m.active.map(([pitch,fret,string])=>`${string}弦${fret}品 / MIDI ${pitch}`).join('，');
  }catch(e){midiStopGuide();midiStatus(e.message);}};
  state.timer=setInterval(tick,30);tick();
 }catch(e){if(revision===midiGuideRequest){midiGuidePending=false;midiStatus(e.message);}}
}
const beforeMidiStopAll=stopAll;
stopAll=function(){const active=!!midiGuide;midiOwnPlayback=false;beforeMidiStopAll();midiStopGuide(false);if(active&&midiConnected)text('LED,GUIDE,0,0');};
const beforeMidiNative=nativeEvent;
nativeEvent=function(kind,value){
 if(kind==='state'){midiConnected=/^BLE已连接/.test(value);if(!midiConnected){midiCap=false;midiStopGuide(false);}}
 if(kind==='error'){midiOwnPlayback=false;midiStopGuide(false);}
 if(kind==='background'){midiStopGuide();if(midiOwnPlayback&&playing)stopAll();}
 if(kind==='rx'&&midiConnected&&value.includes('LED,GUIDE,CAP,1'))midiCap=true;
 if(kind==='rx'&&value.includes('ERROR,LED')&&(midiGuide||midiGuidePending)){midiStopGuide(false);midiStatus(value);}
 beforeMidiNative(kind,value);
};
document.addEventListener('visibilitychange',()=>{if(document.hidden){midiStopGuide();if(midiOwnPlayback&&playing&&midiConnected)stopAll();}});
screen();
