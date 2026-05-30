from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func, inspect, text


db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    verification_code = db.Column(db.String(6))
    is_verified = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, server_default=func.now())

    applications = db.relationship(
        "Application",
        backref="user",
        cascade="all, delete-orphan",
        lazy=True,
    )


class Application(db.Model):
    __tablename__ = "applications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    company = db.Column(db.String(120), nullable=False)
    position = db.Column(db.String(120), nullable=False)
    status = db.Column(db.String(40), nullable=False)
    date_applied = db.Column(db.String(20), nullable=False)
    notes = db.Column(db.Text)

    def __getitem__(self, key):
        # Keeps existing templates working with application["company"] syntax.
        return getattr(self, key)


def init_database(app):
    db.init_app(app)

    with app.app_context():
        db.create_all()
        inspector = inspect(db.engine)

        if "users" in inspector.get_table_names():
            user_columns = [
                column["name"]
                for column in inspector.get_columns("users")
            ]

            with db.engine.begin() as connection:
                if "email" not in user_columns:
                    connection.execute(text("ALTER TABLE users ADD COLUMN email VARCHAR(255)"))
                if "verification_code" not in user_columns:
                    connection.execute(text("ALTER TABLE users ADD COLUMN verification_code VARCHAR(6)"))
                if "is_verified" not in user_columns:
                    connection.execute(text("ALTER TABLE users ADD COLUMN is_verified BOOLEAN DEFAULT false"))
                    connection.execute(text("UPDATE users SET is_verified = true WHERE is_verified IS NULL"))

        if "applications" in inspector.get_table_names():
            application_columns = [
                column["name"]
                for column in inspector.get_columns("applications")
            ]

            if "user_id" not in application_columns:
                with db.engine.begin() as connection:
                    connection.execute(text("ALTER TABLE applications ADD COLUMN user_id INTEGER"))
