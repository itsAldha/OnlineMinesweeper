#!flask/bin/python
from main.flaskrun import flaskrun
from flask import Flask, render_template, request, redirect, url_for, flash, make_response
from markupsafe import escape
from main.forms import LoginForm, GameForm, ChatForm
from main.util import hash_password, verify_password
import sqlite3
import threading, time
from main.game import playgame, getGrid, parseinput

application = Flask(__name__)
application.config['SECRET_KEY'] = 'you-will-never-guess'


# Global Variables
r = 0
waiting = []
gameInstance = []
messages = []

def newGameInstance():
    gridsize = 10
    numberofmines = 25
    currgrid = [[' ' for i in range(gridsize)] for i in range(gridsize)]
    grid = []
    mines = []
    flags = []
    starttime = 0
    cell = 0
    flag = 0
    gameOver = True
    busy = False
    player1 = ''
    player2 = ''
    player1Points = 0
    player2Points = 0
    prevWinner = None
    prevLoser = None
    return [gridsize, numberofmines, currgrid, grid, mines, flags, starttime, cell, flag, gameOver, busy, player1, player2, player1Points, player2Points, prevWinner, prevLoser]

def gameInstanceInit():
    global gameInstance
    for x in range(10):
        gameInstance.append( newGameInstance() )
        messages.append([''])
        
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
    return render_template('login.html', name='Login', form=form)


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
        c.execute( "INSERT INTO users VALUES (?,?,0,0,0,?,'-')",(username,password,session) )
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
    username = request.cookies.get('username')
    # If you leave the game, you lose and the game ends
    conn = sqlite3.connect('user.db')
    c = conn.cursor();
    c.execute("SELECT * FROM users WHERE username=?",(username,))
    result = c.fetchone()
    conn.commit()
    conn.close()
    if (result[6] != '-'):
        print('\n ---> iam({}) in logout() instance is not '-'  <---\n'.format(username, flush=True))
        i = int(result[6])
        global gameInstance
        if username == gameInstance[i][11]:
            gameInstance[i][13]-=100
        elif username == gameInstance[i][12]:
            gameInstance[i][14]-=100
        gameInstance[i][9] = True
        response = make_response( redirect(url_for('gameLoop')) )
        return response
        
    username = request.cookies.get('username')
    flash("Logged out successfully")
    response = make_response( redirect(url_for('index')) )
    response.set_cookie('username', 'username', max_age=0)
    response.set_cookie('session', 'session', max_age=0)
    response.set_cookie('userSession', 'userSession', max_age=0)

    response.set_cookie('turn', 'turn', max_age=0)
    return response


# --------------------------------------- GAME FUNCTIONS ---------------------------------------

def removeFromWaiting(name):
    time.sleep(1.9)
    if name in waiting:
        waiting.remove(name)

@application.route('/lobby')
def lobby():
    username = request.cookies.get('username')
    print('\n ---> iam({}) I just entered lobby() <---\n'.format(username, flush=True))
    userSession = request.cookies.get('userSession')
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
    if (result[6] != '-'):
        i = int(result[6])
        global gameInstance
        if username == gameInstance[i][11]:
            gameInstance[i][13]-=100
        elif username == gameInstance[i][12]:
            gameInstance[i][14]-=100
        gameInstance[i][9] = True
        response = make_response( redirect(url_for('gameLoop')) )
        return response
    
    
    # Send Ready to Players To StartGame
    for x in range(10):
        if gameInstance[x][9] == False and username in gameInstance[x]:
            response = make_response( redirect(url_for('startgame')) )
            conn = sqlite3.connect('user.db')
            c = conn.cursor();
            c.execute( "UPDATE users SET instance = ? WHERE username=?", (str(x),username) )
            conn.commit()
            conn.close()
            print('\n ---> iam({}) JUST SAVED instance({}) in lobby() <---\n'.format(username,str(x)), flush=True)
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
                gameInstance[x] = newGameInstance()
                print('\n ---> iam({}) JUST FOUND INSTANCE ({}) in lobby() <---\n'.format(username,x), flush=True)
                gameInstance[x][9] = False          # Make Game Playable
                gameInstance[x][10] = True          # Make instance busy
                gameInstance[x][11] = waiting[0]    # Add player 1
                gameInstance[x][12] = waiting[1]    # Add player 2
                messages[x] = ['']                  # Empty chatlog for instance
                waiting.remove(gameInstance[x][11]) # Remove player 1 from waiting list
                waiting.remove(gameInstance[x][12]) # Remove player 2 from waiting list
                return render_template('lobby.html', username=username, waiting=waiting)
    return render_template('lobby.html', username=username, waiting=waiting)

    

