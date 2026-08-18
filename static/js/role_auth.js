import { auth, signInWithEmailAndPassword, createUserWithEmailAndPassword } from "./firebase.js";
const role=window.SCHOLAR_ROLE||"student"; const $=id=>document.getElementById(id); const msg=$("authMessage");
function show(text,ok=false){msg.className=ok?"alert alert-success":"alert alert-danger";msg.textContent=text;msg.classList.remove("d-none");}
function mode(register){$("loginTab").classList.toggle("active",!register);$("registerTab").classList.toggle("active",register);$("registerFields").classList.toggle("d-none",!register);$("loginBtn").classList.toggle("d-none",register);$("registerBtn").classList.toggle("d-none",!register);msg.classList.add("d-none");}
$("loginTab").onclick=()=>mode(false);$("registerTab").onclick=()=>mode(true);
async function login(){const email=$("email").value.trim(),password=$("password").value;if(!email||!password)return show("Enter email and password.");try{$("loginBtn").disabled=true;await signInWithEmailAndPassword(auth,email,password);const token=await auth.currentUser.getIdToken();const r=await fetch("/api/me",{headers:{Authorization:`Bearer ${token}`}});const me=await r.json();if(me.role!==role){await auth.signOut();return show(`This account is registered as ${me.role}. Use the ${me.role} portal.`);}window.location.replace(role==="faculty"?"/faculty-dashboard":"/student-dashboard");}catch(e){show(clean(e));}finally{$("loginBtn").disabled=false;}}
async function register(){
const name=String($("name")?.value??"").trim();
const email=String($("email")?.value??"").trim();
const password=String($("password")?.value??"");
if(!name||!email||!password)return show("Please fill the required fields.");
if(password.length<6)return show("Password must contain at least 6 characters.");
const payload={role,name};
if(role==="student"){
  payload.reg_no=String($("regNo")?.value??"").trim();
  payload.department=String($("department")?.value??"").trim();
  payload.year=String($("year")?.value??"").trim();
  payload.semester=String($("semester")?.value??"").trim();
  if(!payload.name||!payload.reg_no||!payload.department||!payload.year||!payload.semester)return show("Student name, register number, department, year and semester are required.");
}else{
  payload.employee_id=String($("employeeId")?.value??"").trim();
  payload.department=String($("department")?.value??"").trim();
  payload.designation=String($("designation")?.value??"").trim();
  payload.subjects=String($("subjects")?.value??"").trim();
  if(!payload.name||!payload.employee_id||!payload.department||!payload.designation)return show("Faculty name, ID, department and designation are required.");
}
try{$("registerBtn").disabled=true;let cred;try{cred=await createUserWithEmailAndPassword(auth,email,password);}catch(e){if(e?.code==="auth/email-already-in-use"){show("This email already has a Firebase account. Checking the password and completing the profile...",true);cred=await signInWithEmailAndPassword(auth,email,password);}else{throw e;}}const token=await cred.user.getIdToken(true);const r=await fetch("/api/profile",{method:"POST",headers:{"Content-Type":"application/json",Authorization:`Bearer ${token}`},body:JSON.stringify(payload)});const data=await r.json();if(!r.ok)throw new Error(data.error||"Profile creation failed.");window.location.replace(role==="faculty"?"/faculty-dashboard":"/student-dashboard");}catch(e){show(clean(e));}finally{$("registerBtn").disabled=false;}}
function clean(e){const c=e?.code||"";if(c.includes("invalid-credential")||c.includes("wrong-password"))return"Email or password is incorrect.";if(c.includes("email-already-in-use"))return"This email is already registered.";if(c.includes("invalid-email"))return"Enter a valid email address.";if(c.includes("weak-password"))return"Password must contain at least 6 characters.";return e?.message||"Authentication failed.";}
$("loginBtn").onclick=login;$("registerBtn").onclick=register;$("password").onkeydown=e=>{if(e.key==="Enter"){if($("loginBtn").classList.contains("d-none"))register();else login();}};
