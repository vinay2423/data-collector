from flask import Flask, request, redirect
import sqlite3
import datetime
import os

app = Flask(__name__)

# ---------------------------
# DATABASE PATH
# ---------------------------
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
    conn.execute("""
    CREATE TABLE IF NOT EXISTS remarks(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        text TEXT,
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
@app.route("/", methods=["GET","POST"])
def dashboard():
    conn = db()
    # Handle remarks submission
    msg = ""
    if request.method=="POST":
        text = request.form.get("remark_text","")
        if text.strip():
            conn.execute("INSERT INTO remarks(text,time) VALUES(?,?)",(text,str(datetime.datetime.now())))
            conn.commit()
            msg="<b class='green'>Remark saved!</b>"
    # Fetch remarks
    remarks = conn.execute("SELECT * FROM remarks ORDER BY id DESC").fetchall()
    # Fetch tickets ordered by start date/time
    tickets = conn.execute("SELECT * FROM tickets ORDER BY start DESC").fetchall()
    conn.close()
    
    html = navbar()
    html += f"<h2>Deployment Dashboard</h2>{msg}<br>"
    
    # Personal remarks area
    html += """
    <div style="margin-bottom:30px;">
    <h3>Your Remarks:</h3>
    <form method="post">
        <textarea name="remark_text" rows="3" placeholder="Write your remarks here..."></textarea><br>
        <button class="green-btn">Save Remark</button>
    </form>
    <div style="margin-top:10px;">
    """
    for r in remarks:
        html += f"<div class='card'>{r['text']}<br><small>{r['time']}</small></div>"
    html += "</div></div>"

    # List tickets
    html += "<h3>Tickets by Start Date/Time:</h3><div class='row'>"
    for t in tickets:
        c=color(t["status"])
        html += f"""
        <div class='card col'>
            <h4><span style="width:12px;height:12px;border-radius:50%;display:inline-block;margin-right:6px;background:{c};"></span>{t['bcr']}</h4>
            <p>Status: <span class='{c}'>{t['status']}</span></p>
            <p>Service: {t['service']}</p>
            <p>Namespace: {t['namespace']}</p>
            <p>Stage: {t['stage']}</p>
            <p>Start: {t['start']}</p>
            <p>End: {t['end']}</p>
            <p>Build URL: <a href="{t['build_url']}" target="_blank">{t['build_url']}</a></p>
            <p>Release URL: <a href="{t['release_url']}" target="_blank">{t['release_url']}</a></p>
            <p>Release Branch: {t['release_branch']}</p>
            <p>Build Number: {t['build_number']}</p>
            <p><a href="/edit/{t['id']}">Edit</a></p>
        </div>
        """
    html += "</div>"
    return html

# ---------------------------
# CREATE TICKET
# ---------------------------
@app.route("/create", methods=["GET","POST"])
def create():
    msg=""
    if request.method=="POST":
        bcr = request.form["bcr"]
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
            cur=conn.execute("""
                INSERT INTO tickets
                (bcr,service,namespace,stage,start,end,status,build_url,release_url,release_branch,build_number)
                VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
                (bcr,service,namespace,stage,start,end,"CREATED",build_url,release_url,release_branch,build_number)
            )
            conn.commit()
            log(cur.lastrowid,"CREATED","Ticket created")
            msg="<b class='green'>Ticket created successfully</b>"
        conn.close()

    html = navbar()
    html += f"<h2>Create Deployment Ticket</h2>{msg}"
    # Place form at top-right corner
    html += """
    <div style="display:flex;justify-content:flex-end;margin-bottom:20px;">
        <div style="background:#4CAF50;padding:20px;border-radius:8px;width:400px;">
            <form method="post">
            <div class="row">
                <div class="col">
                    BCR<br><input name="bcr" required><br><br>
                    Service<br><input name="service"><br><br>
                    Namespace<br><input name="namespace"><br><br>
                    Stage<br><input name="stage"><br><br>
                    Start<br><input name="start"><br><br>
                    End<br><input name="end"><br><br>
                </div>
                <div class="col">
                    Build URL<br><input name="build_url"><br><br>
                    Release URL<br><input name="release_url"><br><br>
                    Release Branch<br><input name="release_branch"><br><br>
                    Build Number<br><input name="build_number"><br><br>
                </div>
            </div>
            <button class="green-btn">Create Ticket</button>
            </form>
        </div>
    </div>
    """
    return html

