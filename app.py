import streamlit as st
import sqlite3
import hashlib
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="UNIVERSITY PORTAL", layout="wide")

conn = sqlite3.connect('school.db', check_same_thread=False)
c = conn.cursor()

# CREATE TABLES
c.execute('''CREATE TABLE IF NOT EXISTS users
             (id TEXT PRIMARY KEY, name TEXT, role TEXT, password TEXT, dept TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS results
             (id INTEGER PRIMARY KEY, student_id TEXT, course TEXT, score INTEGER, grade TEXT, session TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS fees
             (id INTEGER PRIMARY KEY, student_id TEXT, amount REAL, status TEXT, date TEXT)''')

# ADD ADMIN + DEMO DATA IF EMPTY
c.execute("SELECT COUNT(*) FROM users")
if c.fetchone()[0] == 0:
    c.execute("INSERT INTO users VALUES ('ADMIN001', 'Admin User', 'Admin', 'admin123', 'ICT')")
    c.execute("INSERT INTO users VALUES ('STU001', 'Adeola Bello', 'Student', '1234', 'Computer Science')")
    c.execute("INSERT INTO users VALUES ('LEC001', 'Dr. Okafor', 'Lecturer', '1234', 'Computer Science')")
    c.execute("INSERT INTO results VALUES (1, 'STU001', 'CSC201', 85, 'A', '2025/2026')")
    c.execute("INSERT INTO fees VALUES (1, 'STU001', 150000, 'PAID', '2025-08-20')")
    conn.commit()

def login():
    st.title("🏫 FEDERAL UNIVERSITY - STUDENT PORTAL")
    col1, col2 = st.columns(2)
    with col1:
        user_id = st.text_input("User ID")
        password = st.text_input("Password", type="password")
        if st.button("LOGIN"):
            c.execute("SELECT * FROM users WHERE id=? AND password=?", (user_id, password))
            user = c.fetchone()
            if user:
                st.session_state['user'] = user
                st.rerun()
            else:
                st.error("Invalid Credentials")
    with col2:
        st.info("**Demo Logins:**\nAdmin: ADMIN001 / admin123\nStudent: STU001 / 1234\nLecturer: LEC001 / 1234")

def student_dashboard(user):
    st.sidebar.title(f"Welcome, {user[1]}")
    st.sidebar.write(f"Role: {user[2]} | Dept: {user[4]}")
    if st.sidebar.button("Logout"):
        del st.session_state['user']
        st.rerun()

    tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "📝 Results", "💳 School Fees"])

    with tab1:
        st.header("Student Dashboard")
        c.execute("SELECT AVG(score) FROM results WHERE student_id=?", (user[0],))
        cgpa = c.fetchone()[0] or 0
        st.metric("Current CGPA", f"{cgpa:.2f}")

    with tab2:
        st.header("Academic Results")
        df = pd.read_sql_query("SELECT * FROM results WHERE student_id=?", conn, params=(user[0],))
        st.dataframe(df, use_container_width=True)

    with tab3:
        st.header("School Fees")
        df = pd.read_sql_query("SELECT * FROM fees WHERE student_id=?", conn, params=(user[0],))
        st.dataframe(df, use_container_width=True)
        if not df.empty and df.iloc[0]['status'] == 'PAID':
            st.success("Fees Status: PAID ✅")
        else:
            st.warning("Fees Status: NOT PAID ❌")

def admin_dashboard(user):
    st.sidebar.title(f"Admin Panel: {user[1]}")
    if st.sidebar.button("Logout"):
        del st.session_state['user']
        st.rerun()
    st.header("Admin - Manage Students & Results")

    st.subheader("All Students")
    df = pd.read_sql_query("SELECT id, name, role, dept FROM users", conn)
    st.dataframe(df, use_container_width=True)

    st.subheader("Upload Result")
    with st.form("result_form"):
        stu_id = st.text_input("Student ID")
        course = st.text_input("Course Code")
        score = st.number_input("Score", 0, 100)
        session = st.text_input("Session", "2025/2026")
        if st.form_submit_button("Submit Result"):
            grade = 'A' if score >= 70 else 'B' if score >= 60 else 'C'
            c.execute("INSERT INTO results (student_id, course, score, grade, session) VALUES (?,?,?,?,?)",
                      (stu_id, course, score, grade, session))
            conn.commit()
            st.success("Result Uploaded!")

def lecturer_dashboard(user):
    st.sidebar.title(f"Lecturer: {user[1]}")
    if st.sidebar.button("Logout"):
        del st.session_state['user']
        st.rerun()
    st.header(f"{user[4]} Department Results")
    df = pd.read_sql_query("SELECT * FROM results", conn)
    st.dataframe(df, use_container_width=True)

# MAIN APP LOGIC
if 'user' not in st.session_state:
    login()
else:
    user = st.session_state['user']
    if user[2] == 'Admin':
        admin_dashboard(user)
    elif user[2] == 'Student':
        student_dashboard(user)
    elif user[2] == 'Lecturer':
        lecturer_dashboard(user)
