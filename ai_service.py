import json
import re
import requests
from config import Config

def _chat(messages,temperature=0.3,max_tokens=1200):
    if not Config.MISTRAL_API_KEY: raise RuntimeError("AI API key is not configured. Add MISTRAL_API_KEY to .env.")
    response=requests.post(f"{Config.MISTRAL_BASE_URL}/chat/completions",headers={"Authorization":f"Bearer {Config.MISTRAL_API_KEY}","Content-Type":"application/json"},json={"model":Config.MISTRAL_MODEL,"messages":messages,"temperature":temperature,"max_tokens":max_tokens},timeout=90)
    response.raise_for_status();data=response.json()
    try:return data["choices"][0]["message"]["content"].strip()
    except (KeyError,IndexError,TypeError) as exc:raise RuntimeError("AI provider returned an unexpected response.") from exc

def _with_context(question,context):
    if not context:return question
    return "Use the supplied study material when relevant. Do not invent claims about the material.\n\nSTUDY MATERIAL:\n"+context+"\n\nTASK:\n"+question

def ask_ai(question,context="",mode="normal"):
    modes={"normal":"Answer clearly and accurately at a college-student level.","simple":"Explain in very simple language, using an analogy or small example where useful.","exam":"Give an exam-ready answer with headings, key points, examples, and a concise conclusion.","step":"Explain step by step and do not skip important steps."}
    system="You are ScholarSync AI, a helpful academic study copilot. Be accurate, practical, and transparent about uncertainty. "+modes.get(mode,modes["normal"])
    return _chat([{"role":"system","content":system},{"role":"user","content":_with_context(question,context)}],temperature=.25,max_tokens=1800)

def generate_exam_answer(subject,marks,question,context=""):
    task=f"Subject: {subject}\nMarks: {marks}\nQuestion: {question}\n\nWrite a university exam-ready answer. Match depth to {marks} marks, use clear headings and bullets, include examples or simple text diagrams where useful, and finish with a short conclusion."
    return _chat([{"role":"system","content":"You are an expert university exam-answer tutor."},{"role":"user","content":_with_context(task,context)}],temperature=.2,max_tokens=2200)

def generate_quiz(topic,count,context=""):
    count=max(2,min(int(count),25));task=f"Create exactly {count} multiple-choice questions about: {topic}. Return ONLY valid JSON with this schema: {{\"questions\":[{{\"question\":\"...\",\"options\":[\"...\",\"...\",\"...\",\"...\"],\"answer\":0,\"explanation\":\"...\"}}]}}. answer is zero-based 0-3. Make exactly four options per question."
    raw=_chat([{"role":"system","content":"You create accurate educational MCQs and always follow the requested JSON schema."},{"role":"user","content":_with_context(task,context)}],temperature=.2,max_tokens=4000)
    raw=re.sub(r"^```(?:json)?\s*|\s*```$","",raw.strip(),flags=re.I)
    try:questions=json.loads(raw)["questions"]
    except (json.JSONDecodeError,KeyError,TypeError) as exc:raise RuntimeError("AI returned invalid quiz JSON. Please try again.") from exc
    if not isinstance(questions,list) or len(questions)!=count:raise RuntimeError("AI returned an incorrect number of quiz questions.")
    cleaned=[]
    for item in questions:
        if not isinstance(item,dict):raise RuntimeError("AI returned an invalid quiz question.")
        options=item.get("options");answer=item.get("answer")
        if not isinstance(options,list) or len(options)!=4 or not isinstance(answer,int) or not 0<=answer<4:raise RuntimeError("AI returned an invalid quiz option set.")
        cleaned.append({"question":str(item.get("question","")).strip(),"options":[str(o).strip() for o in options],"answer":answer,"explanation":str(item.get("explanation","")).strip()})
    return cleaned

def generate_study_plan(subjects,exam_date,hours,weak_topics="",context=""):
    task=f"Subjects/topics:\n{subjects}\n\nExam date: {exam_date}\nAvailable study time per day: {hours} hours\nWeak topics: {weak_topics or 'None provided'}\n\nCreate a practical day-by-day study plan. Prioritize weak topics, include revision and practice, use realistic daily workloads within the stated hours, and clearly separate study, practice, revision and rest."
    return _chat([{"role":"system","content":"You are a practical academic study-planning assistant."},{"role":"user","content":_with_context(task,context)}],temperature=.3,max_tokens=2400)
