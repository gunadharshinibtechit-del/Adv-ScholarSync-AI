import os
import tempfile
from datetime import datetime, timezone
from functools import wraps
from pathlib import Path
from uuid import uuid4
from flask import Flask, jsonify, render_template, request
from werkzeug.utils import secure_filename
from ai_service import ask_ai, generate_exam_answer, generate_quiz, generate_study_plan
from config import Config
from firebase_service import require_db, verify_id_token
from services.pdf_service import chunk_text, extract_pdf_text
from services.rag_service import retrieve_context, get_document_context

app=Flask(__name__);app.config["SECRET_KEY"]=Config.SECRET_KEY;app.config["MAX_CONTENT_LENGTH"]=Config.MAX_CONTENT_LENGTH;app.config["UPLOAD_FOLDER"]=Config.UPLOAD_FOLDER
ALLOWED_EXTENSIONS={"pdf","txt"};os.makedirs(Config.UPLOAD_FOLDER,exist_ok=True)

def _timestamp(v): return v.isoformat() if hasattr(v,"isoformat") else v
def _auth_required(view):
    @wraps(view)
    def wrapped(*args,**kwargs):
        header=request.headers.get("Authorization","")
        if not header.startswith("Bearer "):return jsonify({"success":False,"error":"Authentication required."}),401
        try:request.user=verify_id_token(header.split(" ",1)[1].strip())
        except ValueError as exc:return jsonify({"success":False,"error":str(exc)}),401
        return view(*args,**kwargs)
    return wrapped

def _json_body():
    data=request.get_json(silent=True)
    if not isinstance(data,dict):raise ValueError("A JSON request body is required.")
    return data

def _doc_ref(uid,document_id):return require_db().collection("users").document(uid).collection("documents").document(document_id)
def _allowed(filename):return "." in filename and filename.rsplit(".",1)[1].lower() in ALLOWED_EXTENSIONS

def _user_ref(uid):
    return require_db().collection("users").document(uid)

def _user_profile(uid):
    return _user_ref(uid).get().to_dict() or {}

def _role_required(role):
    def decorator(view):
        @wraps(view)
        def wrapped(*args,**kwargs):
            profile=_user_profile(request.user["uid"])
            actual=profile.get("role","student")
            if actual!=role:
                return jsonify({"success":False,"error":f"{role.title()} access required."}),403
            request.user_profile=profile
            return view(*args,**kwargs)
        return wrapped
    return decorator

def _roles_required(*roles):
    def decorator(view):
        @wraps(view)
        def wrapped(*args,**kwargs):
            profile=_user_profile(request.user["uid"])
            actual=profile.get("role","student")
            if actual not in roles:
                return jsonify({"success":False,"error":"You do not have permission for this action."}),403
            request.user_profile=profile
            return view(*args,**kwargs)
        return wrapped
    return decorator

@app.route("/")
def home():return render_template("index.html")
@app.route("/student-login")
def student_login():return render_template("role_login.html", role="student")
@app.route("/faculty-login")
def faculty_login():return render_template("role_login.html", role="faculty")
@app.route("/student-dashboard")
def student_dashboard():return render_template("student_dashboard.html")
@app.route("/faculty-dashboard")
def faculty_dashboard():return render_template("faculty_dashboard.html")
@app.route("/faculty-profile")
def faculty_profile_page():return render_template("faculty_profile.html")
@app.route("/dashboard")
def dashboard():return render_template("dashboard.html")
@app.route("/chat")
def chat_page():return render_template("chat.html")
@app.route("/notes")
def notes_page():return render_template("notes.html")
@app.route("/planner")
def planner_page():return render_template("planner.html")
@app.route("/quiz")
def quiz_page():return render_template("quiz.html")
@app.route("/profile")
def profile_page():return render_template("profile.html")
@app.route("/health")
def health():return jsonify({"status":"ok","message":"ScholarSync AI server is running"})

@app.route("/api/me",methods=["GET"])
@_auth_required
def me():
    profile=_user_profile(request.user["uid"])
    profile.update({"uid":request.user["uid"],"email":request.user.get("email",profile.get("email",""))})
    # Never silently assume a missing profile is a student.
    # A missing role can otherwise make the frontend redirect a faculty user to the student portal.
    profile.setdefault("role","unassigned")
    return jsonify(profile)

