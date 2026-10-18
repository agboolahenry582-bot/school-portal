from flask import Flask, request, redirect, session, render_template_string, g
import sqlite3, os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "c&s_success_blue_2026"
DB = "school.db"

# --- DATABASE ---
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DB)
        db.row_factory = sqlite3.Row
    return db

def init_db():
    with sqlite3.connect(DB) as con:
        con.execute('''CREATE TABLE IF NOT EXISTS users 
        (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT, role TEXT)''')
        con.execute('''CREATE TABLE IF NOT EXISTS students
        (id INTEGER PRIMARY KEY, name TEXT, class_name TEXT, 
         notebook_list TEXT, textbook_list TEXT,
         books_total REAL, books_paid REAL,
         fees_total REAL, fees_paid REAL,
         created_by TEXT, date TEXT)''')
        # Default users - change password after first login
        try:
            con.execute("INSERT INTO users (username,password,role) VALUES ('admin','admin123','admin')")
            con.execute("INSERT INTO users (username,password,role) VALUES ('staff1','staff123','staff')")
            con.execute("INSERT INTO users (username,password,role) VALUES ('staff2','staff123','staff')")
            con.commit()
        except: pass

init_db()

# --- HTML TEMPLATE (BLUE THEME) ---
BASE_HTML = """
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>C&S Success Class Private School</title>
<style>
body{font-family:Arial; background:#eef4ff; margin:0; padding:0; color:#1a2a4a}
.header{background:#0b4fbf; color:white; padding:18px; text-align:center; font-weight:bold; font-size:22px}
.card{background:white; margin:15px; padding:15px; border-radius:12px; box-shadow:0 2px 8px rgba(0,0,0,0.1)}
input,select,textarea{width:100%; padding:10px; margin:6px 0; border-radius:8px; border:1px solid #b8cfff}
.btn{background:#0b4fbf; color:white; border:none; padding:12px; border-radius:8px; width:100%; font-weight:bold; cursor:pointer}
.btn:active{transform:scale(0.98)}
.small{font-size:12px; color:gray}
.badge{padding:4px 8px; border-radius:6px; color:white}
.bal{color:red; font-weight:bold} .paid{color:green; font-weight:bold}
.receipt{border:2px dashed #0b4fbf; padding:15px}
@media print{.no-print{display:none}}
</style>
</head>
<body>
<div class="header">C&S SUCCESS CLASS PRIVATE SCHOOL</div>
{{content|safe}}
</body>
</html>
"""

LOGIN_PAGE = """
<div class="card">
<h3>Staff Login</h3>
<form method="post">
<input name="username" placeholder="Username - admin / staff1 / staff2" required>
<input name="password" type="password" placeholder="Password" required>
<button class="btn">LOGIN</button>
</form>
<p class="small">Default: admin/admin123, staff1/staff123, staff2/staff123</p>
</div>
"""

DASHBOARD = """
<div class="card no-print">
<p>Welcome <b>{{user}}</b> ({{role}}) <a href="/logout" style="float:right">Logout</a></p>
<form method="post" action="/add">
<input name="name" placeholder="Student Full Name" required>
<input name="class_name" placeholder="Class (e.g JSS1)">
<textarea name="notebook_list" placeholder="List of Note Books e.g 10pcs 60leaves"></textarea>
<textarea name="textbook_list" placeholder="List of Text Books e.g English, Maths"></textarea>
<input name="books_total" type="number" step="0.01" placeholder="Books Total Price" required>
<input name="books_paid" type="number" step="0.01" placeholder="Books Amount Paid" required>
<input name="fees_total" type="number" step="0.01" placeholder="School Fees Total" required>
<input name="fees_paid" type="number" step="0.01" placeholder="School Fees Paid" required>
<button class="btn">SAVE STUDENT RECORD</button>
</form>
</div>
<div class="card">
<h3>All Records</h3>
{% for s in students %}
<div class="card" style="border-left:5px solid #0b4fbf">
<b>{{s['name']}}</b> - {{s['class_name']}}<br>
<small>Note Books: {{s['notebook_list']}}<br>Text Books: {{s['textbook_list']}}</small><br><br>
Books: <span class="paid">Paid ₦{{s['books_paid']}}</span> | 
<span class="bal">Remains ₦{{s['books_total']-s['books_paid']}}</span><br>
Fees: <span class="paid">Paid ₦{{s['fees_paid']}}</span> | 
<span class="bal">Remains ₦{{s['fees_total']-s['fees_paid']}}</span><br><br>
<a href="/receipt/{{s['id']}}"><button class="btn">PRINT RECEIPT</button></a>
</div>
{% endfor %}
</div>
"""

