from flask import Flask, request, redirect
import sqlite3
import datetime

app = Flask(__name__)

DB = "esp1.db"


# -------------------------------
# DATABASE CONNECTION
# -------------------------------
def db():
    return sqlite3.connect(DB)


# -------------------------------
# INIT DATABASE
# -------------------------------
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
        status TEXT
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


# -------------------------------
# HISTORY LOGGER
# -------------------------------
def log(ticket_id, status, note):
    conn = db()

    conn.execute("""
    INSERT INTO history(ticket_id,status,note,time)
    VALUES(?,?,?,?)
    """,
    (ticket_id, status, note, str(datetime.datetime.now()))
    )

    conn.commit()
    conn.close()


# -------------------------------
# NAVBAR
# -------------------------------
def navbar():
    return """
    <h1>ESP.1 Deployment Tracker</h1>
    <hr>
    <a href="/">Create Ticket</a> |
    <a href="/tickets">Tickets</a> |
    <a href="/history">History</a>
    <hr><br>
    """


# -------------------------------
# CREATE PAGE
# -------------------------------
@app.route("/", methods=["GET","POST"])
def create():

    msg=""

    if request.method == "POST":

        bcr=request.form["bcr"]
        service=request.form["service"]
        namespace=request.form["namespace"]
        stage=request.form["stage"]
        start=request.form["start"]
        end=request.form["end"]

        conn=db()

        # Duplicate check
        exist=conn.execute(
            "SELECT * FROM tickets WHERE bcr=?",
            (bcr,)
        ).fetchone()

        if exist:
            msg="<b style='color:red'>BCR already exists</b>"

        else:

            cur=conn.execute("""
            INSERT INTO tickets(bcr,service,namespace,stage,start,end,status)
            VALUES(?,?,?,?,?,?,?)
            """,
            (bcr,service,namespace,stage,start,end,"CREATED")
            )

            conn.commit()

            ticket_id=cur.lastrowid

            log(ticket_id,"CREATED","Ticket created")

            msg="<b style='color:green'>Ticket Created</b>"

        conn.close()

    return navbar()+f"""

    <h2>Create Deployment Ticket</h2>

    {msg}

    <form method="post">

    BCR<br>
    <input name="bcr" required><br><br>

    Service<br>
    <input name="service"><br><br>

    Namespace<br>
    <input name="namespace"><br><br>

    Stage<br>
    <input name="stage"><br><br>

    Start Time<br>
    <input name="start"><br><br>

    End Time<br>
    <input name="end"><br><br>

    <button>Create Ticket</button>

    </form>
    """


# -------------------------------
# LIST ALL TICKETS TAB
# -------------------------------
@app.route("/tickets")
def tickets():

    conn=db()

    rows=conn.execute(
        "SELECT * FROM tickets ORDER BY id DESC"
    ).fetchall()

    conn.close()

    html="""
    <h2>All BCR Tickets</h2>

    <table border=1 cellpadding=8>
    <tr>
    <th>BCR</th>
    <th>Service</th>
    <th>Namespace</th>
    <th>Stage</th>
    <th>Status</th>
    <th>Action</th>
    </tr>
    """

    for r in rows:

        html+=f"""
        <tr>
        <td>{r[1]}</td>
        <td>{r[2]}</td>
        <td>{r[3]}</td>
        <td>{r[4]}</td>
        <td>{r[7]}</td>
        <td>
        <a href='/edit/{r[0]}'>Edit</a>
        </td>
        </tr>
        """

    html+="</table>"

    return navbar()+html


# -------------------------------
# EDIT TICKET
# -------------------------------
@app.route("/edit/<int:id>", methods=["GET","POST"])
def edit(id):

    conn=db()

    if request.method=="POST":

        bcr=request.form["bcr"]
        service=request.form["service"]
        namespace=request.form["namespace"]
        stage=request.form["stage"]
        start=request.form["start"]
        end=request.form["end"]
        status=request.form["status"]

        conn.execute("""
        UPDATE tickets
        SET bcr=?,service=?,namespace=?,stage=?,start=?,end=?,status=?
        WHERE id=?
        """,
        (bcr,service,namespace,stage,start,end,status,id)
        )

        conn.commit()

        log(id,status,"Status updated")

        conn.close()

        return redirect("/tickets")

    ticket=conn.execute(
        "SELECT * FROM tickets WHERE id=?",
        (id,)
    ).fetchone()

    conn.close()

    return navbar()+f"""

    <h2>Edit Ticket</h2>

    <form method="post">

    BCR<br>
    <input name="bcr" value="{ticket[1]}"><br><br>

    Service<br>
    <input name="service" value="{ticket[2]}"><br><br>

    Namespace<br>
    <input name="namespace" value="{ticket[3]}"><br><br>

    Stage<br>
    <input name="stage" value="{ticket[4]}"><br><br>

    Start<br>
    <input name="start" value="{ticket[5]}"><br><br>

    End<br>
    <input name="end" value="{ticket[6]}"><br><br>

    Status<br>
    <input name="status" value="{ticket[7]}"><br><br>

    <button>Save</button>

    </form>
    """


# -------------------------------
# HISTORY TAB
# -------------------------------
@app.route("/history")
def history():

    conn=db()

    rows=conn.execute("""
    SELECT h.ticket_id,t.bcr,h.status,h.note,h.time
    FROM history h
    JOIN tickets t ON h.ticket_id=t.id
    ORDER BY h.id DESC
    """).fetchall()

    conn.close()

    html="""
    <h2>Status History</h2>

    <table border=1 cellpadding=8>
    <tr>
    <th>BCR</th>
    <th>Status</th>
    <th>Note</th>
    <th>Time</th>
    </tr>
    """

    for r in rows:

        html+=f"""
        <tr>
        <td>{r[1]}</td>
        <td>{r[2]}</td>
        <td>{r[3]}</td>
        <td>{r[4]}</td>
        </tr>
        """

    html+="</table>"

    return navbar()+html


# -------------------------------
# RUN APP
# -------------------------------
if __name__=="__main__":
    app.run(debug=True)
