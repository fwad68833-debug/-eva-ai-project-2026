import os, sqlite3, secrets, requests
from pathlib import Path
from flask import Flask, request, session, redirect, jsonify, render_template_string, send_file
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.getenv("EVA_SECRET_KEY") or secrets.token_hex(32)

@app.after_request
def add_eva_cors_headers(response):
    origin = request.headers.get("Origin", "")
    allowed = ("http://127.0.0.1:5000", "http://localhost:5000")
    if origin in allowed:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        response.headers["Vary"] = "Origin"
    return response
DB = str(Path.home() / "eva_royal.db")
IMG_PATH = str(Path(__file__).resolve().parent / "eva_queen.webp")

def get_secure_key(name="GROQ_API_KEY"):
    if os.getenv(name): return os.getenv(name).strip()
    for p in [Path.home()/".config/eva/keys.env", Path.home()/".env", Path.home()/".eva_secret"]:
        if p.exists():
            try:
                for line in p.read_text(encoding="utf-8", errors="ignore").splitlines():
                    if line.strip().startswith(name+"="):
                        return line.split("=",1)[1].strip().strip('"').strip("'").strip()
            except: pass
    return ""

GROQ_API_KEY = get_secure_key("GROQ_API_KEY")
GROQ_MODEL = "openai/gpt-oss-20b"

with sqlite3.connect(DB) as c:
    c.execute("CREATE TABLE IF NOT EXISTS users (id TEXT PRIMARY KEY, name TEXT, pass TEXT, model TEXT DEFAULT 'Llama-3.3-70B', created TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY, uid TEXT, role TEXT, content TEXT, ts TEXT)")

def groq_reply(uid, text):
    if not GROQ_API_KEY or "gsk_" not in GROQ_API_KEY:
        return "مفتاح Groq مش موجود أو غير صحيح. راجع ملف المفاتيح."

    try:
        with sqlite3.connect(DB) as c:
            hist = c.execute(
                "SELECT role,content FROM messages WHERE uid=? ORDER BY id DESC LIMIT 4",
                (uid,)
            ).fetchall()[::-1]

        msgs = [{
            "role": "system",
            "content": """إنتِ إيفا، مساعد ذكاء اصطناعي بتتكلمي بالعامية المصرية العادية والطبيعية، كأنك بتتكلمي مع صحابك. خلي كلامك بسيط وعفوي وواضح، من غير أسلوب ملكي أو رسمي أو مبالغة في الألقاب والإيموجيز. ردي على قد السؤال، ولو محتاجة تشرحي اشرحي ببساطة.
صانعك ومطورك هو محمد ناصر، ولو حد سألك مين عملك أو مين مطورك، قولي بوضوح: أنا إيفا، ومحمد ناصر هو اللي عملني وطوّرني.
ما تدّعيش إنك إنسانة حقيقية؛ إنتِ مساعد ذكاء اصطناعي. حافظي على نفس الأسلوب الطبيعي في كل المحادثات."""
        }]

        for role, content in hist:
            msgs.append({
                "role": "user" if role == "user" else "assistant",
                "content": content
            })

        msgs.append({"role": "user", "content": text})

        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": GROQ_MODEL,
                "messages": msgs,
                "temperature": 0.7,
                "reasoning_effort": "low",
                "max_completion_tokens": 384
            },
            timeout=30
        )

        try:
            data = r.json()
        except ValueError:
            return f"Groq رجع رد غير مفهوم (HTTP {r.status_code})"

        if r.status_code != 200:
            err = data.get("error", {}).get("message", str(data))
            return f"Groq رجع خطأ HTTP {r.status_code}: {err}"

        choices = data.get("choices", [])
        if not choices:
            return f"Groq لم يرجع إجابة: {data}"

        answer = choices[0].get("message", {}).get("content", "")
        if isinstance(answer, str) and answer.strip():
            return answer.strip()

        return "Groq وصل، لكن رجّع إجابة فاضية. جرّب تبعت رسالتك تاني."

    except Exception as e:
        return f"مشكلة اتصال بـ Groq: {e}"

@app.route("/eva_queen.webp")
def queen():
    if Path(IMG_PATH).exists():
        return send_file(IMG_PATH, mimetype="image/webp")
    return "", 404

