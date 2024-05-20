import tictactoe as ttt

X = "X"
O = "O"
EMPTY = None

board = [[X, EMPTY, O],
        [EMPTY, EMPTY, O],
        [EMPTY, EMPTY, EMPTY]]

#print(ttt.calc_items(board))

print(ttt.actions(board))