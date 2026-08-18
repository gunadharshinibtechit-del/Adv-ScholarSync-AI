import { auth, onAuthStateChanged } from "./firebase.js";
import { authHeaders } from "./app.js";
const $=id=>document.getElementById(id);
async function loadDocs(){const r=await fetch("/api/documents",{headers:await authHeaders()});if(!r.ok)return;const docs=await r.json();const s=$("plannerDoc");docs.forEach(d=>{const o=document.createElement("option");o.value=d.document_id;o.textContent=d.filename;s.appendChild(o);});}
$("planBtn").addEventListener("click",async()=>{const out=$("planOutput");out.textContent="Building a realistic schedule...";$("planBtn").disabled=true;try{const r=await fetch("/api/planner",{method:"POST",headers:{"Content-Type":"application/json",...(await authHeaders())},body:JSON.stringify({subjects:$("subjects").value,exam_date:$("examDate").value,hours:$("hours").value,weak_topics:$("weakTopics").value,document_id:$("plannerDoc").value})});const d=await r.json();out.textContent=r.ok?d.plan:d.error;}catch(e){out.textContent=e.message;}finally{$("planBtn").disabled=false;}});
onAuthStateChanged(auth,u=>{if(u)loadDocs();});
