import json
import random
import time
from datetime import datetime, timezone
from pathlib import Path
import streamlit as st
from supabase import create_client
from streamlit_image_coordinates import streamlit_image_coordinates

st.set_page_config(page_title="Azure DP-900 Trainer", page_icon="☁️", layout="wide")

BASE_DIR = Path(__file__).parent
FLASHCARDS_FILE = BASE_DIR / "flashcards.json"
QUESTIONS_FILE = BASE_DIR / "exam_questions.json"

@st.cache_data
def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def default_progress():
    return {"total_answered": 0, "total_correct": 0, "questions": {}}


def get_supabase():
    """One Supabase client per Streamlit browser session."""
    if "supabase_client" not in st.session_state:
        try:
            url = st.secrets["SUPABASE_URL"]
            key = st.secrets["SUPABASE_KEY"]
        except Exception:
            st.error("Supabase-Verbindung fehlt. Bitte SUPABASE_URL und SUPABASE_KEY in den Streamlit Secrets hinterlegen.")
            st.stop()
        st.session_state.supabase_client = create_client(url, key)
    return st.session_state.supabase_client


def current_user():
    return st.session_state.get("auth_user")


def load_progress():
    user = current_user()
    if user is None:
        return default_progress()

    try:
        response = (
            get_supabase()
            .table("user_progress")
            .select("total_answered,total_correct,questions")
            .eq("user_id", user.id)
            .limit(1)
            .execute()
        )
        rows = response.data if response is not None and response.data else []
        if not rows:
            data = default_progress()
            save_progress(data)
            return data

        row = rows[0]
        return {
            "total_answered": row.get("total_answered", 0),
            "total_correct": row.get("total_correct", 0),
            "questions": row.get("questions") or {},
        }
    except Exception as exc:
        st.error(f"Lernstand konnte nicht geladen werden: {exc}")
        return default_progress()


