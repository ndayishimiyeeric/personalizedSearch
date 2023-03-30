from flask_sqlalchemy import SQLAlchemy
from flask import Flask

# if request.method == 'POST':
#    query = request.form['query']
#    return run_search(query)
# return show_search_form()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///engine.db'
app.secret_key = 'mysecretkey'

db = SQLAlchemy(app)


def create_app():
    db.init_app(app)
    return app
