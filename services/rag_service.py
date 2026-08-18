import re
from collections import Counter
from firebase_service import require_db

_STOP_WORDS={"the","and","for","are","but","not","with","you","your","this","that","from","what","when","where","which","how","why","can","does","into","about","have","has","had","was","were","will","would","could","should","a","an","is","of","to","in","on","at","as","it","be","or","by","we","our"}

def _terms(text): return [w for w in re.findall(r"[a-zA-Z0-9]+",text.lower()) if len(w)>2 and w not in _STOP_WORDS]

def _chunks_ref(uid,document_id):
    return require_db().collection("users").document(uid).collection("documents").document(document_id).collection("chunks")

def retrieve_context(uid,document_id,question,top_k=6):
    query_terms=Counter(_terms(question));scored=[]
    for snapshot in _chunks_ref(uid,document_id).stream():
        data=snapshot.to_dict() or {};text=str(data.get("text","")).strip()
        if not text:continue
        chunk_terms=Counter(_terms(text));score=sum(min(chunk_terms[t],3)*weight for t,weight in query_terms.items());scored.append((score,int(data.get("index",0)),text))
    scored.sort(key=lambda x:(x[0],-x[1]),reverse=True)
    return "\n\n".join(x[2] for x in scored[:top_k])

def get_document_context(uid,document_id,max_chars=14000):
    rows=[]
    for snapshot in _chunks_ref(uid,document_id).stream():
        data=snapshot.to_dict() or {};rows.append((int(data.get("index",0)),str(data.get("text","")).strip()))
    rows.sort(key=lambda x:x[0]);parts=[];total=0
    for _,text in rows:
        if not text:continue
        if total+len(text)>max_chars:
            parts.append(text[:max_chars-total]);break
        parts.append(text);total+=len(text)
    return "\n\n".join(parts)
