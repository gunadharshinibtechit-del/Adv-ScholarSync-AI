import { auth, onAuthStateChanged, signOut } from "./firebase.js";

export async function authHeaders(){
  const user=auth.currentUser;
  if(!user) throw new Error("Your login session has expired.");
  return {Authorization:`Bearer ${await user.getIdToken()}`};
}
window.scholarAuthHeaders=authHeaders;

const path=window.location.pathname;
const publicPath=["/","/student-login","/faculty-login","/login"].includes(path);
const logoutBtn=document.getElementById("logoutBtn");
logoutBtn?.addEventListener("click",async()=>{try{await signOut(auth);location.replace("/");}catch{alert("Logout failed.");}});

const studentPaths=new Set(["/student-dashboard","/chat","/notes","/planner","/quiz","/profile"]);
const facultyPaths=new Set(["/faculty-dashboard","/faculty-profile","/chat"]);

function setNavForRole(role){
  document.querySelectorAll("[data-role-nav]").forEach(el=>{
    el.classList.toggle("d-none",el.dataset.roleNav!==role);
  });
  const home=document.getElementById("ssBrandHome");
  if(home) home.href=role==="faculty"?"/faculty-dashboard":"/student-dashboard";
  document.documentElement.dataset.role=role;
}

async function fetchMe(user){
  const token=await user.getIdToken();
  const r=await fetch("/api/me",{headers:{Authorization:`Bearer ${token}`},cache:"no-store"});
  if(!r.ok) throw new Error("Unable to verify your academic role.");
  return await r.json();
}

async function roleRedirect(user){
  // The role login page also contains the registration flow. Firebase
  // Authentication changes auth.currentUser immediately after account
  // creation, while the Firestore profile is written by role_auth.js
  // immediately afterwards. Do not run the global role guard here, or it
  // can race the profile write and incorrectly report an incomplete profile.
  const authPortal=path==="/student-login" || path==="/faculty-login";
  if(authPortal) return;

  if(!user){
    if(!publicPath) location.replace("/");
    return;
  }
  try{
    const me=await fetchMe(user);
    const role=me.role;
    if(role!=="student" && role!=="faculty"){
      console.error("No valid role in Firestore for",user.uid);
      await signOut(auth);
      alert("Your ScholarSync profile is incomplete. Please register again through the correct portal.");
      location.replace("/");
      return;
    }
    setNavForRole(role);

    if(path==="/"||path==="/login") return location.replace(role==="faculty"?"/faculty-dashboard":"/student-dashboard");
    if(path==="/student-login"||path==="/faculty-login"){
      const requested=path==="/faculty-login"?"faculty":"student";
      if(requested!==role) return location.replace(role==="faculty"?"/faculty-dashboard":"/student-dashboard");
      return;
    }
    if(path==="/dashboard") return location.replace(role==="faculty"?"/faculty-dashboard":"/student-dashboard");

    // Hard client-side page guard: a student can never remain on a faculty page,
    // and a faculty user can never remain on a student-only page.
    if(role==="student" && path==="/faculty-dashboard") return location.replace("/student-dashboard");
    if(role==="student" && path==="/faculty-profile") return location.replace("/student-dashboard");
    if(role==="faculty" && path==="/student-dashboard") return location.replace("/faculty-dashboard");
    if(role==="faculty" && path==="/profile") return location.replace("/faculty-profile");
    if(role==="faculty" && studentPaths.has(path) && !facultyPaths.has(path)) return location.replace("/faculty-dashboard");
    if(role==="student" && facultyPaths.has(path) && !studentPaths.has(path)) return location.replace("/student-dashboard");

    document.querySelectorAll(".ss-navlink").forEach(link=>{
      link.classList.toggle("active",link.getAttribute("href")===path);
    });
  }catch(e){console.error(e);}
}

onAuthStateChanged(auth,user=>{
  document.documentElement.dataset.authenticated=user?"true":"false";
  roleRedirect(user);
});
