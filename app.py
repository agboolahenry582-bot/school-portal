import os, sqlite3
from flask import Flask, request, redirect, session, render_template_string
from datetime import datetime

app = Flask(__name__)
app.secret_key = "c&s_success_2026_final"

# Use /tmp folder which Render allows to write
DB_PATH = "/tmp/school.db"

def init_db():
    try:
        con = sqlite3.connect(DB_PATH)
        con.execute("CREATE TABLE IF NOT EXISTS users (username TEXT, password TEXT, role TEXT)")
        con.execute("CREATE TABLE IF NOT EXISTS students (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, class_name TEXT, notebook_list TEXT, textbook_list TEXT, books_total REAL, books_paid REAL, fees_total REAL, fees_paid REAL, created_by TEXT, date TEXT)")
        cur = con.cursor()
        cur.execute("SELECT * FROM users WHERE username='admin'")
        if not cur.fetchone():
            cur.execute("INSERT INTO users VALUES ('admin','admin123','admin')")
            cur.execute("INSERT INTO users VALUES ('staff1','staff123','staff')")
            cur.execute("INSERT INTO users VALUES ('staff2','staff123','staff')")
            con.commit()
        con.close()
    except Exception as e:
        print("DB Error:", e)

init_db()

BASE = """
<!DOCTYPE html>
<html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<title>C&S Success School</title>
<style>
body{font-family:Arial;background:#eef4ff;margin:0}
.header{background:#0b4fbf;color:white;padding:20px;text-align:center;font-size:22px;font-weight:bold}
.card{background:white;margin:15px;padding:15px;border-radius:10px;box-shadow:0 2px 5px #0002}
input,textarea{width:100%;padding:10px;margin:5px 0;border:1px solid #aaf;border-radius:8px;box-sizing:border-box}
.btn{background:#0b4fbf;color:white;border:0;padding:12px;width:100%;border-radius:8px;font-weight:bold}
</style></head><body>
<div class="header">C&S SUCCESS CLASS PRIVATE SCHOOL</div>
{{content|safe}}
</body></html>
"""

@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        u = request.form.get("username","").strip()
        p = request.form.get("password","").strip()
        try:
            con = sqlite3.connect(DB_PATH)
            con.row_factory = sqlite3.Row
            cur = con.cursor()
            cur.execute("SELECT * FROM users WHERE username=? AND password=?", (u,p))
            row = cur.fetchone()
            con.close()
            if row:
                session["user"] = row["username"]
                session["role"] = row["role"]
                return redirect("/dashboard")
        except Exception as e:
            print("Login error:", e)
        return render_template_string(BASE, content=f"<div class='card'><p style='color:red'>Wrong login! Try admin / admin123<br>Error: {e}</p><a href='/'>Back</a></div>")
    if "user" in session:
        return redirect("/dashboard")
    login_form = """
    <div class='card'>
    <h3>Staff Login</h3>
    <form method='post'>
    <input name='username' placeholder='Username' required>
    <input name='password' type='password' placeholder='Password' required>
    <button class='btn'>LOGIN</button>
    </form>
    <p style='font-size:12px;color:gray'>Default: admin / admin123<br>staff1 / staff123<br>staff2 / staff123</p>
    </div>
    """
    return render_template_string(BASE, content=login_form)

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")
    try:
        con = sqlite3.connect(DB_PATH)
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        cur.execute("SELECT * FROM students ORDER BY id DESC")
        students = cur.fetchall()
        con.close()
    except:
        students = []
    
    html = f"""
    <div class='card'>
    <p>Welcome <b>{session['user']}</b> ({session['role']}) <a href='/logout' style='float:right'>Logout</a></p>
    <form method='post' action='/add'>
    <input name='name' placeholder='Student Full Name e.g Agboola Henry' required>
    <input name='class_name' placeholder='Class e.g JSS2'>
    <textarea name='notebook_list' placeholder='List of Note Books'></textarea>
    <textarea name='textbook_list' placeholder='List of Text Books'></textarea>
    <input name='books_total' type='number' step='0.01' placeholder='Books Total Price'>
    <input name='books_paid' type='number' step='0.01' placeholder='Books Amount Paid'>
    <input name='fees_total' type='number' step='0.01' placeholder='School Fees Total'>
    <input name='fees_paid' type='number' step='0.01' placeholder='School Fees Paid'>
    <button class='btn'>SAVE STUDENT RECORD</button>
    </form>
    </div>
    <div class='card'><h3>All Records ({len(students)})</h3></div>
    """
    for s in students:
        try:
            bt = float(s['books_total'] or 0); bp = float(s['books_paid'] or 0)
            ft = float(s['fees_total'] or 0); fp = float(s['fees_paid'] or 0)
        except:
            bt=bp=ft=fp=0
        html += f"""
        <div class='card' style='border-left:5px solid #0b4fbf'>
        <b>{s['name']}</b> - {s['class_name']}<br>
        Books Paid: &#8358;{bp} | Balance: &#8358;{bt-bp}<br>
        Fees Paid: &#8358;{fp} | Balance: &#8358;{ft-fp}<br><br>
        <a href='/receipt/{s['id']}'><button class='btn'>PRINT RECEIPT</button></a>
        </div>
        """
    return render_template_string(BASE, content=html)

