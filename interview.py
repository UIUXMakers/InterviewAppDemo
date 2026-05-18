import streamlit as st
import sqlite3
import random
import time
import json
import hashlib
import uuid
from datetime import datetime

st.set_page_config(
    page_title="InterviewX AI",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─── DATABASE ─────────────────────────────────────────────────────────────────
def init_db():
    conn = sqlite3.connect("interviewx.db", check_same_thread=False)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE, name TEXT, password_hash TEXT, device_id TEXT,
        plan TEXT DEFAULT 'free', interviews_remaining INTEGER DEFAULT 1,
        interviews_done INTEGER DEFAULT 0, created_at TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS interviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
        type TEXT, domain TEXT, difficulty TEXT, duration INTEGER,
        overall_score INTEGER, confidence_score INTEGER, eye_contact_score INTEGER,
        comm_score INTEGER, technical_score INTEGER, feedback TEXT, created_at TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS subscriptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, plan TEXT,
        price INTEGER, interviews_granted INTEGER, created_at TEXT
    )""")
    conn.commit(); conn.close()

def get_db():
    return sqlite3.connect("interviewx.db", check_same_thread=False)

def hash_pw(pw): return hashlib.sha256(pw.encode()).hexdigest()

def get_device_id():
    if "device_id" not in st.session_state:
        st.session_state.device_id = str(uuid.uuid4())
    return st.session_state.device_id

def register_user(email, name, password):
    conn = get_db(); c = conn.cursor()
    try:
        c.execute("INSERT INTO users (email,name,password_hash,device_id,created_at) VALUES (?,?,?,?,?)",
                  (email, name, hash_pw(password), get_device_id(), datetime.now().isoformat()))
        conn.commit(); return True, "ok"
    except sqlite3.IntegrityError: return False, "Email already registered."
    finally: conn.close()

def login_user(email, password):
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT * FROM users WHERE email=? AND password_hash=?", (email, hash_pw(password)))
    row = c.fetchone(); conn.close(); return row

def save_interview(uid, cfg, scores, feedback):
    conn = get_db(); c = conn.cursor()
    c.execute("""INSERT INTO interviews (user_id,type,domain,difficulty,duration,overall_score,
        confidence_score,eye_contact_score,comm_score,technical_score,feedback,created_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
        (uid, cfg.get("type","Technical"), cfg.get("domain","General"), cfg.get("difficulty","Medium"),
         cfg.get("duration",30), scores["overall"], scores["confidence"], scores["eye"],
         scores["comm"], scores["technical"], json.dumps(feedback), datetime.now().isoformat()))
    c.execute("UPDATE users SET interviews_done=interviews_done+1,interviews_remaining=MAX(0,interviews_remaining-1) WHERE id=?", (uid,))
    conn.commit(); conn.close()

def get_user_interviews(uid):
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT * FROM interviews WHERE user_id=? ORDER BY created_at DESC LIMIT 20", (uid,))
    rows = c.fetchall(); conn.close(); return rows

def upgrade_plan(uid, plan, n):
    conn = get_db(); c = conn.cursor()
    c.execute("UPDATE users SET plan=?,interviews_remaining=interviews_remaining+? WHERE id=?", (plan,n,uid))
    c.execute("INSERT INTO subscriptions (user_id,plan,price,interviews_granted,created_at) VALUES (?,?,?,?,?)",
              (uid,plan,0,n,datetime.now().isoformat()))
    conn.commit(); conn.close()

