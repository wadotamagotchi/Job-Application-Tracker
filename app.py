import os
from functools import wraps

from flask import Flask, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from database import Application, User, db, init_database


try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None


if load_dotenv:
    load_dotenv()


BASE_DIR = os.path.abspath(os.path.dirname(__file__))


def get_database_url():
    database_url = os.environ.get("DATABASE_URL")

    if not database_url:
        sqlite_path = os.path.join(BASE_DIR, "applications.db").replace("\\", "/")
        return f"sqlite:///{sqlite_path}"

    if database_url.startswith("postgres://"):
        return database_url.replace("postgres://", "postgresql+psycopg://", 1)

    if database_url.startswith("postgresql://"):
        return database_url.replace("postgresql://", "postgresql+psycopg://", 1)

    return database_url


# Create the Flask application object.
app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY",
    "dev-secret-key-change-before-deployment",
)
app.config["SQLALCHEMY_DATABASE_URI"] = get_database_url()
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Connect SQLAlchemy to the app and create database tables if needed.
init_database(app)


def login_required(route_function):
    # This decorator protects pages that should only be used after sign-in.
    @wraps(route_function)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            flash("Please sign in to continue.", "error")
            return redirect(url_for("login"))

        return route_function(*args, **kwargs)

    return wrapper


@app.route("/register", methods=["GET", "POST"])
def register():
    # Create a new account and store a hashed password.
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if not username or not password:
            flash("Username and password are required.", "error")
            return render_template("register.html")

        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return render_template("register.html")

        existing_user = User.query.filter_by(username=username).first()

        if existing_user:
            flash("That username is already taken.", "error")
            return render_template("register.html")

        user = User(
            username=username,
            password_hash=generate_password_hash(password),
        )

        db.session.add(user)
        db.session.commit()

        flash("Account created. You can sign in now.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    # Check the username and password, then save the user id in the session.
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]

        user = User.query.filter_by(username=username).first()

        if not user or not check_password_hash(user.password_hash, password):
            flash("Invalid username or password.", "error")
            return render_template("login.html")

        session.clear()
        session["user_id"] = user.id
        session["username"] = user.username

        return redirect(url_for("index"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    # Clear the session so the current user is signed out.
    session.clear()
    flash("You have been signed out.", "success")
    return redirect(url_for("login"))


@app.route("/")
@login_required
def index():
    # Read only the applications owned by the signed-in user.
    applications = (
        Application.query
        .filter_by(user_id=session["user_id"])
        .order_by(Application.id.desc())
        .all()
    )

    status_counts = {
        "Applied": 0,
        "Interview": 0,
        "Offer": 0,
        "Rejected": 0,
    }

    for application in applications:
        if application.status in status_counts:
            status_counts[application.status] += 1

    # Send the applications list to index.html so it can display the table.
    return render_template(
        "index.html",
        applications=applications,
        status_counts=status_counts,
    )


@app.route("/add", methods=["GET", "POST"])
@login_required
def add_application():
    # POST means the user submitted the add form.
    if request.method == "POST":
        application = Application(
            user_id=session["user_id"],
            company=request.form["company"],
            position=request.form["position"],
            status=request.form["status"],
            date_applied=request.form["date_applied"],
            notes=request.form["notes"],
        )

        db.session.add(application)
        db.session.commit()

        # After saving, go back to the homepage.
        return redirect(url_for("index"))

    # GET means the user is opening the blank add form.
    return render_template("add.html")


@app.route("/edit/<int:application_id>", methods=["GET", "POST"])
@login_required
def edit_application(application_id):
    # Load only an application owned by the signed-in user.
    application = Application.query.filter_by(
        id=application_id,
        user_id=session["user_id"],
    ).first()

    # POST means the user submitted the edit form.
    if request.method == "POST":
        if not application:
            return render_template("edit.html", application=None)

        application.company = request.form["company"]
        application.position = request.form["position"]
        application.status = request.form["status"]
        application.date_applied = request.form["date_applied"]
        application.notes = request.form["notes"]

        db.session.commit()

        return redirect(url_for("index"))

    # GET means the user is opening the edit page.
    return render_template("edit.html", application=application)


@app.route("/delete/<int:application_id>", methods=["POST"])
@login_required
def delete_application(application_id):
    # Delete only an application owned by the signed-in user.
    application = Application.query.filter_by(
        id=application_id,
        user_id=session["user_id"],
    ).first()

    if application:
        db.session.delete(application)
        db.session.commit()

    return redirect(url_for("index"))


if __name__ == "__main__":
    # Run the app locally when this file is started directly.
    app.run(debug=True)
