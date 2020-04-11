#!flask/bin/python
from main.flaskrun import flaskrun
from flask import Flask, render_template, request, redirect, url_for, flash, make_response
from markupsafe import escape
from main.forms import LoginForm, GameForm
from main.util import hash_password, verify_password
import sqlite3
import threading, time
from main.game import playgame, getGrid, parseinput

application = Flask(__name__)
application.config['SECRET_KEY'] = 'you-will-never-guess'

# Global Variables
waiting = []
gameInstance = []

def gameInstanceInit():
    gridsize = 10
    numberofmines = 20
    currgrid = [[' ' for i in range(gridsize)] for i in range(gridsize)]
    grid = []
    mines = []
    flags = []
    starttime = 0
    cell = 0
    flag = 0
    gameOver = False
    busy = False
    player1 = ''
    player2 = ''
    player1Points = 0
    player2Points = 0
    prevWinner = None
    prevLoser = None
    global gameInstance
    for x in range(10):
        gameInstance.append([gridsize, numberofmines, currgrid, grid, mines, flags, starttime, cell, flag, gameOver, busy, player1, player2, player1Points, player2Points, prevWinner, prevLoser])
gameInstanceInit()

# --------------------------------------- USER FUNCTIONS ---------------------------------------

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
            c.execute( "UPDATE users SET userSession=? WHERE username=?", (session,username) )
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
    

@application.route('/logout')
def logout():
    flash("Logged out successfully")
    response = make_response( redirect(url_for('index')) )
    response.set_cookie('username', 'username', max_age=0)
    response.set_cookie('session', 'session', max_age=0)
    response.set_cookie('userSession', 'userSession', max_age=0)
    response.set_cookie('instance', 'instance', max_age=0)
    response.set_cookie('turn', 'turn', max_age=0)
    return response





# --------------------------------------- GAME FUNCTIONS ---------------------------------------

def removeFromWaiting(name):
    time.sleep(4.9)
    if name in waiting:
        waiting.remove(name)
 
@application.route('/lobbyupdate')
def lobbyUpdate():
    return lobby()
 
@application.route('/lobby')
def lobby():
    username = request.cookies.get('username')
    userSession = request.cookies.get('userSession')
    instance = request.cookies.get('instance')
    turn = request.cookies.get('turn')
    
    conn = sqlite3.connect('user.db')
    c = conn.cursor();
    c.execute("SELECT * FROM users WHERE username=?",(username,))
    result = c.fetchone()
    conn.commit()
    conn.close()
    
    # If you go to /lobby without logging in
    if (result is None) or (userSession!=result[5]):
        response = make_response( redirect(url_for('index')) )
        response.set_cookie('username', 'username', max_age=0)
        response.set_cookie('session', 'session', max_age=0)
        response.set_cookie('userSession', 'userSession', max_age=0)
        return response

    # If you leave the game, you lose and the game ends
    if (instance is not None) and (turn is not None):
        global gameInstance
        if username == gameInstance[int(instance)][11]:
            gameInstance[int(instance)][13]-=100
        elif username == gameInstance[int(instance)][12]:
            gameInstance[int(instance)][14]-=100
        gameInstance[int(instance)][9] = True
        response = make_response( redirect(url_for('gameLoop')) )
        return response

    # Send Ready to Players To StartGame
    for x in range(10):
        if username in gameInstance[x]:
            response = make_response( redirect(url_for('startgame')) )
            response.set_cookie('instance', str(x))
            return response
    
    # Add Player To Waiting List
    global waiting
    if username not in waiting:
        x = threading.Thread(target=removeFromWaiting, args=(username,))
        x.start()
        waiting.append(username)
        waiting = sorted(waiting)
        return render_template('lobby.html', username=username, waiting=waiting)
    if len(waiting) >= 2:
        for x in range(10):
            if gameInstance[x][10] is not True:     # If instance is not busy
                gameInstance[x][10] = True          # Make instance busy
                gameInstance[x][11] = waiting[0]    # Add player 1
                gameInstance[x][12] = waiting[1]    # Add player 2
                waiting.remove(gameInstance[x][11]) # Remove player 1 from waiting list
                waiting.remove(gameInstance[x][12]) # Remove player 2 from waiting list
                return render_template('lobby.html', username=username, waiting=waiting)

    

@application.route('/startgame')
def startgame():

    username = request.cookies.get('username')
    instance = int( request.cookies.get('instance') )    
    
    print('---> iam({}) instance({}) in startgame()'.format(username,instance), flush=True)
    
    # Remove Previous Game Data
    global gameInstance
    gameInstance[instance][15] = None
    gameInstance[instance][16] = None
    
    if username == gameInstance[instance][11]:
        response = make_response( redirect(url_for('gameInput')) )
        response.set_cookie('turn', 'playing')
        return response;
    elif username == gameInstance[instance][12]:
        response = make_response( redirect(url_for('gameWatch')) )
        response.set_cookie('turn', 'watching')
        return response;
    else:
        response = make_response( redirect(url_for('logout')) )
        return response;