def save_progress(data):
    user = current_user()
    if user is None:
        return

    payload = {
        "user_id": user.id,
        "total_answered": int(data.get("total_answered", 0)),
        "total_correct": int(data.get("total_correct", 0)),
        "questions": data.get("questions", {}),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    try:
        get_supabase().table("user_progress").upsert(payload).execute()
    except Exception as exc:
        st.error(f"Lernstand konnte nicht gespeichert werden: {exc}")

def question_id(question):
    return question["question"]

def record_answer(question, is_correct):
    progress = load_progress()
    qid = question_id(question)
    entry = progress["questions"].setdefault(qid, {
        "category": question["category"],
        "answered": 0,
        "correct": 0,
        "wrong": 0,
        "streak": 0
    })
    entry["category"] = question["category"]
    entry["answered"] += 1
    progress["total_answered"] += 1
    if is_correct:
        entry["correct"] += 1
        entry["streak"] += 1
        progress["total_correct"] += 1
    else:
        entry["wrong"] += 1
        entry["streak"] = 0
    save_progress(progress)

def get_error_questions():
    progress = load_progress()
    by_text = {q["question"]: q for q in exam_questions}
    errors = []
    for qid, stats in progress["questions"].items():
        # A problem question stays in training until it has a 2-answer correct streak.
        if stats.get("wrong", 0) > 0 and stats.get("streak", 0) < 2 and qid in by_text:
            errors.append(by_text[qid])
    return errors

def reset_practice():
    for key, value in {
        "practice_started": False,
        "practice_questions": [],
        "practice_index": 0,
        "practice_answered": False,
        "practice_results": []
    }.items():
        st.session_state[key] = value

def reset_exam():
    st.session_state.exam_started = False
    st.session_state.exam_questions_current = []
    st.session_state.exam_index = 0
    st.session_state.exam_answers = {}
    st.session_state.exam_submitted = False

def reset_errors():
    st.session_state.error_started = False
    st.session_state.error_questions = []
    st.session_state.error_index = 0
    st.session_state.error_answered = False

flashcards = load_json(FLASHCARDS_FILE)
exam_questions = load_json(QUESTIONS_FILE)

# ============================================================
# LOGIN / REGISTRIERUNG
# ============================================================
supabase = get_supabase()

if "auth_user" not in st.session_state:
    st.session_state.auth_user = None

if st.session_state.auth_user is None:
    import base64
    login_bg_path = BASE_DIR / "dashboard_background.jpeg"
    login_bg_b64 = base64.b64encode(login_bg_path.read_bytes()).decode("utf-8") if login_bg_path.exists() else ""
    bg_rule = f'url("data:image/jpeg;base64,{login_bg_b64}")' if login_bg_b64 else "linear-gradient(135deg,#102f4b,#5a5aa0 58%,#b67879)"
    st.markdown(f"""
    <style>
    header[data-testid="stHeader"]{{display:none!important}}
    #MainMenu,footer{{visibility:hidden!important}}
    .stApp{{background:linear-gradient(rgba(8,27,46,.50),rgba(8,27,46,.62)),{bg_rule} center center / cover no-repeat fixed!important}}
    .block-container{{max-width:560px!important;padding:7vh 1.4rem 3rem!important}}
    .login-brand{{text-align:center;color:white;margin-bottom:1rem;text-shadow:0 4px 22px rgba(0,0,0,.38)}}
    .login-brand .cloud{{font-size:2.35rem;line-height:1}}
    .login-brand h1{{color:white!important;font-family:Georgia,serif!important;font-size:2.65rem!important;font-weight:500!important;margin:.35rem 0 .12rem!important}}
    .login-brand .dp{{color:#f8dfd2;font-family:Georgia,serif;font-style:italic;font-size:1.05rem}}
    div[data-testid="stTabs"]{{background:rgba(247,250,255,.94)!important;border:1px solid rgba(255,255,255,.78)!important;border-radius:22px!important;padding:1rem 1.35rem 1.35rem!important;box-shadow:0 26px 70px rgba(4,18,34,.42)!important;backdrop-filter:blur(18px)}}
    button[data-baseweb="tab"]{{font-weight:750!important}}
    div[data-testid="stTextInput"] input{{
    background:rgba(255,255,255,.96)!important;
    color:#17344e!important;
    -webkit-text-fill-color:#17344e!important;
    caret-color:#17344e!important;
    border:1px solid rgba(34,68,99,.16)!important;
    border-radius:12px!important;
}}
div[data-testid="stTextInput"] input::placeholder{{
    color:#6b7f91!important;
    -webkit-text-fill-color:#6b7f91!important;
    opacity:1!important;
}}
    @media(max-width:650px){{.block-container{{padding:3vh 1rem 2rem!important}}.login-brand h1{{font-size:2.05rem!important}}}}
    </style>
    <div class="login-brand"><div class="cloud">☁️</div><h1>Azure Data Lab</h1><div class="dp">DP-900 · Learn smarter. Pass confidently.</div></div>
    """, unsafe_allow_html=True)
    login_tab, register_tab = st.tabs(["🔐 Einloggen", "✨ Registrieren"])

    with login_tab:
        with st.form("login_form"):
            login_email = st.text_input("E-Mail", key="login_email")
            login_password = st.text_input("Passwort", type="password", key="login_password")
            login_submit = st.form_submit_button("Einloggen", use_container_width=True)

        if login_submit:
            if not login_email or not login_password:
                st.warning("Bitte E-Mail und Passwort eingeben.")
            else:
                try:
                    result = supabase.auth.sign_in_with_password({
                        "email": login_email.strip(),
                        "password": login_password,
                    })
                    if result.user and result.session:
                        st.session_state.auth_user = result.user
                        st.success("Erfolgreich eingeloggt.")
                        st.rerun()
                    else:
                        st.error("Login nicht möglich.")
                except Exception as exc:
                    st.error(f"Login fehlgeschlagen: {exc}")

    with register_tab:
        with st.form("register_form"):
            register_email = st.text_input("E-Mail", key="register_email")
            register_password = st.text_input(
                "Passwort", type="password", key="register_password",
                help="Verwende mindestens 6 Zeichen."
            )
            register_password_2 = st.text_input(
                "Passwort wiederholen", type="password", key="register_password_2"
            )
            register_submit = st.form_submit_button("Account erstellen", use_container_width=True)

        if register_submit:
            if not register_email or not register_password:
                st.warning("Bitte E-Mail und Passwort eingeben.")
            elif register_password != register_password_2:
                st.error("Die beiden Passwörter stimmen nicht überein.")
            elif len(register_password) < 6:
                st.error("Das Passwort muss mindestens 6 Zeichen lang sein.")
            else:
                try:
                    result = supabase.auth.sign_up({
                        "email": register_email.strip(),
                        "password": register_password,
                    })
                    if result.session and result.user:
                        st.session_state.auth_user = result.user
                        st.success("Account erstellt – du bist eingeloggt.")
                        st.rerun()
                    else:
                        st.success(
                            "Account erstellt. Bitte bestätige jetzt die E-Mail von Supabase und logge dich danach hier ein."
                        )
                except Exception as exc:
                    st.error(f"Registrierung fehlgeschlagen: {exc}")

    st.stop()

defaults = {
    "cards": flashcards.copy(),
    "card_index": 0,
    "show_answer": False,
    "known": 0,
    "unknown": 0,
    "last_category": "Alle Kategorien",
    "practice_started": False,
    "practice_questions": [],
    "practice_index": 0,
    "practice_answered": False,
    "practice_results": [],
    "exam_started": False,
    "exam_questions_current": [],
    "exam_index": 0,
    "exam_answers": {},
    "exam_submitted": False,
    "error_started": False,
    "error_questions": [],
    "error_index": 0,
    "error_answered": False
}
for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value
if "cards_initialized" not in st.session_state:
    random.shuffle(st.session_state.cards)
    st.session_state.cards_initialized = True

# ============================================================
# DESIGN
# ============================================================

st.markdown("""
<style>
:root{--nav:#102c46;--ink:#16334d}
.stApp{
 background:
 linear-gradient(rgba(19,43,70,.06),rgba(19,43,70,.06)),
 radial-gradient(circle at 78% 8%,rgba(239,153,116,.28),transparent 25%),
 linear-gradient(135deg,#dfe9f8,#f7e6e2);
}
.block-container{max-width:1320px;padding:1.4rem 1.7rem 3rem}
header[data-testid="stHeader"]{background:transparent}
#MainMenu,footer{visibility:hidden}

/* HERO */
.hero{
 height:265px;border-radius:0;position:relative;overflow:hidden;padding:2.3rem 3rem;
 color:white;background:
 radial-gradient(circle at 78% 18%,rgba(245,176,126,.40),transparent 22%),
 linear-gradient(90deg,#203f68 0%,#526594 50%,#a96f76 100%);
 box-shadow:0 18px 42px rgba(19,40,67,.18)
}
.hero:before{
 content:"";position:absolute;inset:0;
 background:linear-gradient(0deg,rgba(10,31,50,.22),transparent 60%);
}
.hero .tag,.hero h1,.hero .dp,.hero .slogan{position:relative;z-index:2}
.hero .tag{font-size:.78rem;letter-spacing:.16em;font-weight:700;color:#d8e7f4}
.hero h1{color:white!important;font-family:Georgia,serif;font-weight:500;font-size:3.15rem;margin:.65rem 0 .1rem}
.hero .dp{font-family:Georgia,serif;font-size:2.1rem}
.hero .slogan{font-family:Georgia,serif;font-style:italic;font-size:1.18rem;margin-top:.55rem;color:#f6e9e8}

/* STAT CARDS */
.statgrid{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin:-52px 18px 18px;position:relative;z-index:5}
.stat{min-height:115px;padding:18px 20px;border-radius:13px;color:white;box-shadow:0 12px 25px rgba(21,41,67,.18)}
.stat .label{font-size:.84rem;font-weight:700}.stat .value{font-family:Georgia,serif;font-size:2.5rem;line-height:1.05;margin:.15rem 0}
.stat .sub{font-size:.78rem;opacity:.78}
.s1{background:linear-gradient(135deg,#5656b8,#3d639a)}
.s2{background:linear-gradient(135deg,#2688a1,#21677d)}
.s3{background:linear-gradient(135deg,#c94e72,#814d78)}
.s4{background:linear-gradient(135deg,#3ca77d,#367963)}

/* hide old Streamlit metrics; dashboard stats above replace them */
div[data-testid="stMetric"]{border-radius:14px}

/* NAV */
div[role="radiogroup"]{
 display:flex;gap:.2rem;padding:.42rem .55rem;border-radius:0;background:#102c46;
 box-shadow:0 10px 24px rgba(16,44,70,.15)
}
div[role="radiogroup"] label{color:white!important;padding:.32rem .45rem!important}
div[role="radiogroup"] label p{color:white!important;font-weight:650!important}

/* MODE CARDS */
.modegrid{display:grid;grid-template-columns:repeat(6,1fr);gap:10px;margin:14px 0}
.modecard{min-height:190px;padding:18px 16px;border-radius:12px;color:#17344e;box-shadow:0 10px 24px rgba(25,48,76,.13)}
.modecard .ico{font-size:2rem}.modecard h3{font-size:1.05rem;margin:.5rem 0;color:#17344e}
.modecard p{font-size:.8rem;line-height:1.35;color:#34536b}
.m1{background:linear-gradient(145deg,#d9e6ff,#c7d9ff)}
.m2{background:linear-gradient(145deg,#d8f5e8,#bde9dc)}
.m3{background:linear-gradient(145deg,#ffead5,#ffd6b6)}
.m4{background:linear-gradient(145deg,#e4dcff,#cbbdff)}
.m5{background:linear-gradient(145deg,#ffe0e8,#f6bfd1)}
.m6{background:linear-gradient(145deg,#d9efff,#b9ddfa)}
.badge{float:right;background:#7054cf;color:white;border-radius:999px;padding:4px 8px;font-size:.67rem}

/* PROGRESS */
.progressbox{background:rgba(238,246,255,.92);border-radius:14px;padding:18px 22px;box-shadow:0 10px 24px rgba(24,48,76,.12);margin-top:12px}
.progressline{display:grid;grid-template-columns:190px 1fr 42px;align-items:center;gap:10px;margin:9px 0;font-size:.82rem}
.track{height:8px;border-radius:999px;background:#d4e1ef;overflow:hidden}.fill{height:100%;border-radius:999px}
.f1{background:#2e9be8}.f2{background:#2ab77c}.f3{background:#f4b21d}.f4{background:#9a38df}

/* GENERAL */
.stButton>button{border:0;border-radius:999px;min-height:2.7rem;font-weight:700;background:linear-gradient(135deg,#6f5be5,#3c91dc);color:white}
div[data-testid="stAlert"],div[data-testid="stExpander"]{border-radius:14px!important}
h1,h2,h3{color:#17344e;letter-spacing:-.02em}
hr{border-color:rgba(24,49,76,.10)!important}
@media(max-width:1000px){.modegrid{grid-template-columns:repeat(3,1fr)}.statgrid{grid-template-columns:repeat(2,1fr);margin:14px 0}.hero{height:auto}.hero h1{font-size:2.3rem}}
</style>
""", unsafe_allow_html=True)

st.markdown('''
<style>
/* --- Target-image structural pass --- */
@media (min-width: 1100px){
  .stApp:before{
    content:"☁️\A Azure\A Data Lab\A\A 🏠  Start\A\A 📘  Lernkarten\A\A 🧠  Übungstest\A\A 🎯  Prüfung\A\A 🚀  Simulation\A\A ❌  Fehlertraining\A\A 📊  Lernstand\A\A ─────────\A\A Better Data.\A Brighter\A Opportunities.";
    white-space:pre;
    position:fixed;
    left:0; top:0; bottom:0;
    width:168px;
    padding:26px 18px;
    box-sizing:border-box;
    background:linear-gradient(180deg,#102d49 0%,#0c263f 100%);
    color:#dbeaff;
    font-family:Arial,sans-serif;
    font-size:13px;
    line-height:1.28;
    z-index:999;
    box-shadow:10px 0 28px rgba(10,31,51,.14);
  }
  .block-container{
    max-width:1360px!important;
    padding-left:198px!important;
    padding-right:24px!important;
    padding-top:18px!important;
  }
}
.hero{
  height:215px!important;
  padding:1.9rem 2.4rem!important;
}
.hero h1{font-size:2.75rem!important;margin:.42rem 0 .05rem!important}
.hero .dp{font-size:1.75rem!important}
.hero .slogan{margin-top:.32rem!important}
.statgrid{
  margin:12px 12px 16px!important;
  gap:12px!important;
}
.stat{
  min-height:102px!important;
  padding:15px 18px!important;
}
.stat .value{font-size:2.15rem!important}
.modegrid{
  margin:10px 0 14px!important;
  gap:9px!important;
}
.modecard{
  min-height:176px!important;
  padding:16px 14px!important;
}
div[role="radiogroup"]{
  background:rgba(255,255,255,.70)!important;
  border-radius:12px!important;
  box-shadow:none!important;
  border:1px solid rgba(31,55,83,.10)!important;
}
div[role="radiogroup"] label,
div[role="radiogroup"] label p{
  color:#24405a!important;
  font-size:.82rem!important;
}
</style>
''', unsafe_allow_html=True)

st.markdown('''
<style>
/* FINAL TARGET PASS */
@media (min-width:1100px){
  .block-container{padding-left:198px!important;max-width:1380px!important}
}

/* Make select navigation unobtrusive */
div[data-testid="stSelectbox"]{max-width:250px;margin:.25rem 0 .6rem}
div[data-testid="stSelectbox"] > div > div{
 background:#173b5c!important;color:white!important;border:0!important;border-radius:10px!important
}

/* Hero exact target mood */
.hero{
 height:238px!important;padding:2rem 2.5rem!important;
 background:
   radial-gradient(circle at 84% 18%,rgba(244,164,111,.44),transparent 23%),
   linear-gradient(90deg,rgba(28,59,94,.98) 0%,rgba(65,76,128,.94) 48%,rgba(153,91,91,.88) 100%)!important;
}
.hero h1{font-size:2.9rem!important;max-width:700px}
.hero .slogan{display:block!important;position:relative!important;z-index:8!important;color:#fff1eb!important}

/* CSS-only study mascot scene */
.mascot-scene{
 position:absolute;right:18px;bottom:0;width:365px;height:230px;z-index:4;
}
.books{position:absolute;right:58px;bottom:10px;width:185px}
.book{height:26px;border-radius:5px;margin-top:3px;border:2px solid rgba(39,24,24,.45);
 box-shadow:0 4px 7px rgba(20,22,35,.25)}
.book:nth-child(1){background:#74442f}.book:nth-child(2){background:#263a55}.book:nth-child(3){background:#744c39}
.book span{color:#e4a66f;font-family:Georgia,serif;font-size:13px;padding-left:14px;line-height:23px}

/* owl assembled in CSS: body, head, eyes, pupils, beak, ears */
.owl{position:absolute;right:82px;bottom:86px;width:120px;height:105px}
.owl-body{position:absolute;left:24px;bottom:0;width:74px;height:70px;border-radius:48% 48% 42% 42%;
 background:radial-gradient(circle at 50% 28%,#9b6b4c,#553b31 65%,#352a28);
 box-shadow:0 8px 14px rgba(18,20,31,.28)}
.owl-head{position:absolute;left:8px;top:0;width:108px;height:76px;border-radius:48% 48% 44% 44%;
 background:radial-gradient(circle at 50% 45%,#a77856,#51392f 68%,#302725);
 box-shadow:0 5px 12px rgba(18,20,31,.25)}
.owl-head:before,.owl-head:after{content:"";position:absolute;top:-14px;width:30px;height:34px;background:#4c342c}
.owl-head:before{left:4px;clip-path:polygon(0 100%,45% 0,100% 100%)}
.owl-head:after{right:4px;clip-path:polygon(0 100%,55% 0,100% 100%)}
.eye{position:absolute;top:17px;width:43px;height:43px;border-radius:50%;background:#f5e7c9;
 border:4px solid #3a2926;box-sizing:border-box;overflow:hidden}
.eye.left{left:10px}.eye.right{right:10px}
.pupil{position:absolute;width:16px;height:19px;border-radius:50%;background:#161719;left:14px;top:11px;
 animation:owlLook 5s ease-in-out infinite}
.pupil:after{content:"";position:absolute;width:5px;height:5px;border-radius:50%;background:white;left:3px;top:3px}
@keyframes owlLook{
 0%,18%{transform:translate(0,0)} 28%,45%{transform:translate(6px,-2px)}
 55%,72%{transform:translate(-6px,2px)} 82%,100%{transform:translate(0,0)}
}
.beak{position:absolute;left:48px;top:49px;width:0;height:0;border-left:7px solid transparent;
 border-right:7px solid transparent;border-top:14px solid #e99138;z-index:4}
.owl-feet{position:absolute;bottom:-2px;left:40px;color:#d88a35;font-size:18px;letter-spacing:9px}
.speech{position:absolute;right:190px;top:13px;background:#fff4df;color:#17334d;padding:10px 14px;
 border-radius:22px 22px 5px 22px;font-weight:700;font-size:12px;box-shadow:0 8px 18px rgba(25,33,50,.18)}
.checklist{position:absolute;right:-5px;top:38px;background:#e7b477;color:#54351f;padding:10px 12px;
 transform:rotate(-3deg);font-family:Georgia,serif;font-style:italic;font-size:12px;line-height:1.45;
 box-shadow:0 6px 14px rgba(30,30,35,.20)}
.cup{position:absolute;right:2px;bottom:11px;width:54px;height:52px;border-radius:4px 4px 15px 15px;
 background:#d2a084;border:3px solid #b97f64;color:#4e3b34;font-size:8px;text-align:center;padding-top:11px;
 box-sizing:border-box;font-weight:800}
.cup:after{content:"";position:absolute;right:-17px;top:11px;width:20px;height:23px;border:5px solid #b97f64;border-left:0;border-radius:0 14px 14px 0}

/* fit target dashboard tighter */
.statgrid{margin:-12px 16px 14px!important}
.modegrid{grid-template-columns:repeat(6,1fr)!important;margin:8px 0 12px!important}
.modecard{min-height:165px!important}
</style>
''', unsafe_allow_html=True)

st.markdown('''
<style>
@media (min-width:1100px){
 .stApp:before{
   content:"☁️\A Azure\A Data Lab\A\A 🏠  Start\A\A 📘  Lernkarten\A\A 🧠  Übungstest\A\A 🎯  Prüfung\A\A 🚀  Simulation\A\A ❌  Fehlertraining\A\A 📊  Lernstand\A\A ─────────────\A\A “Better\A Data.\A Brighter\A Opportunities.”\A\A Microsoft Azure\A\A ◐     ⚙";
   font-family:Arial,sans-serif!important;
   font-size:13px!important;
   line-height:1.25!important;
 }
}
.block-container{padding-bottom:2rem!important}
.hero{margin-bottom:0!important}
.statgrid{margin:0!important;padding:0 14px!important;transform:translateY(-78px);margin-bottom:-62px!important}
.stat{min-height:110px!important;border-radius:12px!important}
.home-title{display:none}
.home-intro{display:none}
.modegrid{
 display:grid!important;grid-template-columns:repeat(6,minmax(0,1fr))!important;
 gap:10px!important;margin:4px 0 12px!important
}
.modecard{
 min-height:185px!important;border-radius:11px!important;padding:16px!important;
 display:flex!important;flex-direction:column!important
}
.modecard .ico{font-size:2.25rem!important}
.modecard h3{font-size:1.12rem!important;margin:.35rem 0!important}
.modecard p{font-size:.78rem!important;min-height:54px!important;margin:.2rem 0 .65rem!important}
.fakebtn{
 display:inline-block;margin-top:auto;width:max-content;padding:8px 15px;border-radius:999px;
 color:white;font-size:.72rem;font-weight:750;box-shadow:0 6px 14px rgba(30,45,70,.12)
}
.b1{background:#665ce2}.b2{background:#32a77f}.b3{background:#cf812f}
.b4{background:#6c4fd3}.b5{background:#dc3f68}.b6{background:#2397dc}
.bottomgrid{display:grid;grid-template-columns:1.2fr 1fr;gap:14px;margin-top:12px}
.progresspanel,.quotepanel{
 min-height:170px;border-radius:12px;box-shadow:0 10px 24px rgba(25,48,76,.12)
}
.progresspanel{background:rgba(239,247,255,.94);padding:17px 20px;color:#17344e}
.progresspanel h3{margin:0 0 10px;font-size:1.05rem}
.pbody{display:grid;grid-template-columns:150px 1fr;gap:18px;align-items:center}
.ring{
 width:105px;height:105px;border-radius:50%;
 background:conic-gradient(#2c9ce7 calc(var(--pct)*1%),#d5e3f1 0);
 display:grid;place-items:center;margin:auto
}
.ring:after{content:"";width:78px;height:78px;background:#eef6ff;border-radius:50%;position:absolute}
.ring span{position:relative;z-index:2;font-family:Georgia,serif;font-size:1.45rem;font-weight:700}
.prow{display:grid;grid-template-columns:150px 1fr 38px;gap:8px;align-items:center;margin:7px 0;font-size:.72rem}
.ptrack{height:7px;background:#d5e2ef;border-radius:99px;overflow:hidden}.pfill{height:100%;border-radius:99px}
.pc1{background:#2e9be8}.pc2{background:#2ab77c}.pc3{background:#f4b21d}.pc4{background:#9a38df}
.quotepanel{
 padding:24px 28px;color:#25425b;position:relative;overflow:hidden;
 background:
   radial-gradient(circle at 84% 70%,rgba(236,142,105,.28),transparent 28%),
   linear-gradient(135deg,#eaf1fb,#f6d7d5);
}
.quotepanel:after{
 content:"▲";position:absolute;right:18px;bottom:-22px;font-size:125px;color:rgba(54,91,128,.20)
}
.quoteMark{font-size:2.2rem;color:#8aa4bf;line-height:.7}
.quoteText{font-family:Georgia,serif;font-style:italic;font-size:1.05rem;line-height:1.45;max-width:300px;margin-top:12px}
.quoteSide{position:absolute;right:20px;bottom:20px;text-align:right;color:white;font-size:.72rem;font-weight:800;letter-spacing:.08em;z-index:2}
@media(max-width:1100px){
 .modegrid{grid-template-columns:repeat(3,1fr)!important}.bottomgrid{grid-template-columns:1fr}
 .statgrid{transform:none;margin:10px 0!important;padding:0!important}
}
</style>
''', unsafe_allow_html=True)

st.markdown('''
<style>
/* ================= TARGET V3 — screenshot corrections ================= */

/* HERO: text must stay clear of the stat cards */
.hero{
    height:245px!important;
    padding:1.65rem 2.25rem!important;
    box-sizing:border-box!important;
}
.hero .tag{font-size:.68rem!important;margin-bottom:.2rem!important}
.hero h1{
    font-size:2.65rem!important;
    line-height:1.03!important;
    margin:.45rem 0 .12rem!important;
    max-width:690px!important;
}
.hero .dp{
    font-size:1.72rem!important;
    line-height:1!important;
    margin-top:.1rem!important;
}
.hero .slogan{
    position:relative!important;
    display:block!important;
    margin-top:.52rem!important;
    font-size:1.05rem!important;
    line-height:1.15!important;
    max-width:620px!important;
    z-index:8!important;
}

/* Mascot slightly smaller so it doesn't crowd the header */
.mascot-scene{
    width:330px!important;
    height:215px!important;
    right:8px!important;
}
.speech{right:174px!important;top:8px!important}
.checklist{right:0!important;top:34px!important}
.owl{transform:scale(.92);transform-origin:bottom right;right:72px!important}
.books{right:48px!important;transform:scale(.92);transform-origin:bottom right}
.cup{right:0!important;transform:scale(.9);transform-origin:bottom right}

/* STAT CARDS: overlap hero only a little, like the target */
.statgrid{
    transform:translateY(-38px)!important;
    margin:0 12px -28px!important;
    padding:0!important;
    gap:12px!important;
}
.stat{
    min-height:104px!important;
    padding:14px 17px!important;
}
.stat .value{font-size:2.05rem!important}

/* Hide the functional select on HOME so there is no fake extra Start bar */
.home-nav-hide{
    height:0!important;
    overflow:hidden!important;
}

/* remove excess separators/air on start */
.start-dashboard{
    margin-top:0!important;
}

/* six cards exactly as a compact row */
.modegrid{
    margin:0!important;
    grid-template-columns:repeat(6,minmax(0,1fr))!important;
    gap:9px!important;
}
.modecard{
    min-height:176px!important;
    height:176px!important;
    padding:14px 14px 12px!important;
    box-sizing:border-box!important;
}
.modecard .ico{font-size:1.95rem!important;line-height:1!important}
.modecard h3{font-size:1.02rem!important;margin:.45rem 0 .3rem!important}
.modecard p{
    font-size:.74rem!important;
    line-height:1.32!important;
    min-height:47px!important;
    margin:0 0 .45rem!important;
}
.fakebtn{
    padding:7px 13px!important;
    font-size:.68rem!important;
}

/* lower dashboard panels visible without huge scroll */
.bottomgrid{
    margin-top:10px!important;
    gap:12px!important;
}
.progresspanel,.quotepanel{
    min-height:158px!important;
    height:158px!important;
    box-sizing:border-box!important;
}
.progresspanel{padding:13px 18px!important}
.progresspanel h3{margin-bottom:5px!important}
.pbody{grid-template-columns:135px 1fr!important;gap:12px!important}
.ring{width:92px!important;height:92px!important}
.ring:after{width:68px!important;height:68px!important}
.ring span{font-size:1.25rem!important}
.prow{margin:5px 0!important}
.quotepanel{padding:19px 24px!important}
.quoteText{font-size:.95rem!important;line-height:1.35!important}

/* main page should start close to target edge */
@media(min-width:1100px){
  .block-container{
      padding-top:0!important;
      padding-right:18px!important;
  }
}
</style>
''', unsafe_allow_html=True)

st.markdown('''
<style>
/* ================= TARGET V4 — GEOMETRY MATCH ================= */
@media (min-width:1100px){
  .block-container{
    max-width:none!important;
    width:100%!important;
    padding-left:188px!important;
    padding-right:18px!important;
    padding-top:0!important;
    margin:0!important;
  }
}

/* Header starts at top and is tall enough for all copy */
.hero{
  height:250px!important;
  margin:0!important;
  padding:56px 72px 24px!important;
  border-radius:0!important;
  box-sizing:border-box!important;
}
.hero .tag{font-size:.72rem!important}
.hero h1{
  font-size:3.0rem!important;
  margin:10px 0 2px!important;
  line-height:1!important;
}
.hero .dp{font-size:2rem!important;margin:0!important;line-height:1.05!important}
.hero .slogan{font-size:1.12rem!important;margin-top:8px!important}

/* mascot aligned to target hero */
.mascot-scene{right:18px!important;bottom:0!important;width:355px!important;height:235px!important}
.owl{transform:scale(1)!important;right:82px!important}
.books{transform:scale(1)!important;right:58px!important}
.cup{transform:scale(1)!important;right:2px!important}
.speech{right:190px!important;top:14px!important}
.checklist{right:-2px!important;top:42px!important}

/* Stats sit just below hero with a small overlap, never over the slogan */
.statgrid{
  transform:translateY(-2px)!important;
  margin:0 18px 16px!important;
  padding:0!important;
  gap:14px!important;
}
.stat{
  min-height:122px!important;
  height:122px!important;
  padding:16px 20px!important;
  box-sizing:border-box!important;
  border-radius:12px!important;
}
.stat .label{font-size:.82rem!important}
.stat .value{font-size:2.35rem!important}
.stat .sub{font-size:.75rem!important}

/* no invisible navigation/gap on start */
div[data-testid="stSelectbox"]{display:none!important}
div[data-testid="stSelectbox"] + div{margin:0!important}
hr{display:none!important}

/* exact six-card row */
.modegrid{
  margin:0 18px 12px!important;
  gap:10px!important;
  grid-template-columns:repeat(6,minmax(0,1fr))!important;
}
.modecard{
  height:214px!important;
  min-height:214px!important;
  padding:18px 16px 14px!important;
  border-radius:12px!important;
}
.modecard .ico{font-size:2.15rem!important}
.modecard h3{font-size:1.08rem!important;margin:9px 0 7px!important}
.modecard p{font-size:.76rem!important;line-height:1.35!important;min-height:58px!important}
.fakebtn{font-size:.7rem!important;padding:8px 14px!important}

/* bottom row like target */
.bottomgrid{
  grid-template-columns:1.18fr 1fr!important;
  gap:14px!important;
  margin:0 18px!important;
}
.progresspanel,.quotepanel{
  height:188px!important;
  min-height:188px!important;
  border-radius:12px!important;
}
.progresspanel{padding:17px 22px!important}
.pbody{grid-template-columns:160px 1fr!important;gap:16px!important}
.ring{width:108px!important;height:108px!important}
.ring:after{width:80px!important;height:80px!important}
.quotepanel{padding:25px 28px!important}

/* Keep non-home content usable */
@media(max-width:1099px){
  div[data-testid="stSelectbox"]{display:block!important}
}
</style>
''', unsafe_allow_html=True)

progress_now = load_progress()
open_errors_now = len(get_error_questions())
answered_now = progress_now["total_answered"]
correct_now = progress_now["total_correct"]
quote_now = round(correct_now / answered_now * 100) if answered_now else 0

# Navigation stays inside the current Streamlit session.
PAGE_MAP = {
    "start": "🏠 Start",
    "cards": "📚 Lernkarten",
    "practice": "🧠 Übungstest",
    "exam": "🎯 Prüfung",
    "simulation": "🔥 Simulation",
    "errors": "❌ Fehlertraining",
    "progress": "📊 Lernstand",
}
if "page_key" not in st.session_state:
    st.session_state.page_key = "start"

page_key = st.session_state.page_key
mode = PAGE_MAP.get(page_key, "🏠 Start")

def go_to(page):
    st.session_state.page_key = page
    st.rerun()


# ============================================================
# ECHTE NAVIGATION + EINHEITLICHES DESIGN FÜR ALLE UNTERSEITEN
# ============================================================
if mode != "🏠 Start":
    # IMPORTANT: the old CSS sidebar was only decoration.
    # On subpages we explicitly switch it off and use Streamlit's real sidebar.
    st.markdown("""
    <style>
    .stApp:before{display:none!important;content:none!important}

    header[data-testid="stHeader"]{
        background:transparent!important;
    }

    .stApp{
        background:
          radial-gradient(circle at 82% 8%,rgba(232,164,145,.22),transparent 28%),
          radial-gradient(circle at 28% 5%,rgba(86,91,185,.16),transparent 31%),
          linear-gradient(135deg,#edf5ff 0%,#f7f3fa 56%,#fff0e9 100%)!important;
        color:#17344f!important;
    }

    /* REAL SIDEBAR */
    section[data-testid="stSidebar"]{
        display:block!important;
        background:linear-gradient(180deg,#102f4b 0%,#0b2943 100%)!important;
        border-right:1px solid rgba(255,255,255,.08)!important;
        width:220px!important;
        min-width:220px!important;
    }
    section[data-testid="stSidebar"] > div{
        padding-top:1.25rem!important;
    }
    section[data-testid="stSidebar"] *{
        color:#eef7ff!important;
    }
    section[data-testid="stSidebar"] div[role="radiogroup"]{
        display:flex!important;
        flex-direction:column!important;
        gap:.28rem!important;
        padding:.35rem!important;
        background:transparent!important;
    }
    section[data-testid="stSidebar"] div[role="radiogroup"] label{
        padding:.62rem .65rem!important;
        border-radius:10px!important;
        background:transparent!important;
    }
    section[data-testid="stSidebar"] div[role="radiogroup"] label:hover{
        background:rgba(86,163,215,.15)!important;
    }
    section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p{
        margin:0!important;
    }

    /* CONTENT: no overlap, no giant blank top */
    .block-container{
        max-width:1240px!important;
        width:auto!important;
        padding:1.15rem 2rem 4rem!important;
        margin:0 auto!important;
    }

    /* compact page banner */
    .subhero{
        position:relative;
        overflow:hidden;
        min-height:150px;
        box-sizing:border-box;
        padding:25px 34px;
        margin:0 0 20px;
        border-radius:22px;
        background:
          radial-gradient(circle at 79% 20%,rgba(233,157,137,.54),transparent 28%),
          linear-gradient(110deg,#123c60 0%,#46589a 57%,#ad7079 100%);
        box-shadow:0 18px 42px rgba(32,52,90,.16);
        color:white;
    }
    .subhero:after{
        content:"🦉";
        position:absolute;
        right:36px;
        bottom:8px;
        font-size:70px;
        filter:drop-shadow(0 8px 8px rgba(0,0,0,.20));
    }
    .subhero .eyebrow{
        font-size:.68rem;
        letter-spacing:.17em;
        font-weight:800;
        color:#e8f4ff;
    }
    .subhero h1{
        font-family:Georgia,serif!important;
        font-size:2.25rem!important;
        line-height:1!important;
        margin:.45rem 0 .2rem!important;
        color:white!important;
    }
    .subhero p{
        margin:.25rem 0 0!important;
        color:#fff5eb!important;
        font-family:Georgia,serif;
        font-style:italic;
    }

    h1,h2,h3{color:#17344f!important}
    hr{border-color:rgba(25,58,86,.10)!important}

    /* controls/cards */
    div[data-testid="stMetric"]{
        background:rgba(255,255,255,.72)!important;
        border:1px solid rgba(255,255,255,.9)!important;
        border-radius:16px!important;
        padding:14px 16px!important;
        box-shadow:0 10px 24px rgba(31,55,86,.08)!important;
    }
    div[data-baseweb="select"] > div,
    div[data-testid="stNumberInput"] input,
    div[data-testid="stTextInput"] input{
        border-radius:12px!important;
        border:1px solid rgba(38,73,106,.14)!important;
        background:rgba(255,255,255,.88)!important;
    }
    div[role="radiogroup"]{
        background:rgba(255,255,255,.64)!important;
        padding:10px 14px!important;
        border-radius:14px!important;
    }
    .stButton>button,.stFormSubmitButton>button{
        border:0!important;
        border-radius:999px!important;
        min-height:42px!important;
        padding:.55rem 1.15rem!important;
        font-weight:750!important;
        color:white!important;
        background:linear-gradient(90deg,#6854df,#279fe1)!important;
        box-shadow:0 8px 18px rgba(75,82,190,.18)!important;
    }
    div[data-testid="stAlert"],details{
        border-radius:15px!important;
    }
    div[data-testid="stProgress"] > div > div > div{
        background:linear-gradient(90deg,#6254df,#2ba7dc)!important;
        border-radius:999px!important;
    }

    @media(max-width:800px){
        section[data-testid="stSidebar"]{width:auto!important;min-width:auto!important}
        .block-container{padding:.8rem 1rem 3rem!important}
        .subhero{min-height:130px;padding:20px}
        .subhero h1{font-size:1.7rem!important}
        .subhero:after{font-size:48px;right:16px}
    }
    </style>
    """, unsafe_allow_html=True)

    # Real clickable navigation in the real Streamlit sidebar.
    st.sidebar.markdown("### ☁️ Azure\n## Data Lab")
    st.sidebar.markdown("---")
    nav_labels = list(PAGE_MAP.values())
    nav_choice = st.sidebar.radio(
        "Navigation",
        nav_labels,
        index=nav_labels.index(mode),
        label_visibility="collapsed",
        key="real_sidebar_navigation"
    )
    st.sidebar.markdown("---")
    st.sidebar.markdown("*Better Data.  \nBrighter Opportunities.*")
    st.sidebar.caption("Microsoft Azure")
    user_email = getattr(current_user(), "email", None)
    if user_email:
        st.sidebar.caption(f"👤 {user_email}")
    if st.sidebar.button("🚪 Ausloggen", use_container_width=True):
        try:
            get_supabase().auth.sign_out()
        except Exception:
            pass
        st.session_state.clear()
        st.rerun()

    if nav_choice != mode:
        reverse_pages = {v: k for k, v in PAGE_MAP.items()}
        go_to(reverse_pages[nav_choice])

    page_copy = {
        "📚 Lernkarten": ("Lernkarten", "Wissen aufbauen. Karte für Karte."),
        "🧠 Übungstest": ("Übungstest", "Gezielt üben und sofort Feedback bekommen."),
        "🎯 Prüfung": ("Prüfung", "Teste dein Wissen ohne sofortige Lösungshinweise."),
        "🔥 Simulation": ("Simulation", "50 Fragen · 45 Minuten · wie in der echten DP-900."),
        "❌ Fehlertraining": ("Fehlertraining", "Aus Fehlern lernen und gezielt besser werden."),
        "📊 Lernstand": ("Lernstand", "Dein Fortschritt auf einen Blick."),
    }
    page_title, page_sub = page_copy[mode]
    st.markdown(
        f"""<div class="subhero">
        <div class="eyebrow">AZURE DATA LAB · DP-900</div>
        <h1>{page_title}</h1>
        <p>{page_sub}</p>
        </div>""",
        unsafe_allow_html=True
    )

# ============================================================
# STARTSEITE
# ============================================================

if mode == "🏠 Start":
    from PIL import Image

    target_path = BASE_DIR / "dashboard_background.jpeg"
    if not target_path.exists():
        st.error("dashboard_background.jpeg fehlt im Projektordner.")
        st.stop()

    # The dashboard stays one unchanged image. Real Streamlit buttons are placed
    # transparently above the visible menu items and cards. This keeps the
    # session/login intact while giving us genuine hover + pointer behaviour.
    st.markdown("""
    <style>
      header[data-testid="stHeader"]{display:none!important}
      .stApp:before{display:none!important}
      .stApp{background:#102c46!important}
      .block-container{max-width:none!important;width:100%!important;padding:0!important;margin:0!important}
      div[data-testid="stVerticalBlock"]{gap:0!important}

      /* Dashboard is the positioning surface for all hotspots. */
      .st-key-dashboard_overlay{
          position:relative!important;
          width:100%!important;
          overflow:visible!important;
      }
      .st-key-dashboard_overlay div[data-testid="stImage"]{
          margin:0!important;
          padding:0!important;
      }
      .st-key-dashboard_overlay div[data-testid="stImage"] img{
          display:block!important;
          width:100%!important;
          height:auto!important;
      }

      /* Every hotspot is a REAL Streamlit button, but visually transparent. */
      .st-key-dashboard_overlay [class*="st-key-hotspot_"]{
          position:absolute!important;
          z-index:30!important;
          margin:0!important;
          padding:0!important;
      }
      .st-key-dashboard_overlay [class*="st-key-hotspot_"] .stButton,
      .st-key-dashboard_overlay [class*="st-key-hotspot_"] .stButton > button{
          width:100%!important;
          height:100%!important;
          min-height:0!important;
          margin:0!important;
          padding:0!important;
      }
      .st-key-dashboard_overlay [class*="st-key-hotspot_"] button{
          cursor:pointer!important;
          border:1px solid transparent!important;
          border-radius:12px!important;
          background:rgba(255,255,255,0)!important;
          box-shadow:none!important;
          color:transparent!important;
          font-size:0!important;
          transition:transform .18s ease, background .18s ease, box-shadow .18s ease, border-color .18s ease!important;
      }
      .st-key-dashboard_overlay [class*="st-key-hotspot_"] button p{
          color:transparent!important;
          font-size:0!important;
      }
      .st-key-dashboard_overlay [class*="st-key-hotspot_"] button:focus{
          outline:none!important;
          box-shadow:none!important;
      }

      /* Left navigation: hand + gentle highlight. */
      .st-key-dashboard_overlay [class*="st-key-hotspot_menu_"] button:hover{
          cursor:pointer!important;
          transform:translateX(3px)!important;
          background:rgba(105,181,231,.13)!important;
          border-color:rgba(178,222,250,.20)!important;
          box-shadow:0 5px 16px rgba(0,0,0,.12)!important;
      }

      /* Six dashboard cards: hand + lift/glow. */
      .st-key-dashboard_overlay [class*="st-key-hotspot_card_"] button:hover{
          cursor:pointer!important;
          transform:translateY(-6px) scale(1.012)!important;
          background:rgba(255,255,255,.08)!important;
          border-color:rgba(255,255,255,.36)!important;
          box-shadow:0 15px 28px rgba(12,36,62,.24)!important;
      }

      /* LEFT MENU — coordinates match the existing dashboard click map. */
      .st-key-hotspot_menu_start{left:.7%!important;top:15.8%!important;width:9.8%!important;height:6.1%!important}
      .st-key-hotspot_menu_cards{left:.7%!important;top:22.0%!important;width:9.8%!important;height:5.7%!important}
      .st-key-hotspot_menu_practice{left:.7%!important;top:28.0%!important;width:9.8%!important;height:5.7%!important}
      .st-key-hotspot_menu_exam{left:.7%!important;top:34.0%!important;width:9.8%!important;height:5.7%!important}
      .st-key-hotspot_menu_simulation{left:.7%!important;top:40.0%!important;width:9.8%!important;height:5.7%!important}
      .st-key-hotspot_menu_errors{left:.7%!important;top:46.0%!important;width:9.8%!important;height:5.7%!important}
      .st-key-hotspot_menu_progress{left:.7%!important;top:52.0%!important;width:9.8%!important;height:5.7%!important}

      /* SIX LARGE CARDS.
         Fine alignment: midpoint between the first (too high) and second
         (too low) test. This moves only the interactive wrappers, not the image. */
      .st-key-dashboard_overlay [class*="st-key-hotspot_card_"]{
          transform:translate(4px,18px)!important;
      }
      .st-key-hotspot_card_cards{left:12.9%!important;top:45.4%!important;width:13.0%!important;height:25.5%!important}
      .st-key-hotspot_card_practice{left:26.5%!important;top:45.4%!important;width:13.0%!important;height:25.5%!important}
      .st-key-hotspot_card_exam{left:40.1%!important;top:45.4%!important;width:13.0%!important;height:25.5%!important}
      .st-key-hotspot_card_simulation{left:calc(53.7% + 50px)!important;top:45.4%!important;width:13.0%!important;height:25.5%!important}
      .st-key-hotspot_card_errors{left:calc(67.3% + 50px)!important;top:45.4%!important;width:13.0%!important;height:25.5%!important}
      .st-key-hotspot_card_progress{left:calc(80.9% + 50px)!important;top:45.4%!important;width:13.0%!important;height:25.5%!important}
    </style>
    """, unsafe_allow_html=True)

    dashboard_image = Image.open(target_path)

    with st.container(key="dashboard_overlay"):
        st.image(dashboard_image, use_container_width=True)

        # Left menu hotspots
        if st.button("Start", key="hotspot_menu_start"):
            go_to("start")
        if st.button("Lernkarten", key="hotspot_menu_cards"):
            go_to("cards")
        if st.button("Übungstest", key="hotspot_menu_practice"):
            go_to("practice")
        if st.button("Prüfung", key="hotspot_menu_exam"):
            go_to("exam")
        if st.button("Simulation", key="hotspot_menu_simulation"):
            go_to("simulation")
        if st.button("Fehlertraining", key="hotspot_menu_errors"):
            go_to("errors")
        if st.button("Lernstand", key="hotspot_menu_progress"):
            go_to("progress")

        # Six large dashboard card hotspots
        if st.button("Lernkarten öffnen", key="hotspot_card_cards"):
            go_to("cards")
        if st.button("Übungstest öffnen", key="hotspot_card_practice"):
            go_to("practice")
        if st.button("Prüfung öffnen", key="hotspot_card_exam"):
            go_to("exam")
        if st.button("Simulation öffnen", key="hotspot_card_simulation"):
            go_to("simulation")
        if st.button("Fehlertraining öffnen", key="hotspot_card_errors"):
            go_to("errors")
        if st.button("Lernstand öffnen", key="hotspot_card_progress"):
            go_to("progress")

    user_email = getattr(current_user(), "email", None)
    c1, c2 = st.columns([5, 1])
    with c1:
        if user_email:
            st.caption(f"👤 Eingeloggt als {user_email}")
    with c2:
        if st.button("🚪 Ausloggen", key="dashboard_logout", use_container_width=True):
            try:
                get_supabase().auth.sign_out()
            except Exception:
                pass
            st.session_state.clear()
            st.rerun()

# ============================================================
# LERNKARTEN
# ============================================================
elif mode == "📚 Lernkarten":
    categories = sorted(set(c["category"] for c in flashcards))
    selected_category = st.selectbox("📂 Kategorie auswählen", ["Alle Kategorien"] + categories)

    filtered_cards = (
        flashcards.copy()
        if selected_category == "Alle Kategorien"
        else [c for c in flashcards if c["category"] == selected_category]
    )

    if st.session_state.last_category != selected_category:
        st.session_state.cards = filtered_cards.copy()
        random.shuffle(st.session_state.cards)
        st.session_state.card_index = 0
        st.session_state.show_answer = False
        st.session_state.known = 0
        st.session_state.unknown = 0
        st.session_state.last_category = selected_category

    cards = st.session_state.cards
    if not cards:
        st.warning("Keine Lernkarten vorhanden.")
        st.stop()

    if st.session_state.card_index >= len(cards):
        st.session_state.card_index = 0

    card = cards[st.session_state.card_index]
    answered = st.session_state.known + st.session_state.unknown
    original_total = len(filtered_cards)
    st.progress(min(answered / original_total, 1.0) if original_total else 0)
    st.caption(
        f"📚 {original_total} Karten | ✅ Gewusst: {st.session_state.known} | "
        f"❌ Nicht gewusst: {st.session_state.unknown}"
    )
    st.divider()
    st.caption(f"📂 {card['category']}")
    st.subheader(f"❓ {card['question']}")

    if not st.session_state.show_answer:
        if st.button("💡 Antwort anzeigen", use_container_width=True):
            st.session_state.show_answer = True
            st.rerun()
    else:
        st.info(card["answer"])
        st.write("### Wusstest du die Antwort?")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Gewusst", use_container_width=True):
                st.session_state.known += 1
                st.session_state.card_index += 1
                st.session_state.show_answer = False
                if st.session_state.card_index >= len(cards):
                    st.session_state.card_index = 0
                    random.shuffle(st.session_state.cards)
                st.rerun()
        with col2:
            if st.button("❌ Nicht gewusst", use_container_width=True):
                st.session_state.unknown += 1
                st.session_state.cards.append(card)
                st.session_state.card_index += 1
                st.session_state.show_answer = False
                st.rerun()

    st.divider()
    answered = st.session_state.known + st.session_state.unknown
    rate = round(st.session_state.known / answered * 100) if answered else 0
    c1, c2, c3 = st.columns(3)
    c1.metric("Gewusst", st.session_state.known)
    c2.metric("Nicht gewusst", st.session_state.unknown)
    c3.metric("Erfolgsquote", f"{rate} %")

    if st.button("🔄 Lernrunde neu starten", use_container_width=True):
        st.session_state.cards = filtered_cards.copy()
        random.shuffle(st.session_state.cards)
        st.session_state.card_index = 0
        st.session_state.show_answer = False
        st.session_state.known = 0
        st.session_state.unknown = 0
        st.rerun()

# ============================================================
# ÜBUNGSTEST
# ============================================================
elif mode == "🧠 Übungstest":
    st.subheader("🧠 Übungstest")
    st.write("Nach jeder Antwort bekommst du sofort Feedback und eine Erklärung.")

    if not st.session_state.practice_started:
        n = st.slider("Wie viele Fragen möchtest du üben?", 5, len(exam_questions), min(10, len(exam_questions)))
        st.caption(f"Fragenpool: {len(exam_questions)} Fragen")
        if st.button("🧠 Übung starten", use_container_width=True):
            st.session_state.practice_questions = random.sample(exam_questions, n)
            st.session_state.practice_index = 0
            st.session_state.practice_answered = False
            st.session_state.practice_results = []
            st.session_state.practice_started = True
            st.rerun()
    else:
        qs = st.session_state.practice_questions
        i = st.session_state.practice_index
        total = len(qs)

        if i >= total:
            score = sum(1 for r in st.session_state.practice_results if r["correct"])
            pct = round(score / total * 100)
            st.success("🏁 Übung beendet!")
            c1, c2 = st.columns(2)
            c1.metric("Richtig", f"{score} / {total}")
            c2.metric("Ergebnis", f"{pct} %")
            st.progress(score / total)

            wrong = [r for r in st.session_state.practice_results if not r["correct"]]
            if wrong:
                st.write("### ❌ Fehlerübersicht")
                for r in wrong:
                    with st.expander(r["question"]):
                        st.write(f"**Deine Antwort:** {r['selected']}")
                        st.write(f"**Richtig:** {r['correct_answer']}")
                        st.info(f"💡 {r['explanation']}")
            else:
                st.success("Alle Fragen richtig beantwortet! 🎉")

            if st.button("🔄 Neue Übung", use_container_width=True):
                reset_practice()
                st.rerun()
        else:
            q = qs[i]
            st.progress(i / total)
            st.caption(f"Frage {i + 1} von {total} · 📂 {q['category']}")
            st.subheader(q["question"])
            selected = st.radio("Wähle eine Antwort:", q["options"], index=None, key=f"practice_{i}")

            if not st.session_state.practice_answered:
                if st.button("Antwort prüfen", use_container_width=True):
                    if selected is None:
                        st.warning("Bitte wähle zuerst eine Antwort.")
                    else:
                        correct = selected == q["correct"]
                        record_answer(q, correct)
                        st.session_state.practice_results.append({
                            "question": q["question"],
                            "selected": selected,
                            "correct_answer": q["correct"],
                            "correct": correct,
                            "explanation": q["explanation"]
                        })
                        st.session_state.practice_answered = True
                        st.rerun()
            else:
                r = st.session_state.practice_results[-1]
                if r["correct"]:
                    st.success("✅ Richtig!")
                else:
                    st.error("❌ Leider falsch.")
                    st.write(f"**Richtige Antwort:** {q['correct']}")
                st.info(f"💡 {q['explanation']}")
                if st.button("➡️ Nächste Frage", use_container_width=True):
                    st.session_state.practice_index += 1
                    st.session_state.practice_answered = False
                    st.rerun()

# ============================================================
# PRÜFUNG
# ============================================================
elif mode == "🎯 Prüfung":
    st.subheader("🎯 DP-900 Prüfungssimulation")
    st.write(
        "Keine Lösungen während der Prüfung. Du kannst zwischen den Fragen "
        "wechseln und deine Antworten bis zur Abgabe ändern."
    )

    if not st.session_state.exam_started:
        n = st.slider(
            "Wie viele Prüfungsfragen?",
            5,
            len(exam_questions),
            min(20, len(exam_questions))
        )
        st.caption(f"Fragenpool: {len(exam_questions)} Fragen")

        if st.button("🚀 Prüfung starten", use_container_width=True):
            st.session_state.exam_questions_current = random.sample(exam_questions, n)
            st.session_state.exam_index = 0
            st.session_state.exam_answers = {}
            st.session_state.exam_submitted = False
            st.session_state.exam_started = True
            st.rerun()

    else:
        qs = st.session_state.exam_questions_current
        total = len(qs)

        # ----------------------------------------------------
        # AUSWERTUNG NACH EXPLIZITER ABGABE
        # ----------------------------------------------------
        if st.session_state.exam_submitted:
            results = []

            for idx, q in enumerate(qs):
                selected = st.session_state.exam_answers.get(idx)
                results.append({
                    "question": q["question"],
                    "category": q["category"],
                    "selected": selected,
                    "correct_answer": q["correct"],
                    "correct": selected == q["correct"],
                    "explanation": q["explanation"]
                })

            save_key = "exam_saved_" + str(id(qs))
            if save_key not in st.session_state:
                for q, result in zip(qs, results):
                    record_answer(q, result["correct"])
                st.session_state[save_key] = True

            score = sum(1 for r in results if r["correct"])
            pct = round(score / total * 100)

            st.success("🏁 Prüfung abgegeben!")
            c1, c2, c3 = st.columns(3)
            c1.metric("Richtig", f"{score} / {total}")
            c2.metric("Falsch / offen", total - score)
            c3.metric("Ergebnis", f"{pct} %")
            st.progress(score / total)

            st.divider()
            st.write("### 📊 Ergebnis nach Themen")

            category_results = {}
            for result in results:
                values = category_results.setdefault(
                    result["category"],
                    {"correct": 0, "total": 0}
                )
                values["total"] += 1
                if result["correct"]:
                    values["correct"] += 1

            for category, values in category_results.items():
                cat_pct = round(values["correct"] / values["total"] * 100)
                st.write(
                    f"**{category}:** {values['correct']} / "
                    f"{values['total']} ({cat_pct} %)"
                )
                st.progress(values["correct"] / values["total"])

            wrong = [r for r in results if not r["correct"]]

            if wrong:
                st.divider()
                st.write("### ❌ Fehleranalyse")

                for result in wrong:
                    with st.expander(result["question"]):
                        answer_text = result["selected"] or "Keine Antwort"
                        st.write(f"**Deine Antwort:** {answer_text}")
                        st.write(f"**Richtige Antwort:** {result['correct_answer']}")
                        st.info(f"💡 {result['explanation']}")
            else:
                st.success("Perfekte Runde – alle Fragen richtig! 🎉")

            st.divider()
            if st.button("🔄 Neue Prüfung starten", use_container_width=True):
                reset_exam()
                st.rerun()

        # ----------------------------------------------------
        # PRÜFUNG LÄUFT
        # ----------------------------------------------------
        else:
            i = st.session_state.exam_index
            q = qs[i]

            answered_count = len(st.session_state.exam_answers)
            st.progress(answered_count / total)
            st.caption(
                f"Frage {i + 1} von {total} · "
                f"{answered_count} beantwortet · 📂 {q['category']}"
            )

            st.subheader(q["question"])

            previous_answer = st.session_state.exam_answers.get(i)
            default_index = (
                q["options"].index(previous_answer)
                if previous_answer in q["options"]
                else None
            )

            selected = st.radio(
                "Wähle eine Antwort:",
                q["options"],
                index=default_index,
                key=f"exam_nav_{i}"
            )

            # Auswahl sofort speichern, damit Zurück/Vorwärts nichts verliert.
            if selected is not None:
                st.session_state.exam_answers[i] = selected

            st.caption("🔒 Lösungen werden erst nach der Abgabe angezeigt.")

            col_back, col_next = st.columns(2)

            with col_back:
                if st.button(
                    "⬅️ Zurück",
                    use_container_width=True,
                    disabled=(i == 0)
                ):
                    st.session_state.exam_index -= 1
                    st.rerun()

            with col_next:
                if st.button(
                    "Weiter ➡️",
                    use_container_width=True,
                    disabled=(i == total - 1)
                ):
                    st.session_state.exam_index += 1
                    st.rerun()

            st.divider()

            # Kleine Fragen-Navigation
            st.write("**Fragenübersicht**")
            nav_cols = st.columns(min(total, 10))

            # For more than 10 questions, use a selectbox instead of dozens of buttons.
            jump_to = st.selectbox(
                "Direkt zu Frage:",
                list(range(1, total + 1)),
                index=i,
                format_func=lambda x: (
                    f"Frage {x} ✓"
                    if (x - 1) in st.session_state.exam_answers
                    else f"Frage {x}"
                )
            )

            if jump_to - 1 != i:
                st.session_state.exam_index = jump_to - 1
                st.rerun()

            unanswered = total - len(st.session_state.exam_answers)

            if unanswered:
                st.warning(
                    f"Noch {unanswered} Frage(n) ohne Antwort. "
                    "Du kannst trotzdem abgeben; offene Fragen zählen dann als falsch."
                )
            else:
                st.success("Alle Fragen sind beantwortet. Du kannst die Prüfung abgeben.")

            if st.button(
                "🏁 Prüfung abgeben",
                type="primary",
                use_container_width=True
            ):
                st.session_state.exam_submitted = True
                st.rerun()



# ============================================================
# REALISTISCHE DP-900 SIMULATION
# ============================================================
elif mode == "🔥 Simulation":
    st.subheader("🔥 Realistische DP-900 Simulation")
    st.write(
        "45 Minuten · 50 zufällige Fragen · gewichteter Mix aus den vier Themenbereichen · "
        "keine Lösungen bis zur Abgabe."
    )

    SIM_COUNTS = {
        "1 – Core Data Concepts": 14,
        "2 – Relational Data": 11,
        "3 – Non-relational Data": 9,
        "4 – Analytics": 16,
    }

    if "sim_started" not in st.session_state:
        st.session_state.sim_started = False
        st.session_state.sim_questions = []
        st.session_state.sim_index = 0
        st.session_state.sim_answers = {}
        st.session_state.sim_end_time = None
        st.session_state.sim_submitted = False
        st.session_state.sim_saved = False

    def reset_simulation():
        st.session_state.sim_started = False
        st.session_state.sim_questions = []
        st.session_state.sim_index = 0
        st.session_state.sim_answers = {}
        st.session_state.sim_end_time = None
        st.session_state.sim_submitted = False
        st.session_state.sim_saved = False

    if not st.session_state.sim_started:
        st.info(
            "Die Simulation ist als realistische Übung gedacht. Die tatsächliche Anzahl und "
            "Zusammensetzung einer echten Prüfung kann variieren."
        )
        if st.button("🔥 45-Minuten-Simulation starten", type="primary", use_container_width=True):
            selected_questions = []
            for category, count in SIM_COUNTS.items():
                pool = [q for q in exam_questions if q["category"] == category]
                selected_questions.extend(random.sample(pool, min(count, len(pool))))

            random.shuffle(selected_questions)
            st.session_state.sim_questions = selected_questions
            st.session_state.sim_index = 0
            st.session_state.sim_answers = {}
            st.session_state.sim_end_time = time.time() + (45 * 60)
            st.session_state.sim_submitted = False
            st.session_state.sim_saved = False
            st.session_state.sim_started = True
            st.rerun()

    else:
        qs = st.session_state.sim_questions
        total = len(qs)
        remaining = max(0, int(st.session_state.sim_end_time - time.time()))

        if remaining <= 0 and not st.session_state.sim_submitted:
            st.session_state.sim_submitted = True

        if st.session_state.sim_submitted:
            results = []
            for idx, q in enumerate(qs):
                selected = st.session_state.sim_answers.get(idx)
                results.append({
                    "question": q["question"],
                    "category": q["category"],
                    "selected": selected,
                    "correct_answer": q["correct"],
                    "correct": selected == q["correct"],
                    "explanation": q["explanation"],
                })

            if not st.session_state.sim_saved:
                for q, result in zip(qs, results):
                    record_answer(q, result["correct"])
                st.session_state.sim_saved = True

            score = sum(1 for r in results if r["correct"])
            pct = round(score / total * 100) if total else 0

            st.success("🏁 Simulation beendet!")
            c1, c2, c3 = st.columns(3)
            c1.metric("Richtig", f"{score} / {total}")
            c2.metric("Falsch / offen", total - score)
            c3.metric("Ergebnis", f"{pct} %")
            st.progress(score / total if total else 0)

            st.write("### 📊 Ergebnis nach Themen")
            cat_results = {}
            for result in results:
                values = cat_results.setdefault(result["category"], {"correct": 0, "total": 0})
                values["total"] += 1
                if result["correct"]:
                    values["correct"] += 1

            for category, values in cat_results.items():
                cat_pct = round(values["correct"] / values["total"] * 100)
                st.write(f"**{category}:** {values['correct']} / {values['total']} ({cat_pct} %)")
                st.progress(values["correct"] / values["total"])

            wrong = [r for r in results if not r["correct"]]
            if wrong:
                st.write("### ❌ Fehleranalyse")
                for result in wrong:
                    with st.expander(result["question"]):
                        st.write(f"**Deine Antwort:** {result['selected'] or 'Keine Antwort'}")
                        st.write(f"**Richtige Antwort:** {result['correct_answer']}")
                        st.info(f"💡 {result['explanation']}")
            else:
                st.success("Alle Fragen richtig! 🎉")

            if st.button("🔄 Neue Simulation", use_container_width=True):
                reset_simulation()
                st.rerun()

        else:
            minutes, seconds = divmod(remaining, 60)
            st.metric("⏱️ Restzeit", f"{minutes:02d}:{seconds:02d}")
            st.caption(
                "Die Restzeit wird bei jeder Aktion aktualisiert. "
                "Nach 45 Minuten wird die Simulation automatisch abgegeben."
            )

            i = st.session_state.sim_index
            q = qs[i]
            answered_count = len(st.session_state.sim_answers)
            st.progress(answered_count / total)
            st.caption(
                f"Frage {i + 1} von {total} · {answered_count} beantwortet · 📂 {q['category']}"
            )
            st.subheader(q["question"])

            previous = st.session_state.sim_answers.get(i)
            default_index = q["options"].index(previous) if previous in q["options"] else None
            selected = st.radio(
                "Wähle eine Antwort:",
                q["options"],
                index=default_index,
                key=f"sim_answer_{i}",
            )
            if selected is not None:
                st.session_state.sim_answers[i] = selected

            back, nxt = st.columns(2)
            with back:
                if st.button("⬅️ Zurück", use_container_width=True, disabled=(i == 0), key="sim_back"):
                    st.session_state.sim_index -= 1
                    st.rerun()
            with nxt:
                if st.button("Weiter ➡️", use_container_width=True, disabled=(i == total - 1), key="sim_next"):
                    st.session_state.sim_index += 1
                    st.rerun()

            jump = st.selectbox(
                "Direkt zu Frage:",
                list(range(1, total + 1)),
                index=i,
                format_func=lambda x: (
                    f"Frage {x} ✓" if (x - 1) in st.session_state.sim_answers else f"Frage {x}"
                ),
                key="sim_jump",
            )
            if jump - 1 != i:
                st.session_state.sim_index = jump - 1
                st.rerun()

            unanswered = total - len(st.session_state.sim_answers)
            if unanswered:
                st.warning(f"Noch {unanswered} Frage(n) ohne Antwort.")
            else:
                st.success("Alle 50 Fragen sind beantwortet.")

            if st.button("🏁 Simulation jetzt abgeben", type="primary", use_container_width=True):
                st.session_state.sim_submitted = True
                st.rerun()


# ============================================================
# FEHLERTRAINING
# ============================================================
elif mode == "❌ Fehlertraining":
    st.subheader("❌ Fehlertraining")
    errors = get_error_questions()

    if not errors and not st.session_state.error_started:
        st.success("Aktuell sind keine offenen Fehlerfragen vorhanden. 🎉")
        st.write("Falsch beantwortete Fragen aus Übungstest und Prüfung erscheinen automatisch hier.")
    elif not st.session_state.error_started:
        st.write(f"Du hast aktuell **{len(errors)} offene Fehlerfragen**.")
        st.caption("Eine Frage verschwindet aus dem Fehlertraining, wenn du sie zweimal hintereinander richtig beantwortet hast.")
        if st.button("🔥 Fehlertraining starten", use_container_width=True):
            st.session_state.error_questions = errors.copy()
            random.shuffle(st.session_state.error_questions)
            st.session_state.error_index = 0
            st.session_state.error_answered = False
            st.session_state.error_started = True
            st.rerun()
    else:
        qs = st.session_state.error_questions
        i = st.session_state.error_index

        if i >= len(qs):
            st.success("🏁 Fehlertraining für diese Runde beendet!")
            remaining = get_error_questions()
            st.write(f"Offene Fehlerfragen danach: **{len(remaining)}**")
            if st.button("🔄 Fehlerliste neu laden", use_container_width=True):
                reset_errors()
                st.rerun()
        else:
            q = qs[i]
            st.progress(i / len(qs))
            st.caption(f"Fehlerfrage {i + 1} von {len(qs)} · 📂 {q['category']}")
            st.subheader(q["question"])
            selected = st.radio("Wähle eine Antwort:", q["options"], index=None, key=f"error_{i}")

            if not st.session_state.error_answered:
                if st.button("Antwort prüfen", use_container_width=True):
                    if selected is None:
                        st.warning("Bitte wähle zuerst eine Antwort.")
                    else:
                        correct = selected == q["correct"]
                        record_answer(q, correct)
                        st.session_state.error_answered = True
                        st.session_state.error_last_correct = correct
                        st.rerun()
            else:
                if st.session_state.get("error_last_correct"):
                    st.success("✅ Richtig!")
                else:
                    st.error("❌ Noch nicht.")
                    st.write(f"**Richtige Antwort:** {q['correct']}")
                st.info(f"💡 {q['explanation']}")
                if st.button("➡️ Nächste Fehlerfrage", use_container_width=True):
                    st.session_state.error_index += 1
                    st.session_state.error_answered = False
                    st.rerun()

# ============================================================
# LERNSTAND
# ============================================================
else:
    st.subheader("📊 Dein DP-900 Lernstand")
    progress = load_progress()
    answered = progress["total_answered"]
    correct = progress["total_correct"]
    pct = round(correct / answered * 100) if answered else 0

    c1, c2, c3 = st.columns(3)
    c1.metric("Beantwortet", answered)
    c2.metric("Richtig", correct)
    c3.metric("Gesamtquote", f"{pct} %")

    st.divider()
    st.write("### Themenbereiche")

    categories = sorted(set(q["category"] for q in exam_questions))
    stats = {c: {"answered": 0, "correct": 0} for c in categories}

    for entry in progress["questions"].values():
        category = entry.get("category")
        if category in stats:
            stats[category]["answered"] += entry.get("answered", 0)
            stats[category]["correct"] += entry.get("correct", 0)

    for category in categories:
        values = stats[category]
        cat_pct = round(values["correct"] / values["answered"] * 100) if values["answered"] else 0
        st.write(f"**{category}** — {cat_pct} % ({values['correct']} von {values['answered']} richtig)")
        st.progress(cat_pct / 100)

    errors = get_error_questions()
    st.divider()
    st.metric("Offene Fehlerfragen", len(errors))

    if answered == 0:
        st.info("Dein dauerhafter Lernstand füllt sich automatisch, sobald du Übungs- oder Prüfungsfragen beantwortest.")
    elif errors:
        st.write("👉 Arbeite als Nächstes im **❌ Fehlertraining** an deinen offenen Fragen.")
    else:
        st.success("Zurzeit sind keine Fehlerfragen offen. 🎉")
