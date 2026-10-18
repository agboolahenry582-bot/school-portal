import sqlite3
from flask import Flask, request, redirect, session, render_template_string
from datetime import datetime

app = Flask(__name__)
app.secret_key = "c&s_final_clean_2026"
DB_PATH = "/tmp/school.db"
MASTER_CODE = "CSS2026"

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
        print(e)
init_db()

BASE = """
<!DOCTYPE html>
<html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<title>C&S Success School</title>
<style>
body{font-family:Arial;background:#eef4ff;margin:0}
.header{background:#0b4fbf;color:white;padding:18px;text-align:center;font-size:20px;font-weight:bold}
.nav{background:white;display:flex;justify-content:space-around;padding:10px;box-shadow:0 2px 4px #0002}
.nav a{background:#0b4fbf;color:white;padding:8px 15px;border-radius:20px;text-decoration:none;font-size:13px;font-weight:bold}
.card{background:white;margin:12px;padding:15px;border-radius:10px;box-shadow:0 2px 5px #0002}
input,textarea{width:100%;padding:10px;margin:5px 0;border:1px solid #aaf;border-radius:8px;box-sizing:border-box}
.btn{background:#0b4fbf;color:white;border:0;padding:12px;width:100%;border-radius:8px;font-weight:bold}
.link{color:#0b4fbf;text-decoration:none}
</style></head><body>
<div class="header">C&S SUCCESS CLASS PRIVATE SCHOOL</div>
{% if session.get('user') %}
<div class="nav">
<a href="/dashboard">➕ ADD</a>
<a href="/records">📚 RECORDS</a>
<a href="/logout">🚪 LOGOUT</a>
</div>
{% endif %}
{{content|safe}}
</body></html>
"""

@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        u = request.form.get("username","").strip()
        p = request.form.get("password","").strip()
        con = sqlite3.connect(DB_PATH)
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        cur.execute("SELECT * FROM users WHERE username=? AND password=?", (u,p))
        row = cur.fetchone()
        con.close()
        if row:
            session["user"]=row["username"]; session["role"]=row["role"]
            return redirect("/dashboard")
        return render_template_string(BASE, content="<div class='card'><p style='color:red'>Wrong login!</p><a href='/'>Back</a></div>")
    if "user" in session:
        return redirect("/dashboard")
    form = """
    <div class='card'><h3>Staff Login</h3>
    <form method='post'>
    <input name='username' placeholder='Username' required>
    <input name='password' type='password' placeholder='Password' required>
    <button class='btn'>LOGIN</button>
    </form>
    <p style='text-align:center;margin-top:15px'><a href='/forgot' class='link'>Forgot Password?</a></p>
    </div>
    """
    return render_template_string(BASE, content=form)

@app.route("/forgot", methods=["GET","POST"])
def forgot():
    msg=""
    if request.method=="POST":
        u=request.form.get("username","").strip()
        rec=request.form.get("recovery","").strip()
        newp=request.form.get("newpass","").strip()
        if rec != MASTER_CODE:
            msg="<p style='color:red'>Wrong Recovery Code!</p>"
        else:
            con=sqlite3.connect(DB_PATH)
            cur=con.cursor()
            cur.execute("SELECT * FROM users WHERE username=?", (u,))
            if not cur.fetchone():
                msg=f"<p style='color:red'>User {u} not found</p>"
            else:
                cur.execute("UPDATE users SET password=? WHERE username=?", (newp,u))
                con.commit()
                msg=f"<p style='color:green'>Password for {u} changed! <a href='/'>Login now</a></p>"
            con.close()
    form=f"""
    <div class='card'><h3>Recover Password</h3>{msg}
    <form method='post'>
    <input name='username' placeholder='Username' required>
    <input name='recovery' placeholder='Master Code (CSS2026)' required>
    <input name='newpass' type='password' placeholder='New Password' required>
    <button class='btn'>RESET</button>
    </form>
    <p style='text-align:center'><a href='/' class='link'>Back to Login</a></p>
    </div>
    """
    return render_template_string(BASE, content=form)

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")
    html=f"""
    <div class='card'>
    <p>Welcome <b>{session['user']}</b> ({session['role']}) | <a href='/records' class='link'>View All Records →</a></p>
    <h3>Add New Student Record</h3>
    <form method='post' action='/add'>
    <input name='name' placeholder='Student Full Name' required>
    <input name='class_name' placeholder='Class'>
    <textarea name='notebook_list' placeholder='Note Books List'></textarea>
    <textarea name='textbook_list' placeholder='Text Books List'></textarea>
    <input name='books_total' type='number' step='0.01' placeholder='Books Total'>
    <input name='books_paid' type='number' step='0.01' placeholder='Books Paid'>
    <input name='fees_total' type='number' step='0.01' placeholder='Fees Total'>
    <input name='fees_paid' type='number' step='0.01' placeholder='Fees Paid'>
    <button class='btn'>SAVE RECORD</button>
    </form>
    </div>
    """
    return render_template_string(BASE, content=html)