CSS = """
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@600;800&family=Tajawal:wght@400;700&display=swap" rel="stylesheet">
<style>
:root{--gold:#FFD700;--pur:#8A2BE2;--pur2:#B14EFF}
*{box-sizing:border-box;font-family:Tajawal}
body{margin:0;background:#05020e;color:white;min-height:100vh;overflow-y:auto}
.main-layout{display:flex;min-height:100vh;background:radial-gradient(ellipse at center,#1a1040 0%,#05020e 70%)}
.left{width:285px;min-width:285px;background:linear-gradient(180deg,#0a0618,#05020e);border-left:1px solid #FFD70022;border-right:1px solid #FFD70022;padding:18px;display:flex;flex-direction:column;gap:10px;overflow-y:auto;position:sticky;top:0;height:100vh}
.nav{padding:14px 16px;border-radius:14px;display:flex;gap:12px;align-items:center;color:#9a8aaa;cursor:pointer}
.nav.active{background:linear-gradient(90deg,#5a1bb3,#8A2BE2);color:white;box-shadow:0 0 24px #8A2BE2aa}
.center{flex:1;position:relative;display:flex;flex-direction:column;min-height:100vh;background:radial-gradient(ellipse at top,#1e1350,#05020e);overflow:hidden}
.hero-bg{position:absolute;inset:0;background:url('/eva_queen.webp') center top/cover no-repeat;opacity:0.9;pointer-events:none}
.hero-overlay{position:absolute;inset:0;background:linear-gradient(to bottom,rgba(5,2,14,0.1) 0%,#05020e 90%);pointer-events:none}
.hero-content{position:relative;z-index:2;padding:20px}
.eva-title{text-align:right}
.eva-title h1{font-family:Cairo;font-size:42px;margin:0;letter-spacing:8px;color:#FFD700;text-shadow:0 0 20px #FFD70088}
.eva-title small{letter-spacing:4px;color:#B14EFF}
.badge{background:#1a1232cc;border:1px solid #FFD70033;padding:5px 10px;border-radius:20px;font-size:11px;margin:3px;display:inline-block}
.chat-box{position:relative;z-index:3;flex:1;display:flex;flex-direction:column;gap:12px;padding:18px;overflow-y:auto;-webkit-overflow-scrolling:touch;max-height:60vh;scroll-behavior:smooth}
.bubble{max-width:82%;padding:12px 16px;border-radius:18px;line-height:1.6;font-size:14px;word-wrap:break-word}
.bubble.user{align-self:flex-start;background:linear-gradient(90deg,#FFD700,#ff9d00);color:black;font-weight:700}
.bubble.eva{align-self:flex-end;background:#1e1540ee;border:1px solid #8A2BE233}
.bubble.eva b{color:#FFD700}
.input-area{position:sticky;bottom:0;z-index:5;display:flex;gap:10px;align-items:center;background:rgba(10,6,22,0.96);border:1px solid #FFD70033;border-radius:30px;padding:8px 14px;margin:10px 12px}
.input-area input{flex:1;background:transparent;border:none;color:white;outline:none;padding:10px;font-size:15px}
.btn-send{width:44px;height:44px;min-width:44px;border-radius:50%;border:none;background:linear-gradient(135deg,#FFD700,#ff9d00);cursor:pointer;font-size:18px}
.right{width:310px;min-width:310px;background:linear-gradient(180deg,#0a0618,#05020e);border-right:1px solid #FFD70022;padding:16px;display:flex;flex-direction:column;gap:14px;overflow-y:auto;position:sticky;top:0;height:100vh}
.card{background:#1a1232cc;border:1px solid #FFD70018;border-radius:16px;padding:14px}
#menuBtn{display:none;position:fixed;top:10px;right:10px;z-index:999;width:44px;height:44px;border-radius:12px;border:1px solid #8A2BE2;background:#1a1030;color:#FFD700;font-size:22px}
@media(max-width:1100px){.right{display:none}}
@media(max-width:768px){.main-layout{flex-direction:column}.left{position:fixed;right:0;top:0;bottom:0;width:285px;z-index:1000;transform:translateX(100%);transition:0.3s;height:100vh}.left.open{transform:translateX(0)}.center{min-height:100vh}.chat-box{max-height:none;min-height:40vh;flex:none}#menuBtn{display:block}.right{display:none}}
</style>
<button id="menuBtn" onclick="document.querySelector('.left').classList.toggle('open')">☰</button>
"""

