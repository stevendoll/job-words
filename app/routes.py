from flask import render_template, flash, redirect, url_for, request
from flask_login import current_user, login_user, logout_user, login_required
import re
import json
from app import app, db
from app.forms import LoginForm, SignupForm, DocumentForm
from app.models import User, Phrase, UserPhrase, Finding, Document, UserDocument

@app.route('/')
@app.route('/index')
def index():
    return render_template('charts.html', title='Home')

@app.route('/charts')
def charts():
    return render_template('charts.html', title='Home')

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

@app.route('/phrases/<phrase_slug>')
def phrase_view(phrase_slug):

    phrase = Phrase.get_phrase(phrase_slug)
    
    return render_template('phrase.html', title='phrase.phrase_text', phrase=phrase)



@app.route('/users/<username>/phrases')
@login_required
def user_phrase_list(username):

    phrases = User.get_by_username(username).phrases
    
    return render_template('user-phrase.html', title='User Phrases', phrases=phrases)


@app.route('/documents', methods=['GET', 'POST'])
def document_list():

    form = DocumentForm()
    if form.validate_on_submit():

        if current_user.is_authenticated:
            Document.add_document(title=form.title.data, body=form.body.data, user=current_user)
        else:
            Document.add_document(title=form.title.data, body=form.body.data, user=None)

        flash('Document added!')

    documents = Document.get_all()
    
    return render_template('document-list.html', title='All documents', documents=documents)

@app.route('/documents/new')
def create_document():
    form = DocumentForm()
    return render_template('document-form.html', title='Create document', form=form)


@app.route('/users/<username>/documents')
@login_required
def user_document_list(username):

    documents = User.get_by_username(username).documents
    
    return render_template('user-document.html', title='User Documents', documents=documents)

@app.route('/api/phrases')
def phrase_list_api():

    # entire market of phrases
    phrases = Phrase.get_all()

    result = {}
    phrase_list = []

    for phrase in phrases:
        if phrase.findings and phrase.findings[-1].jobs_count and phrase.findings[-1].jobs_count > 10:
            phrase_list.append(phrase.serialize())

    # phrases associated with user and/or document
    user_phrases = UserPhrase.get_all()

    for user_phrase in user_phrases:
        if user_phrase.phrase.findings and user_phrase.phrase.findings[-1].jobs_count and user_phrase.phrase.findings[-1].jobs_count > 10:
            phrase_list.append(user_phrase.serialize())
            

    result['phrases'] = phrase_list
    result['phraseCount'] = len(phrase_list)
    
    return json.dumps(result)

