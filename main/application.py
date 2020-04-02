#!flask/bin/python
from flask import Flask, render_template, url_for
from markupsafe import escape
from main.flaskrun import flaskrun

application = Flask(__name__)

# global variables
visitors = 0

@application.route('/login')
def login():
    return 'login'

@application.route('/user/<username>')
def profile(username):
    return '{}\'s profile'.format(escape(username))

with app.test_request_context():
    print(url_for('login'))
    print(url_for('login', next='/'))
    print(url_for('profile', username='John Doe'))

@application.route('/<x>')
def index(x):
    return render_template('index.html', name=x)

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