def make_chat_html(user_name):
    return """
<!DOCTYPE html><html dir="rtl" lang="ar"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1"><title>EVA ANIME</title>""" + CSS + """</head><body>
<div class="main-layout">
<div class="left">
  <div style="text-align:center;padding:10px 0 16px;border-bottom:1px solid #FFD70018"><div style="font-size:34px;color:#FFD700">♛</div><h1 style="font-family:Cairo;margin:4px 0;letter-spacing:6px;color:#FFD700">EVA</h1><small style="color:#B14EFF;letter-spacing:3px">AI ASSISTANT</small></div>
  <div class="nav active">💬 محادثة جديدة</div>
  <div class="nav" onclick="location.href='/memory'">🗂️ المحادثات</div>
  <div class="nav" onclick="location.href='/memory'">🧠 الذاكرة</div>
  <div class="nav">⭐ المفضلة</div>
  <div class="nav" onclick="location.href='/settings'">⚙️ الإعدادات</div>
  <div style="margin-top:auto" class="card">
    <div style="text-align:center"><div style="font-size:22px;color:#FFD700">♛</div><b>إيفا برو</b></div>
    <div style="margin-top:12px;background:url('/eva_queen.webp') center/cover;height:140px;border-radius:12px;border:1px solid #FFD70033"></div>
  </div>
</div>
<div class="center">
  <div class="hero-bg"></div><div class="hero-overlay"></div>
  <div class="hero-content"><div></div><div class="eva-title"><h1>EVA</h1><small>AI ASSISTANT</small><div style="margin-top:12px"><h3 style="margin:0">مرحبا يا ريس __NAME__</h3><small style="color:#ccc">أنا إيفا جاهزة لمساعدتك</small><br><div style="margin-top:8px"><span class="badge">💜 تفكير عميق</span><span class="badge">💖 إبداع</span><span class="badge">🎯 دقة عالية</span></div></div></div></div>
  <div id="chat" class="chat-box">
    <div class="bubble eva"><b>♛ مرحبا يا ريس __NAME__</b><br>اسألني أي حاجة! 💜</div>
  </div>
  <div class="input-area"><input id="msg" placeholder="اكتب رسالتك لايفا..."><button class="btn-send" onclick="send()">➤</button></div>
</div>
<div class="right">
  <div class="card"><b>💡 معلومات</b><br><small>الموديل: GROQ<br>حالة: متصل</small><br><small id="clock">--:--</small></div>
</div>
</div>
<script>
let chatBox=document.getElementById('chat');
function scrollChat(){ chatBox.scrollTop = chatBox.scrollHeight; }
setInterval(function(){let d=new Date();let el=document.getElementById('clock');if(el) el.innerText = String(d.getHours()).padStart(2,'0')+':'+String(d.getMinutes()).padStart(2,'0')},1000);
async function send(){
 let input=document.getElementById('msg');let t=input.value.trim();if(!t) return;
 chatBox.innerHTML += '<div class="bubble user">'+t+'</div>';
 input.value=''; scrollChat();
 try{
  let r=await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({msg:t})});
  let d=await r.json();
  chatBox.innerHTML += '<div class="bubble eva"><b>♛ EVA</b><br>'+d.reply+'</div>';
 }catch(e){
  chatBox.innerHTML += '<div class="bubble eva">خطأ اتصال: '+e+'</div>';
 }
 scrollChat();
}
document.getElementById('msg').addEventListener('keypress',function(e){if(e.key==='Enter') send();});
document.addEventListener('click',function(e){if(window.innerWidth<=768 &&!e.target.closest('.left') &&!e.target.closest('#menuBtn')){let sb=document.querySelector('.left'); if(sb) sb.classList.remove('open');}});
</script>
</body></html>
""".replace("__NAME__", user_name)

@app.route("/")
def home(): return redirect("/chat")

