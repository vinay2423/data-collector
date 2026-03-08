from flask import Flask, request, redirect
import sqlite3
import datetime
import os

app = Flask(__name__)

DB = os.path.join(os.path.dirname(__file__), "esp1.db")

# ---------------------------
# DATABASE CONNECTION
# ---------------------------
def db():
    conn = sqlite3.connect(DB, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

# ---------------------------
# DATABASE INIT
# ---------------------------
def init():
    conn = db()
    conn.execute("""
    CREATE TABLE IF NOT EXISTS tickets(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bcr TEXT UNIQUE,
        requestor TEXT,
        service TEXT,
        namespace TEXT,
        stage TEXT,
        start TEXT,
        end TEXT,
        status TEXT,
        build_url TEXT,
        release_url TEXT,
        release_branch TEXT,
        build_number TEXT
    )
    """)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS history(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticket_id INTEGER,
        status TEXT,
        note TEXT,
        time TEXT
    )
    """)
    conn.commit()
    conn.close()

init()

# ---------------------------
# HISTORY LOGGER
# ---------------------------
def log(ticket_id, status, note):
    conn = db()
    conn.execute(
        "INSERT INTO history(ticket_id,status,note,time) VALUES(?,?,?,?)",
        (ticket_id, status, note, str(datetime.datetime.now()))
    )
    conn.commit()
    conn.close()

# ---------------------------
# NAVBAR
# ---------------------------
def navbar():
    return """
    <style>
    body{font-family:Arial;margin:40px;background:#f7f7f7}
    h1{color:#333}
    .nav a{margin-right:20px;text-decoration:none;font-weight:bold;color:#0077cc;}
    input, textarea{padding:6px;width:100%;}
    button{padding:6px 12px;margin-top:5px;}
    .row{display:flex;gap:20px;flex-wrap:wrap;}
    .col{flex:1;min-width:250px;}
    .card{background:white;padding:15px;border-radius:8px;box-shadow:0 3px 8px rgba(0,0,0,0.15);margin-bottom:20px;}
    .green-btn{background:#4CAF50;color:white;padding:10px 15px;border:none;border-radius:5px;cursor:pointer;}
    .green{color:green;font-weight:bold;}
    .red{color:red;font-weight:bold;}
    .orange{color:orange;font-weight:bold;}
    .blue{color:blue;font-weight:bold;}
    table{border-collapse:collapse;width:100%;background:white;}
    td,th{border:1px solid #ddd;padding:8px;text-align:left;}
    th{background:#f0f0f0}
    </style>
    <h1>ESP.1 Deployment Tracker</h1>
    <div class="nav">
        <a href="/">Dashboard</a>
        <a href="/create">Create Ticket</a>
        <a href="/tickets">Tickets</a>
        <a href="/history">History</a>
    </div>
    <hr><br>
    """

# ---------------------------
# STATUS COLOR
# ---------------------------
def color(status):
    s = status.lower()
    if "fail" in s: return "red"
    if "deploy" in s: return "orange"
    if "done" in s or "complete" in s: return "green"
    return "blue"

# ---------------------------
# DASHBOARD
# ---------------------------
@app.route("/")
def dashboard():
    conn = db()
    tickets = conn.execute("SELECT * FROM tickets ORDER BY datetime(start) ASC").fetchall()
    conn.close()
    html = navbar()
    html += "<h2>Deployment Dashboard (Sorted by Start Time)</h2>"
    html += "<table><tr><th>BCR</th><th>Requestor</th><th>Start</th><th>End</th><th>Status</th></tr>"
    for t in tickets:
        c = color(t["status"])
        html += f"<tr><td>{t['bcr']}</td><td>{t['requestor']}</td><td>{t['start']}</td><td>{t['end']}</td><td class='{c}'>{t['status']}</td></tr>"
    html += "</table>"
    return html

# ---------------------------
# CREATE TICKET
# ---------------------------
@app.route("/create", methods=["GET","POST"])
def create():
    msg=""
    if request.method=="POST":
        bcr = request.form["bcr"]
        requestor = request.form["requestor"]
        service = request.form["service"]
        namespace = request.form["namespace"]
        stage = request.form["stage"]
        start = request.form["start"]
        end = request.form["end"]
        build_url = request.form.get("build_url","")
        release_url = request.form.get("release_url","")
        release_branch = request.form.get("release_branch","")
        build_number = request.form.get("build_number","")
        conn=db()
        exist = conn.execute("SELECT * FROM tickets WHERE bcr=?",(bcr,)).fetchone()
        if exist: msg="<b class='red'>BCR already exists</b>"
        else:
            cur = conn.execute("""
                INSERT INTO tickets
                (bcr,requestor,service,namespace,stage,start,end,status,build_url,release_url,release_branch,build_number)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
                (bcr,requestor,service,namespace,stage,start,end,"CREATED",build_url,release_url,release_branch,build_number)
            )
            conn.commit()
            log(cur.lastrowid,"CREATED","Ticket created")
            msg="<b class='green'>Ticket created successfully</b>"
        conn.close()
    html = navbar()
    html += f"<h2>Create Deployment Ticket</h2>{msg}"
    html += """
    <div style="display:flex;justify-content:flex-end;margin-bottom:20px;">
        <div style="width:400px;">
            <form method="post">
            <b style='color:white;'>Create Ticket</b><br>
            Requestor<br><input name="requestor"><br><br>
            BCR<br><input name="bcr" required><br><br>
            Start<br><input name="start" placeholder="YYYY-MM-DD HH:MM:SS"><br><br>
            End<br><input name="end" placeholder="YYYY-MM-DD HH:MM:SS"><br><br>
            <button class="green-btn">Create Ticket</button>
            </form>
        </div>
    </div>
    """
    return html

# ---------------------------
# TICKETS TAB
# ---------------------------
@app.route("/tickets")
def tickets_tab():
    search = request.args.get("q","")
    conn = db()
    if search:
        rows = conn.execute("SELECT * FROM tickets WHERE bcr LIKE ?",("%"+search+"%",)).fetchall()
    else:
        rows = conn.execute("SELECT bcr,requestor,start,end FROM tickets ORDER BY datetime(start) ASC").fetchall()
    conn.close()
    html = navbar()
    html += "<form>Search BCR: <input name='q'><button>Search</button></form><br>"
    if search:
        for t in rows:
            c=color(t["status"])
            html += f"<div class='card col'>"
            html += f"<h4>{t['bcr']}</h4>"
            for k in t.keys():
                html += f"<p>{k}: {t[k]}</p>"
            html += f"<p><a href='/edit/{t['id']}'>Edit</a></p></div>"
    else:
        html += "<table><tr><th>BCR</th><th>Requestor</th><th>Start</th><th>End</th></tr>"
        for t in rows:
            html += f"<tr><td>{t['bcr']}</td><td>{t['requestor']}</td><td>{t['start']}</td><td>{t['end']}</td></tr>"
        html += "</table>"
    return html

# ---------------------------
# HISTORY TAB
# ---------------------------
@app.route("/history")
def history():
    conn = db()
    rows = conn.execute("""
        SELECT t.bcr,h.status,h.note,h.time
        FROM history h JOIN tickets t ON t.id=h.ticket_id
        ORDER BY h.time DESC
    """).fetchall()
    conn.close()
    html = navbar()
    html += "<h2>History</h2><div class='row'>"
    for r in rows:
        c=color(r["status"])
        html += f"<div class='card col'>"
        html += f"<h4>{r['bcr']} | <span class='{c}'>{r['status']}</span></h4>"
        html += f"<p>Note: {r['note']}</p><p>Time: {r['time']}</p></div>"
    html += "</div>"
    return html

# ---------------------------
# EDIT TICKET
# ---------------------------
@app.route("/edit/<int:id>", methods=["GET","POST"])
def edit(id):
    conn = db()
    ticket = conn.execute("SELECT * FROM tickets WHERE id=?",(id,)).fetchone()
    if request.method=="POST":
        fields = ["bcr","requestor","service","namespace","stage","start","end","status","build_url","release_url","release_branch","build_number"]
        values = [request.form.get(f,"") for f in fields]
        conn.execute(f"UPDATE tickets SET {','.join([f'{f}=?' for f in fields])} WHERE id=?",values+[id])
        conn.commit()
        log(id,request.form.get("status",""),"Status updated")
        conn.close()
        return redirect("/tickets")
    html = navbar()
    html += "<h2>Edit Ticket</h2>"
    html += "<form method='post'>"
    for f in ticket.keys():
        html += f"{f}<br><input name='{f}' value='{ticket[f]}'><br><br>"
    html += "<button class='green-btn'>Save Changes</button></form>"
    conn.close()
    return html

# ---------------------------
# RUN SERVER
# ---------------------------
if __name__=="__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