@application.route('/startgame')
def startgame():
    global r
    r=0;
    username = request.cookies.get('username')
    conn = sqlite3.connect('user.db')
    c = conn.cursor();
    c.execute("SELECT * FROM users WHERE username=?",(username,))
    result = c.fetchone()
    conn.commit()
    conn.close()   
    i = int(result[6])   
    
    print('\n ---> iam({}) instance({}) in startgame() <---\n'.format(username,i), flush=True)
    
    # Remove Previous Game Data
    global gameInstance
    gameInstance[i][15] = None
    gameInstance[i][16] = None
    
    if username == gameInstance[i][11] or username == gameInstance[i][12]:
        response = make_response( redirect(url_for('gameInput')) )
        response.set_cookie('turn', 'playing')
        return response;
    else:
        response = make_response( redirect(url_for('logout')) )
        return response;

@application.route('/gameloop')
def gameLoop():
    username = request.cookies.get('username')
    conn = sqlite3.connect('user.db')
    c = conn.cursor();
    c.execute("SELECT * FROM users WHERE username=?",(username,))
    result = c.fetchone()
    conn.commit()
    conn.close()   
    i = int(result[6])
    turn = request.cookies.get('turn')
    global r;
    r+=1;
    print('\nROUND {}\n---> iam({}) instance({}) turn({}) in gameLoop() <--\n'.format(r,username,i,turn), flush=True)
    
    # Check if Other Player Ended the Game Already
    if ( gameInstance[i][15] is not None ):
        print('user {} entered 15'.format(username), flush=True)
        if username == gameInstance[i][15]:
            flash("Congratulations on winning")
            print('user {} won'.format(username), flush=True)
        elif username == gameInstance[i][16]:
            flash("You lost, better luck next time")
            print('user {} lost'.format(username), flush=True)
        else:
            flash("You should not be here")
        gameInstance[i][15] = None
        gameInstance[i][16] = None
        response = make_response( redirect(url_for('profile')) )
        conn = sqlite3.connect('user.db')
        c = conn.cursor();
        c.execute( "UPDATE users SET instance = ? WHERE username=?", ('-',username) )
        conn.commit()
        conn.close()
        response.set_cookie('turn', 'turn', max_age=0)
        return response
    
    # Check if You Ended the Game, GameOver = True
    if gameInstance[i][9] == True:
        print('---> iam({}) instance({}) turn({}) in gameLoop() Gameover True'.format(username,i,turn), flush=True)
        response = make_response( redirect(url_for('gameOver')) )
        response.set_cookie('turn', 'turn', max_age=0)
        return response

    if turn == "playing":
        response = make_response( redirect(url_for('gameInput')) )
        response.set_cookie('turn', 'playing')
        return response;
    print('\n---> iam({}) instance({}) turn({}) in gameLoop() GameOver Not True, Not Watching, Not Playing <---\n'.format(username,i,turn), flush=True)
    response = make_response( redirect(url_for('profile')) )
    return response;

