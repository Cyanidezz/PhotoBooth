'use strict';
const RemoteConfig=(()=>{
 const el=id=>document.getElementById(id),query=new URLSearchParams(location.search);
 function normalize(value){return (value||'').trim().replace(/\/+$/,'');}
 function load(){let saved={};try{saved=JSON.parse(localStorage.getItem('booth-remote')||'{}');}catch(_){}const requested=normalize(query.get('server'));const token=query.get('token')||saved.token||'';const local=/^(localhost|127\.0\.0\.1|\[::1\]|10\.|192\.168\.|172\.(1[6-9]|2\d|3[01])\.)/.test(location.hostname);return{base:requested||normalize(saved.base)||(local?'':null),token};}
 let value=load();
 function endpoint(path){if(value.base===null)throw Error('ยังไม่ได้ตั้งค่า Camera Server');const url=new URL(path,value.base||location.origin);if(value.token)url.searchParams.set('token',value.token);return url.toString();}
 function websocket(path){const url=new URL(endpoint(path));url.protocol=url.protocol==='https:'?'wss:':'ws:';return url.toString();}
 function show(message=''){el('remoteUrl').value=value.base||'';el('pairingToken').value=value.token||'';el('remoteError').textContent=message;el('remoteSettings').showModal();}
 el('saveRemote').onclick=()=>{const base=normalize(el('remoteUrl').value),token=el('pairingToken').value.trim();if(!/^https:\/\//i.test(base)){el('remoteError').textContent='ภายนอกเครือข่ายต้องใช้ URL ที่ขึ้นต้นด้วย https://';return;}if(!token){el('remoteError').textContent='กรอกรหัสจับคู่ที่แสดงบน Mac';return;}try{localStorage.setItem('booth-remote',JSON.stringify({base,token}));}catch(_){}location.reload();};
 el('closeRemote').onclick=()=>el('remoteSettings').close();el('serverSettings').onclick=()=>show();
 return{get:()=>({...value}),endpoint,websocket,show,needsSetup:()=>value.base===null};
})();