@app.route("/api/profile",methods=["GET","POST"])
@_auth_required
def profile():
    uid=request.user["uid"];ref=_user_ref(uid);existing=ref.get().to_dict() or {}
    if request.method=="GET":
        data=existing;data["email"]=request.user.get("email",data.get("email",""));data.setdefault("role","unassigned");return jsonify(data)
    data=_json_body();role=str(data.get("role",existing.get("role","student"))).lower().strip()
    if role not in {"student","faculty"}:return jsonify({"success":False,"error":"Invalid role."}),400
    if existing.get("role") and existing.get("role")!=role:return jsonify({"success":False,"error":"Account role cannot be changed after registration."}),403
    if role=="faculty":
        payload={"role":"faculty","name":str(data.get("name","")).strip(),"employee_id":str(data.get("employee_id","")).strip(),"department":str(data.get("department","")).strip(),"designation":str(data.get("designation","")).strip(),"subjects":str(data.get("subjects","")).strip(),"email":request.user.get("email","")}
    else:
        payload={"role":"student","name":str(data.get("name","")).strip(),"reg_no":str(data.get("reg_no","")).strip().upper(),"department":str(data.get("department","")).strip(),"year":str(data.get("year","")).strip(),"semester":str(data.get("semester","")).strip(),"goal":str(data.get("goal","")).strip(),"bio":str(data.get("bio","")).strip(),"email":request.user.get("email","")}
    if len(payload.get("name", ""))>100:return jsonify({"success":False,"error":"Name is too long."}),400
    if role=="student" and (not payload["name"] or not payload["reg_no"] or not payload["department"] or not payload["year"] or not payload["semester"]):return jsonify({"success":False,"error":"Student name, register number, department, year and semester are required."}),400
    if role=="faculty" and (not payload["name"] or not payload["employee_id"] or not payload["department"] or not payload["designation"]):return jsonify({"success":False,"error":"Faculty name, employee ID, department and designation are required."}),400
    if role=="student":
        for snap in require_db().collection("users").where("reg_no","==",payload["reg_no"]).stream():
            if snap.id!=uid:return jsonify({"success":False,"error":"This register number is already linked to another account."}),409
    else:
        for snap in require_db().collection("users").where("employee_id","==",payload["employee_id"]).stream():
            if snap.id!=uid:return jsonify({"success":False,"error":"This faculty ID is already linked to another account."}),409
    payload["updated_at"]=datetime.now(timezone.utc);payload.setdefault("created_at",datetime.now(timezone.utc));ref.set(payload,merge=True)
    return jsonify({"success":True,"message":"Profile saved.","role":role})

@app.route("/api/students",methods=["GET"])
@_auth_required
@_role_required("faculty")
def students():
    q=request.args.get("q","").strip().lower();reg=request.args.get("reg_no","").strip().lower();year=request.args.get("year","").strip();semester=request.args.get("semester","").strip();department=request.args.get("department","").strip().lower()
    result=[]
    for snap in require_db().collection("users").where("role","==","student").stream():
        d=snap.to_dict() or {};name=str(d.get("name","")).lower();r=str(d.get("reg_no","")).lower();dept=str(d.get("department","")).lower()
        if q and q not in name and q not in r:continue
        if reg and reg not in r:continue
        if year and str(d.get("year",""))!=year:continue
        if semester and str(d.get("semester",""))!=semester:continue
        if department and department not in dept:continue
        result.append({"uid":snap.id,"name":d.get("name",""),"reg_no":d.get("reg_no",""),"department":d.get("department",""),"year":d.get("year",""),"semester":d.get("semester",""),"goal":d.get("goal","")})
    result.sort(key=lambda x:(str(x.get("name","" )).lower(),str(x.get("reg_no",""))))
    return jsonify({"success":True,"students":result[:200]})

@app.route("/api/students/<student_uid>",methods=["GET"])
@_auth_required
@_role_required("faculty")
def student_detail(student_uid):
    ref=_user_ref(student_uid);snap=ref.get()
    if not snap.exists:return jsonify({"success":False,"error":"Student not found."}),404
    d=snap.to_dict() or {}
    if d.get("role")!="student":return jsonify({"success":False,"error":"This account is not a student."}),404
    docs=[]
    for ds in ref.collection("documents").stream():
        x=ds.to_dict() or {};docs.append({"document_id":ds.id,"filename":x.get("filename",""),"chunk_count":x.get("chunk_count",0),"created_at":_timestamp(x.get("created_at"))})
    docs.sort(key=lambda x:x.get("created_at") or "",reverse=True)
    d.pop("email",None);d["uid"]=student_uid;d["documents"]=docs
    return jsonify({"success":True,"student":d})

