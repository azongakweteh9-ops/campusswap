"""CampusSwap backend: Flask + SQLite REST API."""
import sqlite3, os
from functools import wraps
from flask import Flask, g, jsonify, request, session
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__, static_folder="static", static_url_path="")
app.secret_key = os.environ.get("SECRET_KEY", "dev-only-change-me")
DB = os.path.join(os.path.dirname(__file__), "campusswap.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS users(
  id INTEGER PRIMARY KEY, name TEXT NOT NULL, email TEXT UNIQUE NOT NULL,
  pw_hash TEXT NOT NULL, role TEXT NOT NULL DEFAULT 'student');
CREATE TABLE IF NOT EXISTS items(
  id INTEGER PRIMARY KEY, title TEXT NOT NULL, description TEXT, category TEXT,
  type TEXT CHECK(type IN ('sell','borrow')), price REAL DEFAULT 0,
  status TEXT DEFAULT 'Available', owner_id INTEGER REFERENCES users(id));
CREATE TABLE IF NOT EXISTS transactions(
  id INTEGER PRIMARY KEY, item_id INTEGER REFERENCES items(id),
  borrower_id INTEGER REFERENCES users(id), status TEXT DEFAULT 'Pending',
  created TEXT DEFAULT CURRENT_DATE);
"""

def db():
    if "db" not in g:
        g.db = sqlite3.connect(DB); g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close(_):
    d = g.pop("db", None)
    if d: d.close()

def init():
    with sqlite3.connect(DB) as c:
        c.executescript(SCHEMA)
        if not c.execute("SELECT 1 FROM users").fetchone():
            c.execute("INSERT INTO users(name,email,pw_hash,role) VALUES(?,?,?,?)",
                      ("Admin", "admin@campus.edu", generate_password_hash("admin"), "admin"))

def rows(sql, *a): return [dict(r) for r in db().execute(sql, a).fetchall()]
def err(msg, code=400): return jsonify(error=msg), code

def login_required(f):
    @wraps(f)
    def w(*a, **k):
        if "uid" not in session: return err("Log in first.", 401)
        return f(*a, **k)
    return w

def is_admin():
    r = db().execute("SELECT role FROM users WHERE id=?", (session["uid"],)).fetchone()
    return r and r["role"] == "admin"

@app.get("/")
def home(): return app.send_static_file("index.html")

# ---- Auth ----
@app.get("/api/me")
@login_required
def me():
    r = db().execute("SELECT id,name,email,role FROM users WHERE id=?", (session["uid"],)).fetchone()
    return jsonify(dict(r)) if r else err("Log in first.", 401)

@app.get("/api/users")
@login_required
def users():
    if not is_admin(): return err("Admins only.", 403)
    return jsonify(rows("SELECT id,name,email,role FROM users"))

@app.post("/api/register")
def register():
    d = request.get_json(force=True)
    email = (d.get("email") or "").strip().lower()
    if not email.endswith(".edu"): return err("Use your campus .edu email.")
    if len(d.get("password") or "") < 6: return err("Password needs 6+ characters.")
    if not (d.get("name") or "").strip(): return err("Name is required.")
    try:
        cur = db().execute("INSERT INTO users(name,email,pw_hash) VALUES(?,?,?)",
                           (d["name"].strip(), email, generate_password_hash(d["password"])))
        db().commit()
    except sqlite3.IntegrityError:
        return err("That email already has an account.", 409)
    session["uid"] = cur.lastrowid
    return jsonify(id=cur.lastrowid, name=d["name"]), 201

@app.post("/api/login")
def login():
    d = request.get_json(force=True)
    u = db().execute("SELECT * FROM users WHERE email=?", ((d.get("email") or "").lower(),)).fetchone()
    if not u or not check_password_hash(u["pw_hash"], d.get("password") or ""):
        return err("Email or password is wrong.", 401)
    session["uid"] = u["id"]
    return jsonify(id=u["id"], name=u["name"], role=u["role"])

@app.post("/api/logout")
def logout():
    session.clear(); return jsonify(ok=True)

# ---- Items (CRUD) ----
@app.get("/api/items")
def list_items():
    q, cat, typ = request.args.get("q", ""), request.args.get("category"), request.args.get("type")
    sql, a = "SELECT i.*, u.name AS owner FROM items i JOIN users u ON u.id=i.owner_id WHERE (i.title LIKE ? OR i.description LIKE ?)", [f"%{q}%"] * 2
    if cat: sql += " AND i.category=?"; a.append(cat)
    if typ: sql += " AND i.type=?"; a.append(typ)
    return jsonify(rows(sql + " ORDER BY i.id DESC", *a))

@app.get("/api/items/<int:i>")
def get_item(i):
    r = rows("SELECT i.*, u.name AS owner FROM items i JOIN users u ON u.id=i.owner_id WHERE i.id=?", i)
    return jsonify(r[0]) if r else err("Item not found.", 404)

@app.post("/api/items")
@login_required
def create_item():
    d = request.get_json(force=True)
    if not (d.get("title") or "").strip() or d.get("type") not in ("sell", "borrow"):
        return err("Title and type (sell or borrow) are required.")
    cur = db().execute("INSERT INTO items(title,description,category,type,price,owner_id) VALUES(?,?,?,?,?,?)",
        (d["title"].strip(), d.get("description", ""), d.get("category", "Other"), d["type"],
         max(0, float(d.get("price") or 0)), session["uid"]))
    db().commit()
    return jsonify(id=cur.lastrowid), 201

@app.put("/api/items/<int:i>")
@login_required
def update_item(i):
    it = db().execute("SELECT owner_id FROM items WHERE id=?", (i,)).fetchone()
    if not it: return err("Item not found.", 404)
    if it["owner_id"] != session["uid"]: return err("Only the owner can edit this.", 403)
    d = request.get_json(force=True)
    db().execute("UPDATE items SET title=COALESCE(?,title), description=COALESCE(?,description), "
                 "category=COALESCE(?,category), price=COALESCE(?,price) WHERE id=?",
                 (d.get("title"), d.get("description"), d.get("category"), d.get("price"), i))
    db().commit(); return jsonify(ok=True)

@app.delete("/api/items/<int:i>")
@login_required
def delete_item(i):
    it = db().execute("SELECT owner_id FROM items WHERE id=?", (i,)).fetchone()
    if not it: return err("Item not found.", 404)
    if it["owner_id"] != session["uid"] and not is_admin(): return err("Not allowed.", 403)
    db().execute("DELETE FROM transactions WHERE item_id=?", (i,))
    db().execute("DELETE FROM items WHERE id=?", (i,)); db().commit()
    return jsonify(ok=True)

# ---- Transactions: Pending -> Approved/Declined -> Returned ----
@app.post("/api/items/<int:i>/request")
@login_required
def make_request(i):
    it = db().execute("SELECT * FROM items WHERE id=?", (i,)).fetchone()
    if not it: return err("Item not found.", 404)
    if it["owner_id"] == session["uid"]: return err("You can't request your own item.")
    if it["status"] != "Available": return err("Item is not available.", 409)
    if db().execute("SELECT 1 FROM transactions WHERE item_id=? AND borrower_id=? AND status='Pending'",
                    (i, session["uid"])).fetchone():
        return err("You already have a pending request.", 409)
    cur = db().execute("INSERT INTO transactions(item_id,borrower_id) VALUES(?,?)", (i, session["uid"]))
    db().commit(); return jsonify(id=cur.lastrowid), 201

@app.patch("/api/transactions/<int:t>")
@login_required
def update_tx(t):
    s = (request.get_json(force=True).get("status"))
    tx = db().execute("SELECT t.*, i.owner_id, i.type FROM transactions t JOIN items i ON i.id=t.item_id WHERE t.id=?", (t,)).fetchone()
    if not tx: return err("Request not found.", 404)
    if tx["owner_id"] != session["uid"]: return err("Only the item owner can do this.", 403)
    allowed = {"Pending": ("Approved", "Declined"), "Approved": ("Returned",)}
    if s not in allowed.get(tx["status"], ()): return err(f"Can't go from {tx['status']} to {s}.")
    db().execute("UPDATE transactions SET status=? WHERE id=?", (s, t))
    if s == "Approved":
        db().execute("UPDATE items SET status=? WHERE id=?", ("Sold" if tx["type"] == "sell" else "Borrowed", tx["item_id"]))
        db().execute("UPDATE transactions SET status='Declined' WHERE item_id=? AND id!=? AND status='Pending'", (tx["item_id"], t))
    if s == "Returned":
        db().execute("UPDATE items SET status='Available' WHERE id=?", (tx["item_id"],))
    db().commit(); return jsonify(ok=True)

@app.get("/api/dashboard")
@login_required
def dashboard():
    u = session["uid"]
    return jsonify(
        listings=rows("SELECT * FROM items WHERE owner_id=?", u),
        incoming=rows("SELECT t.*, i.title, b.name AS borrower FROM transactions t JOIN items i ON i.id=t.item_id "
                      "JOIN users b ON b.id=t.borrower_id WHERE i.owner_id=?", u),
        outgoing=rows("SELECT t.*, i.title FROM transactions t JOIN items i ON i.id=t.item_id WHERE t.borrower_id=?", u))

if __name__ == "__main__":
    init(); app.run(debug=True)
