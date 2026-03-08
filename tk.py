@app.route("/tickets")
def tickets():
    search = request.args.get("q", "")
    conn = db()
    if search:
        rows = conn.execute("SELECT * FROM tickets WHERE bcr LIKE ?", ("%"+search+"%",)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM tickets ORDER BY id DESC").fetchall()
    conn.close()

    html = """
    <h2>Tickets</h2>
    <form>
        Search BCR:
        <input name="q" placeholder="Enter BCR">
        <button>Search</button>
    </form>
    <br>
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
            <h3><span class="status-icon {c}-dot"></span>BCR: {r['bcr']}</h3>
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
