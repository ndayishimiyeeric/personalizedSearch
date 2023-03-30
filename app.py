from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask import jsonify, Flask, render_template, request, redirect, url_for, flash, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from search import search
from filter import Filter
from storage import DBStorage, User, app, db
import html
from forms import RegisterForm, LoginForm, SearchForm

app.app_context().push()
db.create_all()

login = LoginManager(app)
login.login_view = 'login'

styles = """
<style>
    .site {
        font-size: .8rem;
        color: green;
    }

    .snippet {
        font-size: .9rem;
        color: gray;
        margin-bottom: 1rem;
    }

    .rel_button {
        cursor: pointer;
        color: blue;
    }
</style>
<script>
    const relevant = (query, link) => {
        fetch('/relevance', {
            method: 'POST',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                "query": query,
                "link": link,
            })
        })
    };
</script>
"""

search_template = styles + """
<form action="/" method="post">
    <input type="text" name="query">
    <input type="submit" value="Search">
</form>
"""

result_template = """
<p class="site">{rank}: {link} <span class="rel_button" onclick='relevant("{query}", "{link}");'>Relevant</span></p>
<a href="{link}">{title}</a>
<p class="snippet">{snippet}</p>
"""


def show_search_form():
    return search_template


def run_search(query):
    results = search(query)
    fi = Filter(results)
    results = fi.filter()
    rendered = []
    results['snippet'] = results['snippet'].apply(lambda x: html.escape(x))

    for i, row in results.iterrows():
        temp = {
            'rank': i + 1,
            'link': row['link'],
            'title': row['title'],
            'snippet': row['snippet'],
            'query': query,
        }
        rendered.append(temp)
    return rendered


@login.user_loader
def load_user(user_id):
    return User.query.get(str(user_id))


@app.route('/', methods=['GET', 'POST'], endpoint='home')
@login_required
def home():
    form = SearchForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            query = form.query.data
            with current_app.app_context():
                rendered = run_search(query)
            return render_template('results.html', form=form, results=rendered)
    return render_template('home.html', form=form)


@app.route('/relevance', methods=['POST'], endpoint='relevance')
@login_required
def mark_relevance():
    data = request.get_json()
    query = data['query']
    link = data['link']
    storage = DBStorage()
    storage.update_relevance(query, link, 10)
    return jsonify(success=True)


@app.route('/register', methods=['GET', 'POST'], endpoint='register')
def register_user():
    form = RegisterForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data

        # check if user already exists
        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email address already exists')
            return redirect(url_for('register'))

        # create a hashed password
        hashed_password = generate_password_hash(password, method='sha256')

        # created a new user
        new_user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))

    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'], endpoint='login')
def user_login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data

        user = User.query.filter_by(email=email).first()
        if not user or not check_password_hash(user.password, password):
            flash('Please check your login details and try again.')
            return redirect(url_for('login'))

        if load_user(user.id):
            login_user(user)
            return redirect(url_for('home'))

    return render_template('login.html', form=form)


@app.route('/logout', endpoint='logout')
@login_required
def logout():
    if load_user(current_user.id):
        logout_user()
        return redirect(url_for('login'))
    else:
        return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)
