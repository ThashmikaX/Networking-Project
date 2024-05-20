import tictactoe as ttt

X = "X"
O = "O"
EMPTY = None

board = [[X, EMPTY, X],
        [EMPTY, EMPTY, O],
        [EMPTY, EMPTY, EMPTY]]

#print(ttt.calc_items(board))

print(ttt.player(board))

# print(ttt.actions(board))

print(ttt.result(board, (0, 1)))