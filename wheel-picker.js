'use strict';
const WheelPicker=(()=>{
 const wheel=document.getElementById('secondsWheel'),input=document.getElementById('countdownSeconds'),step=44;let value=3;
 const clamp=n=>Math.max(0,Math.min(15,Math.round(n)));
 function paint(n){value=clamp(n);input.value=String(value);for(const row of wheel.children)row.setAttribute('aria-selected',String(Number(row.dataset.value)===value));wheel.setAttribute('aria-activedescendant','seconds-option-'+value);}
 function set(n){paint(n);wheel.scrollTo({top:value*step,behavior:'instant'});}
 for(let n=0;n<=15;n++){const row=document.createElement('div');row.id='seconds-option-'+n;row.className='wheel-option';row.dataset.value=String(n);row.setAttribute('role','option');row.setAttribute('aria-label',n===0?'0 วินาที ถ่ายทันที':n+' วินาที');row.textContent=String(n);row.onclick=()=>set(n);wheel.append(row);}
 wheel.addEventListener('scroll',()=>paint(wheel.scrollTop/step),{passive:true});
 wheel.addEventListener('keydown',e=>{let next=value;if(e.key==='ArrowDown')next++;else if(e.key==='ArrowUp')next--;else if(e.key==='Home')next=0;else if(e.key==='End')next=15;else if(e.key==='PageDown')next+=5;else if(e.key==='PageUp')next-=5;else return;e.preventDefault();set(next);});
 paint(3);return{set,read:()=>{paint(wheel.scrollTop/step);return value;}};
})();
