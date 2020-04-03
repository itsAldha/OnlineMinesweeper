from flask import Flask, render_template, request, redirect, url_for, flash, make_response
from markupsafe import escape
from main.application import application

# Global Variables
visitors = 0 

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

@application.route('/delete-cookie')
def delete_cookie():
    username = request.cookies.get('username')
    response = make_response("Cookie Removed")
    response.set_cookie('username', username, max_age=0)
    return response

@application.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        flash('Login requested for user {}, remember_me={}'.format(
            form.username.data, form.remember_me.data))
        return redirect(url_for('index'))
    return render_template('login.html', name='Sign In', form=form)

@application.route('/who')
def who():
    global user
    return user

@application.route('/user/<username>')
def profile(username):
    return '{}\'s profile'.format(escape(username))

@application.route('/')
@application.route('/<val>')
def index(val=None):
    return render_template('index.html', name=val)

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
    return render_template('team.html', **ourteam)