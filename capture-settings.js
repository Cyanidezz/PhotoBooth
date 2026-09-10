'use strict';
const CaptureSettings=(()=>{
 const el=id=>document.getElementById(id);let options={seconds:3,countdownSound:true,shutterSound:true,mode:'continuous'};
 try{const saved=JSON.parse(localStorage.getItem('booth-capture-settings')||'null');if(saved&&Number.isInteger(saved.seconds)&&saved.seconds>=0&&saved.seconds<=15&&['manual','continuous'].includes(saved.mode))options={seconds:saved.seconds,countdownSound:saved.countdownSound!==false,shutterSound:saved.shutterSound!==false,mode:saved.mode};}catch(_){}
 const players={};
 for(const name of ['tick','last','shutter','test']){const player=new Audio('/sounds/'+name+'.wav?v=8');player.preload='auto';player.playsInline=true;players[name]={player,generation:0};}
 function report(error){const message=error?.name==='NotAllowedError'?'เบราว์เซอร์บล็อกเสียง กรุณากดลองเสียงอีกครั้ง':'โหลดหรือเล่นเสียงไม่ได้ ตรวจสอบอินเทอร์เน็ตแล้วลองใหม่';el('photoSettingsError').textContent=message;if(!el('photoSettings').open)el('status').textContent=message;}
 function unlock(){if(!options.countdownSound&&!options.shutterSound)return;for(const name of ['tick','last','shutter']){const entry=players[name],player=entry.player,generation=++entry.generation;player.muted=true;try{const promise=player.play();promise?.then(()=>{if(entry.generation===generation){player.pause();player.currentTime=0;player.muted=false;}}).catch(()=>{if(entry.generation===generation)player.muted=false;});}catch(_){player.muted=false;}}}
 function play(name,onStarted){const entry=players[name],player=entry.player;++entry.generation;try{player.muted=false;player.volume=1;player.currentTime=0;const promise=player.play();promise?.then(()=>onStarted?.()).catch(report);}catch(e){report(e);}}
 function tick(n){if(options.countdownSound)play(n===1?'last':'tick');}
 function shutter(){if(options.shutterSound)play('shutter');}
 const api={get:()=>({...options}),unlock,tick,shutter,onChange:null};
 el('captureSettings').onclick=()=>{el('countdownSeconds').value=options.seconds;el('countdownSound').checked=options.countdownSound;el('shutterSound').checked=options.shutterSound;el('captureMode').value=options.mode;el('modeLabel').hidden=typeof config!=='undefined'&&config?.boxes.length!==3;el('photoSettingsError').textContent='';el('photoSettings').showModal();WheelPicker.set(options.seconds);};
 el('closePhotoSettings').onclick=()=>el('photoSettings').close();
 el('savePhotoSettings').onclick=()=>{WheelPicker.read();const raw=el('countdownSeconds').value.trim(),seconds=Number(raw);if(!raw||!Number.isInteger(seconds)||seconds<0||seconds>15){el('photoSettingsError').textContent='กรอกจำนวนเต็มตั้งแต่ 0 ถึง 15 วินาที';return;}options={seconds,countdownSound:el('countdownSound').checked,shutterSound:el('shutterSound').checked,mode:el('captureMode').value};try{localStorage.setItem('booth-capture-settings',JSON.stringify(options));}catch(_){}unlock();el('photoSettings').close();api.onChange?.();};
 el('testSound').onclick=()=>{el('photoSettingsError').textContent='กำลังเล่นเสียงตัวอย่าง…';play('test',()=>{el('photoSettingsError').textContent='ส่งเสียงตัวอย่างแล้ว หากยังไม่ได้ยิน ให้เพิ่มระดับเสียงสื่อและตรวจว่าเสียงออกหูฟังหรือ Bluetooth อยู่หรือไม่';});};return api;
})();
