(function(root){
'use strict';
function parse(input,name='MIDI'){
 const data=input instanceof Uint8Array?input:new Uint8Array(input);
 if(data.length>4000000)throw Error('MIDI超过4MB');
 let pos=0,order=0;const dv=new DataView(data.buffer,data.byteOffset,data.byteLength);
 function chunk(tag){if(pos+8>data.length||String.fromCharCode(...data.slice(pos,pos+4))!==tag)throw Error('MIDI块无效或截断');const n=dv.getUint32(pos+4),start=pos+8;pos=start+n;if(pos>data.length)throw Error('MIDI块长度超过文件');return data.slice(start,pos);}
 const header=chunk('MThd');if(header.length!==6)throw Error('MIDI头长度无效');
 const h=new DataView(header.buffer,header.byteOffset,header.byteLength),format=h.getUint16(0),count=h.getUint16(2),division=h.getUint16(4);
 if(format>1||!count||count>256||(format===0&&count!==1)||!division||(division&0x8000))throw Error('支持PPQ时间制的标准MIDI 0/1，不支持SMPTE或格式2');
 const events=[],tempos=[{tick:0,order:-1,value:500000}],names=[];let lastTick=0;
 for(let track=0;track<count;track++){
  const b=chunk('MTrk');let i=0,tick=0,running=0,ended=false;names.push('轨道 '+(track+1));
  function byte(){if(i>=b.length)throw Error('MIDI事件被截断');return b[i++];}
  function vlq(){let n=0;for(let j=0;j<4;j++){const v=byte();n=n*128+(v&127);if(v<128)return n;}throw Error('MIDI可变长度数超过4字节');}
  while(i<b.length){
   tick+=vlq();if(!Number.isSafeInteger(tick))throw Error('MIDI时间溢出');
   let status=byte();if(status&128)running=status<240?status:0;else{i--;status=running;if(!status)throw Error('MIDI running status缺少状态字节');}
   if(++order>250000)throw Error('MIDI事件超过250000条');
   if(status===255||status===240||status===247){
    const kind=status===255?byte():null,n=vlq(),payload=b.slice(i,i+n);i+=n;if(payload.length!==n)throw Error('MIDI事件内容截断');
    if(kind===3)names[track]=new TextDecoder('utf-8').decode(payload).slice(0,100);
    if(kind===81){const value=payload[0]*65536+payload[1]*256+payload[2];if(n!==3||!value)throw Error('无效速度事件');tempos.push({tick,order,value});}
    if(kind===47){if(n)throw Error('无效轨道结束标记');ended=true;break;}
    continue;
   }
   if(status<128||status>=240)throw Error('不支持的MIDI通道状态');
   const kind=status>>4,a=byte(),c=(kind===12||kind===13)?0:byte();if(a>127||c>127)throw Error('MIDI通道数据无效');
   events.push({tick,order,track,channel:status&15,kind,a,b:c});
  }
  if(!ended)throw Error('MIDI轨道缺少结束标记');lastTick=Math.max(lastTick,tick);
 }
 tempos.sort((a,b)=>a.tick-b.tick||a.order-b.order);
 let previous=0,elapsed=0,tempo=500000;const map=[];
 for(const t of tempos){elapsed+=(t.tick-previous)*tempo/division/1e6;map.push({tick:t.tick,seconds:elapsed,value:t.value});previous=t.tick;tempo=t.value;}
 function seconds(tick){let lo=0,hi=map.length;while(lo<hi){const m=(lo+hi)>>1;if(map[m].tick<=tick)lo=m+1;else hi=m;}const t=map[lo-1];return t.seconds+(tick-t.tick)*t.value/division/1e6;}
 const held=new Map(),released=new Map(),pedal=Array(16).fill(false),program=Array(16).fill(0),notes=[];
 function finish(n,tick){if(tick>n.tick){notes.push({start:seconds(n.tick),end:seconds(tick),pitch:n.pitch,velocity:n.velocity,track:n.track,channel:n.channel,program:n.program});if(notes.length>20000)throw Error('MIDI超过20000音符');}}
 function flush(channel,tick){for(const n of released.get(channel)||[])finish(n,tick);released.delete(channel);}
 events.sort((a,b)=>a.tick-b.tick||a.order-b.order);
 for(const e of events){const key=e.channel+':'+e.a;
  if(e.kind===12){program[e.channel]=e.a;continue;}
  if(e.kind===9&&e.b){if(!held.has(key))held.set(key,[]);held.get(key).push({tick:e.tick,pitch:e.a,velocity:e.b,track:e.track,channel:e.channel,program:program[e.channel]});}
  else if(e.kind===8||(e.kind===9&&!e.b)){
   const q=held.get(key);if(q?.length){const n=q.shift();if(pedal[e.channel]){if(!released.has(e.channel))released.set(e.channel,[]);released.get(e.channel).push(n);}else finish(n,e.tick);}
  }else if(e.kind===11&&[64,120,121,123].includes(e.a)){
   if(e.a===64)pedal[e.channel]=e.b>=64;
   else{pedal[e.channel]=false;if(e.a===120||e.a===123)for(const q of held.values())while(q.length&&q[0].channel===e.channel)finish(q.shift(),e.tick);}
   if(!pedal[e.channel])flush(e.channel,e.tick);
  }
 }
 for(const q of held.values())for(const n of q)finish(n,lastTick);
 for(const q of released.values())for(const n of q)finish(n,lastTick);
 if(!notes.length)throw Error('MIDI没有可用音符');
 notes.sort((a,b)=>a.start-b.start||a.track-b.track||a.pitch-b.pitch);
 const initialTempo=map.filter(t=>t.tick===0).at(-1).value;
 const score={version:1,name:String(name).slice(0,100),duration:seconds(lastTick),bpm:Math.max(30,Math.min(300,Math.round(60000000/initialTempo))),names,notes};
 validate(score);return score;
}
function validate(s){
 if(!s||s.version!==1||typeof s.name!=='string'||s.name.length>100||!Number.isFinite(s.duration)||s.duration<=0||s.duration>7200||!Number.isInteger(s.bpm)||s.bpm<30||s.bpm>300||!Array.isArray(s.names)||s.names.length>256||!s.names.every(n=>typeof n==='string'&&n.length<=100)||!Array.isArray(s.notes)||s.notes.length>20000||!s.notes.length)throw Error('MIDI缓存无效或曲目超过2小时');
 for(const n of s.notes){if(!Number.isFinite(n.start)||!Number.isFinite(n.end)||n.start<0||n.end<=n.start||n.end>s.duration+.001||!Number.isInteger(n.pitch)||n.pitch<0||n.pitch>127||!Number.isInteger(n.velocity)||n.velocity<1||n.velocity>127||!Number.isInteger(n.track)||n.track<0||n.track>=s.names.length||!Number.isInteger(n.channel)||n.channel<0||n.channel>15||!Number.isInteger(n.program)||n.program<0||n.program>127)throw Error('MIDI音符数据无效');}
 return s;
}
const open=[64,59,55,50,45,40];
function fingering(pitch){const choices=open.flatMap((base,i)=>pitch>=base&&pitch<=base+20?[[pitch-base,i+1]]:[]);choices.sort((a,b)=>a[0]-b[0]||a[1]-b[1]);return choices[0]||null;}
function masks(notes,at,transpose=0){let frets=0,strings=0;const active=[];for(const n of notes)if(n.start<=at&&at<n.end){const f=fingering(n.pitch+transpose);if(f){frets|=1<<f[0];strings|=1<<(f[1]-1);active.push([n.pitch+transpose,...f]);}}return {frets,strings,active};}
function groups(score){const found=new Map();for(const n of score.notes){const key=n.track+':'+n.channel+':'+n.program;if(!found.has(key))found.set(key,{key,track:n.track,channel:n.channel,program:n.program,count:0,name:score.names[n.track]});found.get(key).count++;}return [...found.values()];}
function instrument(g){if(g.channel===9)return 'drums';if(g.program>=24&&g.program<32)return 'guitar';if(g.program>=32&&g.program<40)return 'bass';if(g.program>=40&&g.program<52)return 'violin';return 'piano';}
const drumMap={36:0,35:0,38:1,40:1,42:2,44:2,46:3,39:4,49:5,57:5,51:6,59:6,41:7,43:7,45:7,47:8,48:8,50:9,37:10,56:11};
function toTang(score,options,Tang){
 validate(score);const transpose=options.transpose||0,rate=options.rate||1;
 if(!Number.isInteger(transpose)||Math.abs(transpose)>36||rate<.25||rate>1.5)throw Error('移调或速度超范围');
 const project=Tang.fresh();project.name=score.name.slice(0,100);project.bpm=score.bpm;project.guitar_sustain=127;project.violin_legato=true;
 const ticks=score.bpm*480/60/rate;project.bars=Math.max(1,Math.ceil(score.duration*ticks/1920));
 if(project.bars>256)throw Error('曲目超过手机编曲256小节上限，请选择较短文件或提高速度');
 project.loop_end=project.bars*1920;project.parameters['bus.guitar']=68;project.parameters['bus.piano']=65;project.parameters['bus.violin']=36;project.parameters['bus.bass']=50;project.parameters['bus.drums']=82;project.parameters['guitar.mix']=0;project.parameters['guitar.amp']=0;
 let skipped=0,trimmed=0;
 for(const g of groups(score)){
  const config=options.tracks[g.key];if(!config?.enabled)continue;const type=config.instrument;
  if(!['piano','guitar','bass','violin','drums'].includes(type))throw Error('未知乐器映射');
  const track={id:Tang.id(),name:(g.name+' / CH'+(g.channel+1)).slice(0,120),instrument:type,level:85,muted:false,solo:false,clips:[]};
  const clip={id:Tang.id(),name:'MIDI导入',start:0,length:project.bars*1920,notes:[]};
  for(const n of score.notes.filter(n=>n.track===g.track&&n.channel===g.channel&&n.program===g.program)){
   let pitch=n.pitch+transpose;if(type==='drums'){pitch=drumMap[n.pitch];if(pitch===undefined){skipped++;continue;}}
   const start=Math.round(n.start*ticks),end=Math.round(n.end*ticks);
   if(end>start)clip.notes.push({id:Tang.id(),start,duration:end-start,pitch,velocity:n.velocity});
  }
  track.clips.push(clip);if(clip.notes.length)project.tracks.push(track);
 }
 if(!project.tracks.length)throw Error('请至少选择一个有音符的轨道');
 // The FPGA has pitch-based note-offs: trim an earlier repeated pitch at its
 // next attack, including overlaps created by the imported sustain pedal.
 const same=new Map();for(const t of project.tracks)if(['piano','violin'].includes(t.instrument))for(const n of t.clips[0].notes){const key=t.instrument+':'+n.pitch;if(!same.has(key))same.set(key,[]);same.get(key).push(n);}
 for(const a of same.values()){a.sort((x,y)=>x.start-y.start);for(let i=0;i<a.length-1;i++)if(a[i].start+a[i].duration>a[i+1].start){a[i].duration=a[i+1].start-a[i].start;trimmed++;}}
 for(const t of project.tracks)t.clips[0].notes=t.clips[0].notes.filter(n=>n.duration>0);
 Tang.validate(project);return {project,skipped,trimmed};
}
const api={parse,validate,fingering,masks,groups,instrument,toTang};root.MidiFile=api;if(typeof module!=='undefined')module.exports=api;
})(typeof globalThis!=='undefined'?globalThis:this);
