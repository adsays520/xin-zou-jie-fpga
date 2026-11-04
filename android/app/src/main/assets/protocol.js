(function(root){
'use strict';
function integer(v,min,max){if(!Number.isInteger(v)||v<min||v>max)throw Error(`参数须为${min}–${max}整数`);return v;}
function frame(op,a=0,b=0,c=0){const d=[0xa5,...[op,a,b,c].map(v=>integer(v,0,255))];return [...d,d.reduce((x,y)=>x^y,0)];}
function crc16(d){let c=65535;for(const b of d){c^=b<<8;for(let i=0;i<8;i++)c=((c<<1)^((c&32768)?0x1021:0))&65535;}return c;}
function data(op,address,words){integer(address,0,op===0x21?8176:4080);if(address%16||words.length!==16||![0x11,0x21,0x31].includes(op))throw Error('上传块格式错误');const d=[165,op,address>>8,address&255];words.forEach(w=>d.push(integer(w,0,65535)>>8,w&255));const crc=crc16(d);return [...d,crc>>8,crc&255];}
function fx(p){['drive','tone','level','mix','rate','depth','threshold'].forEach(k=>integer(p[k],0,127));integer(p.amp,0,10);integer(p.mod,0,5);const flags=+!!p.cabinet|(+!!p.gate<<1)|(+!!p.compressor<<2);return [frame(64,p.amp,p.drive,p.tone),frame(65,p.level,p.mix,flags),frame(66,p.mod,p.rate,p.depth),frame(67,p.threshold,0,0),frame(68)];}
function space(p){Object.values(p).forEach(v=>integer(v,0,127));integer(p.delay_feedback,0,96);return [frame(96,p.chorus_mix,p.chorus_rate,p.chorus_depth),frame(97,p.delay_mix,p.delay_time,p.delay_feedback),frame(98)];}
function note(t,p,v,on){integer(v,1,127);if(t===1){integer(p,21,108);return frame(5,p,v,+on);}if(t===3){integer(p,55,100);return frame(8,p,v,+on);}throw Error('拨弦乐器请使用弦品演奏');}
function pluck(s,f,v){return frame(2,integer(s,1,6),integer(f,0,20),integer(v,1,127));}
function hit(n,v){return frame(80,integer(n,0,11),integer(v,1,127));}
function envelope(words,drawn=false){if(words.length!==4096)throw Error('包络必须4096点');const op=drawn?48:16,result=[frame(op)];for(let i=0;i<4096;i+=16)result.push(data(op+1,i,words.slice(i,i+16)));result.push(frame(op+2));if(!drawn)result.push(frame(19,1));return result;}
const api={frame,crc16,data,fx,space,note,pluck,hit,envelope};root.FPGA=api;if(typeof module!=='undefined')module.exports=api;
})(typeof globalThis!=='undefined'?globalThis:this);
