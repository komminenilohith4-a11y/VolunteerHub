from flask import Flask, request, redirect, session, render_template
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "supersecretkey"

# Database setup
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


# Create database
with app.app_context():
    db.create_all()


# ---------------- HOME ----------------

@app.route("/")
def home():
    if "user_id" not in session:
        return redirect("/login")

    entries = Entry.query.filter_by(user_id=session["user_id"]).all()
    total = sum(e.hours for e in entries)

    return render_template(
        "home.html",
        entries=entries,
        total=total
    )


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

    return render_template("edit.html", entry=entry)


# ---------------- LOGIN ----------------

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(
            username=request.form["username"]
        ).first()

        if user and check_password_hash(
            user.password,
            request.form["password"]
        ):
            session["user_id"] = user.id
            return redirect("/")

        return "Invalid login"

    return render_template("login.html")


# ---------------- REGISTER ----------------

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        hashed = generate_password_hash(
            request.form["password"]
        )

        user = User(
            username=request.form["username"],
            password=hashed
        )

        db.session.add(user)
        db.session.commit()

        return redirect("/login")

    return render_template("register.html")


# ---------------- LOGOUT ----------------

@app.route("/logout")
def logout():
    session.clear()

    return redirect("/login")


if __name__ == "__main__":
    app.run(debug=True)
