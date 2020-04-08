from game import playgame, getGrid, parseinput

gameInstance = []

def gameInstanceInit():
    gridsize = 10
    numberofmines = 2
    currgrid = [[' ' for i in range(gridsize)] for i in range(gridsize)]
    grid = []
    mines = []
    flags = []
    starttime = 0
    cell = 0
    flag = 0
    gameOver = False
    busy = False
    global gameInstance
    for x in range(10):
        gameInstance.append([gridsize, numberofmines, currgrid, grid, mines, flags, starttime, cell, flag, gameOver, busy, 'player1', 'player2'])

def gameInstancePrint(gameID):
        msg = getGrid(gameInstance[gameID][2])
        #print( msg )

def gameInstanceRun(gameID):
    global gameInstance
    if gameInstance[gameID][9] == False:
        prompt = input('Enter the cell: ')
        result = parseinput(prompt, gameInstance[gameID][0])
        
        gameInstance[gameID][2], gameInstance[gameID][3], \
        gameInstance[gameID][4], gameInstance[gameID][5], \
        gameInstance[gameID][6], gameInstance[gameID][7], \
        gameInstance[gameID][8], gameInstance[gameID][9] = playgame(result, gameInstance[gameID][0], \
                                                   gameInstance[gameID][1], gameInstance[gameID][2], gameInstance[gameID][3], \
                                                   gameInstance[gameID][4], gameInstance[gameID][5], gameInstance[gameID][6], \
                                                   gameInstance[gameID][7], gameInstance[gameID][8], gameInstance[gameID][9])
    




gameInstanceInit()
while True:
    gameInstancePrint(0)
    gameInstanceRun(0)













