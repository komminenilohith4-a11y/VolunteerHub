from flask import Flask, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "supersecretkey"

# database setup
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///volunteer.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# ---------------- MODELS ----------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class Entry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    hours = db.Column(db.Float, nullable=False)

# create database
with app.app_context():
    db.create_all()

# ---------------- HOME ----------------
@app.route("/")
def home():
    if "user_id" not in session:
        return redirect("/login")

    entries = Entry.query.filter_by(user_id=session["user_id"]).all()
    total = sum(e.hours for e in entries)

    html = f"""
    <h1>Volunteer Hours Tracker</h1>
    <p>Logged in as user #{session["user_id"]}</p>

    <h2>Total Hours: {total}</h2>

    <form method="POST" action="/add">
        <input name="name" placeholder="Activity name" required>
        <input name="hours" type="number" step="0.1" placeholder="Hours" required>
        <button>Add</button>
    </form>

    <h3>Your Log</h3>
    """

    for e in entries:
        html += f"""
        <p>
            {e.name} - {e.hours} hours
            <a href="/edit/{e.id}">Edit</a>
            <a href="/delete/{e.id}">Delete</a>
        </p>
        """

    html += '<br><a href="/logout">Logout</a>'
    return html


# ---------------- ADD ----------------
@app.route("/add", methods=["POST"])
def add():
    if "user_id" not in session:
        return redirect("/login")

    entry = Entry(
        user_id=session["user_id"],
        name=request.form["name"],
        hours=float(request.form["hours"])
    )
    db.session.add(entry)
    db.session.commit()

    return redirect("/")


# ---------------- DELETE ----------------
@app.route("/delete/<int:id>")
def delete(id):
    if "user_id" not in session:
        return redirect("/login")

    entry = Entry.query.get(id)

    if entry and entry.user_id == session["user_id"]:
        db.session.delete(entry)
        db.session.commit()

    return redirect("/")


# ---------------- EDIT ----------------
@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):
    if "user_id" not in session:
        return redirect("/login")

    entry = Entry.query.get(id)

    if not entry or entry.user_id != session["user_id"]:
        return redirect("/")

    if request.method == "POST":
        entry.name = request.form["name"]
        entry.hours = float(request.form["hours"])
        db.session.commit()
        return redirect("/")

    return f"""
    <h1>Edit Entry</h1>
    <form method="POST">
        <input name="name" value="{entry.name}" required>
        <input name="hours" type="number" step="0.1" value="{entry.hours}" required>
        <button>Save</button>
    </form>
    <a href="/">Back</a>
    """


# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(username=request.form["username"]).first()

        if user and check_password_hash(user.password, request.form["password"]):
            session["user_id"] = user.id
            return redirect("/")

        return "Invalid login"

    return """
    <h1>Login</h1>
    <form method="POST">
        <input name="username" placeholder="Username">
        <input name="password" type="password" placeholder="Password">
        <button>Login</button>
    </form>
    <a href="/register">Register</a>
    """


# ---------------- REGISTER ----------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        hashed = generate_password_hash(request.form["password"])

        user = User(username=request.form["username"], password=hashed)
        db.session.add(user)
        db.session.commit()

        return redirect("/login")

    return """
    <h1>Register</h1>
    <form method="POST">
        <input name="username" placeholder="Username">
        <input name="password" type="password" placeholder="Password">
        <button>Create Account</button>
    </form>
    """


# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


if __name__ == "__main__":
    app.run(debug=True)