@application.route('/gameloop')
def gameLoop():
    username = request.cookies.get('username')
    instance = int( request.cookies.get('instance') )
    turn = request.cookies.get('turn')
    
    print('---> iam({}) instance({}) turn({}) in gameLoop()'.format(username,instance,turn), flush=True)
    
    # Check if Other Player Ended the Game Already
    if ( gameInstance[instance][15] is not None ):
        print('user {} entered 15'.format(username), flush=True)
        if username == gameInstance[instance][15]:
            flash("Congratulations on winning")
            print('user {} won'.format(username), flush=True)
        elif username == gameInstance[instance][16]:
            flash("You lost, better luck next time")
            print('user {} lost'.format(username), flush=True)
        else:
            flash("You should not be here")
        gameInstance[instance][15] = None
        gameInstance[instance][16] = None
        response = make_response( redirect(url_for('profile')) )
        response.set_cookie('instance', 'instance', max_age=0)
        response.set_cookie('turn', 'turn', max_age=0)
        return response
    
    # Check if GameOver = True
    if gameInstance[instance][9] is True:
        print('---> iam({}) instance({}) turn({}) in gameLoop() Gameover True'.format(username,instance,turn), flush=True)
        gameInstance[instance][9] = False
        response = make_response( redirect(url_for('gameOver')) )
        response.set_cookie('turn', 'turn', max_age=0)
        return response
    if turn == "watching":
        response = make_response( redirect(url_for('gameInput')) )
        response.set_cookie('turn', 'playing')
        return response;
    if turn == "playing":
        response = make_response( redirect(url_for('gameWatch')) )
        response.set_cookie('turn', 'watching')
        return response;
    print('---> iam({}) instance({}) turn({}) in gameLoop() Gameover True'.format(username,instance,turn), flush=True)
    response = make_response( redirect(url_for('logout')) )
    return response;

@application.route('/gameover')
def gameOver():
    username = request.cookies.get('username')
    instance = int( request.cookies.get('instance') )
    global gameInstance
    won = False
    if ( username == gameInstance[instance][11] ) and (gameInstance[instance][13] > gameInstance[instance][14]):
        won = True
    if ( username == gameInstance[instance][12] ) and (gameInstance[instance][14] > gameInstance[instance][13]):
        won = True
    
    # Update the User Database
    conn = sqlite3.connect('user.db')
    c = conn.cursor();
    c.execute( "UPDATE users SET games = games + 1 WHERE username=?", (gameInstance[instance][11],) )
    c.execute( "UPDATE users SET games = games + 1 WHERE username=?", (gameInstance[instance][12],) )
    
    if ( username == gameInstance[instance][11]  and  won == True ) or ( username == gameInstance[instance][12]  and  won == False ):
        c.execute( "UPDATE users SET won = won + 1 WHERE username=?", (gameInstance[instance][11],) )
        c.execute( "UPDATE users SET lost = lost + 1 WHERE username=?", (gameInstance[instance][12],) )
    else:
        c.execute( "UPDATE users SET won = won + 1 WHERE username=?", (gameInstance[instance][12],) )
        c.execute( "UPDATE users SET lost = lost + 1 WHERE username=?", (gameInstance[instance][11],) )
    conn.commit()
    conn.close()
    
    gameInstance[instance][0] = 10
    gameInstance[instance][1] = 20
    gameInstance[instance][2] = [[' ' for i in range(10)] for i in range(10)]
    gameInstance[instance][3] = []
    gameInstance[instance][4] = []
    gameInstance[instance][5] = []
    gameInstance[instance][6] = 0
    gameInstance[instance][7] = 0
    gameInstance[instance][8] = 0
    gameInstance[instance][9] = False
    gameInstance[instance][10] = False
    
    if ( username == gameInstance[instance][11]  and  won == True ) or ( username == gameInstance[instance][12]  and  won == False ):
        gameInstance[instance][15] = gameInstance[instance][11]
        gameInstance[instance][16] = gameInstance[instance][12]
    else:
        gameInstance[instance][15] = gameInstance[instance][12]
        gameInstance[instance][16] = gameInstance[instance][11]
    
    gameInstance[instance][11] = ''
    gameInstance[instance][12] = ''
    gameInstance[instance][13] = 0
    gameInstance[instance][14] = 0
    
    if won is True:
        flash("Congratulations on winning")
    else:
        flash("You lost, better luck next time")
    
    response = make_response( redirect(url_for('profile')) )
    response.set_cookie('instance', 'instance', max_age=0)
    return response

