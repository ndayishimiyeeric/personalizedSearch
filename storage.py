import sqlite3
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from flask import Flask
import uuid
import pandas as pd

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///engine.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'mysecretkey'

db = SQLAlchemy(app)


class DBStorage:
    def __init__(self):
        self.con = sqlite3.connect('links.db')
        self.setup_tables()

    def setup_tables(self):
        cur = self.con.cursor()
        cur.execute(
            "CREATE TABLE IF NOT EXISTS results (query text, rank integer, link text, title text, snippet text, html text, created text, relevance integer, PRIMARY KEY (query, rank))")
        self.con.commit()
        cur.close()

    def query_results(self, query):
        df = pd.read_sql(f"select * from results where query='{query}' order by rank asc;", self.con)
        return df

    def insert_row(self, values):
        cur = self.con.cursor()
        try:
            cur.execute(
                "INSERT INTO results (query, rank, link, title, snippet, html, created) VALUES (?, ?, ?, ?, ?, ?, ?)",
                values)
            self.con.commit()
        except sqlite3.IntegrityError:
            pass
        cur.close()

    def update_relevance(self, query, link, relevance):
        cur = self.con.cursor()
        cur.execute(f"UPDATE results SET relevance=? WHERE query=? AND link=?", [relevance, query, link])
        self.con.commit()
        cur.close()


class Link(db.Model):
    __tablename__ = 'links'

    query = db.Column(db.String(100), nullable=False)
    rank = db.Column(db.Integer, nullable=False)
    link = db.Column(db.String(100), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    snippet = db.Column(db.String(100), nullable=False)
    html = db.Column(db.String(100), nullable=False)
    created = db.Column(db.String(100), nullable=False)
    relevance = db.Column(db.Integer, nullable=False, default=0)
    id = db.Column(db.String(100), primary_key=True, default=lambda: str(uuid.uuid4()))

    def __repr__(self):
        return '<Link %r>' % self.link


def is_authenticated():
    return True


class User(db.Model, UserMixin):
    __tablename__ = 'users'
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    is_authenticated = db.Column(db.Boolean, default=True)
    is_anonymous = db.Column(db.Boolean, default=False)
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    def __repr__(self):
        return '<User %r>' % self.username

    def is_authenticated(self):
        return self.is_authenticated

    def is_active(self):
        return self.is_active

    def is_anonymous(self) -> bool:
        return self.is_anonymous

    def get_id(self):
        return str(self.id)
