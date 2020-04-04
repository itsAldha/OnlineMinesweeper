#!flask/bin/python
from main.flaskrun import flaskrun
from flask import Flask, render_template, request, redirect, url_for, flash, make_response
from markupsafe import escape
from main.forms import LoginForm

application = Flask(__name__)
application.config['SECRET_KEY'] = 'you-will-never-guess'

# Global Variables
visitors = 0 
username = "username"
password = "password"


@application.route('/save')
def save():
    response = make_response( redirect(url_for('index')) )
    global visitors 
    password = visitors+20
    response.set_cookie('username', str(password) )
    return response

@application.route('/load')
def load():
    username = request.cookies.get('username')
    if username is None:
        return "Who are you?"
    else:
        msg = "Welcome back!" + username
        return msg

@application.route('/logout')
def logout():
    username = request.cookies.get('username')
    if username is None:
        flash("You are logged out already")
    else:
        flash("Logged out successfully")
    response = make_response( redirect(url_for('index')) )
    response.set_cookie('username', username, max_age=0)
    return response

@application.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        flash('User {} is logged-in.'.format(form.username.data))
        global username, password
        username = form.username.data
        password = form.password.data
        response = make_response( redirect(url_for('index')) )
        response.set_cookie('username', username )
        return response
    return render_template('login.html', name='Sign In', form=form)

@application.route('/who')
def who():
    global username, password
    msg = "username is " + username +" and password is " + password
    return msg

@application.route('/user/<username>')
def profile(username):
    return '{}\'s profile'.format(escape(username))

@application.route('/')
@application.route('/<val>')
def index(val=None):
    username = request.cookies.get('username')
    return render_template('index.html', name=val, username=username)

@application.route('/counter')
def counter():
    global visitors
    visitors+=1
    return render_template('counter.html',num=visitors)

@application.route('/team')
def team():
    ourteam = {
        'member1' : "aldha",
        'member2' : "juliana",
        'member3' : "juan"
        }
    username = request.cookies.get('username')
    return render_template('team.html', **ourteam,username=username)


if __name__ == '__main__':
    flaskrun(application)