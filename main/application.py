#!flask/bin/python
from flask import Flask, render_template, request, redirect, url_for, flash, make_response
from markupsafe import escape
from main.flaskrun import flaskrun

application = Flask(__name__)

# Global Variables
visitors = 0


@application.route('/delete-cookie')
def delete_cookie():
    username = request.cookies.get('username')
    response = make_response("Cookie Removed")
    response.set_cookie('username', username, max_age=0)
    return response

@application.route('/load')
def load():
    username = request.cookies.get('username')
    if username is None:
        return "Who are you?"
    else:
        msg = "Welcome back!" + username
        return msg

@application.route('/save')
def save():
    response = make_response( redirect(url_for('index')) )
    global visitors
    password = visitors+20
    response.set_cookie('username', str(password) )
    return response

@application.route('/login')
def login():
    return 'login'

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

if __name__ == '__main__':
    flaskrun(application)