# ─── CSS ──────────────────────────────────────────────────────────────────────
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Sans:wght@300;400;500;600;700&display=swap');
html,body,[data-testid="stAppViewContainer"],[data-testid="stApp"]{background:#141414!important;color:#fff!important;font-family:'DM Sans',sans-serif!important;}
[data-testid="stSidebar"],[data-testid="stHeader"],[data-testid="stToolbar"],footer,#MainMenu,[data-testid="stDecoration"],[data-testid="stStatusWidget"],[data-testid="stBottom"]{display:none!important;}
.block-container{padding:0!important;max-width:100%!important;}
.stButton>button{background:#e50914!important;color:#fff!important;border:none!important;border-radius:4px!important;font-family:'DM Sans',sans-serif!important;font-weight:600!important;font-size:15px!important;padding:12px 28px!important;cursor:pointer!important;width:100%!important;transition:background 0.2s!important;}
.stButton>button:hover{background:#f40612!important;}
.stButton>button:focus{box-shadow:none!important;border:none!important;outline:none!important;}
.stTextInput>div>div>input{background:rgba(255,255,255,0.08)!important;border:1px solid rgba(255,255,255,0.2)!important;color:#fff!important;border-radius:4px!important;font-family:'DM Sans',sans-serif!important;font-size:15px!important;}
.stTextInput>div>div>input:focus{border-color:#e50914!important;box-shadow:none!important;}
.stTextInput label,.stSelectbox label,.stTextArea label{color:rgba(255,255,255,0.5)!important;font-size:12px!important;font-weight:600!important;letter-spacing:1px!important;text-transform:uppercase!important;font-family:'DM Sans',sans-serif!important;}
.stSelectbox>div>div{background:#2a2a2a!important;border:1px solid rgba(255,255,255,0.15)!important;color:#fff!important;border-radius:4px!important;}
[data-baseweb="select"]>div{background:#2a2a2a!important;border-color:rgba(255,255,255,0.15)!important;color:#fff!important;}
[data-baseweb="popover"],[data-baseweb="menu"]{background:#2a2a2a!important;}
li[role="option"]{background:#2a2a2a!important;color:#fff!important;}
li[role="option"]:hover{background:#3a3a3a!important;}
.stSelectbox [data-testid="stMarkdownContainer"] p{color:#fff!important;}
.stTextArea textarea{background:rgba(255,255,255,0.06)!important;border:1px solid rgba(255,255,255,0.15)!important;color:#fff!important;border-radius:4px!important;font-family:'DM Sans',sans-serif!important;}
.stRadio>div{flex-direction:row!important;gap:12px!important;}
.stRadio label,.stCheckbox label{color:rgba(255,255,255,0.8)!important;}
.stProgress>div>div>div{background:#e50914!important;}
.stProgress>div>div{background:rgba(255,255,255,0.1)!important;}
[data-testid="stMetricValue"]{color:#fff!important;font-family:'Bebas Neue',sans-serif!important;font-size:36px!important;letter-spacing:1px!important;}
[data-testid="stMetricLabel"]{color:rgba(255,255,255,0.5)!important;font-size:12px!important;text-transform:uppercase!important;letter-spacing:1px!important;}
hr{border-color:rgba(255,255,255,0.08)!important;}
::-webkit-scrollbar{width:4px;height:4px;}
::-webkit-scrollbar-track{background:#141414;}
::-webkit-scrollbar-thumb{background:#e50914;border-radius:2px;}
[data-baseweb="tab-list"]{background:transparent!important;border-bottom:1px solid rgba(255,255,255,0.08)!important;}
[data-baseweb="tab"]{color:rgba(255,255,255,0.5)!important;font-family:'DM Sans',sans-serif!important;}
[aria-selected="true"]{color:#fff!important;border-bottom:2px solid #e50914!important;}
[data-testid="column"]{padding:0 8px!important;}
.stAlert{background:rgba(20,20,20,0.9)!important;border-radius:6px!important;}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:0.3}}
@keyframes fadeIn{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:translateY(0)}}
@keyframes wave{0%,100%{transform:scaleY(0.4)}50%{transform:scaleY(1)}}
@keyframes ticker{from{transform:translateX(0)}to{transform:translateX(-50%)}}
@keyframes blink{0%,100%{opacity:1}50%{opacity:0.2}}
@keyframes scan{0%{top:8%}100%{top:88%}}
@keyframes fadeup{from{opacity:0;transform:translateY(4px)}to{opacity:1;transform:translateY(0)}}
@keyframes glow{0%,100%{box-shadow:0 0 8px rgba(0,212,170,0.4)}50%{box-shadow:0 0 18px rgba(0,212,170,0.8)}}
</style>
"""

# ─── HTML HELPERS ──────────────────────────────────────────────────────────────
def ring(score, label, color="#e50914", size=90):
    r = size//2-8; circ = 2*3.14159*r; off = circ-(score/100)*circ; fs = 18 if size>80 else 14
    return f"""<div style="display:flex;flex-direction:column;align-items:center;gap:8px;">
      <svg width="{size}" height="{size}" xmlns="http://www.w3.org/2000/svg">
        <circle cx="{size//2}" cy="{size//2}" r="{r}" fill="none" stroke="rgba(255,255,255,0.1)" stroke-width="6"/>
        <circle cx="{size//2}" cy="{size//2}" r="{r}" fill="none" stroke="{color}" stroke-width="6"
          stroke-dasharray="{circ:.1f}" stroke-dashoffset="{off:.1f}" stroke-linecap="round"
          transform="rotate(-90 {size//2} {size//2})"/>
        <text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle"
          fill="#fff" font-size="{fs}" font-weight="600" font-family="DM Sans">{score}%</text>
      </svg>
      <span style="font-size:11px;color:rgba(255,255,255,0.55);font-weight:600;text-align:center;font-family:'DM Sans',sans-serif;">{label}</span>
    </div>"""

def bar(label, value, color="#e50914"):
    return f"""<div style="margin-bottom:14px;">
      <div style="display:flex;justify-content:space-between;margin-bottom:6px;">
        <span style="font-size:13px;color:rgba(255,255,255,0.65);font-family:'DM Sans',sans-serif;">{label}</span>
        <span style="font-size:13px;font-weight:700;color:{color};font-family:'DM Sans',sans-serif;">{value}%</span>
      </div>
      <div style="background:rgba(255,255,255,0.1);border-radius:4px;height:6px;overflow:hidden;">
        <div style="width:{value}%;height:100%;background:{color};border-radius:4px;"></div>
      </div></div>"""

def card(content, extra="", border="rgba(255,255,255,0.08)"):
    return f'<div style="background:rgba(20,20,20,0.85);border:1px solid {border};border-radius:8px;backdrop-filter:blur(12px);padding:28px;{extra}">{content}</div>'

def tag(text, color="#e50914", bg="rgba(229,9,20,0.12)", border="rgba(229,9,20,0.3)"):
    return f'<span style="background:{bg};border:1px solid {border};color:{color};padding:4px 12px;border-radius:20px;font-size:11px;font-weight:700;font-family:\'DM Sans\',sans-serif;display:inline-block;margin:3px;">{text}</span>'

def stitle(text, sub=""):
    s = f'<p style="color:rgba(255,255,255,0.45);font-size:15px;margin:6px 0 0;font-family:\'DM Sans\',sans-serif;">{sub}</p>' if sub else ""
    return f'<div style="padding:32px 48px 0;"><h1 style="font-family:\'Bebas Neue\',sans-serif;font-size:44px;letter-spacing:2px;color:#fff;margin:0;">{text}</h1>{s}</div>'

def navbar(page, name):
    pages = ["Dashboard","New Interview","Community","Plans","Human Interview"]
    links = []
    for p in pages:
        a = "color:#fff;font-weight:700;border-bottom:2px solid #e50914;padding-bottom:2px;" if page==p else "color:rgba(255,255,255,0.55);"
        links.append(f'<a href="?nav={p.replace(" ","_")}" style="text-decoration:none;font-size:14px;font-family:\'DM Sans\',sans-serif;{a}padding:4px 0;margin:0 12px;transition:color 0.2s;">{p}</a>')
    links.append('<a href="?nav=Logout" style="text-decoration:none;font-size:14px;font-family:\'DM Sans\',sans-serif;color:rgba(255,100,100,0.8);padding:4px 0;margin:0 12px;font-weight:600;">Sign Out</a>')
    initials = name[0].upper() if name else "U"
    return f"""<div style="background:rgba(20,20,20,0.98);border-bottom:1px solid rgba(255,255,255,0.07);
        padding:0 48px;display:flex;align-items:center;height:64px;position:sticky;top:0;z-index:999;">
      <div style="display:flex;align-items:center;gap:10px;margin-right:32px;flex-shrink:0;">
        <div style="width:36px;height:36px;background:#e50914;border-radius:4px;display:flex;align-items:center;
            justify-content:center;font-family:'Bebas Neue',sans-serif;font-size:22px;color:#fff;line-height:1;">IX</div>
        <span style="font-family:'Bebas Neue',sans-serif;font-size:26px;letter-spacing:2px;color:#fff;">InterviewX AI</span>
      </div>
      <div style="display:flex;align-items:center;gap:0;flex:1;">{"".join(links)}</div>
      <div style="display:flex;align-items:center;gap:12px;">
        <div style="width:8px;height:8px;border-radius:50%;background:#e50914;animation:pulse 2s infinite;"></div>
        <div style="width:36px;height:36px;border-radius:50%;background:#e50914;display:flex;align-items:center;
            justify-content:center;font-weight:700;font-size:15px;color:#fff;">{initials}</div>
      </div></div>"""

# ─── DATA ─────────────────────────────────────────────────────────────────────
AQ = {
    "Technical": [
        "Walk me through how you'd design a URL shortener at scale. What are the key components you'd consider?",
        "Explain the difference between REST and GraphQL. When would you prefer one over the other?",
        "What is the CAP theorem and how does it influence your architectural decisions?",
        "How would you approach optimizing a database query that's taking 10+ seconds?",
        "Explain how you'd implement rate limiting in a distributed API system.",
        "What's the difference between horizontal and vertical scaling? Give me a real scenario where each applies.",
        "Walk me through the SOLID principles — can you give me a concrete violation you've seen or fixed?",
        "How do microservices communicate? What failure patterns have you encountered?",
        "Explain event-driven architecture. When does it shine and when does it cause problems?",
        "How would you implement a distributed cache? What eviction strategies would you support?",
    ],
    "HR": [
        "Tell me about yourself — walk me through your journey and what brings you here.",
        "Describe a time you faced a significant challenge at work. What did you do and what was the outcome?",
        "Where do you see yourself professionally in the next five years?",
        "Tell me about a conflict you had with a colleague or manager. How did you handle it?",
        "What's your single biggest professional achievement and why does it stand out to you?",
        "How do you prioritise when you have multiple competing deadlines?",
        "Describe your ideal work environment and management style.",
        "What motivates you most in your day-to-day work?",
        "Tell me about a time you failed. What did you learn?",
        "Why are you leaving your current role, and what specifically drew you to us?",
    ],
    "System Design": [
        "Design a notification system for 50 million users. Walk me through your approach end-to-end.",
        "How would you architect the backend for a ride-sharing platform like Ola? What are the critical services?",
        "Design a real-time collaborative document editor. How do you handle conflicts and sync?",
        "Design a global leaderboard that handles millions of score updates per second.",
        "How would you build a video streaming platform? Focus on upload, storage, and delivery.",
        "Design a payment processing system with guaranteed consistency. What are your trade-offs?",
        "Walk me through designing an e-commerce search system — relevance, speed, and scale.",
        "Design a content delivery network from scratch. What are the caching layers you'd use?",
    ],
    "Behavioural": [
        "Tell me about a time you led a project under pressure. How did you keep the team aligned?",
        "Describe a situation where you had to influence someone without authority.",
        "Give me an example of when you disagreed with a business decision. What did you do?",
        "Tell me about a time you took initiative that went beyond your job description.",
        "Describe a situation where you had to learn something completely new very quickly.",
        "Tell me about a time you made a mistake that impacted the team. How did you recover?",
    ],
    "Coding": [
        "Given an array of integers, find the two numbers that sum to a target. Walk me through your approach and optimise for time complexity.",
        "Implement a LRU cache with O(1) get and put operations. Walk me through your design.",
        "Given a binary tree, return the level-order traversal as a list of lists.",
        "Implement a function to detect a cycle in a linked list. Can you do it without extra space?",
        "Write a function to merge K sorted arrays. What's the time complexity of your solution?",
    ],
}

AF = [
    "Interesting — can you give me a concrete example from your actual experience?",
    "Good thinking. How would you handle this if the load was 10x higher?",
    "I see your point. What trade-offs did you consciously make with that approach?",
    "Let's dig deeper — what would you change if you were starting from scratch today?",
    "Nice. How did stakeholders or the team respond to that?",
    "That's solid. What edge cases does your solution not cover yet?",
    "Good answer. How does this hold up in a failure scenario?",
]

TIPS = [
    "Maintain eye contact with the camera lens, not the screen.",
    "Slow down — measured pacing signals confidence.",
    "Use STAR: Situation, Task, Action, Result for behavioural questions.",
    "Pause briefly before answering — it shows you think before you speak.",
    "Avoid filler words like 'umm', 'basically', and 'you know'.",
    "Sit upright — good posture directly affects how you come across on video.",
    "Smile occasionally — warmth matters as much as technical ability.",
    "Summarise your answer at the end to leave a strong final impression.",
]

OBSERVATIONS = [
    "✅ Eye contact: Strong — maintain it",
    "⚠️ Slight head tilt — straighten up",
    "✅ Voice pace: Clear and measured",
    "✅ Facial expression: Confident",
    "⚠️ Filler word detected: 'basically'",
    "✅ Posture: Upright and composed",
    "⚠️ Eyes drifting — bring focus back",
    "✅ Smile signal: Great warmth",
    "✅ Hand gestures: Natural",
    "⚠️ Speaking too fast — slow down",
    "✅ Engagement level: High",
    "✅ Voice clarity: Excellent",
    "✅ Blink rate: Normal — relaxed",
    "⚠️ Shoulders tensing — breathe",
    "✅ Jaw relaxed — good composure",
]

TRANSCRIPTS = [
    "I would approach this by first understanding the scale requirements and constraints before jumping into a design...",
    "In my experience, we faced a very similar challenge — the solution we landed on was a combination of caching and async processing...",
    "The key trade-offs here are between consistency and availability — depending on the use case I'd lean towards eventual consistency...",
    "Starting with a monolithic approach and gradually decomposing into services is often the most pragmatic path forward...",
    "For the caching layer I'd consider Redis with an LRU eviction policy, and a TTL of around 5 minutes for most reads...",
    "Using the STAR framework — the situation was that our team had a critical launch with only two weeks of runway...",
    "Separation of concerns is the most important principle here — each service should own exactly one piece of domain logic...",
    "Implementing a Kafka-based message queue gives us durability, replay, and natural backpressure handling...",
]

INTERVIEWERS = [
    {"name":"Arjun Mehta","role":"ex-Google SWE L6","exp":"12 yrs","rating":4.9,"price":"₹1,499","avatar":"AM","specialty":"System Design, DSA, FAANG Prep","available":["Today 6:00 PM","Today 8:00 PM","Tomorrow 10:00 AM"],"tag":"FAANG","color":"#e50914"},
    {"name":"Priya Sharma","role":"ex-Microsoft PM","exp":"9 yrs","rating":4.8,"price":"₹1,299","avatar":"PS","specialty":"Product Management, HR, Leadership","available":["Today 8:00 PM","Saturday 11:00 AM"],"tag":"Product","color":"#7c3aed"},
    {"name":"Rahul Verma","role":"ServiceNow Architect","exp":"11 yrs","rating":4.7,"price":"₹999","avatar":"RV","specialty":"ServiceNow, ITSM, Cloud Architecture","available":["Tomorrow 9:00 AM","Tomorrow 4:00 PM"],"tag":"Enterprise","color":"#0ea5e9"},
    {"name":"Sneha Patel","role":"ex-Amazon SDE II","exp":"7 yrs","rating":4.9,"price":"₹1,199","avatar":"SP","specialty":"Java, Spring Boot, Backend, DSA","available":["Today 7:00 PM","Sunday 11:00 AM"],"tag":"FAANG","color":"#e50914"},
    {"name":"Vikram Nair","role":"AI/ML Lead — Flipkart","exp":"8 yrs","rating":4.8,"price":"₹1,399","avatar":"VN","specialty":"Machine Learning, Python, Data Engineering","available":["Saturday 4:00 PM","Sunday 3:00 PM"],"tag":"AI/ML","color":"#10b981"},
    {"name":"Ananya Roy","role":"Telecom Domain Expert","exp":"14 yrs","rating":4.6,"price":"₹899","avatar":"AR","specialty":"5G, BSS/OSS, Network Architecture","available":["Tomorrow 3:00 PM","Saturday 10:00 AM"],"tag":"Telecom","color":"#f59e0b"},
]

PLANS = [
    {"name":"Free Trial","price":"₹0","n":1,"tag":"","color":"#6d6d6e","features":["1 AI Interview (15 min)","Basic overall feedback","Standard voice","Gemini Flash AI"]},
    {"name":"Single Interview","price":"₹129","n":1,"tag":"","color":"#6d6d6e","features":["1 Full 30-min interview","Detailed feedback report","Camera analysis","GPT-4o-mini AI"]},
    {"name":"Starter","price":"₹349","n":5,"tag":"Popular","color":"#e50914","features":["5 AI interviews","Full feedback + PDF","Resume-based questions","Priority support"]},
    {"name":"Main Plan","price":"₹899","n":10,"tag":"Best Value","color":"#e50914","features":["10 AI interviews","HD Azure Neural voice","FAANG-style questions","Video analytics","PDF portfolio"]},
    {"name":"Premium","price":"₹2,499","n":25,"tag":"Pro","color":"#ffd700","features":["25 AI interviews","All interview types","Salary & FAANG estimation","AI coaching mode","Community access","Full analytics"]},
]

POSTS = [
    {"user":"anon_dev_2847","time":"2 min ago","text":"Just cleared Google L4! The system design round was intense — they asked distributed caching twice. Practice that hard.","likes":84,"tag":"Success Story"},
    {"user":"prep_warrior","time":"9 min ago","text":"InterviewX caught that I was saying 'basically' every 3 sentences 😅 Fixed it in 2 sessions. Cleared Amazon SDE last week.","likes":132,"tag":"Tip"},
    {"user":"ms_aspirant","time":"18 min ago","text":"Microsoft values culture-add more than pure LC. The behavioural prep here is genuinely spot on. Don't skip it.","likes":67,"tag":"Insight"},
    {"user":"tn_developer","time":"31 min ago","text":"ServiceNow CAD exam prep module is 🔥 — cleared it this morning. Mock with Vikram was better than anything on YouTube.","likes":91,"tag":"Success Story"},
    {"user":"fresher_2025","time":"1 hr ago","text":"As a fresher this is gold. The AI tells you exactly what you're doing wrong in real time. No interviewer gives this level of detail.","likes":45,"tag":"Review"},
    {"user":"data_eng_dk","time":"2 hr ago","text":"They asked about Kafka partitioning strategies and backpressure. Both came up in InterviewX's Data Engineering track. Not a coincidence.","likes":78,"tag":"Tip"},
]

TRENDING = [
    "System Design for 10M users 🔥","ServiceNow CAD Exam Prep","FAANG DSA — Two Pointers",
    "Behavioural STAR Method Guide","AI/ML Interview Questions 2025","Python Data Engineering",
    "Cloud Architecture Patterns","Java Spring Boot Microservices","Kafka & Event Streaming",
    "LLM Fine-tuning Interview Qs","Telecom 5G Architecture","Product Sense Frameworks",
]

STRENGTHS = [
    "Structured thinking with clear problem decomposition",
    "Confident delivery with minimal filler words",
    "Effective use of real-world examples to support your points",
    "Maintained strong eye contact throughout the session",
    "Good active listening — picked up on follow-up cues",
    "Logical flow from problem → approach → solution",
]

IMPROVE = [
    "Elaborate further on scalability trade-offs when designing systems",
    "Use the STAR method more consistently in behavioural answers",
    "Slightly rushed pacing under pressure — slow down on complex concepts",
    "Quantify your impact more: numbers make achievements memorable",
    "Ask clarifying questions before jumping into system design",
    "Mention alternative approaches before settling on your choice",
]

# ─── SESSION STATE ─────────────────────────────────────────────────────────────
def init_state():
    D = {
        "screen":"splash","user":None,"current_page":"Dashboard",
        "interview_config":{},"interview_active":False,"interview_phase":"intro",
        "chat_log":[],"question_idx":0,"interview_start":None,
        "cam_stats":{"eye":84,"confidence":77,"posture":"Good","stress":"Low","attention":91},
        "current_question":"","ai_tip_idx":0,"scores":{},"feedback_data":{},
        "otp_sent":False,"otp_code":"","booked_interviewer":None,"liked_posts":{},
        "obs_idx":0,
    }
    for k,v in D.items():
        if k not in st.session_state: st.session_state[k] = v

# ─── SCREENS ──────────────────────────────────────────────────────────────────
def splash_screen():
    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown("""
    <div style="min-height:60vh;width:100%;background:radial-gradient(ellipse at center,rgba(229,9,20,0.13) 0%,transparent 62%),#141414;
        display:flex;flex-direction:column;align-items:center;justify-content:center;padding:60px 20px;box-sizing:border-box;">
      <div style="text-align:center;animation:fadeIn 0.9s ease forwards;">
        <div style="display:flex;align-items:center;justify-content:center;gap:20px;margin-bottom:28px;">
          <div style="width:88px;height:88px;background:#e50914;border-radius:16px;display:flex;align-items:center;
              justify-content:center;font-family:'Bebas Neue',sans-serif;font-size:56px;color:#fff;line-height:1;
              box-shadow:0 0 60px rgba(229,9,20,0.5);">IX</div>
          <span style="font-family:'Bebas Neue',sans-serif;font-size:88px;letter-spacing:5px;color:#fff;line-height:1;">InterviewX AI</span>
        </div>
        <p style="font-size:20px;color:rgba(255,255,255,0.5);letter-spacing:5px;font-weight:300;text-transform:uppercase;margin-bottom:28px;">AI Based Interview Intelligence</p>
        <p style="max-width:820px;margin:0 auto 48px;font-size:18px;line-height:1.9;color:rgba(255,255,255,0.7);font-family:'DM Sans',sans-serif;">
          AI-Based mock interviews with live voice interaction, real-time camera analysis,
          instant technical feedback, human expert sessions, and personalised improvement guidance — all in one platform.
        </p>
        <div style="display:flex;gap:8px;justify-content:center;margin-bottom:8px;">
          <div style="width:10px;height:10px;border-radius:50%;background:#e50914;animation:pulse 1s 0s infinite;"></div>
          <div style="width:10px;height:10px;border-radius:50%;background:#e50914;animation:pulse 1s 0.2s infinite;"></div>
          <div style="width:10px;height:10px;border-radius:50%;background:#e50914;animation:pulse 1s 0.4s infinite;"></div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("<div style='margin-top:20px'></div>", unsafe_allow_html=True)

    left, center, right = st.columns([3, 1.2, 3])

    with center:
        if st.button(
            "Enter InterviewX →",
            key="splash_enter",
            use_container_width=True
        ):
            st.session_state.screen = "select"
            st.rerun()

def selection_screen():
    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown("""
    <div style="padding:24px 48px 0;">
      <div style="display:flex;align-items:center;gap:10px;">
        <div style="width:36px;height:36px;background:#e50914;border-radius:4px;display:flex;align-items:center;
            justify-content:center;font-family:'Bebas Neue',sans-serif;font-size:22px;color:#fff;line-height:1;">IX</div>
        <span style="font-family:'Bebas Neue',sans-serif;font-size:26px;letter-spacing:2px;color:#fff;">InterviewX AI</span>
      </div>
    </div>
    <div style="text-align:center;padding:36px 24px 40px;">
      <h1 style="font-family:'Bebas Neue',sans-serif;font-size:52px;letter-spacing:3px;margin-bottom:10px;color:#fff;">Ready to Ace Your Interview?</h1>
      <p style="color:rgba(255,255,255,0.5);font-size:17px;font-family:'DM Sans',sans-serif;">Choose how you want to prepare today</p>
    </div>
    <div style="display:flex;justify-content:center;gap:40px;padding:0 24px 40px;flex-wrap:wrap;">
      <div style="width:340px;background:rgba(20,20,20,0.9);border:1px solid rgba(229,9,20,0.35);border-radius:10px;padding:44px 36px;text-align:center;">
        <div style="font-size:64px;margin-bottom:20px;">🤖</div>
        <h2 style="font-family:'Bebas Neue',sans-serif;font-size:34px;letter-spacing:2px;color:#e50914;margin-bottom:12px;">AI Process</h2>
        <p style="color:rgba(255,255,255,0.6);font-size:15px;line-height:1.8;margin-bottom:28px;font-family:'DM Sans',sans-serif;">
          Practice mock interviews with our AI agent. Live voice, camera analysis, instant feedback — available 24/7. Subscription-based.
        </p>
        <div style="display:flex;flex-wrap:wrap;gap:6px;justify-content:center;">
          <span style="background:rgba(229,9,20,0.12);border:1px solid rgba(229,9,20,0.3);color:#e50914;padding:5px 12px;border-radius:20px;font-size:11px;font-weight:700;font-family:'DM Sans',sans-serif;">24/7 Available</span>
          <span style="background:rgba(229,9,20,0.12);border:1px solid rgba(229,9,20,0.3);color:#e50914;padding:5px 12px;border-radius:20px;font-size:11px;font-weight:700;font-family:'DM Sans',sans-serif;">Instant Feedback</span>
          <span style="background:rgba(229,9,20,0.12);border:1px solid rgba(229,9,20,0.3);color:#e50914;padding:5px 12px;border-radius:20px;font-size:11px;font-weight:700;font-family:'DM Sans',sans-serif;">Camera Analysis</span>
          <span style="background:rgba(229,9,20,0.12);border:1px solid rgba(229,9,20,0.3);color:#e50914;padding:5px 12px;border-radius:20px;font-size:11px;font-weight:700;font-family:'DM Sans',sans-serif;">Subscription Plans</span>
        </div>
      </div>
      <div style="width:340px;background:rgba(20,20,20,0.9);border:1px solid rgba(255,215,0,0.25);border-radius:10px;padding:44px 36px;text-align:center;">
        <div style="font-size:64px;margin-bottom:20px;">👩‍💼👨‍💼</div>
        <h2 style="font-family:'Bebas Neue',sans-serif;font-size:34px;letter-spacing:2px;color:#ffd700;margin-bottom:12px;">Human Interview</h2>
        <p style="color:rgba(255,255,255,0.6);font-size:15px;line-height:1.8;margin-bottom:28px;font-family:'DM Sans',sans-serif;">
          Book real industry experts — ex-FAANG engineers, domain specialists, HR leaders. Pay per session. No subscription needed.
        </p>
        <div style="display:flex;flex-wrap:wrap;gap:6px;justify-content:center;">
          <span style="background:rgba(255,215,0,0.1);border:1px solid rgba(255,215,0,0.3);color:#ffd700;padding:5px 12px;border-radius:20px;font-size:11px;font-weight:700;font-family:'DM Sans',sans-serif;">Real Experts</span>
          <span style="background:rgba(255,215,0,0.1);border:1px solid rgba(255,215,0,0.3);color:#ffd700;padding:5px 12px;border-radius:20px;font-size:11px;font-weight:700;font-family:'DM Sans',sans-serif;">No Subscription</span>
          <span style="background:rgba(255,215,0,0.1);border:1px solid rgba(255,215,0,0.3);color:#ffd700;padding:5px 12px;border-radius:20px;font-size:11px;font-weight:700;font-family:'DM Sans',sans-serif;">Pay Per Session</span>
          <span style="background:rgba(255,215,0,0.1);border:1px solid rgba(255,215,0,0.3);color:#ffd700;padding:5px 12px;border-radius:20px;font-size:11px;font-weight:700;font-family:'DM Sans',sans-serif;">Industry Specific</span>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)
    c1,c2,c3,c4 = st.columns([1.2,1.4,1.4,1.2])

    with c2:
        if st.button(
            "🤖  Start AI Interview",
            key="sel_ai",
            use_container_width=True
        ):
            st.session_state.interview_mode = "ai"
            st.session_state.screen = "login"
            st.rerun()

    with c3:
        if st.button(
            "👩‍💼👨‍💼  Book Human Expert",
            key="sel_human",
            use_container_width=True
        ):
            st.session_state.interview_mode = "human"
            st.session_state.screen = "login"
            st.rerun()

def login_screen():
    st.markdown(CSS, unsafe_allow_html=True)
    # Full page centered - no excess space
    st.markdown("""
    <div style="position:fixed;inset:0;background:linear-gradient(135deg,#0a0a0a 0%,#1a0505 50%,#0a0a0a 100%);z-index:0;"></div>
    <div style="position:fixed;top:20px;left:48px;display:flex;align-items:center;gap:10px;z-index:10;">
      <div style="width:32px;height:32px;background:#e50914;border-radius:4px;display:flex;align-items:center;
          justify-content:center;font-family:'Bebas Neue',sans-serif;font-size:20px;color:#fff;line-height:1;">IX</div>
      <span style="font-family:'Bebas Neue',sans-serif;font-size:22px;letter-spacing:2px;color:#fff;">InterviewX AI</span>
    </div>
    """, unsafe_allow_html=True)

    # Push card to vertical center using spacing
    st.markdown("<div style='height:80px;'></div>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 1.55, 1])
    with col:
        st.markdown("""
        <div style="background:rgba(18,18,18,0.97);border:1px solid rgba(255,255,255,0.1);border-radius:8px;padding:36px 36px 28px;">
          <h2 style="font-size:28px;font-weight:700;margin-bottom:5px;color:#fff;font-family:'DM Sans',sans-serif;">Sign In to InterviewX</h2>
          <div style="display:flex;gap:10px;margin-bottom:16px;">
            <div style="flex:1;background:#fff;color:#333;border-radius:4px;padding:12px;text-align:center;font-weight:700;font-size:13px;font-family:'DM Sans',sans-serif;cursor:pointer;">G &nbsp; Continue with Google</div>
            <div style="flex:1;background:#000;color:#fff;border:1px solid rgba(255,255,255,0.2);border-radius:4px;padding:12px;text-align:center;font-weight:700;font-size:13px;font-family:'DM Sans',sans-serif;cursor:pointer;"> &nbsp; Continue with Apple</div>
          </div>
          <div style="text-align:center;color:rgba(255,255,255,0.22);font-size:12px;margin-bottom:16px;font-family:'DM Sans',sans-serif;">— or sign in with email —</div>
        </div>
        """, unsafe_allow_html=True)

        tab_l, tab_r = st.tabs(["Sign In", "Create Account"])
        with tab_l:
            email = st.text_input("Email Address", key="login_email", placeholder="you@example.com")
            password = st.text_input("Password", type="password", key="login_pass", placeholder="Your password")
            if not st.session_state.otp_sent:
                if st.button("Send OTP →", key="send_otp"):
                    if email and password:
                        st.session_state.otp_code = "123456"; st.session_state.otp_sent = True; st.rerun()
                    else: st.error("Please enter email and password.")
            else:
                st.markdown('<p style="color:rgba(255,255,255,0.5);font-size:13px;margin-bottom:6px;font-family:\'DM Sans\',sans-serif;">OTP sent &nbsp;•&nbsp; Demo code: <strong style="color:#e50914;">123456</strong></p>', unsafe_allow_html=True)
                otp = st.text_input("Enter OTP", key="otp_val", placeholder="6-digit OTP")
                if st.button("Verify & Sign In", key="verify_login"):
                    if otp == st.session_state.otp_code:
                        u = login_user(email, password)
                        if u:
                            st.session_state.user = {"id":u[0],"email":u[1],"name":u[2],"plan":u[5],"interviews_remaining":u[6],"interviews_done":u[7]}
                            st.session_state.screen = "app"; st.session_state.otp_sent = False; st.rerun()
                        else: st.error("Invalid credentials.")
                    else: st.error("Incorrect OTP.")
            if st.button("← Back to Home", key="login_back"):
                st.session_state.screen = "select"; st.session_state.otp_sent = False; st.rerun()

        with tab_r:
            rn = st.text_input("Full Name", key="reg_name", placeholder="Your full name")
            re = st.text_input("Email Address", key="reg_email", placeholder="you@example.com")
            rp = st.text_input("Password", type="password", key="reg_pass", placeholder="Create a strong password")
            if st.button("Create Account →", key="do_register"):
                if rn and re and rp:
                    ok, msg = register_user(re, rn, rp)
                    if ok:
                        u = login_user(re, rp)
                        if u:
                            st.session_state.user = {"id":u[0],"email":u[1],"name":u[2],"plan":u[5],"interviews_remaining":u[6],"interviews_done":u[7]}
                            st.session_state.screen = "app"; st.rerun()
                    else: st.error(msg)
                else: st.error("Please fill all fields.")
            if st.button("← Back to Home", key="reg_back"):
                st.session_state.screen = "select"; st.rerun()

        st.markdown('<p style="text-align:center;font-size:12px;color:rgba(255,255,255,0.2);margin-top:10px;font-family:\'DM Sans\',sans-serif;">First interview is free — no credit card required</p>', unsafe_allow_html=True)

# ─── PAGES ────────────────────────────────────────────────────────────────────
def page_dashboard():
    u = st.session_state.user
    history = get_user_interviews(u["id"])
    done = len(history)
    avg = int(sum(r[6] for r in history)/max(1,done)) if history else 0

    st.markdown(f"""
    <div style="padding:32px 48px 0;">
      <div style="background:linear-gradient(135deg,rgba(229,9,20,0.09),rgba(20,20,20,0.97));border:1px solid rgba(229,9,20,0.22);border-radius:10px;padding:36px 44px;margin-bottom:24px;">
        <p style="color:#e50914;font-size:12px;font-weight:700;letter-spacing:3px;text-transform:uppercase;margin-bottom:8px;font-family:'DM Sans',sans-serif;">Welcome Back, {u['name'].title()}</p>
        <h1 style="font-family:'Bebas Neue',sans-serif;font-size:46px;letter-spacing:2px;margin-bottom:12px;color:#fff;">Your Interview Dashboard</h1>
        <p style="color:rgba(255,255,255,0.55);font-size:16px;margin-bottom:0;font-family:'DM Sans',sans-serif;">
          {done} mock interview{'s' if done!=1 else ''} completed &nbsp;•&nbsp;
          Avg score: <strong style="color:#e50914;">{avg if done else '--'}{'%' if done else ''}</strong> &nbsp;•&nbsp;
          Plan: <strong style="color:#ffd700;">{u.get('plan','free').title()}</strong>
        </p>
      </div>
    </div>
    """, unsafe_allow_html=True)

    cols = st.columns(4)
    for col,(lbl,val,delta) in zip(cols,[("Interviews Done",done,"+1 this week"),("Avg Score",f"{avg}%" if done else "—","Keep going!"),("Interviews Left",u.get("interviews_remaining",1),"Upgrade for more"),("Plan",u.get("plan","free").title(),"Active")]):
        with col: st.metric(lbl,val,delta)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    items = " &nbsp;&nbsp;•&nbsp;&nbsp; ".join([f"🔥 {t}" for t in TRENDING])
    st.markdown(f"""
    <div style="background:#e50914;border-radius:4px;padding:11px 0;margin:0 48px 20px;overflow:hidden;">
      <div style="white-space:nowrap;animation:ticker 30s linear infinite;display:inline-block;">
        <span style="font-size:13px;font-weight:600;color:#fff;padding:0 32px;font-family:'DM Sans',sans-serif;">{items} &nbsp;&nbsp;•&nbsp;&nbsp; {items}</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    cl, cr = st.columns(2)
    with cl:
        rings_h = "".join([ring(78,"AI Readiness","#e50914",88),ring(71,"Confidence","#ffd700",88),ring(83,"Eye Contact","#00d4aa",88),ring(67,"Communication","#7c3aed",88)])
        st.markdown(card(f'<p style="font-size:12px;font-weight:700;letter-spacing:2px;color:rgba(255,255,255,0.4);text-transform:uppercase;margin-bottom:18px;font-family:\'DM Sans\',sans-serif;">Performance Overview</p><div style="display:flex;gap:16px;justify-content:space-around;flex-wrap:wrap;">{rings_h}</div>',"margin:0 48px 18px;"), unsafe_allow_html=True)
        bars_h = bar("Technical Accuracy",74,"#e50914")+bar("Communication",67,"#7c3aed")+bar("Confidence",71,"#ffd700")+bar("Eye Contact",83,"#00d4aa")+bar("Posture Quality",79,"#e50914")+bar("Filler Word Control",62,"#f97316")
        st.markdown(card(f'<p style="font-size:12px;font-weight:700;letter-spacing:2px;color:rgba(255,255,255,0.4);text-transform:uppercase;margin-bottom:18px;font-family:\'DM Sans\',sans-serif;">Detailed Breakdown</p>{bars_h}',"margin:0 48px 18px;"), unsafe_allow_html=True)
    with cr:
        if history:
            rows = ""
            for h in history[:5]:
                sc=h[6]; cc="#00d4aa" if sc>=75 else "#ffd700" if sc>=60 else "#e50914"; d=h[11][:10] if h[11] else "—"
                rows += f'<div style="display:flex;justify-content:space-between;align-items:center;padding:12px 0;border-bottom:1px solid rgba(255,255,255,0.06);"><div><p style="font-size:14px;font-weight:600;color:#fff;margin-bottom:2px;font-family:\'DM Sans\',sans-serif;">{h[2].title()} — {h[3]}</p><p style="font-size:12px;color:rgba(255,255,255,0.35);font-family:\'DM Sans\',sans-serif;">{d} &nbsp;•&nbsp; {h[4].title()} &nbsp;•&nbsp; {h[5]} min</p></div><div style="text-align:right;"><span style="font-family:\'Bebas Neue\',sans-serif;font-size:30px;color:{cc};">{sc}</span><span style="font-size:12px;color:rgba(255,255,255,0.3);font-family:\'DM Sans\',sans-serif;">/100</span></div></div>'
            st.markdown(card(f'<p style="font-size:12px;font-weight:700;letter-spacing:2px;color:rgba(255,255,255,0.4);text-transform:uppercase;margin-bottom:4px;font-family:\'DM Sans\',sans-serif;">Interview History</p>{rows}',"margin:0 0 18px 0;"), unsafe_allow_html=True)
        else:
            st.markdown(card('<p style="font-size:12px;font-weight:700;letter-spacing:2px;color:rgba(255,255,255,0.4);text-transform:uppercase;margin-bottom:14px;font-family:\'DM Sans\',sans-serif;">Interview History</p><div style="text-align:center;padding:28px 0;"><p style="font-size:36px;margin-bottom:10px;">🎯</p><p style="color:rgba(255,255,255,0.4);font-size:15px;font-family:\'DM Sans\',sans-serif;">No interviews yet — start your first one!</p></div>',"margin:0 0 18px 0;"), unsafe_allow_html=True)

        plan=u.get("plan","free"); rem=u.get("interviews_remaining",1)
        tm={"free":1,"single":1,"starter":5,"main":10,"premium":25}; tot=tm.get(plan,1)
        used=max(0,tot-rem); pct=int((used/tot)*100) if tot else 100
        st.markdown(card(f'<span style="background:#e50914;color:#fff;padding:4px 14px;border-radius:20px;font-size:11px;font-weight:700;font-family:\'DM Sans\',sans-serif;">{plan.upper()} PLAN</span><p style="font-size:18px;font-weight:700;color:#fff;margin:10px 0 2px;font-family:\'DM Sans\',sans-serif;">{rem} interview{"s" if rem!=1 else ""} remaining</p><div style="background:rgba(255,255,255,0.1);border-radius:4px;height:8px;overflow:hidden;margin:10px 0 6px;"><div style="width:{pct}%;height:100%;background:#e50914;border-radius:4px;"></div></div><p style="font-size:12px;color:rgba(255,255,255,0.35);font-family:\'DM Sans\',sans-serif;">{used} of {tot} used</p>',"margin:0 0 18px 0;","rgba(229,9,20,0.2)"), unsafe_allow_html=True)
        if st.button("⚡ Upgrade Plan", key="dash_upgrade"):
            st.session_state.current_page = "Plans"; st.rerun()

    tags_h = "".join([tag(t) for t in TRENDING])
    st.markdown(card(f'<p style="font-size:12px;font-weight:700;letter-spacing:2px;color:rgba(255,255,255,0.4);text-transform:uppercase;margin-bottom:14px;font-family:\'DM Sans\',sans-serif;">🔥 Trending This Week</p><div style="display:flex;flex-wrap:wrap;gap:4px;">{tags_h}</div>',"margin:0 48px 40px;"), unsafe_allow_html=True)

def page_setup():
    st.markdown(stitle("Configure Your Interview","Customise every detail of your mock session"), unsafe_allow_html=True)
    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)
    st.markdown("<div style='padding:0 48px;'>", unsafe_allow_html=True)
    c1,c2,c3 = st.columns(3)
    with c1:
        level = st.selectbox("Experience Level",["Fresher (0 yrs)","1–3 Years","3–6 Years","6–10 Years","10+ Years"])
        itype = st.selectbox("Interview Type",list(AQ.keys()))
        domain = st.selectbox("Domain / Stack",["General","Java","Python","Cloud / AWS","ServiceNow","AI & ML","Data Engineering","React / Frontend","Telecom / 5G","DevOps","QA / SDET"])
    with c2:
        role = st.selectbox("Target Role",["Software Engineer","Senior SWE","Staff Engineer","Product Manager","Data Engineer","ML Engineer","DevOps Engineer","QA Lead","Business Analyst","Solution Architect"])
        diff = st.selectbox("Difficulty",["Easy","Medium","Hard","FAANG Level"])
        pers = st.selectbox("AI Personality",["Friendly & Encouraging","Strict & Rigorous","FAANG Interview Style","Startup Culture Fit","HR & Culture Focus"])
    with c3:
        dur = st.selectbox("Session Duration",["15 minutes","30 minutes","45 minutes","60 minutes"])
        comp = st.selectbox("Target Company Type",["Any / General","FAANG+","MNC India","Startup","PSU / Government","Consulting","Product Company"])
        cam = st.checkbox("Enable Camera Analysis", value=True)

    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
    st.markdown("""
    <div style="background:rgba(229,9,20,0.07);border:1px solid rgba(229,9,20,0.2);border-radius:8px;padding:18px 20px;margin-bottom:18px;">
      <p style="color:#e50914;font-size:13px;font-weight:700;margin-bottom:5px;font-family:'DM Sans',sans-serif;">🤖 What the AI will do during your session:</p>
      <p style="color:rgba(255,255,255,0.65);font-size:14px;line-height:1.8;font-family:'DM Sans',sans-serif;margin:0;">
        Ask dynamic questions matching your type and domain &nbsp;•&nbsp; Follow up intelligently &nbsp;•&nbsp;
        Observe your camera for eye contact, posture and expressions &nbsp;•&nbsp; Detect filler words and pacing &nbsp;•&nbsp;
        Generate a full feedback report with salary estimation at the end
      </p>
    </div>
    """, unsafe_allow_html=True)
    _,cb,_ = st.columns([1,1,1])
    with cb:
        if st.button("🎯  Begin Interview Session", key="start_iv"):
            dm={"15 minutes":15,"30 minutes":30,"45 minutes":45,"60 minutes":60}
            st.session_state.interview_config={"level":level,"type":itype,"domain":domain,"role":role,"difficulty":diff,"personality":pers,"duration":dm.get(dur,30),"company":comp,"camera":cam}
            st.session_state.interview_active=True; st.session_state.interview_phase="intro"
            st.session_state.chat_log=[]; st.session_state.question_idx=0
            st.session_state.interview_start=time.time(); st.session_state.current_question=""
            st.session_state.obs_idx=0; st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

def page_interview():
    cfg = st.session_state.interview_config
    qs = AQ.get(cfg.get("type","Technical"), AQ["Technical"])
    elapsed = int(time.time()-(st.session_state.interview_start or time.time()))
    mins,secs = elapsed//60, elapsed%60

    cs = st.session_state.cam_stats
    cs["eye"]=max(60,min(98,cs["eye"]+random.uniform(-2,2)))
    cs["confidence"]=max(55,min(95,cs["confidence"]+random.uniform(-1.5,1.5)))
    cs["attention"]=max(70,min(99,cs["attention"]+random.uniform(-2,2)))
    cs["posture"]="Adjust slightly" if random.random()>0.88 else "Good"
    cs["stress"]="Medium" if random.random()>0.82 else "Low"

    if st.session_state.interview_phase=="intro" and not st.session_state.current_question:
        st.session_state.current_question=qs[0]; st.session_state.interview_phase="live"

    obs = OBSERVATIONS[st.session_state.obs_idx % len(OBSERVATIONS)]
    st.session_state.obs_idx=(st.session_state.obs_idx+1)%len(OBSERVATIONS)
    obs_color="#00d4aa" if obs.startswith("✅") else "#ffd700"
    eye_p=int(cs["eye"]); conf_p=int(cs["confidence"]); attn_p=int(cs["attention"])
    s=elapsed%5

    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown(f"""
    <div style="background:rgba(14,14,14,0.99);border-bottom:1px solid rgba(255,255,255,0.07);
        padding:0 24px;display:flex;align-items:center;height:52px;gap:14px;position:sticky;top:0;z-index:999;">
      <div style="display:flex;align-items:center;gap:8px;">
        <div style="width:26px;height:26px;background:#e50914;border-radius:3px;display:flex;align-items:center;
            justify-content:center;font-family:'Bebas Neue',sans-serif;font-size:17px;color:#fff;line-height:1;">IX</div>
        <span style="font-family:'Bebas Neue',sans-serif;font-size:20px;letter-spacing:2px;color:#fff;">InterviewX AI</span>
      </div>
      <div style="flex:1;"></div>
      <span style="background:rgba(229,9,20,0.15);border:1px solid rgba(229,9,20,0.4);color:#e50914;
          padding:4px 14px;border-radius:20px;font-size:12px;font-weight:700;font-family:'DM Sans',sans-serif;
          animation:blink 2s infinite;">● LIVE SESSION</span>
      <span style="font-family:'Bebas Neue',sans-serif;font-size:24px;letter-spacing:2px;
          color:{'#e50914' if mins>=cfg.get('duration',30)-5 else '#fff'};">
        {str(mins).zfill(2)}:{str(secs).zfill(2)}
      </span>
    </div>
    """, unsafe_allow_html=True)

    col_c, col_m = st.columns([1,2.8])

    with col_c:

        camera = st.camera_input("")

        if camera:
            st.success("✅ Camera Active")

        st.markdown("""
        <div style="
            background:rgba(20,20,20,0.92);
            border:1px solid rgba(255,255,255,0.08);
            border-radius:12px;
            padding:16px;
            margin-top:12px;
        ">

        <div style="
            display:flex;
            align-items:center;
            justify-content:space-between;
            margin-bottom:14px;
        ">
            <span style="
                font-size:11px;
                color:#e50914;
                font-weight:700;
                letter-spacing:1px;
            ">
                LIVE CAMERA ANALYSIS
            </span>
        </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(bar("Eye Contact", int(cs["eye"]), "#00ffaa"), unsafe_allow_html=True)
        st.markdown(bar("Confidence", int(cs["confidence"]), "#7c3aed"), unsafe_allow_html=True)
        st.markdown(bar("Attention", int(cs["attention"]), "#e50914"), unsafe_allow_html=True)
        st.markdown("<div style='margin-top:10px'></div>", unsafe_allow_html=True)

        left, center, right = st.columns([1.5, 1.2, 1.5])

        with center:
            if st.button(
                "End Interview",
                key="end_interview",
                use_container_width=True
            ):
                _finish_interview()

    with col_m:
        q = st.session_state.current_question
        phase = st.session_state.interview_phase
        wave_bars="".join([f'<span style="display:inline-block;width:4px;height:20px;background:#e50914;border-radius:2px;margin:0 2px;animation:wave 1s ease-in-out {i*0.1}s infinite;"></span>' for i in range(5)])
        status=f'<div style="display:inline-flex;align-items:center;gap:0;">{wave_bars}</div>' if phase in ["thinking","intro"] else '<span style="background:rgba(0,212,170,0.12);color:#00d4aa;padding:4px 12px;border-radius:20px;font-size:11px;font-weight:700;font-family:\'DM Sans\',sans-serif;">● Listening to your answer</span>'

        st.markdown(f"""
        <div style="padding:12px 12px 0 0;">
        <div style="background:rgba(229,9,20,0.05);border:1px solid rgba(229,9,20,0.15);border-radius:10px;padding:20px 24px;margin-bottom:13px;">
          <div style="display:flex;align-items:center;gap:13px;margin-bottom:12px;">
            <div style="width:44px;height:44px;border-radius:50%;background:linear-gradient(135deg,#e50914,#7c3aed);
                display:flex;align-items:center;justify-content:center;font-size:20px;flex-shrink:0;">🤖</div>
            <div>
              <p style="font-weight:700;font-size:15px;color:#fff;margin-bottom:4px;font-family:'DM Sans',sans-serif;">InterviewX AI Interviewer</p>
              <div>{status}</div>
            </div>
          </div>
          <p style="font-size:16px;line-height:1.75;color:#fff;margin:0;font-family:'DM Sans',sans-serif;">{q if q else "Initialising your interview session..."}</p>
        </div>
        """, unsafe_allow_html=True)

        if st.session_state.chat_log:
            ch=""
            for msg in st.session_state.chat_log[-6:]:
                if msg["role"]=="ai":
                    ch+=f'<div style="display:flex;gap:9px;margin-bottom:11px;align-items:flex-start;"><span style="font-size:15px;flex-shrink:0;">🤖</span><div style="background:rgba(229,9,20,0.07);border:1px solid rgba(229,9,20,0.12);border-radius:8px;padding:11px 15px;font-size:13px;line-height:1.6;color:rgba(255,255,255,0.85);font-family:\'DM Sans\',sans-serif;max-width:88%;">{msg["text"]}</div></div>'
                else:
                    ch+=f'<div style="display:flex;gap:9px;margin-bottom:11px;align-items:flex-start;flex-direction:row-reverse;"><span style="font-size:15px;flex-shrink:0;">👤</span><div style="background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.09);border-radius:8px;padding:11px 15px;font-size:13px;line-height:1.6;color:rgba(255,255,255,0.82);font-family:\'DM Sans\',sans-serif;max-width:88%;">{msg["text"]}</div></div>'
            st.markdown(f'<div style="border:1px solid rgba(255,255,255,0.06);border-radius:8px;padding:14px;margin-bottom:13px;max-height:190px;overflow-y:auto;">{ch}</div>', unsafe_allow_html=True)

        # Voice capture indicator
        st.markdown("""
        <div style="background:rgba(229,9,20,0.06);border:1px solid rgba(229,9,20,0.15);border-radius:8px;padding:13px 17px;margin-bottom:11px;">
          <div style="display:flex;align-items:center;gap:10px;">
            <span style="font-size:20px;">🎙</span>
            <div>
              <p style="font-size:13px;font-weight:600;color:#fff;margin-bottom:2px;font-family:'DM Sans',sans-serif;">Voice Response Active</p>
              <p style="font-size:12px;color:rgba(255,255,255,0.4);margin:0;font-family:'DM Sans',sans-serif;">Speak naturally — AI is observing your voice, expressions and eye contact in real time</p>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # Live transcript simulation
        tr = TRANSCRIPTS[st.session_state.question_idx%len(TRANSCRIPTS)] if st.session_state.chat_log else ""
        if tr:
            words=tr.split(); vc=min(len(words),max(3,(elapsed%14)+4))
            partial=" ".join(words[:vc]); cursor="█" if vc<len(words) else ""
            st.markdown(f"""
            <div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.08);border-radius:8px;
                padding:13px 17px;margin-bottom:11px;min-height:58px;">
              <p style="font-size:11px;color:rgba(255,255,255,0.3);margin-bottom:5px;font-weight:700;
                  letter-spacing:1px;font-family:'DM Sans',sans-serif;">LIVE TRANSCRIPT</p>
              <p style="font-size:14px;color:rgba(255,255,255,0.8);line-height:1.6;margin:0;font-family:'DM Sans',sans-serif;">{partial}<span style="color:#e50914;animation:blink 0.8s infinite;">{cursor}</span></p>
            </div>
            """, unsafe_allow_html=True)

        _,cs1,cs2 = st.columns([1,1.2,1])
        with cs1:
            if st.button("✅  Answer Complete — Next", key=f"submit_{st.session_state.question_idx}"):
                sim=TRANSCRIPTS[st.session_state.question_idx%len(TRANSCRIPTS)]
                _handle_answer(sim,qs); st.rerun()
        with cs2:
            if st.button("Skip →", key=f"skip_{st.session_state.question_idx}"):
                _handle_answer("[Skipped]",qs); st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

def _handle_answer(answer, qs):
    st.session_state.chat_log.append({"role":"ai","text":st.session_state.current_question})
    st.session_state.chat_log.append({"role":"user","text":answer})
    st.session_state.ai_tip_idx+=1
    ni=st.session_state.question_idx+1
    if ni>=len(qs) or ni>=8: _finish_interview(); return
    if random.random()>0.55: nq=random.choice(AF)
    else: nq=qs[ni]; st.session_state.question_idx=ni
    st.session_state.current_question=nq; st.session_state.interview_phase="live"

def _finish_interview():
    cs=st.session_state.cam_stats
    scores={"overall":random.randint(62,92),"confidence":int(cs["confidence"]),"eye":int(cs["eye"]),"comm":random.randint(60,88),"technical":random.randint(58,90)}
    feedback={"strengths":random.sample(STRENGTHS,4),"improvements":random.sample(IMPROVE,3)}
    save_interview(st.session_state.user["id"],st.session_state.interview_config,scores,feedback)
    st.session_state.user["interviews_done"]=st.session_state.user.get("interviews_done",0)+1
    st.session_state.user["interviews_remaining"]=max(0,st.session_state.user.get("interviews_remaining",1)-1)
    st.session_state.scores=scores; st.session_state.feedback_data=feedback
    st.session_state.interview_active=False; st.session_state.current_page="Feedback"; st.rerun()

def page_feedback():
    scores=st.session_state.scores; fb=st.session_state.feedback_data; cfg=st.session_state.interview_config
    if not scores: st.warning("No feedback available. Complete an interview first."); return
    ov=scores.get("overall",75)
    hiring=min(95,int(ov*0.9+random.randint(-5,5))); faang=max(25,int(ov*0.65+random.randint(-8,8)))
    em="🎉" if ov>=80 else "💪" if ov>=65 else "📚"
    msg=("Excellent performance! You're interview-ready. Focus on refining edge cases." if ov>=80 else
         "Good effort with clear room for growth. A few more sessions will make a big difference." if ov>=65 else
         "You have the potential — structured practice over 2 weeks will significantly boost your score.")
    rings="".join([ring(ov,"Overall Score","#e50914",100),ring(hiring,"Hiring Probability","#00d4aa",100),ring(faang,"FAANG Readiness","#ffd700",100),ring(scores.get("eye",80),"Eye Contact","#7c3aed",100),ring(scores.get("confidence",72),"Confidence","#0ea5e9",100)])

    st.markdown(stitle("Interview Feedback",f"{cfg.get('type','Technical')} Round  •  {cfg.get('domain','General')}  •  {cfg.get('difficulty','Medium')} Difficulty"), unsafe_allow_html=True)
    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)
    st.markdown(card(f'<div style="text-align:center;margin-bottom:22px;"><p style="font-size:40px;margin-bottom:8px;">{em}</p><p style="font-size:16px;color:rgba(255,255,255,0.7);font-family:\'DM Sans\',sans-serif;max-width:600px;margin:0 auto;">{msg}</p></div><div style="display:flex;justify-content:center;gap:26px;flex-wrap:wrap;">{rings}</div>',"margin:0 48px 22px;background:linear-gradient(135deg,rgba(229,9,20,0.07),rgba(20,20,20,0.95));","rgba(229,9,20,0.2)"), unsafe_allow_html=True)

    cs1,ci1=st.columns(2)
    with cs1:
        sh="".join([f'<div style="display:flex;gap:12px;margin-bottom:11px;"><span style="color:#00d4aa;font-size:14px;flex-shrink:0;">✓</span><p style="font-size:14px;color:rgba(255,255,255,0.85);line-height:1.65;font-family:\'DM Sans\',sans-serif;margin:0;">{s}</p></div>' for s in fb.get("strengths",[])])
        st.markdown(card(f'<p style="font-size:16px;font-weight:700;color:#00d4aa;margin-bottom:16px;font-family:\'DM Sans\',sans-serif;">✅ Your Strengths</p>{sh}',"margin:0 0 22px 48px;"), unsafe_allow_html=True)
    with ci1:
        ih="".join([f'<div style="display:flex;gap:12px;margin-bottom:11px;"><span style="color:#ffd700;font-size:14px;flex-shrink:0;">→</span><p style="font-size:14px;color:rgba(255,255,255,0.85);line-height:1.65;font-family:\'DM Sans\',sans-serif;margin:0;">{s}</p></div>' for s in fb.get("improvements",[])])
        st.markdown(card(f'<p style="font-size:16px;font-weight:700;color:#ffd700;margin-bottom:16px;font-family:\'DM Sans\',sans-serif;">⚠️ Areas to Improve</p>{ih}',"margin:0 48px 22px 0;"), unsafe_allow_html=True)

    cats=[("Technical",scores.get("technical",72),"Solid core knowledge. Deepen system design and edge-case thinking."),("Communication",scores.get("comm",68),"Clear articulation. Reduce pacing variance under pressure."),("Behavioural (STAR)",int(scores.get("overall",75)*0.88),"Good examples — quantify your impact more for stronger answers."),("Camera Presence",scores.get("eye",80),"Strong eye contact. Minor posture drift — keep your back straight.")]
    ch="".join([f'<div style="padding:15px;background:rgba(255,255,255,0.03);border-radius:8px;"><div style="display:flex;justify-content:space-between;margin-bottom:5px;"><span style="font-weight:700;font-size:15px;color:#fff;font-family:\'DM Sans\',sans-serif;">{c}</span><span style="font-family:\'Bebas Neue\',sans-serif;font-size:26px;color:{"#00d4aa" if sc>=75 else "#ffd700"};">{sc}%</span></div><p style="font-size:13px;color:rgba(255,255,255,0.6);line-height:1.6;font-family:\'DM Sans\',sans-serif;margin:0;">{n}</p></div>' for c,sc,n in cats])
    st.markdown(card(f'<p style="font-size:16px;font-weight:700;margin-bottom:16px;font-family:\'DM Sans\',sans-serif;">📋 Detailed Analysis</p><div style="display:grid;grid-template-columns:1fr 1fr;gap:13px;">{ch}</div>',"margin:0 48px 22px;"), unsafe_allow_html=True)
    st.markdown(card(f'<p style="font-size:16px;font-weight:700;color:#ffd700;margin-bottom:16px;font-family:\'DM Sans\',sans-serif;">💰 Salary Estimate</p><div style="display:flex;gap:32px;flex-wrap:wrap;"><div><p style="color:rgba(255,255,255,0.4);font-size:13px;font-family:\'DM Sans\',sans-serif;margin-bottom:3px;">Startup (India)</p><p style="font-family:\'Bebas Neue\',sans-serif;font-size:26px;color:#ffd700;margin:0;">₹12L – ₹20L</p></div><div><p style="color:rgba(255,255,255,0.4);font-size:13px;font-family:\'DM Sans\',sans-serif;margin-bottom:3px;">MNC / Product Co.</p><p style="font-family:\'Bebas Neue\',sans-serif;font-size:26px;color:#ffd700;margin:0;">₹20L – ₹40L</p></div><div><p style="color:rgba(255,255,255,0.4);font-size:13px;font-family:\'DM Sans\',sans-serif;margin-bottom:3px;">FAANG India</p><p style="font-family:\'Bebas Neue\',sans-serif;font-size:26px;color:#ffd700;margin:0;">₹45L – ₹90L</p></div><div><p style="color:rgba(255,255,255,0.4);font-size:13px;font-family:\'DM Sans\',sans-serif;margin-bottom:3px;">FAANG US / Remote</p><p style="font-family:\'Bebas Neue\',sans-serif;font-size:26px;color:#ffd700;margin:0;">$120K – $220K</p></div></div><p style="font-size:12px;color:rgba(255,255,255,0.22);margin-top:10px;font-family:\'DM Sans\',sans-serif;">Based on your score, domain, and current market benchmarks</p>',"margin:0 48px 32px;","rgba(255,215,0,0.15)"), unsafe_allow_html=True)

    c1,c2,c3=st.columns(3)
    with c1:
        if st.button("🔄 Try Another Interview",key="retry_iv"):
            st.session_state.current_page="New Interview"; st.rerun()
    with c2:
        if st.button("📄 Download PDF Report",key="dl_pdf"): st.toast("PDF export queued! (simulated)",icon="📄")
    with c3:
        if st.button("🏠 Back to Dashboard",key="back_dash"):
            st.session_state.current_page="Dashboard"; st.rerun()

def page_plans():
    st.markdown(stitle("Choose Your Plan","AI interviews are subscription-based. Human interviews are pay-per-session — no subscription."), unsafe_allow_html=True)
    st.markdown("<div style='height:26px'></div>", unsafe_allow_html=True)
    cols=st.columns(5)
    for i,(plan,col) in enumerate(zip(PLANS,cols)):
        with col:
            border="rgba(229,9,20,0.5)" if plan["tag"]=="Best Value" else "rgba(255,215,0,0.35)" if plan["tag"]=="Pro" else "rgba(255,255,255,0.1)"
            tdiv=f'<div style="text-align:center;margin-bottom:9px;"><span style="background:{plan["color"]};color:{"#000" if plan["color"]=="#ffd700" else "#fff"};padding:4px 15px;border-radius:20px;font-size:11px;font-weight:700;font-family:\'DM Sans\',sans-serif;">{plan["tag"]}</span></div>' if plan["tag"] else ""
            feats="".join([f'<div style="display:flex;gap:7px;margin-bottom:7px;"><span style="color:{plan["color"]};font-size:13px;">✓</span><span style="font-size:13px;color:rgba(255,255,255,0.75);font-family:\'DM Sans\',sans-serif;">{f}</span></div>' for f in plan["features"]])
            st.markdown(f'<div style="background:rgba(18,18,18,0.95);border:1px solid {border};border-radius:10px;padding:22px 17px;">{tdiv}<p style="font-size:16px;font-weight:700;color:#fff;margin-bottom:5px;font-family:\'DM Sans\',sans-serif;">{plan["name"]}</p><p style="font-family:\'Bebas Neue\',sans-serif;font-size:34px;color:{plan["color"]};margin-bottom:4px;">{plan["price"]}</p><p style="font-size:12px;color:rgba(255,255,255,0.35);margin-bottom:16px;font-family:\'DM Sans\',sans-serif;">{plan["n"]} interview{"s" if plan["n"]>1 else ""}</p>{feats}</div>', unsafe_allow_html=True)
            if st.button(f"Get {plan['name']}",key=f"plan_{i}"):
                with st.spinner("Processing payment..."): time.sleep(1.2)
                km={"Free Trial":"free","Single Interview":"single","Starter":"starter","Main Plan":"main","Premium":"premium"}
                upgrade_plan(st.session_state.user["id"],km.get(plan["name"],"free"),plan["n"])
                st.session_state.user["plan"]=km.get(plan["name"],"free")
                st.session_state.user["interviews_remaining"]=st.session_state.user.get("interviews_remaining",0)+plan["n"]
                st.success(f"✅ {plan['name']} activated! {plan['n']} interview(s) added."); st.balloons()
    st.markdown("<div style='height:22px'></div>", unsafe_allow_html=True)
    st.markdown(card('<p style="font-size:15px;font-weight:700;color:#ffd700;margin-bottom:5px;font-family:\'DM Sans\',sans-serif;">👩‍💼👨‍💼 Human Interviews — no subscription needed</p><p style="font-size:14px;color:rgba(255,255,255,0.55);margin:0;font-family:\'DM Sans\',sans-serif;">Book real industry experts directly. Pay once per session. Prices from ₹899.</p>',"margin:0 48px;","rgba(255,215,0,0.15)"), unsafe_allow_html=True)
    st.markdown("<div style='height:40px'></div>", unsafe_allow_html=True)

def page_human():
    st.markdown(stitle("Human Interviewer Marketplace","Real experts. One-time payment. No subscription required."), unsafe_allow_html=True)
    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)
    for i in range(0,len(INTERVIEWERS),2):
        cols=st.columns(2)
        for j,col in enumerate(cols):
            if i+j>=len(INTERVIEWERS): break
            iv=INTERVIEWERS[i+j]
            with col:
                ml="48px" if j==0 else "0"; mr="0" if j==0 else "48px"
                st.markdown(f'<div style="background:rgba(18,18,18,0.95);border:1px solid rgba(255,255,255,0.08);border-radius:10px;padding:24px;margin:0 {mr} 16px {ml};"><div style="display:flex;gap:13px;align-items:center;margin-bottom:15px;"><div style="width:48px;height:48px;border-radius:50%;background:linear-gradient(135deg,{iv["color"]},#7c3aed);display:flex;align-items:center;justify-content:center;font-weight:700;font-size:15px;color:#fff;flex-shrink:0;">{iv["avatar"]}</div><div style="flex:1;"><div style="display:flex;justify-content:space-between;align-items:flex-start;"><div><p style="font-weight:700;font-size:16px;color:#fff;margin-bottom:2px;font-family:\'DM Sans\',sans-serif;">{iv["name"]}</p><p style="font-size:13px;color:rgba(255,255,255,0.5);margin:0;font-family:\'DM Sans\',sans-serif;">{iv["role"]}</p></div><span style="background:rgba(255,215,0,0.1);border:1px solid rgba(255,215,0,0.3);color:#ffd700;padding:3px 10px;border-radius:20px;font-size:11px;font-weight:700;font-family:\'DM Sans\',sans-serif;">{iv["tag"]}</span></div></div></div><p style="font-size:13px;color:rgba(255,255,255,0.65);margin-bottom:5px;font-family:\'DM Sans\',sans-serif;">⭐ {iv["rating"]} &nbsp;•&nbsp; {iv["exp"]} experience</p><p style="font-size:13px;color:rgba(255,255,255,0.75);margin-bottom:5px;font-family:\'DM Sans\',sans-serif;">📌 {iv["specialty"]}</p><p style="font-size:12px;color:rgba(255,255,255,0.4);margin-bottom:14px;font-family:\'DM Sans\',sans-serif;">🕐 Next: {iv["available"][0]}</p><div style="display:flex;justify-content:space-between;align-items:center;border-top:1px solid rgba(255,255,255,0.06);padding-top:13px;"><span style="font-family:\'Bebas Neue\',sans-serif;font-size:28px;color:#ffd700;">{iv["price"]}</span><span style="font-size:12px;color:rgba(255,255,255,0.3);font-family:\'DM Sans\',sans-serif;">per session</span></div></div>', unsafe_allow_html=True)
                if st.button(f"Check availability — {iv['name'].split()[0]}",key=f"book_{i}_{j}"):
                    st.session_state.booked_interviewer=iv; st.rerun()
    if st.session_state.booked_interviewer:
        iv=st.session_state.booked_interviewer
        st.markdown("---")
        st.markdown(f'<div style="padding:0 48px;"><div style="background:rgba(20,20,20,0.97);border:1px solid rgba(229,9,20,0.3);border-radius:10px;padding:28px;max-width:520px;margin:0 auto;"><h3 style="font-size:22px;font-weight:700;margin-bottom:4px;color:#fff;font-family:\'DM Sans\',sans-serif;">Book with {iv["name"]}</h3><p style="color:rgba(255,255,255,0.45);font-size:14px;margin-bottom:20px;font-family:\'DM Sans\',sans-serif;">{iv["role"]} &nbsp;•&nbsp; {iv["price"]} per session</p></div></div>', unsafe_allow_html=True)
        _,bc,_=st.columns([1,2,1])
        with bc:
            slot=st.selectbox("Available Slots",iv["available"]+["Tomorrow 6:00 PM","Saturday 2:00 PM"])
            c1p,c2p=st.columns(2)
            with c1p:
                if st.button("Pay via Razorpay",key="pay_rzp"):
                    with st.spinner("Connecting to Razorpay..."): time.sleep(1.2)
                    st.success(f"✅ Booked with {iv['name']} for {slot}!"); st.session_state.booked_interviewer=None; st.balloons(); st.rerun()
            with c2p:
                if st.button("Pay via Stripe",key="pay_stripe"):
                    with st.spinner("Connecting to Stripe..."): time.sleep(1.2)
                    st.success(f"✅ Booked with {iv['name']} for {slot}!"); st.session_state.booked_interviewer=None; st.balloons(); st.rerun()
            if st.button("✕ Cancel",key="cancel_book"):
                st.session_state.booked_interviewer=None; st.rerun()

def page_community():
    st.markdown(stitle("Community","Real experiences from real users — updated live"), unsafe_allow_html=True)
    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
    cf,cs=st.columns([2.2,1])
    with cf:
        for i,post in enumerate(POSTS):
            liked=st.session_state.liked_posts.get(i,False)
            tc={"Success Story":"#00d4aa","Tip":"#ffd700","Insight":"#7c3aed","Review":"#0ea5e9"}.get(post["tag"],"#e50914")
            st.markdown(f'<div style="background:rgba(18,18,18,0.9);border:1px solid rgba(255,255,255,0.07);border-radius:10px;padding:20px;margin:0 0 13px 48px;"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:9px;"><div style="display:flex;align-items:center;gap:9px;"><span style="font-size:13px;font-weight:700;color:#e50914;font-family:\'DM Sans\',sans-serif;">@{post["user"]}</span><span style="background:{tc}20;color:{tc};padding:2px 10px;border-radius:20px;font-size:11px;font-weight:700;font-family:\'DM Sans\',sans-serif;">{post["tag"]}</span></div><span style="font-size:12px;color:rgba(255,255,255,0.3);font-family:\'DM Sans\',sans-serif;">{post["time"]}</span></div><p style="font-size:14px;line-height:1.75;color:rgba(255,255,255,0.85);margin-bottom:13px;font-family:\'DM Sans\',sans-serif;">{post["text"]}</p><div style="display:flex;gap:13px;border-top:1px solid rgba(255,255,255,0.05);padding-top:11px;"><span style="font-size:13px;color:{"#e50914" if liked else "rgba(255,255,255,0.35)"};font-family:\'DM Sans\',sans-serif;">❤️ {post["likes"]+(1 if liked else 0)}</span><span style="font-size:13px;color:rgba(255,255,255,0.3);font-family:\'DM Sans\',sans-serif;">💬 Reply</span></div></div>', unsafe_allow_html=True)
            _,lb,_=st.columns([2.5,0.65,1])
            with lb:
                if st.button("❤️ Liked" if liked else "❤️ Like",key=f"like_{i}"):
                    st.session_state.liked_posts[i]=not liked; st.rerun()
    with cs:
        tr="".join([f'<div style="display:flex;justify-content:space-between;padding:9px 0;border-bottom:1px solid rgba(255,255,255,0.06);"><span style="font-size:13px;color:rgba(255,255,255,0.7);font-family:\'DM Sans\',sans-serif;">{i+1}. {t}</span><span style="font-size:11px;color:#e50914;">🔥</span></div>' for i,t in enumerate(TRENDING[:6])])
        st.markdown(card(f'<p style="font-size:14px;font-weight:700;margin-bottom:13px;font-family:\'DM Sans\',sans-serif;">🔥 Trending Today</p>{tr}',"margin:0 48px 16px 0;"), unsafe_allow_html=True)
        lb_r="".join([f'<div style="display:flex;align-items:center;gap:9px;padding:9px 0;border-bottom:1px solid rgba(255,255,255,0.06);"><span style="font-size:16px;">{"🥇🥈🥉4️⃣5️⃣"[i*2:i*2+2] if i<3 else ["4️⃣","5️⃣"][i-3]}</span><span style="flex:1;font-size:13px;color:rgba(255,255,255,0.8);font-family:\'DM Sans\',sans-serif;">@{u}</span><span style="font-size:13px;color:#e50914;font-weight:700;font-family:\'DM Sans\',sans-serif;">{p}</span></div>' for i,(u,p) in enumerate([("prep_warrior",987),("ms_aspirant",914),("tn_developer",843),("anon_dev_2847",782),("fresher_2025",741)])])
        st.markdown(card(f'<p style="font-size:14px;font-weight:700;margin-bottom:13px;font-family:\'DM Sans\',sans-serif;">🏆 Leaderboard</p>{lb_r}',"margin:0 48px 16px 0;"), unsafe_allow_html=True)
        st.markdown(card('<p style="font-size:14px;font-weight:700;margin-bottom:9px;font-family:\'DM Sans\',sans-serif;">🤖 AI Community Summary</p><p style="font-size:13px;color:rgba(255,255,255,0.6);line-height:1.7;font-family:\'DM Sans\',sans-serif;margin:0;">Most users today struggled with <strong style="color:#e50914;">system design scalability</strong>. FAANG questions on <strong style="color:#ffd700;">distributed caching</strong> are trending. ServiceNow CAD prep is spiking this week.</p>',"margin:0 48px 16px 0;"), unsafe_allow_html=True)

# ─── APP SHELL ────────────────────────────────────────────────────────────────
def run_app():
    u=st.session_state.user
    qp=st.query_params.get("nav","")
    if qp:
        nm={"Dashboard":"Dashboard","New_Interview":"New Interview","Community":"Community","Plans":"Plans","Human_Interview":"Human Interview","Logout":"Logout"}
        if qp in nm:
            tgt=nm[qp]; st.query_params.clear()
            if tgt=="Logout":
                st.session_state.clear(); init_state(); st.rerun()
            else:
                st.session_state.current_page=tgt; st.rerun()

    st.markdown(CSS, unsafe_allow_html=True)
    if st.session_state.interview_active:
        page_interview(); return

    st.markdown(navbar(st.session_state.current_page,u["name"]), unsafe_allow_html=True)

    # Hidden nav buttons (fallback)
    nc=st.columns(6)
    for col,pg in zip(nc,["Dashboard","New Interview","Community","Plans","Human Interview","Logout"]):
        with col:
            st.markdown('<div style="display:none">', unsafe_allow_html=True)
            if st.button(pg,key=f"nav_{pg}"):
                if pg=="Logout": st.session_state.clear(); init_state(); st.rerun()
                else: st.session_state.current_page=pg; st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    pg=st.session_state.current_page
    if pg=="Dashboard": page_dashboard()
    elif pg=="New Interview": page_setup()
    elif pg=="Feedback": page_feedback()
    elif pg=="Plans": page_plans()
    elif pg=="Human Interview": page_human()
    elif pg=="Community": page_community()

# ─── ENTRY ────────────────────────────────────────────────────────────────────
init_db(); init_state()
st.markdown(CSS, unsafe_allow_html=True)
s=st.session_state.screen
if s=="splash": splash_screen()
elif s=="select": selection_screen()
elif s=="login": login_screen()
elif s=="app":
    if st.session_state.user: run_app()
    else: st.session_state.screen="login"; st.rerun()