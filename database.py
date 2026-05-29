from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func


db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
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

        if app.config["SQLALCHEMY_DATABASE_URI"].startswith("sqlite:///"):
            inspector = db.inspect(db.engine)

            if "applications" in inspector.get_table_names():
                columns = [
                    column["name"]
                    for column in inspector.get_columns("applications")
                ]

                if "user_id" not in columns:
                    with db.engine.begin() as connection:
                        connection.exec_driver_sql(
                            "ALTER TABLE applications ADD COLUMN user_id INTEGER"
                        )
