# ---------------------------
# TICKETS (TIMELINE WITH FILTERS & LINKS)
# ---------------------------
@app.route("/tickets")
def tickets_tab():
    filter_status = request.args.get("status","")
    search = request.args.get("q","")
    conn = db()
    query = "SELECT * FROM tickets"
    params = []
    if search and filter_status:
        query += " WHERE bcr LIKE ? AND status LIKE ?"
        params = [f"%{search}%", f"%{filter_status}%"]
    elif search:
        query += " WHERE bcr LIKE ?"
        params = [f"%{search}%"]
    elif filter_status:
        query += " WHERE status LIKE ?"
        params = [f"%{filter_status}%"]
    query += " ORDER BY id DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()

    html = """
    <h2>Tickets</h2>
    <form style="margin-bottom:10px;">
        Search BCR:
        <input name="q" placeholder="Enter BCR">
        <button>Search</button>
    </form>
    <div style="margin-bottom:15px;">
        Filter by Status:
        <a href="/tickets?status=done" class="green">✔ Done</a> |
        <a href="/tickets?status=deploy" class="orange">🔄 Deploying</a> |
        <a href="/tickets?status=fail" class="red">❌ Fail</a> |
        <a href="/tickets">All</a>
    </div>
    <style>
        .timeline{position:relative;max-width:900px;margin:0 auto;}
        .timeline::after{content:'';position:absolute;width:6px;background:#ddd;top:0;bottom:0;left:50%;margin-left:-3px;}
        .entry{padding:15px 40px;position:relative;background:white;width:45%;border-radius:8px;margin-bottom:20px;box-shadow:0 3px 8px rgba(0,0,0,0.15);transition:transform 0.2s, box-shadow 0.2s;}
        .entry.left{left:0;}
        .entry.right{left:50%;}
        .entry::after{content:"";position:absolute;width:20px;height:20px;background:white;border:4px solid #0077cc;top:20px;right:-10px;border-radius:50%;z-index:1;}
        .entry.right::after{left:-10px;}
        .entry h3{margin:0;font-size:16px;color:#0077cc;display:flex;align-items:center;gap:8px;}
        .entry p{margin:5px 0;font-size:14px;line-height:1.3;}
        .entry:hover{transform:translateY(-5px);box-shadow:0 6px 15px rgba(0,0,0,0.2);}
        .green{color:green;font-weight:bold;}
        .red{color:red;font-weight:bold;}
        .orange{color:orange;font-weight:bold;}
        .blue{color:blue;font-weight:bold;}
        .status-icon{width:12px;height:12px;border-radius:50%;display:inline-block;margin-right:6px;}
        .green-dot{background:green;}
        .red-dot{background:red;}
        .orange-dot{background:orange;}
        .blue-dot{background:blue;}
        a{color:#0077cc;text-decoration:none;}
    </style>
    <div class="timeline">
    """
    side = True
    for r in rows:
        c = color(r["status"])
        cls = "left" if side else "right"
        side = not side
        build_url = r["build_url"] if "build_url" in r.keys() else ""
        release_url = r["release_url"] if "release_url" in r.keys() else ""
        release_branch = r["release_branch"] if "release_branch" in r.keys() else ""
        build_number = r["build_number"] if "build_number" in r.keys() else ""
        html += f"""
        <div class="entry {cls}">
            <h3><span class="status-icon {c}-dot"></span>
                <a href="/history?q={r['bcr']}">{r['bcr']}</a>
            </h3>
            <p><b>Status:</b> <span class="{c}">{r['status']}</span></p>
            <p><b>Service:</b> {r['service']}</p>
            <p><b>Namespace:</b> {r['namespace']}</p>
            <p><b>Stage:</b> {r['stage']}</p>
            <p><b>Start:</b> {r['start']}</p>
            <p><b>End:</b> {r['end']}</p>
            <p><b>Build URL:</b> <a href="{build_url}" target="_blank">{build_url}</a></p>
            <p><b>Release URL:</b> <a href="{release_url}" target="_blank">{release_url}</a></p>
            <p><b>Release Branch:</b> {release_branch}</p>
            <p><b>Build Number:</b> {build_number}</p>
            <p><a href="/edit/{r['id']}">Edit Ticket</a></p>
        </div>
        """
    html += "</div>"
    return navbar() + html

# ---------------------------
# HISTORY (FILTERABLE & LINKABLE)
# ---------------------------
@app.route("/history")
def history():
    search_bcr = request.args.get("q","")
    conn = db()
    query = """
        SELECT t.bcr, h.status, h.note, h.time
        FROM history h
        JOIN tickets t ON t.id=h.ticket_id
    """
    params = []
    if search_bcr:
        query += " WHERE t.bcr LIKE ?"
        params = [f"%{search_bcr}%"]
    query += " ORDER BY h.time DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()

    html = """
    <h2>Status History</h2>
    <form>
        Filter by BCR:
        <input name="q" placeholder="Enter BCR" value="{search}">
        <button>Search</button>
    </form>
    <style>
        .timeline{position:relative;max-width:800px;margin:0 auto;}
        .timeline::after{content:'';position:absolute;width:6px;background:#ddd;top:0;bottom:0;left:50%;margin-left:-3px;}
        .entry{padding:10px 40px;position:relative;background:white;width:50%;border-radius:6px;margin-bottom:20px;box-shadow:0 2px 5px rgba(0,0,0,0.1);transition:transform 0.2s;}
        .entry.left{left:0;}
        .entry.right{left:50%;}
        .entry::after{content:"";position:absolute;width:20px;height:20px;background:white;border:4px solid #0077cc;top:15px;right:-10px;border-radius:50%;z-index:1;}
        .entry.right::after{left:-10px;}
        .entry h3{margin:0;font-size:16px;color:#0077cc;display:flex;align-items:center;gap:8px;}
        .entry p{margin:5px 0;font-size:14px;}
        .entry:hover{transform:translateY(-3px);box-shadow:0 5px 12px rgba(0,0,0,0.15);}
        .green{color:green;font-weight:bold;}
        .red{color:red;font-weight:bold;}
        .orange{color:orange;font-weight:bold;}
        .blue{color:blue;font-weight:bold;}
        .status-icon{width:12px;height:12px;border-radius:50%;display:inline-block;margin-right:6px;}
        .green-dot{background:green;}
        .red-dot{background:red;}
        .orange-dot{background:orange;}
        .blue-dot{background:blue;}
        a{color:#0077cc;text-decoration:none;}
    </style>
    <div class="timeline">
    """
    side = True
    for r in rows:
        c = color(r["status"])
        cls = "left" if side else "right"
        side = not side
        html += f"""
        <div class="entry {cls}">
            <h3><span class="status-icon {c}-dot"></span>
                <a href="/tickets?q={r['bcr']}">{r['bcr']}</a> | <span class="{c}">{r['status']}</span>
            </h3>
            <p><b>Note:</b> {r['note']}</p>
            <p><b>Time:</b> {r['time']}</p>
        </div>
        """
    html += "</div>"
    return navbar() + html.format(search=search_bcr)
