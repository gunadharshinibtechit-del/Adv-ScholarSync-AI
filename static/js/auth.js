import { auth, signInWithEmailAndPassword, createUserWithEmailAndPassword } from "./firebase.js";
const $ = id => document.getElementById(id);
const msg = $("authMessage");
const loginTab = $("loginTab"), registerTab = $("registerTab");
const loginBtn = $("loginBtn"), registerBtn = $("registerBtn"), nameWrap = $("nameWrap");
function showMessage(text, success=false){msg.className=success?"alert alert-success":"alert alert-danger";msg.textContent=text;msg.classList.remove("d-none");}
function setMode(register){
  loginTab.classList.toggle("active",!register); registerTab.classList.toggle("active",register);
  nameWrap.classList.toggle("d-none",!register); loginBtn.classList.toggle("d-none",register); registerBtn.classList.toggle("d-none",!register);
  $("authTitle").textContent=register?"Create your study workspace":"Sign in to your workspace";
  $("authSubtitle").textContent=register?"Save your profile, PDFs and study tools under one account.":"Your notes, chats and study tools stay organized in one place.";
  $("password").setAttribute("autocomplete",register?"new-password":"current-password"); msg.classList.add("d-none");
}
loginTab?.addEventListener("click",()=>setMode(false)); registerTab?.addEventListener("click",()=>setMode(true));
$("togglePassword")?.addEventListener("click",()=>{const input=$("password");const show=input.type==="password";input.type=show?"text":"password";$("togglePassword").textContent=show?"Hide":"Show";});
async function login(){const email=$("email").value.trim(),password=$("password").value;if(!email||!password)return showMessage("Enter your email and password.");try{loginBtn.disabled=true;await signInWithEmailAndPassword(auth,email,password);showMessage("Signed in. Opening your workspace...",true);window.location.replace("/chat");}catch(e){showMessage(cleanFirebaseError(e));}finally{loginBtn.disabled=false;}}
async function register(){const name=$("name").value.trim(),email=$("email").value.trim(),password=$("password").value;if(!name||!email||!password)return showMessage("Please fill all fields.");if(password.length<6)return showMessage("Password must contain at least 6 characters.");try{registerBtn.disabled=true;const cred=await createUserWithEmailAndPassword(auth,email,password);const token=await cred.user.getIdToken();await fetch("/api/profile",{method:"POST",headers:{"Content-Type":"application/json",Authorization:`Bearer ${token}`},body:JSON.stringify({name,email})});showMessage("Account created. Welcome to ScholarSync!",true);window.location.replace("/chat");}catch(e){showMessage(cleanFirebaseError(e));}finally{registerBtn.disabled=false;}}
function cleanFirebaseError(e){const code=e?.code||"";if(code.includes("invalid-credential")||code.includes("wrong-password"))return"Email or password is incorrect.";if(code.includes("email-already-in-use"))return"This email is already registered. Try Sign In.";if(code.includes("invalid-email"))return"Please enter a valid email address.";if(code.includes("weak-password"))return"Choose a stronger password with at least 6 characters.";return e?.message||"Authentication failed. Please try again.";}
loginBtn?.addEventListener("click",login);registerBtn?.addEventListener("click",register);$("password")?.addEventListener("keydown",e=>{if(e.key==="Enter") loginBtn.classList.contains("d-none")?register():login();});
