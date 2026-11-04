(function(root){
'use strict';
// Bound wireless backlog and recover from an occasional UI timer stall without
// discarding note-off events or bursting an entire overdue passage at once.
class PlaybackClock {
 constructor(events,now){this.events=events;this.anchor=now;this.last=now;this.index=0;this.blocked=null;this.recoveries=0;}
 step(now,depth){
  const delta=Math.max(0,now-this.last);this.last=now;
  if(depth>=12){this.anchor+=delta;if(this.blocked===null)this.blocked=now;if(now-this.blocked>=3000)throw Error('蓝牙连续积压3秒，已停止；请检查连接或减少密集自动化');return [];}
  if(this.blocked!==null){this.anchor+=delta;this.blocked=null;}
  let at=(now-this.anchor)/1000;const next=this.events[this.index];
  if(next&&at-next.at>.15){this.anchor=now-next.at*1000;at=next.at;this.recoveries++;}
  const due=[];
  while(this.index<this.events.length&&this.events[this.index].at<=at&&due.length<6&&depth+due.length<12)due.push(this.events[this.index++]);
  return due;
 }
 get done(){return this.index===this.events.length;}
}
root.PlaybackClock=PlaybackClock;
if(typeof module!=='undefined')module.exports=PlaybackClock;
})(typeof globalThis!=='undefined'?globalThis:this);
