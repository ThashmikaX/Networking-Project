import tictactoe as ttt

X = "X"
O = "O"
EMPTY = None

board = [[O, X, X],
        [X, X, O],
        [O, O, O]]

#print(ttt.calc_items(board))

#print(ttt.player(board))

# print(ttt.actions(board))

#print(ttt.result(board, (0, 1)))

print(ttt.winner(board))

print(ttt.terminal(board))

print(ttt.utility(board))