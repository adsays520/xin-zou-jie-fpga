const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..'),assets=path.join(root,'android/app/src/main/assets');
const M=require(path.join(assets,'midi_file.js'));
const context={crypto:globalThis.crypto,console,Uint8Array,TextEncoder,TextDecoder,DataView};vm.createContext(context);
for(const name of ['protocol.js','tang.js','tang_core.js'])vm.runInContext(fs.readFileSync(path.join(assets,name),'utf8'),context);
const Tang=vm.runInContext('Tang',context),fixtures=JSON.parse(fs.readFileSync(path.join(__dirname,'midi_fixtures.json')));
let notes=0;
for(const expected of fixtures){
 const got=M.parse(fs.readFileSync(path.resolve(root,expected.file)),expected.name);assert.equal(got.notes.length,expected.notes.length);assert(Math.abs(got.duration-expected.duration)<1e-6);
 got.notes.forEach((n,i)=>{const e=expected.notes[i];for(const k of ['pitch','velocity','track','channel'])assert.equal(n[k],e[k]);for(const k of ['start','end'])assert(Math.abs(n[k]-e[k])<1e-6);});
 const tracks=Object.fromEntries(M.groups(got).map(g=>[g.key,{enabled:true,instrument:M.instrument(g)}]));
 const result=M.toTang(got,{tracks,rate:1,transpose:0},Tang);const plan=Tang.compile(result.project);assert(plan.events.length>0);notes+=got.notes.length;
 if(expected.name==='Twinkle_Star.mid'){
  assert.equal(got.bpm,80);
  const slow=M.toTang(got,{tracks,rate:.5,transpose:0},Tang);assert(Math.abs(slow.project.tracks[0].clips[0].notes[1].start/result.project.tracks[0].clips[0].notes[1].start-2)<.001);
 }
}
function vlq(n){const a=[n&127];while(n>>7){n>>=7;a.unshift((n&127)|128);}return a;}
function midi(...tracks){const header=Buffer.from([77,84,104,100,0,0,0,6,0,tracks.length>1?1:0,0,tracks.length,1,224]);return Buffer.concat([header,...tracks.map(t=>{const h=Buffer.alloc(8);h.write('MTrk');h.writeUInt32BE(t.length,4);return Buffer.concat([h,Buffer.from(t)]);})]);}
// Tempo and pedal live on a separate track using the same MIDI channel.
const conductor=[0,255,81,3,7,161,32,...vlq(480),255,81,3,15,66,64,...vlq(960),255,47,0];
const pedal=[...vlq(240),176,64,127,...vlq(720),176,64,0,...vlq(480),255,47,0];
const melody=[0,144,60,100,...vlq(480),60,0,...vlq(480),144,64,100,...vlq(480),64,0,0,255,47,0];
const score=M.parse(midi(conductor,pedal,melody));assert.deepEqual(score.notes.map(n=>[n.start,n.end]),[[0,1.5],[1.5,2.5]]);
for(const data of [Buffer.alloc(0),midi([0,64,100,0,255,47,0]),midi([0,144,64]),midi([255,255,255,255,255])])assert.throws(()=>M.parse(data));
let bad=midi([0,144,64,100,1,128,64,0,0,255,47,0]);bad[9]=2;assert.throws(()=>M.parse(bad));
assert.deepEqual(M.fingering(40),[0,6]);assert.deepEqual(M.fingering(84),[20,1]);assert.equal(M.fingering(85),null);
assert.equal(M.masks([{start:0,end:1,pitch:40},{start:0,end:1,pitch:84}],.5).frets,0x100001);
assert.equal(M.masks([{start:0,end:1,pitch:40}],1).strings,0);
const x=M.parse(midi([0,144,60,100,120,60,90,120,128,60,0,120,60,0,0,255,47,0]));
const tracks=Object.fromEntries(M.groups(x).map(g=>[g.key,{enabled:true,instrument:'piano'}]));
const converted=M.toTang(x,{tracks,rate:1,transpose:0},Tang);assert.equal(converted.trimmed,1);Tang.compile(converted.project);
assert.throws(()=>M.validate({...x,notes:[{...x.notes[0],pitch:999}]}));
assert.throws(()=>M.toTang(x,{tracks:{},rate:1,transpose:0},Tang));
assert.throws(()=>M.toTang(x,{tracks,rate:1,transpose:100},Tang));
console.log(JSON.stringify({passed:true,files:fixtures.length,notes_compared:notes,tempo:true,cross_track_pedal:true,running_status:true,repeated_pitches:true,malformed_rejected:true,all_native_projects_compiled:true}));
