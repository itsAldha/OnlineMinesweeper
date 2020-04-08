import random
import re
import time
from string import ascii_lowercase


def setupgrid(gridsize, start, numberofmines):
    emptygrid = [['0' for i in range(gridsize)] for i in range(gridsize)]

    mines = getmines(emptygrid, start, numberofmines)

    for i, j in mines:
        emptygrid[i][j] = 'X'

    grid = getnumbers(emptygrid)

    return (grid, mines)


def getGrid(grid):
    gridsize = len(grid)
    msg = []

    # Print left row numbers
    for i in enumerate(grid):
        row = ''
        for j in i:
            row = str(j)
            row = row[2:48]
            li = list(row.split("', '")) 
        msg.append(li)

    
    print("------------->")
    print(msg)
    print("------------->")
    return msg


def getrandomcell(grid):
    gridsize = len(grid)

    a = random.randint(0, gridsize - 1)
    b = random.randint(0, gridsize - 1)

    return (a, b)


def getneighbors(grid, rowno, colno):
    gridsize = len(grid)
    neighbors = []

    for i in range(-1, 2):
        for j in range(-1, 2):
            if i == 0 and j == 0:
                continue
            elif -1 < (rowno + i) < gridsize and -1 < (colno + j) < gridsize:
                neighbors.append((rowno + i, colno + j))

    return neighbors


def getmines(grid, start, numberofmines):
    mines = []
    neighbors = getneighbors(grid, *start)

    for i in range(numberofmines):
        cell = getrandomcell(grid)
        while cell == start or cell in mines or cell in neighbors:
            cell = getrandomcell(grid)
        mines.append(cell)

    return mines


def getnumbers(grid):
    for rowno, row in enumerate(grid):
        for colno, cell in enumerate(row):
            if cell != 'X':
                # Gets the values of the neighbors
                values = [grid[r][c] for r, c in getneighbors(grid,
                                                              rowno, colno)]
                # Counts how many are mines
                grid[rowno][colno] = str(values.count('X'))

    return grid


def showcells(grid, currgrid, rowno, colno):
    # Exit function if the cell was already shown
    if currgrid[rowno][colno] != ' ':
        return
    # Show current cell
    currgrid[rowno][colno] = grid[rowno][colno]
    # Get the neighbors if the cell is empty
    if grid[rowno][colno] == '0':
        for r, c in getneighbors(grid, rowno, colno):
            # Repeat function for each neighbor that doesn't have a flag
            if currgrid[r][c] != 'F':
                showcells(grid, currgrid, r, c)


def parseinput(inputstring, gridsize):
    cell = ()
    flag = False
    message = "Invalid cell. "

    pattern = r'([a-{}])([0-9]+)(f?)'.format(ascii_lowercase[gridsize - 1])
    validinput = re.match(pattern, inputstring)


    if validinput:
        rowno = int(validinput.group(2)) - 1
        colno = ascii_lowercase.index(validinput.group(1))
        flag = bool(validinput.group(3))

        if -1 < rowno < gridsize:
            cell = (rowno, colno)
            message = ''

    return {'cell': cell, 'flag': flag, 'message': message}



def playgame(result, gridsize, numberofmines, currgrid, grid, mines, flags, starttime, cell, flag, gameOver):

    message = result['message']
    cell = result['cell']
    flag = result['flag']

    if cell:
        print('\n\n')
        rowno, colno = cell
        currcell = currgrid[rowno][colno]
        
        if not grid:
            grid, mines = setupgrid(gridsize, cell, numberofmines)
        if not starttime:
            starttime = time.time()

        if flag:
            # Add a flag if the cell is empty
            if currcell == ' ':
                currgrid[rowno][colno] = 'F'
                flags.append(cell)
            # Remove the flag if there is one
            elif currcell == 'F':
                currgrid[rowno][colno] = ' '
                flags.remove(cell)
            else:
                message = 'Cannot put a flag there'

        # If there is a flag there, show a message
        elif cell in flags:
            message = 'There is a flag there'

        elif grid[rowno][colno] == 'X':
            print('Game Over\n')
            gameOver = True
            return currgrid, grid, mines, flags, starttime, cell, flag, gameOver, 1

        elif currcell == ' ':
            showcells(grid, currgrid, rowno, colno)

        else:
            message = "That cell is already shown"

        if set(flags) == set(mines):
            minutes, seconds = divmod(int(time.time() - starttime), 60)
            print(
                'You Win. '
                'It took you {} minutes and {} seconds.\n'.format(minutes,
                                                                  seconds))
            gameOver = True
            return currgrid, grid, mines, flags, starttime, cell, flag, gameOver, 2
    print(message)
    return currgrid, grid, mines, flags, starttime, cell, flag, gameOver, 0
 
