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
    raise NotImplementedError


def terminal(board):
    """
    Returns True if game is over, False otherwise.
    """
    return False


def utility(board):
    """
    Returns 1 if X has won the game, -1 if O has won, 0 otherwise.
    """
    raise NotImplementedError


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