@app.route("/api/faculty/notes",methods=["POST"])
@_auth_required
@_role_required("faculty")
def faculty_note():
    data=_json_body();student_uid=str(data.get("student_uid","")).strip();note=str(data.get("note","")).strip()
    if not student_uid or not note or len(note)>2000:return jsonify({"success":False,"error":"Student and a note under 2000 characters are required."}),400
    student=_user_profile(student_uid)
    if student.get("role")!="student":return jsonify({"success":False,"error":"Student not found."}),404
    require_db().collection("users").document(student_uid).collection("faculty_notes").add({"faculty_uid":request.user["uid"],"faculty_name":request.user_profile.get("name","Faculty"),"note":note,"created_at":datetime.now(timezone.utc)})
    return jsonify({"success":True,"message":"Mentoring note saved."})

@app.route("/api/faculty/announcements",methods=["GET","POST"])
@_auth_required
@_roles_required("faculty","student")
def announcements():
    db=require_db();collection=db.collection("announcements")
    if request.method=="GET":
        rows=[]
        for snap in collection.stream():
            d=snap.to_dict() or {};d["id"]=snap.id;d["created_at"]=_timestamp(d.get("created_at"));rows.append(d)
        rows.sort(key=lambda x:x.get("created_at") or "", reverse=True)
        return jsonify({"success":True,"announcements":rows[:20]})
    if request.user_profile.get("role")!="faculty":return jsonify({"success":False,"error":"Faculty access required."}),403
    data=_json_body();title=str(data.get("title","")).strip();message=str(data.get("message","")).strip();target=str(data.get("target","all")).strip()
    if not title or not message:return jsonify({"success":False,"error":"Title and message are required."}),400
    db.collection("announcements").add({"title":title,"message":message,"target":target,"faculty_uid":request.user["uid"],"faculty_name":request.user_profile.get("name","Faculty"),"created_at":datetime.now(timezone.utc)})
    return jsonify({"success":True,"message":"Announcement posted."})

@app.route("/api/documents",methods=["GET"])
@_auth_required
def documents():
    uid=request.user["uid"];docs=[]
    for snapshot in require_db().collection("users").document(uid).collection("documents").stream():
        data=snapshot.to_dict() or {};docs.append({"document_id":snapshot.id,"filename":data.get("filename","Unnamed file"),"chunk_count":data.get("chunk_count",0),"created_at":_timestamp(data.get("created_at")),"size_bytes":data.get("size_bytes",0)})
    docs.sort(key=lambda x:x.get("created_at") or "",reverse=True);return jsonify(docs)

@app.route("/api/documents/<document_id>",methods=["DELETE"])
@_auth_required
def delete_document(document_id):
    uid=request.user["uid"];ref=_doc_ref(uid,document_id)
    if not ref.get().exists:return jsonify({"success":False,"error":"Document not found."}),404
    db=require_db();batch=db.batch();count=0
    for snap in ref.collection("chunks").stream():
        batch.delete(snap.reference);count+=1
        if count==450:batch.commit();batch=db.batch();count=0
    batch.delete(ref);batch.commit();return jsonify({"success":True})

@app.route("/api/upload",methods=["POST"])
@_auth_required
def upload():
    if "file" not in request.files:return jsonify({"success":False,"error":"No file was uploaded."}),400
    file=request.files["file"]
    if not file.filename:return jsonify({"success":False,"error":"Please choose a file."}),400
    if not _allowed(file.filename):return jsonify({"success":False,"error":"Only PDF and TXT files are supported."}),400
    original_name=secure_filename(file.filename);suffix=Path(original_name).suffix.lower();temp_path=None
    try:
        with tempfile.NamedTemporaryFile(delete=False,suffix=suffix,dir=Config.UPLOAD_FOLDER) as temp:file.save(temp);temp_path=temp.name
        text=extract_pdf_text(temp_path) if suffix==".pdf" else Path(temp_path).read_text(encoding="utf-8",errors="replace").strip();chunks=chunk_text(text)
        if not chunks:return jsonify({"success":False,"error":"No readable text was found. If this is a scanned PDF, use a text-based/OCR PDF."}),400
        uid=request.user["uid"];document_id=uuid4().hex;doc_ref=_doc_ref(uid,document_id);db=require_db();doc_ref.set({"filename":original_name,"chunk_count":len(chunks),"created_at":datetime.now(timezone.utc),"size_bytes":os.path.getsize(temp_path)})
        batch=db.batch();writes=0
        for index,chunk in enumerate(chunks):
            batch.set(doc_ref.collection("chunks").document(f"chunk_{index:04d}"),{"text":chunk,"index":index});writes+=1
            if writes==450:batch.commit();batch=db.batch();writes=0
        if writes:batch.commit()
        return jsonify({"success":True,"document_id":document_id,"filename":original_name,"chunk_count":len(chunks)})
    except Exception as exc:
        app.logger.exception("Upload processing failed");return jsonify({"success":False,"error":f"Could not process the file: {exc}"}),500
    finally:
        if temp_path:
            try:os.remove(temp_path)
            except OSError:pass