RECEIPT = """
<div class="card receipt" id="receipt">
<center><h2 style="color:#0b4fbf">C&S SUCCESS CLASS PRIVATE SCHOOL</h2>
<p>Payment Receipt</p>
<p>{{date}}</p></center>
<hr>
<p><b>Student:</b> {{s['name']}} ({{s['class_name']}})</p>
<p><b>Note Books:</b> {{s['notebook_list']}}</p>
<p><b>Text Books:</b> {{s['textbook_list']}}</p>
<hr>
<p>Books Total: ₦{{s['books_total']}}<br>
Books Paid: ₦{{s['books_paid']}}<br>
<b>Books Balance: ₦{{s['books_total']-s['books_paid']}}</b></p>
<hr>
<p>Fees Total: ₦{{s['fees_total']}}<br>
Fees Paid: ₦{{s['fees_paid']}}<br>
<b>Fees Balance: ₦{{s['fees_total']-s['fees_paid']}}</b></p>
<hr>
<p><b>Received by:</b> {{s['created_by']}}</p>
<center><p class="small">Thank you! This receipt can be screenshotted and sent to parents.</p></center>
</div>
<div class="card no-print">
<button class="btn" onclick="window.print()">PRINT / SCREENSHOT</button>
<a href="/"><button class="btn" style="background:gray; margin-top:10px">BACK</button></a>
</div>
"""

# --- ROUTES ---
@app.before_request
def before(): g._database = None
@app.teardown_appcontext
def close(exception): 
    db = getattr(g, '_database', None)
    if db: db.close()

@app.route("/", methods=["GET","POST"])
def login():
    if request.method=="POST":
        db=get_db()
        u=db.execute("SELECT * FROM users WHERE username=? AND password=?",
                     (request.form['username'], request.form['password'])).fetchone()
        if u:
            session['user']=u['username']; session['role']=u['role']; return redirect("/dashboard")
        return render_template_string(BASE_HTML, content="<div class='card'><p style='color:red'>Wrong login</p>"+LOGIN_PAGE+"</div>")
    if 'user' in session: return redirect("/dashboard")
    return render_template_string(BASE_HTML, content=LOGIN_PAGE)

@app.route("/dashboard")
def dashboard():
    if 'user' not in session: return redirect("/")
    db=get_db()
    students=db.execute("SELECT * FROM students ORDER BY id DESC").fetchall()
    content=render_template_string(DASHBOARD, user=session['user'], role=session['role'], students=students)
    return render_template_string(BASE_HTML, content=content)

@app.route("/add", methods=["POST"])
def add():
    if 'user' not in session: return redirect("/")
    db=get_db()
    db.execute("INSERT INTO students (name,class_name,notebook_list,textbook_list,books_total,books_paid,fees_total,fees_paid,created_by,date) VALUES (?,?,?,?,?,?,?,?,?,?)",
               (request.form['name'], request.form['class_name'], request.form['notebook_list'], request.form['textbook_list'],
                float(request.form['books_total']), float(request.form['books_paid']),
                float(request.form['fees_total']), float(request.form['fees_paid']),
                session['user'], datetime.now().strftime("%d-%m-%Y %H:%M")))
    db.commit()
    return redirect("/dashboard")

@app.route("/receipt/<int:id>")
def receipt(id):
    if 'user' not in session: return redirect("/")
    db=get_db()
    s=db.execute("SELECT * FROM students WHERE id=?", (id,)).fetchone()
    content=render_template_string(RECEIPT, s=s, date=datetime.now().strftime("%d-%m-%Y"))
    return render_template_string(BASE_HTML, content=content)

@app.route("/logout")
def logout():
    session.clear(); return redirect("/")

if __name__=="__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
