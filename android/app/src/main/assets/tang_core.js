'use strict';
const Tang=(()=>{
const BAR=1920,PPQ=480,types=['guitar','piano','bass','violin','drums'];
const id=()=>Array.from(crypto.getRandomValues(new Uint8Array(12)),x=>x.toString(16).padStart(2,'0')).join('');
const defaults=()=>Object.fromEntries(Object.entries(PARAMS).map(([k,v])=>[k,v[3]]));
function fresh(){return {name:'手机编曲',bpm:110,bars:4,tracks:[],automation:[],parameters:defaults(),loop_start:0,loop_end:BAR*4,guitar_sustain:127,violin_legato:false,format:'tang-arrangement-v1'};}
function round(v){const f=Math.floor(v),r=v-f;return r===.5?(f%2===0?f:f+1):Math.round(v);}
function integer(v,a,b){if(!Number.isInteger(v)||v<a||v>b)throw Error(`整数超出${a}–${b}`);}
function validate(p){
 if(!p||typeof p!=='object')throw Error('工程不能为空');
 if(p.format!=='tang-arrangement-v1')throw Error('不是Tang工程');integer(p.bpm,30,300);integer(p.bars,1,256);
 if(typeof p.name!=='string'||p.name.length<1||p.name.length>120||!Array.isArray(p.tracks)||p.tracks.length>64)throw Error('工程名或轨道数错误');
 const ids=new Set();let total=0;function unique(s){if(typeof s!=='string'||!s||ids.has(s))throw Error('重复或缺失ID');ids.add(s);}
 for(const t of p.tracks){unique(t.id);if(!types.includes(t.instrument)||typeof t.name!=='string'||t.name.length>120||!Array.isArray(t.clips)||t.clips.length>1024)throw Error('轨道格式错误');integer(t.level,0,127);if(typeof t.muted!=='boolean'||typeof t.solo!=='boolean')throw Error('Mute/Solo须为布尔值');
 for(const c of t.clips){unique(c.id);integer(c.start,0,p.bars*BAR-1);integer(c.length,1,p.bars*BAR-c.start);if(!Array.isArray(c.notes))throw Error('音符列表错误');
 for(const n of c.notes){unique(n.id);integer(n.start,0,c.length-1);integer(n.duration,1,c.length-n.start);integer(n.pitch,0,t.instrument==='drums'?11:127);integer(n.velocity,1,127);if(++total>20000)throw Error('超过20000音符');}}}
 if(!p.parameters)p.parameters=defaults();if(p.parameters['bus.bass']===undefined)p.parameters['bus.bass']=100;
 for(const [k,spec] of Object.entries(PARAMS))integer(p.parameters[k],spec[1],spec[2]);
 if(!Array.isArray(p.automation)||p.automation.length>23)throw Error('自动化错误');const targets=new Set();
 for(const lane of p.automation){if(!PARAMS[lane.target]||targets.has(lane.target)||!['step','linear'].includes(lane.interpolation)||!Array.isArray(lane.points)||lane.points.length>4096)throw Error('自动化格式错误');targets.add(lane.target);let ticks=new Set();
 for(const x of lane.points){integer(x.tick,0,p.bars*BAR);integer(x.value,PARAMS[lane.target][1],PARAMS[lane.target][2]);if(ticks.has(x.tick))throw Error('自动化点重叠');ticks.add(x.tick);}}
 integer(p.guitar_sustain??127,0,127);if(p.violin_legato!==undefined&&typeof p.violin_legato!=='boolean')throw Error('连奏须为布尔值');return p;
}
function valueAt(lane,t,fallback){const a=lane.points.slice().sort((a,b)=>a.tick-b.tick);let prev=null;for(const n of a){if(n.tick>t){if(prev&&lane.interpolation==='linear')return round(prev.value+(n.value-prev.value)*((t-prev.tick)/(n.tick-prev.tick)));break;}prev=n;}return prev?prev.value:fallback;}
function params(values,previous=null){const frames=['guitar','piano','drums','violin','bass'].map((s,i)=>previous&&previous['bus.'+s]===values['bus.'+s]?null:FPGA.frame(112,i,values['bus.'+s],0)).filter(Boolean);let g={};for(const [k,v] of Object.entries(values))if(k.startsWith('guitar.'))g[k.slice(7)]=v;g.mod=g.modulation;const gf=(!previous||Object.keys(values).some(k=>k.startsWith('guitar.')&&values[k]!==previous[k]))?FPGA.fx(g):[];const space={};for(const [k,v] of Object.entries(values))if(k.startsWith('space.'))space[k.slice(6)]=v;if(!previous||Object.keys(values).some(k=>k.startsWith('space.')&&values[k]!==previous[k]))frames.push(...FPGA.space(space));frames.push(...gf);return frames;}
function note(instrument,pitch,velocity,on){
 if(instrument==='drums')return on?FPGA.hit(pitch,velocity):null;
 let base;
 if(instrument==='piano')base=FPGA.note(1,pitch,velocity,on);
 else if(instrument==='violin')base=FPGA.note(3,pitch,velocity,on);
 else {if(!on)return null;const open=[64,59,55,50,45,40];let candidates=[];for(let i=0;i<6;i++){if(instrument==='bass'&&i<2)continue;const fret=pitch-open[i]+(instrument==='bass'?12:0);if(fret>=0&&fret<=20)candidates.push([fret,i+1]);}if(!candidates.length)throw Error(instrument+' MIDI '+pitch+'超出弦品音域');candidates.sort((a,b)=>a[0]-b[0]||a[1]-b[1]);base=FPGA.pluck(candidates[0][1],candidates[0][0],velocity);}
 return FPGA.frame({guitar:10,bass:11,piano:12,violin:13}[instrument],base[2],base[3],base[4]);
}
function hex(b){return b.map(x=>x.toString(16).padStart(2,'0')).join('');}
function compile(p){validate(p);const length=p.bars*BAR,seconds=60/p.bpm/PPQ;const active=p.tracks.filter(t=>!t.muted&&t.level>0),solo=active.some(t=>t.solo);let notes=[];
 for(const t of active.filter(t=>!solo||t.solo))for(const c of t.clips)for(const n of c.notes)notes.push({...n,start:c.start+n.start,end:c.start+n.start+n.duration,instrument:t.instrument,velocity:Math.max(1,Math.min(127,round(n.velocity*t.level/100)))});
 notes.sort((a,b)=>a.start-b.start||a.id.localeCompare(b.id));let held=new Map();const limits={guitar:32,piano:16,bass:8,violin:1};
 const boundaries=notes.filter(n=>n.instrument!=='drums').flatMap(n=>[[n.start,1,n],[n.end,0,n]]).sort((a,b)=>a[0]-b[0]||a[1]-b[1]||a[2].id.localeCompare(b[2].id));
 for(const [,on,n] of boundaries){if(!on){held.delete(n.id);continue;}note(n.instrument,n.pitch,n.velocity,true);const same=Array.from(held.values()).filter(x=>x.instrument===n.instrument);if(same.length>=limits[n.instrument])throw Error(n.instrument+'超过声部上限');if(['piano','violin'].includes(n.instrument)&&same.some(x=>x.pitch===n.pitch))throw Error('相同音高重叠，无法独立松音');held.set(n.id,n);}
 let events=[],order=0;function add(at,priority,bytes){if(events.length>100000)throw Error('手机工程事件过多，请缩短曲谱或减少自动化');if(bytes)events.push({at,priority,hex:hex(bytes),order:order++});}
 add(0,-3,FPGA.frame(82));add(0,-2,FPGA.frame(3,1));add(0,-2,FPGA.frame(35));add(0,-2,FPGA.frame(6));if((p.guitar_sustain??127)===127&&notes.some(n=>n.instrument==='guitar'))add(0,-2,FPGA.frame(19));add(0,-1,FPGA.frame(14,1));
 let linked=new Set(),next=new Set();const violin=notes.filter(n=>n.instrument==='violin');if(p.violin_legato!==false)for(let i=0;i<violin.length-1;i++)if(violin[i].end===violin[i+1].start){linked.add(violin[i].id);next.add(violin[i+1].id);}
 for(const n of notes){let b=note(n.instrument,n.pitch,n.velocity,true);if(next.has(n.id))b=FPGA.frame(b[1],b[2],b[3],3);add(n.start*seconds,3,b);if(!linked.has(n.id))add(n.end*seconds,0,note(n.instrument,n.pitch,1,false));}
 let ticks=new Set([0]);for(const l of p.automation){for(const pt of l.points)if(pt.tick<length)ticks.add(pt.tick);if(l.interpolation==='linear'){const step=Math.max(1,round(.05/seconds));for(let t=0;t<length;t+=step)ticks.add(t);}}
 let previous=null;for(const tick of [...ticks].sort((a,b)=>a-b)){let values={...p.parameters};for(const l of p.automation)values[l.target]=valueAt(l,tick,values[l.target]);const key=JSON.stringify(values);if(key!==JSON.stringify(previous)){for(const b of params(values,previous))add(tick*seconds,2,b);previous=values;}}
 events.sort((a,b)=>a.at-b.at||a.priority-b.priority||a.order-b.order);let preparation=[];
 if((p.guitar_sustain??127)<127&&notes.some(n=>n.instrument==='guitar')){const tail=round(225+(1400-225)*p.guitar_sustain/126)/1000;let words=[];for(let i=0;i<4096;i++){let t=i*65536/(3994*48000),g=t>=tail?0:t<.004?t/.004:t<.065?1-.28*(t-.004)/.061:.72*Math.cos((t-.065)/(tail-.065)*Math.PI/2)**2;words.push(round(g*32768));}words[0]=words[4095]=0;preparation=[{hex:hex(FPGA.frame(3,1)),delay:0},{hex:hex(FPGA.frame(4)),delay:0},{hex:hex(FPGA.frame(19)),delay:0},{hex:hex(FPGA.frame(14,1)),delay:80},...FPGA.envelope(words).map((b,i,a)=>({hex:hex(b),delay:i===0?5:i>=a.length-2?10:5}))];}
 const setup=events.filter(e=>e.at===0&&e.priority<3),musical=events.filter(e=>!(e.at===0&&e.priority<3));
 function batch(a){const out=[];for(const e of a){const last=out[out.length-1];if(last&&last.at===e.at&&e.hex.length===12&&last.hex.length%12===0&&last.hex.length+12<=72)last.hex+=e.hex;else out.push({at:e.at,hex:e.hex});}return out;}
 preparation.push(...batch(setup).map(e=>({hex:e.hex,delay:0})));
 return {format:'fpga-mobile-events-v1',name:p.name,bpm:p.bpm,duration:length*seconds,preparation,events:batch(musical)};
}
return {fresh,validate,compile,id,defaults,BAR,PPQ};})();
if(typeof module!=='undefined')module.exports=Tang;