@app.route("/records")
def records():
    if "user" not in session:
        return redirect("/")
    q = request.args.get("q","").strip()
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    if q:
        cur.execute("SELECT * FROM students WHERE name LIKE ? ORDER BY id DESC", (f"%{q}%",))
    else:
        cur.execute("SELECT * FROM students ORDER BY id DESC")
    students = cur.fetchall()
    con.close()
    
    html = f"""
    <div class='card'>
    <h3>Student Records - Separate Area</h3>
    <form method='get' action='/records'>
    <input name='q' value='{q}' placeholder='Search by name...'>
    <button class='btn' style='background:#00a86b'>SEARCH</button>
    </form>
    <p>Total: <b>{len(students)}</b> record(s)</p>
    </div>
    """
    for s in students:
        bt=float(s['books_total'] or 0); bp=float(s['books_paid'] or 0)
        ft=float(s['fees_total'] or 0); fp=float(s['fees_paid'] or 0)
        # ONLY ADMIN CAN SEE DELETE BUTTON
        delete_btn = ""
        if session.get("role") == "admin":
            delete_btn = f"<a href='/delete/{s['id']}' onclick=\"return confirm('Delete {s['name']}?')\"><button class='btn' style='background:#d33;margin-top:5px'>DELETE</button></a>"
        else:
            delete_btn = "<p style='font-size:11px;color:gray'>Only admin can delete</p>"
        
        html+=f"""
        <div class='card' style='border-left:5px solid #0b4fbf'>
        <b>{s['name']}</b> - {s['class_name']}<br>
        <small>By {s['created_by']} on {s['date']}</small><br><br>
        Books: Paid &#8358;{bp} Balance &#8358;{bt-bp}<br>
        Fees: Paid &#8358;{fp} Balance &#8358;{ft-fp}<br><br>
        <a href='/receipt/{s['id']}'><button class='btn'>PRINT RECEIPT</button></a>
        {delete_btn}
        </div>
        """
    return render_template_string(BASE, content=html)

@app.route("/add", methods=["POST"])
def add():
    if "user" not in session:
        return redirect("/")
    con = sqlite3.connect(DB_PATH)
    con.execute("INSERT INTO students (name,class_name,notebook_list,textbook_list,books_total,books_paid,fees_total,fees_paid,created_by,date) VALUES (?,?,?,?,?,?,?,?,?,?)",
    (request.form.get('name'), request.form.get('class_name'), request.form.get('notebook_list'), request.form.get('textbook_list'),
     float(request.form.get('books_total') or 0), float(request.form.get('books_paid') or 0),
     float(request.form.get('fees_total') or 0), float(request.form.get('fees_paid') or 0),
     session['user'], datetime.now().strftime("%d-%m-%Y %H:%M")))
    con.commit()
    con.close()
    return redirect("/records")

@app.route("/delete/<int:id>")
def delete(id):
    if "user" not in session:
        return redirect("/")
    if session.get("role") != "admin":
        return render_template_string(BASE, content="<div class='card'><p style='color:red'>Only ADMIN can delete! Ask your boss.</p><a href='/records' class='link'>Back</a></div>")
    con=sqlite3.connect(DB_PATH)
    con.execute("DELETE FROM students WHERE id=?", (id,))
    con.commit()
    con.close()
    return redirect("/records")

@app.route("/receipt/<int:id>")
def receipt(id):
    if "user" not in session:
        return redirect("/")
    con=sqlite3.connect(DB_PATH)
    con.row_factory=sqlite3.Row
    cur=con.cursor()
    cur.execute("SELECT * FROM students WHERE id=?", (id,))
    s=cur.fetchone()
    con.close()
    if not s:
        return "Not found"
    content=f"""
    <div class='card' style='border:2px dashed #0b4fbf'>
    <center><h2 style='color:#0b4fbf'>C&S SUCCESS SCHOOL</h2><p>Payment Receipt</p></center><hr>
    <p><b>Student:</b> {s['name']} - {s['class_name']}</p>
    <p><b>Note Books:</b> {s['notebook_list']}<br><b>Text Books:</b> {s['textbook_list']}</p><hr>
    <p>Books Total: &#8358;{s['books_total']} Paid: &#8358;{s['books_paid']} <b>Bal: &#8358;{float(s['books_total'] or 0)-float(s['books_paid'] or 0)}</b></p>
    <p>Fees Total: &#8358;{s['fees_total']} Paid: &#8358;{s['fees_paid']} <b>Bal: &#8358;{float(s['fees_total'] or 0)-float(s['fees_paid'] or 0)}</b></p><hr>
    <p>By {s['created_by']} on {s['date']}</p>
    <p style='margin-top:30px'>__________________<br>Signature</p>
    </div>
    <div class='card'><button class='btn' onclick='window.print()'>PRINT</button><br><br><a href='/records'><button class='btn' style='background:gray'>BACK TO RECORDS</button></a></div>
    """
    return render_template_string(BASE, content=content)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__=="__main__":
    app.run(host="0.0.0.0", port=5000)