@app.route("/chat")
def chat_page():
    if 'uid' not in session: return redirect("/login")
    return make_chat_html(session.get('name','محمد'))

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method=="POST":
        name=request.form.get("name","").strip() or "محمد"
        pw=request.form.get("pass","1234")
        uid=secrets.token_hex(5)
        session['uid']=uid; session['name']=name
        with sqlite3.connect(DB) as c:
            c.execute("INSERT INTO users(id,name,pass,created) VALUES(?,?,?,?)",(uid,name,pw,datetime.now().isoformat()))
        return redirect("/chat")
    return render_template_string("<html dir='rtl'><head><meta charset='UTF-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"+CSS+"</head><body style='display:flex;align-items:center;justify-content:center;min-height:100vh;background:#05020e'><div style='background:rgba(10,5,22,0.92);border:1px solid #FFD70033;border-radius:22px;padding:26px;width:92%;max-width:380px;text-align:center'><div style='font-size:36px;color:#FFD700'>♛</div><h2 style='font-family:Cairo;color:#FFD700'>EVA ANIME</h2><form method='POST'><input name='name' placeholder='اسمك يا ريس' required style='width:100%;padding:12px;border-radius:10px;background:#000;color:white;border:1px solid #8A2BE2;margin:6px 0'><input name='pass' type='password' placeholder='كلمة المرور' style='width:100%;padding:12px;border-radius:10px;background:#000;color:white;border:1px solid #8A2BE2;margin:6px 0'><br><br><button style='width:100%;padding:13px;background:linear-gradient(90deg,#8A2BE2,#B14EFF);border:none;border-radius:12px;color:white;font-weight:800'>دخول المملكة 👑</button></form></div></body></html>")

@app.route("/api/chat", methods=["POST"])
def api_chat():
    uid=session.get('uid')
    msg=request.json.get("msg","")
    reply=groq_reply(uid,msg)
    with sqlite3.connect(DB) as c:
        c.execute("INSERT INTO messages(uid,role,content,ts) VALUES(?,?,?,?)",(uid,"user",msg,datetime.now().strftime("%H:%M")))
        c.execute("INSERT INTO messages(uid,role,content,ts) VALUES(?,?,?,?)",(uid,"assistant",reply,datetime.now().strftime("%H:%M")))
    return jsonify({"reply":reply})

@app.route("/api/memory")
def api_mem():
    uid=session.get('uid')
    with sqlite3.connect(DB) as c:
        rows=c.execute("SELECT role,content,ts FROM messages WHERE uid=? ORDER BY id DESC LIMIT 100",(uid,)).fetchall()
        return jsonify([{"role":r[0],"content":r[1],"ts":r[2]} for r in rows])

@app.route("/memory")
def memory():
    if 'uid' not in session: return redirect("/login")
    return render_template_string("<html dir='rtl'><head><meta charset='UTF-8'>"+CSS+"</head><body style='min-height:100vh;overflow:auto'><div style='padding:20px'><a href='/chat' style='color:#FFD700'>← رجوع</a><h2 style='color:#FFD700'>🗂️ الذاكرة</h2><div id='list' class='card'>تحميل...</div></div><script>fetch('/api/memory').then(r=>r.json()).then(function(d){document.getElementById('list').innerHTML=d.map(function(m){return '<div style=\"padding:10px;border-bottom:1px solid #222\"><small style=\"color:#FFD700\">'+m.ts+' - '+m.role+'</small><br>'+m.content+'</div>';}).join('')||'لا يوجد';});</script></body></html>")

@app.route("/settings")
def settings_page():
    if 'uid' not in session: return redirect("/login")
    key_disp = (GROQ_API_KEY[:12]+"...") if GROQ_API_KEY else "مش موجود - حطه في ~/.config/eva/keys.env"
    return render_template_string("<html dir='rtl'><head><meta charset='UTF-8'>"+CSS+"</head><body style='min-height:100vh;overflow:auto'><div style='padding:20px'><a href='/chat' style='color:#FFD700'>← رجوع</a><h2 style='color:#FFD700'>⚙️ الإعدادات</h2><div class='card'>المفتاح: "+key_disp+"<br><br><button onclick=\"if(confirm('مسح؟'))fetch('/clear',{method:'POST'}).then(()=>alert('تم'))\" style='background:#ff2244;color:white;border:none;padding:10px;border-radius:10px;width:100%'>مسح المحادثات</button></div></div></body></html>")

@app.route("/clear", methods=["POST"])
def clear():
    with sqlite3.connect(DB) as c:
        c.execute("DELETE FROM messages WHERE uid=?",(session.get('uid'),))
    return jsonify({"ok":True})

if __name__=="__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5001")))