@app.route("/api/chat",methods=["POST"])
@_auth_required
def chat():
    try:
        data=_json_body();question=str(data.get("question","")).strip();mode=str(data.get("mode","normal"));document_id=str(data.get("document_id","")).strip()
        if not question or len(question)>5000:return jsonify({"success":False,"error":"Question is required and must be under 5000 characters."}),400
        context=""
        if document_id:
            if not _doc_ref(request.user["uid"],document_id).get().exists:return jsonify({"success":False,"error":"Document not found."}),404
            context=retrieve_context(request.user["uid"],document_id,question)
        return jsonify({"success":True,"answer":ask_ai(question,context=context,mode=mode)})
    except Exception as exc:app.logger.exception("Chat failed");return jsonify({"success":False,"error":str(exc)}),500

@app.route("/api/answer",methods=["POST"])
@_auth_required
def answer():
    try:
        data=_json_body();subject=str(data.get("subject","")).strip();question=str(data.get("question","")).strip();marks=int(data.get("marks",5));document_id=str(data.get("document_id","")).strip();context=""
        if not subject or not question or marks not in {2,5,10,13,16}:return jsonify({"success":False,"error":"Provide subject, question, and marks of 2, 5, 10, 13, or 16."}),400
        if document_id:
            if not _doc_ref(request.user["uid"],document_id).get().exists:return jsonify({"success":False,"error":"Document not found."}),404
            context=retrieve_context(request.user["uid"],document_id,question)
        return jsonify({"success":True,"answer":generate_exam_answer(subject,marks,question,context)})
    except (ValueError,TypeError):return jsonify({"success":False,"error":"Invalid exam-answer request."}),400
    except Exception as exc:app.logger.exception("Answer generation failed");return jsonify({"success":False,"error":str(exc)}),500

@app.route("/api/quiz",methods=["POST"])
@_auth_required
def quiz():
    try:
        data=_json_body();topic=str(data.get("topic","")).strip();count=int(data.get("count",5));document_id=str(data.get("document_id","")).strip();context=""
        if not topic or not 2<=count<=25:return jsonify({"success":False,"error":"Topic is required and question count must be 2–25."}),400
        if document_id:
            if not _doc_ref(request.user["uid"],document_id).get().exists:return jsonify({"success":False,"error":"Document not found."}),404
            context=retrieve_context(request.user["uid"],document_id,topic,top_k=8)
        return jsonify({"success":True,"questions":generate_quiz(topic,count,context)})
    except (ValueError,TypeError):return jsonify({"success":False,"error":"Invalid quiz request."}),400
    except Exception as exc:app.logger.exception("Quiz generation failed");return jsonify({"success":False,"error":str(exc)}),500

@app.route("/api/planner",methods=["POST"])
@_auth_required
def planner():
    try:
        data=_json_body();subjects=str(data.get("subjects","")).strip();exam_date=str(data.get("exam_date","")).strip();hours=float(data.get("hours",2));weak_topics=str(data.get("weak_topics","")).strip();document_id=str(data.get("document_id","")).strip();context=""
        if not subjects or not exam_date or not 0<hours<=12:return jsonify({"success":False,"error":"Subjects, exam date, and 0–12 study hours are required."}),400
        if document_id:
            if not _doc_ref(request.user["uid"],document_id).get().exists:return jsonify({"success":False,"error":"Document not found."}),404
            context=get_document_context(request.user["uid"],document_id,12000)
        return jsonify({"success":True,"plan":generate_study_plan(subjects,exam_date,hours,weak_topics,context)})
    except (ValueError,TypeError):return jsonify({"success":False,"error":"Invalid planner request."}),400
    except Exception as exc:app.logger.exception("Planner generation failed");return jsonify({"success":False,"error":str(exc)}),500

@app.errorhandler(413)
def too_large(_):return jsonify({"success":False,"error":f"File is too large. Maximum size is {Config.MAX_CONTENT_LENGTH//(1024*1024)} MB."}),413

if __name__=="__main__":app.run(host="127.0.0.1",port=int(os.getenv("PORT","5000")),debug=False)
