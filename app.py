from flask import Flask, request, session, render_template, redirect
import sqlite3, random

app = Flask(__name__)
app.secret_key = "secret123"

def init_db():
    conn = sqlite3.connect("db.sqlite3")
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS users (username TEXT, password TEXT, coin INTEGER)")
    conn.commit()
    conn.close()

init_db()

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        u = request.form["username"]
        p = request.form["password"]

        conn = sqlite3.connect("db.sqlite3")
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=? AND password=?", (u,p))
        user = c.fetchone()
        conn.close()

        if user:
            session["user"] = u
            return redirect("/")
        return "Sai tài khoản"

    return render_template("login.html")

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        u = request.form["username"]
        p = request.form["password"]

        conn = sqlite3.connect("db.sqlite3")
        c = conn.cursor()
        c.execute("INSERT INTO users VALUES (?,?,?)", (u,p,0))
        conn.commit()
        conn.close()

        return redirect("/login")

    return render_template("register.html")

def get_coin(user):
    conn = sqlite3.connect("db.sqlite3")
    c = conn.cursor()
    c.execute("SELECT coin FROM users WHERE username=?", (user,))
    coin = c.fetchone()[0]
    conn.close()
    return coin

def update_coin(user, amount):
    conn = sqlite3.connect("db.sqlite3")
    c = conn.cursor()
    c.execute("UPDATE users SET coin=? WHERE username=?", (amount,user))
    conn.commit()
    conn.close()

_hidden = 0

def gk(choice, streak):
    global _hidden
    _hidden += streak * 0.5
    _hidden *= 0.9

    if _hidden > 3:
        if random.random() < 0.8:
            _hidden = 0
            return choice

    if random.random() < 0.33:
        return choice

    return random.randint(0,2)

def mul(streak):
    table = [(1,1.2),(2,1.6),(3,2.2),(4,3.5),(5,5.8)]
    for s,m in reversed(table):
        if streak >= s:
            return m
    return 1

@app.route("/", methods=["GET","POST"])
def index():
    if "user" not in session:
        return redirect("/login")

    user = session["user"]
    coin = get_coin(user)
    msg = ""

    if request.method == "POST":
        action = request.form.get("action")

        if action == "start":
            bet = int(request.form["bet"])
            if bet > coin:
                msg = "Không đủ coin"
            else:
                session["bet"] = bet
                session["cur"] = bet
                session["streak"] = 0
                update_coin(user, coin - bet)

        elif action == "play":
            choice = ["trai","giua","phai"].index(request.form["choice"])
            k = gk(choice, session["streak"])

            if choice == k:
                msg = "❌ Thủ môn bắt trúng!"
                session.clear()
                session["user"] = user
            else:
                session["streak"] += 1
                m = mul(session["streak"])
                session["cur"] = int(session["bet"] * m)
                msg = f"✅ {session['cur']} coin"

        elif action == "stop":
            update_coin(user, coin + session["cur"])
            msg = f"🎉 +{session['cur']}"
            session.clear()
            session["user"] = user

    return render_template("index.html", coin=get_coin(user), cur=session.get("cur",0), playing="bet" in session, msg=msg)

@app.route("/admin", methods=["GET","POST"])
def admin():
    if request.method == "POST":
        u = request.form["user"]
        amount = int(request.form["coin"])

        conn = sqlite3.connect("db.sqlite3")
        c = conn.cursor()
        c.execute("UPDATE users SET coin = coin + ? WHERE username=?", (amount,u))
        conn.commit()
        conn.close()

    return render_template("admin.html")

app.run()
