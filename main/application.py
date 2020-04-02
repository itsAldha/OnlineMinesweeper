#!flask/bin/python
from flask import Flask, render_template
from main.flaskrun import flaskrun

application = Flask(__name__)

# global variables
visitors = 0

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
    member1 = "juliana"
    member2 = "aldha"
    member3 = "juan"

    ourteam = {
        'member1' : member1,
        'member2' : member2,
        'member3' : member3
        }
    return renderrender_template('team.html',**ourteam)

if __name__ == '__main__':
    flaskrun(application)
