"""
Tic Tac Toe Player
"""

import math
import threading
import queue

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

    x_count = 0
    o_count = 0

    for row in board:
        for cell in row:
            if cell == X:
                x_count += 1
            elif cell == O:
                o_count += 1

    if x_count > o_count:
        return O
    else:
        return X


def actions(board):
    """
    Returns set of all possible actions (i, j) available on the board.
    """

    result = set()
    for i in range(3):
        for j in range(3):
            if board[i][j] == EMPTY:
                result.add((i, j))

    return result


def result(board, action):
    """
    Returns the board that results from making move (i, j) on the board.
    """

    i, j = action

    if i < 0 or i > 2 or j < 0 or j > 2:
        raise ValueError("Invalid action.")
    if board[i][j] != EMPTY:
        raise ValueError("Invalid action. Cell is not empty.")
    
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

    if terminal(board):
        return None

    current_player = player(board)

    if current_player == X:
        v = -math.inf
        best_move = None
        for action in actions(board):
            min_value = min_val(result(board, action))
            if min_value > v:
                v = min_value
                best_move = action
    else:
        v = math.inf
        best_move = None
        for action in actions(board):
            max_value = max_val(result(board, action))
            if max_value < v:
                v = max_value
                best_move = action

    return best_move


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


def min_val(board):
    """
    return the minimum value that can get from the current board

    """
    if terminal(board):
        return utility(board)
    
    v = math.inf
    for action in actions(board):
        v = min(v, max_val(result(board, action)))
    return v


def max_val(board):
    """
    return the maximum value that can get from the current board
    """
    
    if terminal(board):
        return utility(board)
    
    v = -math.inf
    for action in actions(board):
        v = max(v, min_val(result(board, action)))
    return v

import threading
import queue
import math

def threaded_minimax(board):
    """Returns the optimal action using threading for parallel evaluation."""
    
    if terminal(board):
        print("[MINIMAX] Game is already terminal")
        return None

    current_player = player(board)
    print(f"[MINIMAX] Finding best move for player {current_player}")
    
    possible_actions = actions(board)
    print(f"[MINIMAX] Evaluating {len(possible_actions)} moves in parallel")
    
    result_queue = queue.Queue()
    threads = []
    
    def evaluate_move(action):
        thread_id = threading.current_thread().name
        print(f"[THREAD-{thread_id}] Evaluating move {action}")
        new_board = result(board, action)
        value = min_val(new_board) if current_player == X else max_val(new_board)
        result_queue.put((action, value))
    
    for action in possible_actions:
        thread = threading.Thread(target=evaluate_move, args=(action,))
        threads.append(thread)
        thread.start()
    
    for thread in threads:
        thread.join()
    
    best_action = None
    best_value = -math.inf if current_player == X else math.inf
    results = []

    while not result_queue.empty():
        results.append(result_queue.get())
    
    print(f"[MINIMAX] Collected {len(results)} results")
    
    for action, value in results:
        if (current_player == X and value > best_value) or (current_player == O and value < best_value):
            best_value = value
            best_action = action

    print(f"[MINIMAX] Best move: {best_action} with value {best_value}")
    return best_action
