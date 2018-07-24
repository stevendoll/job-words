from flask import render_template, flash, redirect, url_for
from app import app
from app.forms import LoginForm
from app.models import User

@app.route('/')
@app.route('/index')
def index():
    user = {'username': 'Miguel'}
    return render_template('index.html', title='Home', user=user)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        flash('Login requested for user {}, remember_me={}'.format(
            form.username.data, form.remember_me.data))
        return redirect(url_for('index'))
    return render_template('login.html', title='Sign In', form=form)

@app.route('/users')
def user_list():

    users = User.get_all()
    
    return render_template('user.html', title='Users', users=users)

