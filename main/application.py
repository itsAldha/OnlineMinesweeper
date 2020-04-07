#!flask/bin/python
from main.flaskrun import flaskrun
from flask import Flask, render_template, request, redirect, url_for, flash, make_response
from markupsafe import escape
from main.forms import LoginForm
from main.util import hash_password, verify_password
import sqlite3

application = Flask(__name__)
application.config['SECRET_KEY'] = 'you-will-never-guess'

# Global Variables
visitors = 0 
waiting = []

@application.route('/logout')
def logout():
    username = request.cookies.get('username')
    session = request.cookies.get('session')
    userSession = request.cookies.get('userSession')
    if username is None:
        flash("You are logged out already")
    else:
        flash("Logged out successfully")
    response = make_response( redirect(url_for('index')) )
    response.set_cookie('username', username, max_age=0)
    response.set_cookie('session', session, max_age=0)
    response.set_cookie('userSession', userSession, max_age=0)
    return response

@application.route('/register', methods=['GET', 'POST'])
def register():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        
        if ( len(username) < 4 ) or ( len(password) < 6 ):
            flash('Registration failed. Username must be no less than 4 characters, and password must be no less than 6 characters')
            return redirect(url_for('index'))
        
        password = hash_password(form.password.data)
        
        conn = sqlite3.connect('user.db')
        c = conn.cursor();
        c.execute("SELECT * FROM users WHERE username=?", (username,) )
        result = c.fetchone() 
        if result is not None:
            flash('Registration failed. Username exists')
            conn.commit()
            conn.close()
            return redirect(url_for('index'))
            
        session = request.cookies.get('session')
        c.execute( "INSERT INTO users VALUES (?,?,0,0,0,?)",(username,password,session) )
        conn.commit()
        conn.close()
        
        flash('User {} is registered and logged-in.'.format(form.username.data))
        response = make_response( redirect(url_for('index')) )
        response.set_cookie('username', username )
        response.set_cookie('userSession', session )
        return response
    return render_template('register.html', name='Register', form=form)
    
@application.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        
        conn = sqlite3.connect('user.db')
        c = conn.cursor();
        c.execute("SELECT * FROM users WHERE username=?", (username,) )
        result = c.fetchone() 
        
        if result is None:
            conn.commit()
            conn.close()
            flash('Login failed. Username does not exist')
            return redirect(url_for('index'))
        if username==result[0] and verify_password(result[1],password):
            session = request.cookies.get('session')
            c.execute( "UPDATE users SET session=? WHERE username=?", (session,username) )
            conn.commit()
            conn.close()
            flash('User {} is logged-in.'.format(form.username.data))
            response = make_response( redirect(url_for('index')) )
            response.set_cookie('username', username )
            response.set_cookie('userSession', session )
            return response
        else:
            conn.commit()
            conn.close()
            flash('Login failed. Wrong username or password.')
            return redirect(url_for('index'))
    return render_template('login.html', name='Sign In', form=form)

@application.route('/profile')
def profile():
    username = request.cookies.get('username')
    userSession = request.cookies.get('userSession')

    conn = sqlite3.connect('user.db')
    c = conn.cursor();
    c.execute("SELECT * FROM users WHERE username=?",(username,))
    result = c.fetchone()
    conn.commit()
    conn.close()
    
    if (result is None) or (userSession!=result[5]):
        response = make_response( redirect(url_for('index')) )
        response.set_cookie('username', 'username', max_age=0)
        response.set_cookie('session', 'session', max_age=0)
        response.set_cookie('userSession', 'userSession', max_age=0)
        return response
    return render_template('profile.html', username=username, games=result[2], won=result[3], lost=result[4])

        

@application.route('/joinGame')
def joinGame():
    username = request.cookies.get('username')
    userSession = request.cookies.get('userSession')

    conn = sqlite3.connect('user.db')
    c = conn.cursor();
    c.execute("SELECT * FROM users WHERE username=?",(username,))
    result = c.fetchone()
    conn.commit()
    conn.close()
    
    if (result is None) or (userSession!=result[5]):
        response = make_response( redirect(url_for('index')) )
        response.set_cookie('username', 'username', max_age=0)
        response.set_cookie('session', 'session', max_age=0)
        response.set_cookie('userSession', 'userSession', max_age=0)
        return response
    
    # Add Player To Waiting List
    if username not in waiting:
        waiting.append(username)
    return render_template('game.html', username=username, waiting=waiting)

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
        'member1' : "Aldha",
        'member2' : "Juliana",
        'member3' : "Juan"
        }
    username = request.cookies.get('username')
    return render_template('team.html', **ourteam, name='Team', username=username)


if __name__ == '__main__':
    flaskrun(application)