@application.route('/gameover')
def gameOver():
    username = request.cookies.get('username')
    print('\n ---> iam({}) I just entered gameOver() <---\n'.format(username, flush=True))
    conn = sqlite3.connect('user.db')
    c = conn.cursor();
    c.execute("SELECT * FROM users WHERE username=?",(username,))
    result = c.fetchone()
    conn.commit()
    conn.close()   
    i = int(result[6])
    global gameInstance
    won = False
    if ( username == gameInstance[i][11] ) and (gameInstance[i][13] > gameInstance[i][14]):
        won = True
    if ( username == gameInstance[i][12] ) and (gameInstance[i][14] > gameInstance[i][13]):
        won = True
    
    # Update the User Database
    conn = sqlite3.connect('user.db')
    c = conn.cursor();
    c.execute( "UPDATE users SET games = games + 1 WHERE username=?", (gameInstance[i][11],) )
    c.execute( "UPDATE users SET games = games + 1 WHERE username=?", (gameInstance[i][12],) )
    
    if ( username == gameInstance[i][11]  and  won == True ) or ( username == gameInstance[i][12]  and  won == False ):
        c.execute( "UPDATE users SET won = won + 1 WHERE username=?", (gameInstance[i][11],) )
        c.execute( "UPDATE users SET lost = lost + 1 WHERE username=?", (gameInstance[i][12],) )
    else:
        c.execute( "UPDATE users SET won = won + 1 WHERE username=?", (gameInstance[i][12],) )
        c.execute( "UPDATE users SET lost = lost + 1 WHERE username=?", (gameInstance[i][11],) )
    conn.commit()
    conn.close()
    
    gameInstance[i][0] = 10
    gameInstance[i][1] = 25
    gameInstance[i][2] = [[' ' for i in range(10)] for i in range(10)]
    gameInstance[i][3] = []
    gameInstance[i][4] = []
    gameInstance[i][5] = []
    gameInstance[i][6] = 0
    gameInstance[i][7] = 0
    gameInstance[i][8] = 0
    gameInstance[i][9] = True
    gameInstance[i][10] = False
    
    if ( username == gameInstance[i][11]  and  won == True ) or ( username == gameInstance[i][12]  and  won == False ):
        gameInstance[i][15] = gameInstance[i][11]
        gameInstance[i][16] = gameInstance[i][12]
    else:
        gameInstance[i][15] = gameInstance[i][12]
        gameInstance[i][16] = gameInstance[i][11]
    
    
    if won is True:
        flash("Congratulations on winning")
    else:
        flash("You lost, better luck next time")
    
    response = make_response( redirect(url_for('profile')) )
    conn = sqlite3.connect('user.db')
    c = conn.cursor();
    c.execute( "UPDATE users SET instance = ? WHERE username=?", ('-',username) )
    conn.commit()
    conn.close()
    return response

@application.route('/gamewatch')
def gameWatch():
    username = request.cookies.get('username')
    print('\n ---> iam({}) I just entered gameWatch() <---\n'.format(username, flush=True))
    username = request.cookies.get('username')
    conn = sqlite3.connect('user.db')
    c = conn.cursor();
    c.execute("SELECT * FROM users WHERE username=?",(username,))
    result = c.fetchone()
    conn.commit()
    conn.close()   
    i = int(result[6])
    
    if gameInstance[i][11] != username:
        enemy = gameInstance[i][11]
    else:
        enemy = gameInstance[i][12]
    
    msg = getGrid( gameInstance[i][2] )
    return render_template('gamewatch.html', name='Game Board', instance=i, enemy=enemy, username=username)

@application.route('/gameboard')
def gameBoard():
    username = request.cookies.get('username')
    conn = sqlite3.connect('user.db')
    c = conn.cursor();
    c.execute("SELECT * FROM users WHERE username=?",(username,))
    result = c.fetchone()
    conn.commit()
    conn.close()   
    if (result[6] == '-'):
        print('----> Instance is NONE in gameBoard() <----', flush=True)
        i = 0
    else:
        i = int(result[6])
    msg = getGrid( gameInstance[i][2] )

    return render_template('gameboard.html', name='Game Board', msg=msg, gameOver=gameInstance[i][9],player1=gameInstance[i][11],player1points=gameInstance[i][13],player2=gameInstance[i][12],player2points=gameInstance[i][14])


@application.route('/chat', methods=['GET', 'POST'])
def Chat():
    username = request.cookies.get('username')
    conn = sqlite3.connect('user.db')
    c = conn.cursor();
    c.execute("SELECT * FROM users WHERE username=?",(username,))
    result = c.fetchone()
    conn.commit()
    conn.close()
    if (result[6] == '-'):
        return "No Chat"
    i = int(result[6])
    return render_template('chat.html', messages=messages[i])
    
