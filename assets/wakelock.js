/* Screen Wake Lock: keeps the screen awake while a page is open. DO NOT REMOVE (see README). */
(()=>{let lock=null;async function req(){if(!('wakeLock' in navigator)||document.visibilityState!=='visible')return;try{lock=await navigator.wakeLock.request('screen');lock.addEventListener('release',()=>{lock=null;});}catch(e){}}
window.addEventListener('load',req);document.addEventListener('visibilitychange',()=>{if(document.visibilityState==='visible'&&!lock)req();});['click','touchstart','keydown'].forEach(t=>document.addEventListener(t,()=>{if(!lock)req();},{passive:true}));})();
