"""
Tic Tac Toe Player
"""

import math

X = "X"
O = "O"
EMPTY = None


def initial_state():
    """
    Returns starting state of the board.
    """
    return [[EMPTY, EMPTY, EMPTY],
            [EMPTY, EMPTY, EMPTY],
            [EMPTY, EMPTY, EMPTY]]


def player(board):
    """
    Returns player who has the next turn on a board.
    """

    count_X , count_O = calc_items(board)
    player = None

    if board == initial_state():
        return user 
    
    if count_O > count_X:
        player = "X"
    elif count_X > count_O:
        player = "O"
    else:
        player = user

    return player



def actions(board):
    """
    Returns set of all possible actions (i, j) available on the board.
    """

    actions = []
    for i in range(3):
        for j in range(3):
            if board[i][j] == EMPTY:
                actions.append((i, j))

    return actions


def result(board, action):
    """
    Returns the board that results from making move (i, j) on the board.
    """

    i, j = action
    current_player = player(board)

    if board[i][j] != EMPTY:
        raise Exception("Invalid Move")

    new_board = [row.copy() for row in board]
    new_board[i][j] = current_player

    return new_board


def winner(board):
    """
    Returns the winner of the game, if there is one.
    """

    # Check rows
    for i in range(3):
        if board[i][0] == board[i][1] == board[i][2] and board[i][0] != EMPTY:
            return board[i][0]

    # Check columns
    for i in range(3):
        if board[0][i] == board[1][i] == board[2][i] and board[0][i] != EMPTY:
            return board[0][i]

    # Check diagonals
    if board[0][0] == board[1][1] == board[2][2] and board[0][0] != EMPTY:
        return board[0][0]
    if board[0][2] == board[1][1] == board[2][0] and board[0][2] != EMPTY:
        return board[0][2]

    return None


def terminal(board):
    """
    Returns True if game is over, False otherwise.
    """

    if winner(board) is not None:
        return True

    for i in range(3):
        for j in range(3):
            if board[i][j] == EMPTY:
                return False

    return True


def utility(board):
    """
    Returns 1 if X has won the game, -1 if O has won, 0 otherwise.
    """

    if winner(board) == "X":
        return 1
    elif winner(board) == "O":
        return -1
    else:
        return 0


def minimax(board):
    """
    Returns the optimal action for the current player on the board.
    """
    raise NotImplementedError

def calc_items(board):
    """
    Retun the X and O count in the board at this instance
    
    """
    count_X, count_O = 0, 0

    for i in board:
        for j in i:
            if j == X:
                count_X += 1
            elif j == O:
                count_O += 1

    
    return (count_X, count_O)

