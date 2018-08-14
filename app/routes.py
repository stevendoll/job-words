from flask import render_template, flash, redirect, url_for, request
from flask_login import current_user, login_user, logout_user, login_required
import re
from app import app, db
from app.forms import LoginForm, SignupForm
from app.models import User, Phrase, UserPhrase, Finding, Document

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

@app.route('/phrases')
def phrase_list():

    term = request.args.get('term', '')

    regex = r'[^a-zA-Z\s]'
    term = re.sub(regex, '', term.lower().strip())


    if len(term) > 0:
        if current_user.is_anonymous:
            phrase = Phrase.lookup(term)
        else:
            phrase = Phrase.lookup(term, user=current_user)

        if phrase == None:
            flash('Something went wrong')
        elif phrase.search_count == 1:
            flash('New search phrase! ')
        else:
            flash('Searched ' + str(phrase.search_count) + ' times!')


    phrases = Phrase.get_all()

    if current_user.is_anonymous:
        my_phrases = None
    else:
        my_phrases = User.get_by_username(current_user.username).phrases
    
    return render_template('phrase-list.html', title='Search Phrases', phrases=phrases, my_phrases=my_phrases)

@app.route('/phrases/<phrase>')
def phrase_view(phrase):

    phrase = Phrase.get_phrase(phrase.replace('-', ' '))
    
    return render_template('phrase.html', title='phrase.phrase', phrase=phrase)



@app.route('/users/<username>/phrases')
@login_required
def user_phrase_list(username):

    phrases = User.get_by_username(username).phrases
    
    return render_template('user-phrase.html', title='User Phrases', phrases=phrases)


@app.route('/documents')
def document_list():

    documents = Document.get_all()
    
    return render_template('document-list.html', title='All documents', documents=documents)


@app.route('/users/<username>/documents')
@login_required
def user_document_list(username):

    documents = User.get_by_username(username).documents
    
    return render_template('user-document.html', title='User Documents', documents=documents)

