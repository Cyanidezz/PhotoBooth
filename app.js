'use strict';
const $=id=>document.getElementById(id);let config=null,busy=false,connected=false,resultId='';
function getSessionId(){let saved;try{saved=sessionStorage.getItem('booth-session');}catch(_){}if(saved&&/^[a-f0-9-]{32,36}$/i.test(saved))return saved;const bytes=new Uint8Array(16);crypto.getRandomValues(bytes);const id=Array.from(bytes,b=>b.toString(16).padStart(2,'0')).join('');try{sessionStorage.setItem('booth-session',id);}catch(_){}return id;}
const sessionId=getSessionId();
let socket,peer,reconnectTimer;
function status(text){$('status').textContent=text;}
function controls(){const complete=!!resultId;$('shoot').disabled=busy||!connected||!config;$('shoot').hidden=complete;$('retake').hidden=!complete;$('download').hidden=!complete;$('showQr').hidden=!complete;$('print').hidden=!complete;$('captureSettings').disabled=busy;$('back').disabled=busy;}
function framePage(){const page=Math.round($('frames').scrollLeft/Math.max(1,$('frames').clientWidth));$('pageNumber').textContent=`${page+1} / ${Math.ceil(FRAMES.length/2)}`;$('previousPage').disabled=page===0;$('nextPage').disabled=page>=Math.ceil(FRAMES.length/2)-1;}
for(let i=0;i<FRAMES.length;i+=2){const page=document.createElement('div');page.className='framepage';for(const item of FRAMES.slice(i,i+2)){const button=document.createElement('button');button.className='framecard';button.innerHTML=`<img src="${item.id}.png" alt="${item.label}"><span>${item.label}</span>`;button.onclick=()=>selectFrame(item);page.append(button);}$('frames').append(page);}
$('frames').addEventListener('scroll',framePage,{passive:true});$('previousPage').onclick=()=>$('frames').scrollBy({left:-$('frames').clientWidth,behavior:'smooth'});$('nextPage').onclick=()=>$('frames').scrollBy({left:$('frames').clientWidth,behavior:'smooth'});framePage();
function selectFrame(item){config=item;resultId='';const overlay=$('liveFrame');overlay.onload=()=>document.querySelector('.live').style.aspectRatio=`${overlay.naturalWidth}/${overlay.naturalHeight}`;overlay.src=`/api/frame/${item.id}.png`;overlay.hidden=false;$('result').hidden=true;$('preview').hidden=false;$('selection').hidden=true;$('booth').hidden=false;$('modeLabel').hidden=item.boxes.length!==3;socketSend({action:'reset',frame:item.id});status(connected?'พร้อมถ่าย':'กำลังเชื่อมต่อ Camera Server…');controls();}
function socketSend(message){if(socket?.readyState===WebSocket.OPEN)socket.send(JSON.stringify(message));}
function connectSocket(){clearTimeout(reconnectTimer);const protocol=location.protocol==='https:'?'wss':'ws';socket=new WebSocket(`${protocol}://${location.host}/ws/${sessionId}`);socket.onopen=()=>{$('serverState').textContent='Camera Server พร้อมใช้งาน';};socket.onmessage=event=>handle(JSON.parse(event.data));socket.onclose=()=>{connected=false;$('serverState').textContent='Camera Server ขาดการเชื่อมต่อ';controls();reconnectTimer=setTimeout(connectSocket,1500);};}
function handle(message){if(message.event==='connected'){connected=true;controls();return;}if(message.event==='countdown'){$('count').textContent=message.value;CaptureSettings.tick(message.value);status(`ถ่ายใน ${message.value} วินาที`);}else if(message.event==='shutter'){$('count').textContent='';CaptureSettings.shutter();status('Nikon กำลังถ่ายและดาวน์โหลดภาพเต็ม…');}else if(message.event==='shot_ready'){status(`รับภาพเต็มแล้ว ${message.count} / ${config.boxes.length}`);}else if(message.event==='pose'){status(`เปลี่ยนท่าสำหรับภาพที่ ${message.next}`);}else if(message.event==='waiting'){busy=false;status(`ถ่ายแล้ว ${message.next-1} / ${message.total} · กดถ่ายช่องถัดไปเมื่อพร้อม`);controls();}else if(message.event==='complete'){busy=false;resultId=message.image.split('/').pop().replace('.jpg','');$('result').src=message.image;$('result').hidden=false;$('preview').hidden=true;$('liveFrame').hidden=true;$('download').href=message.image;$('download').download=`Retire-${resultId}.jpg`;$('qrImage').src=message.qr;status('ประกอบภาพความละเอียดเต็มเสร็จแล้ว');controls();}else if(message.event==='error'){busy=false;$('count').textContent='';status(`เกิดข้อผิดพลาด: ${message.message}`);controls();}}
let previewRetry;
async function connectPreview(){
 clearTimeout(previewRetry);const old=peer;peer=null;old?.close();
 const pc=new RTCPeerConnection();peer=pc;const video=$('preview');
 $('serverState').textContent='กำลังรอภาพจาก Capture Card…';
 pc.addTransceiver('video',{direction:'recvonly'});
 pc.ontrack=event=>{if(peer!==pc)return;video.srcObject=event.streams[0]||new MediaStream([event.track]);video.muted=true;video.playsInline=true;
  video.onplaying=()=>{if(peer===pc&&video.videoWidth>0&&video.readyState>=2){$('serverState').textContent='Live View พร้อมใช้งาน';if(!busy&&!resultId)status('ได้รับภาพจาก Capture Card แล้ว');}};
  video.play().catch(()=>{if(peer===pc)$('serverState').textContent='แตะเลือกเฟรมเพื่อเริ่มแสดงภาพ';});
 };
 pc.onconnectionstatechange=()=>{if(peer===pc&&['failed','disconnected'].includes(pc.connectionState)){$('serverState').textContent='Live View ขาดการเชื่อมต่อ กำลังลองใหม่…';clearTimeout(previewRetry);previewRetry=setTimeout(()=>connectPreview().catch(previewError),1500);}};
 try{
  await pc.setLocalDescription(await pc.createOffer());
  if(pc.iceGatheringState!=='complete')await new Promise((resolve,reject)=>{const timer=setTimeout(()=>reject(Error('หมดเวลารอการเชื่อมต่อเครือข่าย')),12000);pc.onicegatheringstatechange=()=>{if(pc.iceGatheringState==='complete'){clearTimeout(timer);resolve();}};});
  if(peer!==pc)return;
  const response=await fetch('/api/offer',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(pc.localDescription)});
  if(!response.ok)throw Error('Camera Server เปิด Capture Card ไม่สำเร็จ');
  await pc.setRemoteDescription(await response.json());
 }catch(error){if(peer===pc){peer=null;pc.close();}throw error;}
}
function previewError(error){$('serverState').textContent=`เปิด Live View ไม่ได้: ${error.message}`;}
$('frames').addEventListener('click',()=>{if($('preview').srcObject)$('preview').play().catch(previewError);});
$('shoot').onclick=()=>{if(busy||!connected||!config)return;busy=true;CaptureSettings.unlock();controls();const options=CaptureSettings.get();socketSend({action:'capture',frame:config.id,mode:options.mode,countdown:options.seconds});};
$('retake').onclick=()=>{resultId='';$('result').hidden=true;$('preview').hidden=false;$('liveFrame').hidden=false;socketSend({action:'reset',frame:config.id});status('พร้อมถ่ายชุดใหม่');controls();};
$('back').onclick=()=>{$('booth').hidden=true;$('selection').hidden=false;config=null;resultId='';framePage();controls();};
$('showQr').onclick=()=>$('qrDialog').showModal();$('closeQr').onclick=()=>$('qrDialog').close();
$('print').onclick=async()=>{if(!resultId)return;$('print').disabled=true;try{const response=await fetch(`/api/print/${resultId}`,{method:'POST'});if(!response.ok)throw Error((await response.json()).detail||'สั่งพิมพ์ไม่สำเร็จ');status('ส่งงานไปยังเครื่องพิมพ์แล้ว');}catch(error){status(error.message);}finally{$('print').disabled=false;}};
connectSocket();connectPreview().catch(error=>{$('serverState').textContent='เปิด Live View ไม่ได้';console.error(error);});CaptureSettings.onChange=controls;controls();if('serviceWorker'in navigator&&location.protocol==='https:')navigator.serviceWorker.register('/sw.js').catch(()=>{});