@application.route('/gamewatch')
def gameWatch():
    username = request.cookies.get('username')
    instance = int( request.cookies.get('instance') )
    
    if gameInstance[instance][11] != username:
        enemy = gameInstance[instance][11]
    else:
        enemy = gameInstance[instance][12]
    
    msg = getGrid( gameInstance[instance][2] )
    return render_template('gamewatch.html', name='Game Board', instance=instance, enemy=enemy, username=username)

@application.route('/gameboard')
def gameBoard():
    instance = int( request.cookies.get('instance') )
    msg = getGrid( gameInstance[instance][2] )
    return render_template('gameboard.html', name='Game Board', msg=msg)

@application.route('/gameinput', methods=['GET', 'POST'])
def gameInput():
    username = request.cookies.get('username')
    instance = int( request.cookies.get('instance') )
    msg = getGrid( gameInstance[instance][2] )
    form = GameForm()
    if form.validate_on_submit():
        prompt = form.choice.data
        flag = form.flag.data
        inp = prompt
        if flag:
            inp+="f"
        result = parseinput(inp, gameInstance[instance][0])
        
        gameInstance[instance][2], gameInstance[instance][3], \
        gameInstance[instance][4], gameInstance[instance][5], \
        gameInstance[instance][6], gameInstance[instance][7], \
        gameInstance[instance][8], gameInstance[instance][9], state = playgame(result, gameInstance[instance][0], \
                                                   gameInstance[instance][1], gameInstance[instance][2], gameInstance[instance][3], \
                                                   gameInstance[instance][4], gameInstance[instance][5], gameInstance[instance][6], \
                                                   gameInstance[instance][7], gameInstance[instance][8], gameInstance[instance][9])
        
        # State 0 : Game Went On
        # State 1 : You hit a mine
        # State 2 : You Found all the mines
        
        # Points Distribution
        if state == 0:
            if username == gameInstance[instance][11]:
                gameInstance[instance][13]+=1
            elif username == gameInstance[instance][12]:
                gameInstance[instance][14]+=1
        else:
            if state == 1:
                if username == gameInstance[instance][11]:
                    gameInstance[instance][13]-=100
                elif username == gameInstance[instance][12]:
                    gameInstance[instance][14]-=100
            elif state == 2:
                if username == gameInstance[instance][11]:
                    gameInstance[instance][13]+=10
                elif username == gameInstance[instance][12]:
                    gameInstance[instance][14]+=10
        response = make_response( redirect(url_for('gameLoop')) )
        return response;
    return render_template('gameinput.html', name='Game Input', instance=instance, username=username, msg=msg, form=form)

# --------------------------------------- MAIN FUNCTIONS ---------------------------------------

@application.route('/')
@application.route('/<val>')
def index(val=None):
    username = request.cookies.get('username')
    instance = request.cookies.get('instance')
    turn = request.cookies.get('turn')
    
    # If you leave the game, you lose and the game ends
    if (instance is not None) and (turn is not None):
        global gameInstance
        if username == gameInstance[int(instance)][11]:
            gameInstance[int(instance)][13]-=100
        elif username == gameInstance[int(instance)][12]:
            gameInstance[int(instance)][14]-=100
        gameInstance[int(instance)][9] = True
        response = make_response( redirect(url_for('gameLoop')) )
        return response
    
    return render_template('index.html', name=val, username=username)



@application.route('/profile')
def profile():
    print('profile page', flush=True)
    username = request.cookies.get('username')
    userSession = request.cookies.get('userSession')
    instance = request.cookies.get('instance')
    turn = request.cookies.get('turn')

    conn = sqlite3.connect('user.db')
    c = conn.cursor();
    c.execute("SELECT * FROM users WHERE username=?",(username,))
    result = c.fetchone()
    conn.commit()
    conn.close()
    
    # If you go to /profile without logging in
    if (result is None) or (userSession!=result[5]):
        response = make_response( redirect(url_for('index')) )
        response.set_cookie('username', 'username', max_age=0)
        response.set_cookie('session', 'session', max_age=0)
        response.set_cookie('userSession', 'userSession', max_age=0)
        return response
    
    # If you leave the game, you lose and the game ends
    if (instance is not None) and (turn is not None):
        global gameInstance
        if username == gameInstance[int(instance)][11]:
            gameInstance[int(instance)][13]-=100
        elif username == gameInstance[int(instance)][12]:
            gameInstance[int(instance)][14]-=100
        gameInstance[int(instance)][9] = True
        response = make_response( redirect(url_for('gameLoop')) )
        return response
    
    return render_template('profile.html', username=username, games=result[2], won=result[3], lost=result[4])
    
    

if __name__ == '__main__':
    flaskrun(application)