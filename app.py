
from flask import Flask, render_template_string, request, redirect, session
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'blue-cs-secret-2026'

# DB setup
def get_db():
    conn = sqlite3.connect('school.db', check_same_thread=False)
    return conn

conn = get_db()
c = conn.cursor()
c.execute("CREATE TABLE IF NOT EXISTS users (id TEXT PRIMARY KEY, name TEXT, role TEXT, password TEXT, dept TEXT)")
c.execute("CREATE TABLE IF NOT EXISTS results (id INTEGER PRIMARY KEY, student_id TEXT, course TEXT, score INTEGER, grade TEXT)")
c.execute("CREATE TABLE IF NOT EXISTS fees (id INTEGER PRIMARY KEY, student_id TEXT, amount REAL, status TEXT, date TEXT)")
conn.commit()

c.execute("SELECT COUNT(*) FROM users")
if c.fetchone()[0] == 0:
    c.execute("INSERT INTO users VALUES ('ADMIN001', 'Admin User', 'Admin', 'admin123', 'ICT')")
    c.execute("INSERT INTO users VALUES ('STU001', 'Adeola Bello', 'Student', '1234', 'Computer Science')")
    c.execute("INSERT INTO users VALUES ('LEC001', 'Dr. Okafor', 'Lecturer', '1234', 'Computer Science')")
    conn.commit()

# BLUE C&S TEMPLATE
HTML = """
<!DOCTYPE html>
<html>
<head>
<title>C&S School Portal</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body { margin:0; font-family: Arial; background:#eef5ff; }
.header { background: linear-gradient(90deg, #0033a0, #0066ff); color:white; padding:20px; text-align:center; }
.header h1 { margin:0; font-size:28px; }
.header p { margin:5px; opacity:0.9; }
.card { background:white; max-width:500px; margin:30px auto; padding:25px; border-radius:12px; box-shadow:0 4px 15px rgba(0,51,160,0.15); border-top:5px solid #0066ff; }
input { width:100%; padding:12px; margin:10px 0; border:2px solid #cddfff; border-radius:8px; }
button { width:100%; padding:12px; background:#0033a0; color:white; border:none; border-radius:8px; font-size:16px; font-weight:bold; cursor:pointer; }
button:hover { background:#0066ff; }
.info { background:#dbe8ff; padding:10px; border-radius:8px; margin-top:15px; font-size:14px; }
.badge { background:#0033a0; color:white; padding:4px 10px; border-radius:20px; font-size:12px; }
</style>
</head>
<body>
<div class="header">
<h1>🔵 C&S SCHOOL PORTAL</h1>
<p>Cherubim & Seraphim College - Blue Portal</p>
</div>
<div class="card">
{{content}}
</div>
</body>
</html>
"""

@app.route('/', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        uid = request.form['id']
        pwd = request.form['password']
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE id=? AND password=?", (uid, pwd))
        user = cur.fetchone()
        if user:
            session['user'] = user
            return redirect('/dashboard')
        else:
            content = "<h3 style='color:red'>Invalid ID or Password</h3><a href='/'><button>Try Again</button></a>"
            return render_template_string(HTML.replace("{{content}}", content))
    
    content = """
    <h2 style="color:#0033a0; text-align:center;">Login</h2>
    <form method="post">
    <input name="id" placeholder="Enter ID e.g STU001" required>
    <input name="password" type="password" placeholder="Password" required>
    <button type="submit">LOGIN</button>
    </form>
    <div class="info">
    <b>Demo Accounts:</b><br>
    Student: STU001 / 1234<br>
    Admin: ADMIN001 / admin123<br>
    Lecturer: LEC001 / 1234
    </div>
    """
    return render_template_string(HTML.replace("{{content}}", content))

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/')
    user = session['user']
    content = f"""
    <h2 style="color:#0033a0;">Welcome, {user[1]} <span class="badge">{user[2]}</span></h2>
    <p><b>ID:</b> {user[0]}<br><b>Dept:</b> {user[4]}</p>
    <hr>
    <p style="color:green; font-weight:bold;">✅ You are now in BLUE C&S Portal!</p>
    <p>Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
    <a href="/"><button>Logout</button></a>
    """
    return render_template_string(HTML.replace("{{content}}", content))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