# ---------------------------
# EDIT TICKET
# ---------------------------
@app.route("/edit/<int:id>", methods=["GET","POST"])
def edit(id):
    conn = db()
    ticket = conn.execute("SELECT * FROM tickets WHERE id=?",(id,)).fetchone()
    if request.method=="POST":
        bcr = request.form["bcr"]
        service = request.form["service"]
        namespace = request.form["namespace"]
        stage = request.form["stage"]
        start = request.form["start"]
        end = request.form["end"]
        status = request.form["status"]
        build_url = request.form.get("build_url","")
        release_url = request.form.get("release_url","")
        release_branch = request.form.get("release_branch","")
        build_number = request.form.get("build_number","")
        conn.execute("""
            UPDATE tickets
            SET bcr=?,service=?,namespace=?,stage=?,start=?,end=?,status=?,
                build_url=?,release_url=?,release_branch=?,build_number=?
            WHERE id=?
        """,(bcr,service,namespace,stage,start,end,status,build_url,release_url,release_branch,build_number,id))
        conn.commit()
        log(id,status,"Status updated")
        conn.close()
        return redirect("/tickets")
    # Fallback values
    build_url = ticket["build_url"] if "build_url" in ticket.keys() else ""
    release_url = ticket["release_url"] if "release_url" in ticket.keys() else ""
    release_branch = ticket["release_branch"] if "release_branch" in ticket.keys() else ""
    build_number = ticket["build_number"] if "build_number" in ticket.keys() else ""
    conn.close()

    html = navbar()
    html += "<h2>Edit Ticket</h2>"
    html += """
    <div class="row">
        <div class="col">
            <form method="post">
                BCR<br><input name="bcr" value="{bcr}"><br><br>
                Service<br><input name="service" value="{service}"><br><br>
                Namespace<br><input name="namespace" value="{namespace}"><br><br>
                Stage<br><input name="stage" value="{stage}"><br><br>
                Status<br><input name="status" value="{status}"><br><br>
        </div>
        <div class="col">
                Start<br><input name="start" value="{start}"><br><br>
                End<br><input name="end" value="{end}"><br><br>
                Build URL<br><input name="build_url" value="{build_url}"><br><br>
                Release URL<br><input name="release_url" value="{release_url}"><br><br>
                Release Branch<br><input name="release_branch" value="{release_branch}"><br><br>
                Build Number<br><input name="build_number" value="{build_number}"><br><br>
                <button class="green-btn">Save Changes</button>
            </form>
        </div>
    </div>
    """.format(**ticket, build_url=build_url, release_url=release_url, release_branch=release_branch, build_number=build_number)
    return html

# ---------------------------
# TICKETS TAB (side-by-side)
# ---------------------------
@app.route("/tickets")
def tickets_tab():
    search = request.args.get("q","")
    conn=db()
    rows = conn.execute(
        "SELECT * FROM tickets WHERE bcr LIKE ? ORDER BY start DESC",
        (f"%{search}%",)
    ).fetchall()
    conn.close()
    html=navbar()
    html += """
    <form style="margin-bottom:10px;">
        Search BCR: <input name="q" placeholder="Enter BCR">
        <button>Search</button>
    </form>
    <div class="row">
    """
    for t in rows:
        c=color(t["status"])
        html += f"""
        <div class='card col'>
            <h4><span style="width:12px;height:12px;border-radius:50%;display:inline-block;margin-right:6px;background:{c};"></span>{t['bcr']}</h4>
            <p>Status: <span class='{c}'>{t['status']}</span></p>
            <p>Service: {t['service']}</p>
            <p>Namespace: {t['namespace']}</p>
            <p>Stage: {t['stage']}</p>
            <p>Start: {t['start']}</p>
            <p>End: {t['end']}</p>
            <p>Build URL: <a href="{t['build_url']}" target="_blank">{t['build_url']}</a></p>
            <p>Release URL: <a href="{t['release_url']}" target="_blank">{t['release_url']}</a></p>
            <p>Release Branch: {t['release_branch']}</p>
            <p>Build Number: {t['build_number']}</p>
            <p><a href="/edit/{t['id']}">Edit</a></p>
        </div>
        """
    html += "</div>"
    return html

# ---------------------------
# HISTORY TAB (modern cards)
# ---------------------------
@app.route("/history")
def history():
    search_bcr=request.args.get("q","")
    conn=db()
    query="SELECT t.bcr,h.status,h.note,h.time FROM history h JOIN tickets t ON t.id=h.ticket_id"
    params=[]
    if search_bcr:
        query+=" WHERE t.bcr LIKE ?"
        params=[f"%{search_bcr}%"]
    query+=" ORDER BY h.time DESC"
    rows=conn.execute(query,params).fetchall()
    conn.close()
    html=navbar()
    html += """
    <form style="margin-bottom:10px;">
        Search BCR: <input name="q" placeholder="Enter BCR">
        <button>Search</button>
    </form>
    <div class='row'>
    """
    for r in rows:
        c=color(r["status"])
        html += f"""
        <div class='card col'>
            <h4><span style="width:12px;height:12px;border-radius:50%;display:inline-block;margin-right:6px;background:{c};"></span>{r['bcr']} | {r['status']}</h4>
            <p>Note: {r['note']}</p>
            <p>Time: {r['time']}</p>
        </div>
        """
    html += "</div>"
    return html

# ---------------------------
# RUN SERVER
# ---------------------------
if __name__=="__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
