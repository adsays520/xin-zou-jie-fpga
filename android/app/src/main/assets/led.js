'use strict';
const ledPage=tabs.length;tabs.push('灯效 / 展示');
const beforeLedScreen=screen;
screen=function(){if(page!==ledPage){beforeLedScreen();return;}
 $('nav').innerHTML=tabs.map((s,i)=>`<button onclick="page=${i};screen()" class="${page===i?'primary':''}">${s}</button>`).join('');
 $('main').innerHTML=`<section><h2>赛博灯效</h2><p class="notice">上电默认炫彩展示：青色、蓝紫、洋红渐变与双向流光；触摸和拨弦会叠加高亮。</p><div class="row">${btn('常态炫彩展示',"text('LED,MODE,DEMO')",'primary')}${btn('仅实时跟灯',"text('LED,MODE,LIVE')")}${btn('逐颗测试',"text('LED,TEST')")}${btn('关灯',"text('LED,MODE,OFF')")}${btn('读取状态',"text('LED,STATUS');text('LED,TX,STATUS')")}</div>${field('展示亮度','ledBrightness',32,0,255,"text('LED,BRIGHT,'+this.value)")}<p class="notice">新映射：GPIO3 输出13颗灯链，GPIO7 输出14颗灯链。整体交换输出，各灯链的按键位置保持对应。</p></section><section><h2>自定义颜色与闪烁</h2><label>输出<select id="ledPin"><option value="0">两路</option><option value="3">GPIO3 · 13颗</option><option value="7">GPIO7 · 14颗</option></select></label><label>颜色<input id="ledColor" type="color" value="#00d8ff"></label><label>周期(ms，0为常亮)<input id="ledPeriod" type="number" value="1000" min="0" max="60000"></label><label>点亮时间(ms)<input id="ledOn" type="number" value="500" min="0" max="59990"></label><p>${btn('应用颜色','applyLedOutput()','primary')}${btn('恢复炫彩展示',"text('LED,MODE,DEMO')")}</p></section>`;
};
function applyLedOutput(){const hex=$('ledColor').value,r=parseInt(hex.slice(1,3),16),g=parseInt(hex.slice(3,5),16),b=parseInt(hex.slice(5,7),16),period=+$('ledPeriod').value,on=period===0?0:+$('ledOn').value;if(!Number.isInteger(period)||!Number.isInteger(on)||period<0||period>60000||(period!==0&&(period<100||on<10||on>period-10)))throw Error('常亮周期填0；闪烁周期100–60000ms，点亮与熄灭各至少10ms');text(`LED,OUTPUT,${$('ledPin').value},${r},${g},${b},${period},${on}`);}
screen();
