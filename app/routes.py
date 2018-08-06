from flask import render_template, flash, redirect, url_for, request
from flask_login import current_user, login_user, logout_user, login_required
import re
from app import app, db
from app.forms import LoginForm, SignupForm
from app.models import User, Phrase

@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html', title='Home')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or user.password_hash is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        return redirect(url_for('index'))
    return render_template('login.html', title='Sign In', form=form)

@app.route('/logout')
def logout():
    logout_user()
    flash('Goodbye')
    return redirect(url_for('index'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = SignupForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('signup.html', title='Sign up', form=form)

@app.route('/users')
@login_required
def user_list():

    users = User.get_all()
    
    return render_template('user.html', title='Users', users=users)

@app.route('/search_phrases')
def phrase_list():

    term = request.args.get('term', '')

    regex = r'[^a-zA-Z\s]'
    term = re.sub(regex, '', term.lower().strip())

    # try:
    phrase = Phrase.lookup(term)

    if phrase == None:
        flash('Something went wrong')
    elif phrase.search_count == 1:
        flash('New search phrase! ')
    else:
        flash('Searched ' + str(phrase.search_count) + ' times!')

    # except:
    #     flash('Something went wrong')


    phrases = Phrase.get_all()
    
    return render_template('phrase.html', title='Search Phrases', phrases=phrases)