@application.route('/gamechat', methods=['GET', 'POST'])
def gameChat():
    username = request.cookies.get('username')
    conn = sqlite3.connect('user.db')
    c = conn.cursor();
    c.execute("SELECT * FROM users WHERE username=?",(username,))
    result = c.fetchone()
    conn.commit()
    conn.close()
    if (result[6] == '-'):
        return "No Chat"
    i = int(result[6])
    form = ChatForm()
    if form.validate_on_submit():
        message = form.chat.data
        form.chat.data = ""
        fullmessage = username + ": " + message
        messages[i].append(fullmessage)
        count = 0
        for x in range( len(messages[i]) ):
            count+=1
            n = len( messages[i][x] )
            while n > 20:
                count +=1
                n -= 20
        while count > 7:
            messages[i] = messages[i][1:]
            count -= 1
    return render_template('gamechat.html', form=form)


@application.route('/gameinput', methods=['GET', 'POST'])
def gameInput():
    global gameInstance
    username = request.cookies.get('username')
    print('\n ---> iam({}) I just entered gameInput() <---\n'.format(username, flush=True))
    conn = sqlite3.connect('user.db')
    c = conn.cursor();
    c.execute("SELECT * FROM users WHERE username=?",(username,))
    result = c.fetchone()
    conn.commit()
    conn.close()
    if (result[6] == '-'):
        print('\n-----> iam({}) in gameInput() I HAVE NO INSTANCE <---\n'.format(username,result[6],turn), flush=True)
        response = make_response( redirect(url_for('profile')) )
        return response;
    i = int(result[6])
    msg = getGrid( gameInstance[i][2] )
    form = GameForm()
    if form.validate_on_submit():
        prompt = form.choice.data
        flag = form.flag.data
        inp = prompt
        if flag:
            inp+="f"
        result = parseinput(inp, gameInstance[i][0])
        points = 0

        gameInstance[i][2], gameInstance[i][3], \
        gameInstance[i][4], gameInstance[i][5], \
        gameInstance[i][6], gameInstance[i][7], \
        gameInstance[i][8], gameInstance[i][9], points = playgame(result, gameInstance[i][0], \
                                                   gameInstance[i][1], gameInstance[i][2], gameInstance[i][3], \
                                                   gameInstance[i][4], gameInstance[i][5], gameInstance[i][6], \
                                                   gameInstance[i][7], gameInstance[i][8], gameInstance[i][9])
        
        print('\n ---> iam({}) instance({}) JUST FINISHED GAME INPUT Gameover is {} <---\n'.format(username,i,gameInstance[i][9]), flush=True)
    
        # State 0 : Game Went On
        # State 1 : You hit a mine
        # State 2 : You Found all the mines
        
        # Points Distribution
        if username == gameInstance[i][11]:
            gameInstance[i][13]+=points
        elif username == gameInstance[i][12]:
            gameInstance[i][14]+=points
        
        response = make_response( redirect(url_for('gameLoop')) )
        return response;
    return render_template('gameinput.html', name='Game Input', instance=i, username=username, msg=msg, form=form)

# --------------------------------------- MAIN FUNCTIONS ---------------------------------------

@application.route('/')
def index(val=None):
    username = request.cookies.get('username')
    
    # If you are a guest
    if (username is None):
        return render_template('index.html', name=val, username=username)

    # If you leave the game, you lose and the game ends
    conn = sqlite3.connect('user.db')
    c = conn.cursor();
    c.execute("SELECT * FROM users WHERE username=?",(username,))
    result = c.fetchone()
    conn.commit()
    conn.close()
    if (result[6] != '-'):
        i = int(result[6])
        global gameInstance
        if username == gameInstance[i][11]:
            gameInstance[i][13]-=100
        elif username == gameInstance[i][12]:
            gameInstance[i][14]-=100
        gameInstance[i][9] = True
        response = make_response( redirect(url_for('gameLoop')) )
        return response
    
    return render_template('index.html', name=val, username=username)



@application.route('/profile')
def profile():
    print('profile page', flush=True)
    username = request.cookies.get('username')
    userSession = request.cookies.get('userSession')

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
    if (result[6] != '-'):
        i = int(result[6])
        global gameInstance
        if username == gameInstance[i][11]:
            gameInstance[i][13]-=100
        elif username == gameInstance[i][12]:
            gameInstance[i][14]-=100
        gameInstance[i][9] = True
        response = make_response( redirect(url_for('gameLoop')) )
        return response
    
    return render_template('profile.html', username=username, games=result[2], won=result[3], lost=result[4])
    
    

if __name__ == '__main__':
    flaskrun(application)