@app.route("/add", methods=["POST"])
def add():
    if "user" not in session:
        return redirect("/")
    try:
        con = sqlite3.connect(DB_PATH)
        con.execute("INSERT INTO students (name,class_name,notebook_list,textbook_list,books_total,books_paid,fees_total,fees_paid,created_by,date) VALUES (?,?,?,?,?,?,?,?,?,?)",
        (request.form.get('name'), request.form.get('class_name'), request.form.get('notebook_list'), request.form.get('textbook_list'),
         float(request.form.get('books_total') or 0), float(request.form.get('books_paid') or 0),
         float(request.form.get('fees_total') or 0), float(request.form.get('fees_paid') or 0),
         session['user'], datetime.now().strftime("%d-%m-%Y %H:%M")))
        con.commit()
        con.close()
    except Exception as e:
        print("Add error:", e)
    return redirect("/dashboard")

@app.route("/receipt/<int:id>")
def receipt(id):
    if "user" not in session:
        return redirect("/")
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute("SELECT * FROM students WHERE id=?", (id,))
    s = cur.fetchone()
    con.close()
    if not s:
        return "Not found"
    content = f"""
    <div class='card' style='border:2px dashed #0b4fbf'>
    <center><h2 style='color:#0b4fbf'>C&S SUCCESS CLASS PRIVATE SCHOOL</h2><p>Payment Receipt</p></center><hr>
    <p><b>Student:</b> {s['name']} ({s['class_name']})</p>
    <p><b>Note Books:</b> {s['notebook_list']}</p>
    <p><b>Text Books:</b> {s['textbook_list']}</p><hr>
    <p>Books Total: &#8358;{s['books_total']}<br>Paid: &#8358;{s['books_paid']}<br><b>Balance: &#8358;{float(s['books_total'] or 0)-float(s['books_paid'] or 0)}</b></p><hr>
    <p>Fees Total: &#8358;{s['fees_total']}<br>Paid: &#8358;{s['fees_paid']}<br><b>Balance: &#8358;{float(s['fees_total'] or 0)-float(s['fees_paid'] or 0)}</b></p><hr>
    <p><b>Received by:</b> {s['created_by']} on {s['date']}</p>
    </div>
    <div class='card'><button class='btn' onclick='window.print()'>PRINT / SCREENSHOT</button><br><br><a href='/dashboard'><button class='btn' style='background:gray'>BACK</button></a></div>
    """
    return render_template_string(BASE, content=content)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
