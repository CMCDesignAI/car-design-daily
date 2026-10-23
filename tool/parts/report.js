// Usage: PartsReport.button({car,tab,imageKey}) -> <button>; append inside a position:relative image wrapper (card + lightbox).
window.PartsReport=(()=>{const ENDPOINT="https://parts-report.cmcdesignai.workers.dev";
const R=["不是這個零件","車型錯誤","視角不一致","重複","其他"];
function open(info){const m=document.createElement("div");m.className="rpt-mask";
m.innerHTML=`<div class="rpt-box"><h3>回報錯誤圖片</h3>${R.map((r,i)=>`<label><input type="radio" name="rpt" value="${r}" ${i?"":"checked"}> ${r}</label>`).join("")}<textarea maxlength="500" rows="3" placeholder="補充說明（選填）"></textarea><div class="rpt-act"><button class="rpt-cancel">取消</button><button class="rpt-send">送出</button></div></div>`;
const close=()=>m.remove();m.onclick=e=>{if(e.target===m)close()};m.querySelector(".rpt-cancel").onclick=close;
m.querySelector(".rpt-send").onclick=async e=>{e.target.disabled=true;e.target.textContent="送出中…";
try{const r=await fetch(ENDPOINT,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({...info,reason:m.querySelector("input:checked").value,note:m.querySelector("textarea").value})});
m.querySelector(".rpt-box").innerHTML=r.ok?"<h3>謝謝回報！</h3>":"<h3>送出失敗，請稍後再試</h3>";}catch{m.querySelector(".rpt-box").innerHTML="<h3>送出失敗</h3>"}setTimeout(close,1200)};
(document.querySelector("dialog[open]")||document.body).appendChild(m)}
function button(info){const b=document.createElement("button");b.className="rpt-btn";b.type="button";b.textContent="⚑ 回報";b.title="回報錯誤圖片";
b.onclick=e=>{e.stopPropagation();e.preventDefault();open(info)};return b}
return{button,open}})();
